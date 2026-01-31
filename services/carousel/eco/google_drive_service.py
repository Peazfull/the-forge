from __future__ import annotations

from typing import Optional
import json
import io
import streamlit as st

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
except Exception:  # pragma: no cover
    service_account = None
    build = None
    MediaIoBaseUpload = None


SCOPES = ["https://www.googleapis.com/auth/drive"]


def _get_drive_service():
    if service_account is None or build is None or MediaIoBaseUpload is None:
        raise RuntimeError("google-api-python-client non installé")
    sa_path = st.secrets.get("GOOGLE_DRIVE_SA_PATH")
    sa_json = st.secrets.get("GOOGLE_DRIVE_SA_JSON")
    if sa_json:
        info = json.loads(sa_json)
        credentials = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    elif sa_path:
        credentials = service_account.Credentials.from_service_account_file(sa_path, scopes=SCOPES)
    else:
        raise RuntimeError("GOOGLE_DRIVE_SA_PATH/GOOGLE_DRIVE_SA_JSON manquant dans secrets")
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def _delete_existing(service, folder_id: str, filename: str) -> None:
    query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    for f in results.get("files", []):
        service.files().delete(fileId=f["id"]).execute()


def upload_bytes_to_drive(filename: str, data: bytes, mime_type: str) -> Optional[str]:
    service = _get_drive_service()
    folder_id = st.secrets.get("GOOGLE_DRIVE_FOLDER_ID")
    if not folder_id:
        raise RuntimeError("GOOGLE_DRIVE_FOLDER_ID manquant dans secrets")
    
    _delete_existing(service, folder_id, filename)
    
    file_metadata = {"name": filename, "parents": [folder_id]}
    media = MediaIoBaseUpload(io.BytesIO(data), mimetype=mime_type, resumable=False)
    created = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    return created.get("id")

from typing import Optional, Tuple, List, Dict

from front.components.news_source import NewsSourceConfig
from services.news_brewery.bfm_bourse_job import JobConfig, get_bfm_job
from services.news_brewery.beincrypto_job import JobConfig as BeInJobConfig, get_beincrypto_job
from services.news_brewery.boursedirect_job import JobConfig as BourseDirectJobConfig, get_boursedirect_job
from services.news_brewery.boursedirect_indices_job import (
    JobConfig as BourseDirectIndicesJobConfig,
    get_boursedirect_indices_job,
)
from services.news_brewery.boursier_economie_job import (
    JobConfig as BoursierEconomieJobConfig,
    get_boursier_economie_job,
)
from services.news_brewery.boursier_macroeconomie_job import (
    JobConfig as BoursierMacroeconomieJobConfig,
    get_boursier_macroeconomie_job,
)
from services.news_brewery.boursier_france_job import (
    JobConfig as BoursierFranceJobConfig,
    get_boursier_france_job,
)
from services.news_brewery.rss_utils import (
    fetch_beincrypto_dom_items,
    fetch_boursedirect_dom_items,
    fetch_boursier_dom_items,
    fetch_boursier_macroeconomie_dom_items,
    fetch_boursier_france_dom_items,
    fetch_dom_items,
    fetch_rss_items,
    merge_article_items,
)


def get_news_sources() -> list[NewsSourceConfig]:
    return [
        NewsSourceConfig(
            key="news",
            label="BFM Bourse",
            icon="📈",
            entry_url="https://www.tradingsat.com/actualites/",
            rss_feed_url="https://www.tradingsat.com/rssfeed.php",
            fetch_dom_items=fetch_dom_items,
            fetch_rss_items=fetch_rss_items,
            job_factory=get_bfm_job,
            job_config_class=JobConfig,
            supports_scroll=True,
            supports_headless=True,
            supports_captcha_pause=True,
            supports_firecrawl=True,
        ),
        NewsSourceConfig(
            key="bein",
            label="BeInCrypto",
            icon="₿",
            entry_url="https://fr.beincrypto.com/",
            rss_feed_url="https://fr.beincrypto.com/feed/",
            fetch_dom_items=fetch_beincrypto_dom_items,
            fetch_rss_items=fetch_rss_items,
            job_factory=get_beincrypto_job,
            job_config_class=BeInJobConfig,
            supports_scroll=False,
            supports_headless=False,
            supports_captcha_pause=False,
            supports_firecrawl=True,
        ),
        NewsSourceConfig(
            key="boursedirect",
            label="Bourse Direct",
            icon="💼",
            entry_url="https://www.boursedirect.fr/fr/actualites/categorie/marches",
            rss_feed_url="https://www.boursedirect.fr/fr/actualites/categorie/marches",
            fetch_dom_items=fetch_boursedirect_dom_items,
            fetch_rss_items=fetch_rss_items,
            job_factory=get_boursedirect_job,
            job_config_class=BourseDirectJobConfig,
            supports_scroll=False,
            supports_headless=False,
            supports_captcha_pause=False,
            supports_firecrawl=True,
        ),
        NewsSourceConfig(
            key="boursedirect_indices",
            label="Bourse Direct Indices",
            icon="📊",
            entry_url="https://www.boursedirect.fr/fr/actualites/categorie/indices",
            rss_feed_url="https://www.boursedirect.fr/fr/actualites/categorie/indices",
            fetch_dom_items=fetch_boursedirect_dom_items,
            fetch_rss_items=fetch_rss_items,
            job_factory=get_boursedirect_indices_job,
            job_config_class=BourseDirectIndicesJobConfig,
            supports_scroll=False,
            supports_headless=False,
            supports_captcha_pause=False,
            supports_firecrawl=True,
        ),
        NewsSourceConfig(
            key="boursier_economie",
            label="Boursier Économie",
            icon="💰",
            entry_url="https://www.boursier.com/actualites/economie",
            rss_feed_url="https://www.boursier.com/actualites/economie",
            fetch_dom_items=fetch_boursier_dom_items,
            fetch_rss_items=fetch_rss_items,
            job_factory=get_boursier_economie_job,
            job_config_class=BoursierEconomieJobConfig,
            supports_scroll=False,
            supports_headless=False,
            supports_captcha_pause=False,
            supports_firecrawl=True,
        ),
        NewsSourceConfig(
            key="boursier_macroeconomie",
            label="Boursier Macroéconomie",
            icon="🌍",
            entry_url="https://www.boursier.com/actualites/macroeconomie",
            rss_feed_url="https://www.boursier.com/actualites/macroeconomie",
            fetch_dom_items=fetch_boursier_macroeconomie_dom_items,
            fetch_rss_items=fetch_rss_items,
            job_factory=get_boursier_macroeconomie_job,
            job_config_class=BoursierMacroeconomieJobConfig,
            supports_scroll=False,
            supports_headless=False,
            supports_captcha_pause=False,
            supports_firecrawl=True,
        ),
        NewsSourceConfig(
            key="boursier_france",
            label="Boursier France",
            icon="🇫🇷",
            entry_url="https://www.boursier.com/actualites/france",
            rss_feed_url="https://www.boursier.com/actualites/france",
            fetch_dom_items=fetch_boursier_france_dom_items,
            fetch_rss_items=fetch_rss_items,
            job_factory=get_boursier_france_job,
            job_config_class=BoursierFranceJobConfig,
            supports_scroll=False,
            supports_headless=False,
            supports_captcha_pause=False,
            supports_firecrawl=True,
        ),
    ]


def collect_mega_urls(
    mega_hours: int = 20,
    source_keys: Optional[list[str]] = None,
) -> Tuple[List[Dict[str, str]], List[Dict[str, object]]]:
    results: list[dict] = []
    seen = set()
    status_entries: list[dict] = []
    sources = get_news_sources()

    def _should_run(source_key: str) -> bool:
        return not source_keys or source_key in source_keys

    def _record(source_key: str, source_label: str, status: str, count: int = 0, message: str = "") -> None:
        status_entries.append({
            "source_key": source_key,
            "source_label": source_label,
            "status": status,
            "count": count,
            "message": message,
        })

    def _add(source_key: str, source_label: str, items: list[dict]) -> None:
        if source_keys and source_key not in source_keys:
            return
        for item in items:
            url = item.get("url", "")
            if not url or url in seen:
                continue
            seen.add(url)
            results.append({
                "source_key": source_key,
                "source_label": source_label,
                "url": url,
                "title": item.get("title", ""),
                "label_dt": item.get("label_dt", ""),
            })

    for source in sources:
        if not _should_run(source.key):
            continue

        try:
            max_items = int(source.default_max_total)
            rss_feed = source.rss_feed_url
            mode = "last_hours"

            rss_items = source.fetch_rss_items(
                feed_url=rss_feed,
                max_items=max_items,
                mode=mode,
                hours_window=mega_hours,
                ignore_time_filter=False,
            )

            if source.supports_dom_fallback:
                dom_kwargs = {
                    "page_url": source.entry_url,
                    "max_items": max_items,
                    "mode": mode,
                    "hours_window": mega_hours,
                }
                if source.supports_firecrawl:
                    try:
                        dom_kwargs["use_firecrawl_fallback"] = True
                        dom_items = source.fetch_dom_items(**dom_kwargs)
                    except TypeError:
                        dom_kwargs.pop("use_firecrawl_fallback", None)
                        dom_items = source.fetch_dom_items(**dom_kwargs)
                else:
                    dom_items = source.fetch_dom_items(**dom_kwargs)

                items = merge_article_items(dom_items, rss_items, max_items)
            else:
                items = rss_items

            _add(source.key, source.label, items)
            _record(source.key, source.label, "ok", len(items))
        except Exception as exc:
            _record(source.key, source.label, "error", message=str(exc))

    return results, status_entries

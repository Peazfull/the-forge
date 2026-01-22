# =========================
# 🇺🇸 US — TOP ~200 MARKET CAP
# =========================

US_TOP_200 = [
    "AAPL","MSFT","NVDA","AMZN","GOOGL","GOOG","META","BRK-B","LLY","AVGO",
    "TSLA","JPM","V","UNH","XOM","MA","HD","COST","MRK","ABBV",
    "PEP","KO","ADBE","CRM","NFLX","AMD","WMT","BAC","INTC","ORCL",
    "CSCO","QCOM","TXN","ACN","LIN","MCD","TMO","DHR","AMAT","NEE",
    "PM","IBM","GE","ISRG","CAT","SPGI","RTX","NOW","GS","BLK",
    "CVX","UNP","HON","LOW","INTU","DE","MDT","ADI","LRCX","GILD",
    "BKNG","ZTS","VRTX","CI","ELV","AXP","PLD","CB","MO","MMC",
    "DUK","SO","USB","TGT","PNC","SCHW","FDX","GM","F","CL",
    "MET","AON","ICE","PGR","TRV","ALL","MS","C","COF","AIG",
    "SLB","ETN","EMR","NSC","ROP","CTAS","ECL","SRE","PSA","KMI",
    "AEP","OXY","AFL","MPC","VLO","HUM","DG","ROST","MAR","HLT",
    "IDXX","PAYX","FAST","ODFL","PCAR","MNST","EXC","XEL","WELL","DLR",
    "AMT","CCI","EQIX","PLTR","SNOW","PANW","CRWD","FTNT","DDOG","ZS",
    "MDB","NET","SHOP","SQ","PYPL","UBER","ABNB","LYFT","RIVN","LCID"
]

# =========================
# 🇫🇷 FRANCE — SBF 120
# (format Yahoo Finance : .PA)
# =========================

FR_SBF_120 = [
    "AI.PA","AIR.PA","ALO.PA","BNP.PA","CAP.PA","CS.PA","DG.PA","DSY.PA",
    "EL.PA","ENGI.PA","ERF.PA","GLE.PA","HO.PA","KER.PA","LR.PA","MC.PA",
    "ML.PA","ORA.PA","OR.PA","PUB.PA","RI.PA","RMS.PA","SAF.PA","SAN.PA",
    "SGO.PA","STM.PA","SU.PA","TTE.PA","URW.AS","VIE.PA","VIV.PA","WLN.PA",
    "ACA.PA","BN.PA","CA.PA","RNO.PA","EDF.PA","STLA","VIV.PA","FR.PA",
    "SCR.PA","BIM.PA","CO.PA","EN.PA","FGR.PA","GET.PA","ILD.PA","IPN.PA",
    "JCQ.PA","KORI.PA","MMT.PA","NEX.PA","RXL.PA","SESG.PA","SW.PA","TFI.PA",
    "UBI.PA","VK.PA","ZC.PA","AMUN.PA","CNP.PA","DIM.PA","ELIOR.PA",
    "FNAC.PA","GFC.PA","ICAD.PA","NEOEN.PA","OVH.PA","SEB.PA","SOI.PA",
    "SPIE.PA","TEP.PA","TRI.PA","VRLA.PA","XPO.PA"
]

# =========================
# 🇪🇺 EUROPE — TOP ~200
# (STOXX-style, Yahoo symbols)
# =========================

EU_TOP_200 = [
    # 🇩🇪 Allemagne
    "SAP.DE","SIE.DE","DTE.DE","ALV.DE","BAS.DE","BAYN.DE","BMW.DE","VOW.DE",
    "MBG.DE","IFX.DE","LIN.DE","MUV2.DE","ADS.DE","DB1.DE","RWE.DE",

    # 🇫🇷 France
    "MC.PA","OR.PA","TTE.PA","SAN.PA","BNP.PA","AIR.PA","CS.PA","ENGI.PA",
    "DG.PA","KER.PA","RMS.PA","SGO.PA","SU.PA","VIE.PA",

    # 🇳🇱 Pays-Bas
    "ASML.AS","INGA.AS","PHIA.AS","ADYEN.AS","PRX.AS","NN.AS","DSM.AS",

    # 🇪🇸 Espagne
    "SAN.MC","IBE.MC","ITX.MC","BBVA.MC","FER.MC","ACS.MC","REP.MC",

    # 🇮🇹 Italie
    "ENEL.MI","ENI.MI","ISP.MI","UCG.MI","STM.PA","PRY.MI","G.MI",

    # 🇨🇭 Suisse
    "NESN.SW","ROG.SW","NOVN.SW","ZURN.SW","CSGN.SW","UBSG.SW",

    # 🇬🇧 UK
    "SHEL.L","AZN.L","BP.L","HSBA.L","ULVR.L","RIO.L","GSK.L","BATS.L",
    "REL.L","LSEG.L","NG.L","DGE.L",

    # 🇸🇪 / 🇩🇰 / 🇳🇴
    "NOVO-B.CO","DSV.CO","MAERSK-B.CO","EQNR.OL","VOLV-B.ST","ERIC-B.ST",

    # 🇧🇪 / 🇦🇹 / 🇫🇮
    "ABI.BR","UCB.BR","KBC.BR","OMV.VI","NDA-FI.HE"
]

# =========================
# 🪙 CRYPTO — TOP 30
# (format Yahoo Finance : -USD)
# =========================

CRYPTO_TOP_30 = [
    "BTC-USD","ETH-USD","BNB-USD","SOL-USD","XRP-USD","ADA-USD","AVAX-USD",
    "DOGE-USD","DOT-USD","MATIC-USD","LINK-USD","UNI-USD","ATOM-USD","LTC-USD",
    "BCH-USD","XLM-USD","ALGO-USD","VET-USD","ICP-USD","FIL-USD","HBAR-USD",
    "APT-USD","NEAR-USD","ARB-USD","OP-USD","STX-USD","INJ-USD","TIA-USD",
    "SUI-USD","TAO-USD"
]

# =========================
# 📊 INDICES MAJEURS
# =========================

INDICES = [
    "^GSPC",      # S&P 500
    "^DJI",       # Dow Jones
    "^IXIC",      # NASDAQ
    "^RUT",       # Russell 2000
    "^FCHI",      # CAC 40
    "^STOXX50E",  # Euro STOXX 50
    "^GDAXI",     # DAX
    "^FTSE",      # FTSE 100
    "^N225",      # Nikkei 225
    "^HSI",       # Hang Seng
]

# =========================
# 🛢️ COMMODITIES
# =========================

COMMODITIES = [
    "GC=F",   # Gold
    "SI=F",   # Silver
    "CL=F",   # Crude Oil WTI
    "BZ=F",   # Brent Crude
    "NG=F",   # Natural Gas
    "HG=F",   # Copper
    "PL=F",   # Platinum
    "PA=F",   # Palladium
]

# =========================
# 📖 MAPPING SYMBOL → NAME
# =========================

SYMBOL_TO_NAME = {
    # 🇺🇸 US
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "NVIDIA", "AMZN": "Amazon",
    "GOOGL": "Alphabet (Class A)", "GOOG": "Alphabet (Class C)", "META": "Meta Platforms",
    "BRK-B": "Berkshire Hathaway", "LLY": "Eli Lilly", "AVGO": "Broadcom", "TSLA": "Tesla",
    "JPM": "JPMorgan Chase", "V": "Visa", "UNH": "UnitedHealth Group", "XOM": "Exxon Mobil",
    "MA": "Mastercard", "HD": "Home Depot", "COST": "Costco", "MRK": "Merck & Co", "ABBV": "AbbVie",
    "PEP": "PepsiCo", "KO": "Coca-Cola", "ADBE": "Adobe", "CRM": "Salesforce", "NFLX": "Netflix",
    "AMD": "Advanced Micro Devices", "WMT": "Walmart", "BAC": "Bank of America", "INTC": "Intel",
    "ORCL": "Oracle", "CSCO": "Cisco", "QCOM": "Qualcomm", "TXN": "Texas Instruments",
    "ACN": "Accenture", "LIN": "Linde", "MCD": "McDonald's", "TMO": "Thermo Fisher Scientific",
    "DHR": "Danaher", "AMAT": "Applied Materials", "NEE": "NextEra Energy",
    "PM": "Philip Morris International", "IBM": "IBM", "GE": "General Electric",
    "ISRG": "Intuitive Surgical", "CAT": "Caterpillar", "SPGI": "S&P Global",
    "RTX": "RTX Corporation", "NOW": "ServiceNow", "GS": "Goldman Sachs", "BLK": "BlackRock",
    "CVX": "Chevron", "UNP": "Union Pacific", "HON": "Honeywell", "LOW": "Lowe's",
    "INTU": "Intuit", "DE": "Deere & Company", "MDT": "Medtronic", "ADI": "Analog Devices",
    "LRCX": "Lam Research", "GILD": "Gilead Sciences", "BKNG": "Booking Holdings", "ZTS": "Zoetis",
    "VRTX": "Vertex Pharmaceuticals", "CI": "Cigna", "ELV": "Elevance Health",
    "AXP": "American Express", "PLD": "Prologis", "CB": "Chubb", "MO": "Altria",
    "MMC": "Marsh McLennan", "DUK": "Duke Energy", "SO": "Southern Company", "USB": "U.S. Bancorp",
    "TGT": "Target", "PNC": "PNC Financial", "SCHW": "Charles Schwab", "FDX": "FedEx",
    "GM": "General Motors", "F": "Ford", "CL": "Colgate-Palmolive", "MET": "MetLife",
    "AON": "Aon", "ICE": "Intercontinental Exchange", "PGR": "Progressive", "TRV": "Travelers",
    "ALL": "Allstate", "MS": "Morgan Stanley", "C": "Citigroup", "COF": "Capital One",
    "AIG": "American International Group", "SLB": "Schlumberger", "ETN": "Eaton",
    "EMR": "Emerson Electric", "NSC": "Norfolk Southern", "ROP": "Roper Technologies",
    "CTAS": "Cintas", "ECL": "Ecolab", "SRE": "Sempra Energy", "PSA": "Public Storage",
    "KMI": "Kinder Morgan", "AEP": "American Electric Power", "OXY": "Occidental Petroleum",
    "AFL": "Aflac", "MPC": "Marathon Petroleum", "VLO": "Valero Energy", "HUM": "Humana",
    "DG": "Dollar General", "ROST": "Ross Stores", "MAR": "Marriott", "HLT": "Hilton",
    "IDXX": "IDEXX Laboratories", "PAYX": "Paychex", "FAST": "Fastenal",
    "ODFL": "Old Dominion Freight Line", "PCAR": "PACCAR", "MNST": "Monster Beverage",
    "EXC": "Exelon", "XEL": "Xcel Energy", "WELL": "Welltower", "DLR": "Digital Realty",
    "AMT": "American Tower", "CCI": "Crown Castle", "EQIX": "Equinix", "PLTR": "Palantir",
    "SNOW": "Snowflake", "PANW": "Palo Alto Networks", "CRWD": "CrowdStrike", "FTNT": "Fortinet",
    "DDOG": "Datadog", "ZS": "Zscaler", "MDB": "MongoDB", "NET": "Cloudflare",
    "SHOP": "Shopify", "SQ": "Block", "PYPL": "PayPal", "UBER": "Uber", "ABNB": "Airbnb",
    "LYFT": "Lyft", "RIVN": "Rivian", "LCID": "Lucid Motors",
    
    # 🇫🇷 France
    "AI.PA": "Air Liquide", "AIR.PA": "Airbus", "ALO.PA": "Alstom", "BNP.PA": "BNP Paribas",
    "CAP.PA": "Capgemini", "CS.PA": "AXA", "DG.PA": "Vinci", "DSY.PA": "Dassault Systèmes",
    "EL.PA": "EssilorLuxottica", "ENGI.PA": "Engie", "GLE.PA": "Société Générale",
    "HO.PA": "Thales", "KER.PA": "Kering", "MC.PA": "LVMH", "ML.PA": "Michelin",
    "ORA.PA": "Orange", "OR.PA": "L'Oréal", "PUB.PA": "Publicis", "RI.PA": "Pernod Ricard",
    "RMS.PA": "Hermès", "SAF.PA": "Safran", "SAN.PA": "Sanofi", "SGO.PA": "Saint-Gobain",
    "STM.PA": "STMicroelectronics", "SU.PA": "Schneider Electric", "TTE.PA": "TotalEnergies",
    "VIE.PA": "Veolia", "VIV.PA": "Vivendi", "WLN.PA": "Worldline", "ACA.PA": "Crédit Agricole",
    "BN.PA": "Danone", "CA.PA": "Carrefour", "RNO.PA": "Renault", "EDF.PA": "EDF",
    "STLA": "Stellantis", "FR.PA": "Valeo", "BIM.PA": "Bureau Veritas", "CO.PA": "Casino",
    "EN.PA": "Bouygues", "GET.PA": "Getlink", "IPN.PA": "Ipsen", "UBI.PA": "Ubisoft",
    "AMUN.PA": "Amundi", "CNP.PA": "CNP Assurances", "FNAC.PA": "Fnac Darty",
    "NEOEN.PA": "Neoen", "OVH.PA": "OVHcloud", "SEB.PA": "Groupe SEB", "SPIE.PA": "SPIE",
    
    # 🇪🇺 Europe
    "SAP.DE": "SAP", "SIE.DE": "Siemens", "DTE.DE": "Deutsche Telekom", "ALV.DE": "Allianz",
    "BAS.DE": "BASF", "BAYN.DE": "Bayer", "BMW.DE": "BMW", "VOW.DE": "Volkswagen",
    "MBG.DE": "Mercedes-Benz Group", "IFX.DE": "Infineon", "LIN.DE": "Linde",
    "MUV2.DE": "Munich Re", "ADS.DE": "Adidas", "DB1.DE": "Deutsche Börse", "RWE.DE": "RWE",
    "ASML.AS": "ASML", "INGA.AS": "ING Group", "PHIA.AS": "Philips", "ADYEN.AS": "Adyen",
    "PRX.AS": "Prosus", "NN.AS": "NN Group", "DSM.AS": "DSM-Firmenich",
    "NESN.SW": "Nestlé", "ROG.SW": "Roche", "NOVN.SW": "Novartis",
    "ZURN.SW": "Zurich Insurance", "UBSG.SW": "UBS", "SHEL.L": "Shell",
    "AZN.L": "AstraZeneca", "BP.L": "BP", "HSBA.L": "HSBC", "ULVR.L": "Unilever",
    "RIO.L": "Rio Tinto", "GSK.L": "GSK", "NOVO-B.CO": "Novo Nordisk", "DSV.CO": "DSV",
    "MAERSK-B.CO": "Maersk", "EQNR.OL": "Equinor", "VOLV-B.ST": "Volvo",
    "ERIC-B.ST": "Ericsson", "ABI.BR": "AB InBev", "UCB.BR": "UCB", "KBC.BR": "KBC Group",
    
    # 🪙 Crypto
    "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "BNB-USD": "BNB", "SOL-USD": "Solana",
    "XRP-USD": "XRP", "ADA-USD": "Cardano", "AVAX-USD": "Avalanche", "DOGE-USD": "Dogecoin",
    "DOT-USD": "Polkadot", "MATIC-USD": "Polygon", "LINK-USD": "Chainlink",
    "UNI-USD": "Uniswap", "ATOM-USD": "Cosmos", "LTC-USD": "Litecoin",
    "BCH-USD": "Bitcoin Cash", "XLM-USD": "Stellar", "ALGO-USD": "Algorand",
    "VET-USD": "VeChain", "ICP-USD": "Internet Computer", "FIL-USD": "Filecoin",
    "HBAR-USD": "Hedera", "APT-USD": "Aptos", "NEAR-USD": "Near Protocol",
    "ARB-USD": "Arbitrum", "OP-USD": "Optimism", "STX-USD": "Stacks",
    "INJ-USD": "Injective", "TIA-USD": "Celestia", "SUI-USD": "Sui", "TAO-USD": "Bittensor",
    
    # 📊 Indices
    "^GSPC": "S&P 500", "^DJI": "Dow Jones Industrial Average", "^IXIC": "NASDAQ Composite",
    "^RUT": "Russell 2000", "^FCHI": "CAC 40", "^STOXX50E": "Euro STOXX 50",
    "^GDAXI": "DAX 40", "^FTSE": "FTSE 100", "^SSMI": "SMI (Switzerland)",
    "^IBEX": "IBEX 35 (Spain)", "^FTMIB": "FTSE MIB (Italy)",
    "^N225": "Nikkei 225", "^HSI": "Hang Seng Index",

    # 🇪🇺 Obligations 10Y
    "FR10Y=RR": "France 10Y",
    "DE10Y=RR": "Germany 10Y",
    "ES10Y=RR": "Spain 10Y",
    "IT10Y=RR": "Italy 10Y",
    "GB10Y=RR": "UK 10Y",
    
    # 🛢️ Commodities
    "GC=F": "Gold", "SI=F": "Silver", "CL=F": "WTI Crude Oil", "BZ=F": "Brent Crude",
    "NG=F": "Natural Gas", "HG=F": "Copper", "PL=F": "Platinum", "PA=F": "Palladium",

    # 💱 FX (EUR pairs)
    "EURUSD=X": "EUR/USD", "EURGBP=X": "EUR/GBP", "EURJPY=X": "EUR/JPY",
    "EURCHF=X": "EUR/CHF", "EURAUD=X": "EUR/AUD", "EURCAD=X": "EUR/CAD",
    "EURNZD=X": "EUR/NZD", "EURNOK=X": "EUR/NOK", "EURSEK=X": "EUR/SEK",
    "EURDKK=X": "EUR/DKK", "EURPLN=X": "EUR/PLN", "EURHUF=X": "EUR/HUF",
    "EURCZK=X": "EUR/CZK",
}

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
# 🇪🇺 INDICES EUROPÉENS
# =========================

EU_INDICES = [
    "^FCHI",      # CAC 40
    "^STOXX50E",  # Euro STOXX 50
    "^GDAXI",     # DAX
    "^FTSE",      # FTSE 100
    "^SSMI",      # SMI (Switzerland)
    "^IBEX",      # IBEX 35 (Spain)
    "^FTMIB",     # FTSE MIB (Italy)
]

# =========================
# 🇪🇺 OBLIGATIONS 10 ANS
# =========================

EU_BONDS_10Y = [
    "FR10Y=RR",  # France 10Y
    "DE10Y=RR",  # Germany 10Y
    "ES10Y=RR",  # Spain 10Y
    "IT10Y=RR",  # Italy 10Y
    "GB10Y=RR",  # UK 10Y
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

# =========================
# 🛢️ COMMODITIES MAJEURES
# =========================

COMMODITIES_MAJOR = [
    "GC=F",  # Gold
    "SI=F",  # Silver
    "CL=F",  # Crude Oil WTI
    "BZ=F",  # Brent Crude
    "NG=F",  # Natural Gas
    "HG=F",  # Copper
]

# =========================
# 🪙 CRYPTO MAJEURES
# =========================

CRYPTO_MAJOR = [
    "BTC-USD",  # Bitcoin
    "ETH-USD",  # Ethereum
    "BNB-USD",  # BNB
    "SOL-USD",  # Solana
    "XRP-USD",  # XRP
]

# =========================
# 💱 PAIRES EUR (EUROPE)
# =========================

EU_FX_PAIRS = [
    "EURUSD=X",
    "EURGBP=X",
    "EURJPY=X",
    "EURCHF=X",
    "EURAUD=X",
    "EURCAD=X",
    "EURNZD=X",
]

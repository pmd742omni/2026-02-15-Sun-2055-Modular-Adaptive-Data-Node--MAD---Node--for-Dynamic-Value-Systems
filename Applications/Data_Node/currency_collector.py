"""
Modular Adaptive Data Node (MAD-Node) - Global Currency and Cryptocurrency Catalog Collector
Maintains authoritative ISO 4217 fiat currencies and major cryptocurrency registries
with continuous online periodic ingestion and offline fallback for collision prevention.
"""

import json
import datetime
import urllib.request
import urllib.error
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("madn.currency_collector")

# Authoritative ISO 4217 World Sovereign Currencies & Precious Metal Standards
GLOBAL_ISO_FIAT_CURRENCIES = [
    {"code": "USD", "name": "United States Dollar", "symbol": "$", "category": "fiat", "country_or_issuer": "United States", "is_iso4217": 1, "default_decimals": 2},
    {"code": "ZAR", "name": "South African Rand", "symbol": "R", "category": "fiat", "country_or_issuer": "South Africa (CMA)", "is_iso4217": 1, "default_decimals": 2},
    {"code": "ZWG", "name": "Zimbabwe Gold (ZiG)", "symbol": "ZiG", "category": "gold_backed", "country_or_issuer": "Zimbabwe (RBZ)", "is_iso4217": 1, "default_decimals": 2},
    {"code": "EUR", "name": "Euro", "symbol": "€", "category": "fiat", "country_or_issuer": "Eurozone", "is_iso4217": 1, "default_decimals": 2},
    {"code": "GBP", "name": "British Pound Sterling", "symbol": "£", "category": "fiat", "country_or_issuer": "United Kingdom", "is_iso4217": 1, "default_decimals": 2},
    {"code": "BWP", "name": "Botswana Pula", "symbol": "P", "category": "fiat", "country_or_issuer": "Botswana", "is_iso4217": 1, "default_decimals": 2},
    {"code": "JPY", "name": "Japanese Yen", "symbol": "¥", "category": "fiat", "country_or_issuer": "Japan", "is_iso4217": 1, "default_decimals": 0},
    {"code": "CNY", "name": "Chinese Yuan Renminbi", "symbol": "¥", "category": "fiat", "country_or_issuer": "China", "is_iso4217": 1, "default_decimals": 2},
    {"code": "INR", "name": "Indian Rupee", "symbol": "₹", "category": "fiat", "country_or_issuer": "India", "is_iso4217": 1, "default_decimals": 2},
    {"code": "CAD", "name": "Canadian Dollar", "symbol": "CA$", "category": "fiat", "country_or_issuer": "Canada", "is_iso4217": 1, "default_decimals": 2},
    {"code": "AUD", "name": "Australian Dollar", "symbol": "A$", "category": "fiat", "country_or_issuer": "Australia", "is_iso4217": 1, "default_decimals": 2},
    {"code": "CHF", "name": "Swiss Franc", "symbol": "CHF", "category": "fiat", "country_or_issuer": "Switzerland", "is_iso4217": 1, "default_decimals": 2},
    {"code": "NGN", "name": "Nigerian Naira", "symbol": "₦", "category": "fiat", "country_or_issuer": "Nigeria", "is_iso4217": 1, "default_decimals": 2},
    {"code": "KES", "name": "Kenyan Shilling", "symbol": "KSh", "category": "fiat", "country_or_issuer": "Kenya", "is_iso4217": 1, "default_decimals": 2},
    {"code": "GHS", "name": "Ghanaian Cedi", "symbol": "GH₵", "category": "fiat", "country_or_issuer": "Ghana", "is_iso4217": 1, "default_decimals": 2},
    {"code": "ZMW", "name": "Zambian Kwacha", "symbol": "ZK", "category": "fiat", "country_or_issuer": "Zambia", "is_iso4217": 1, "default_decimals": 2},
    {"code": "MZN", "name": "Mozambican Metical", "symbol": "MT", "category": "fiat", "country_or_issuer": "Mozambique", "is_iso4217": 1, "default_decimals": 2},
    {"code": "NAD", "name": "Namibian Dollar", "symbol": "N$", "category": "fiat", "country_or_issuer": "Namibia", "is_iso4217": 1, "default_decimals": 2},
    {"code": "SZL", "name": "Eswatini Lilangeni", "symbol": "E", "category": "fiat", "country_or_issuer": "Eswatini", "is_iso4217": 1, "default_decimals": 2},
    {"code": "LSL", "name": "Lesotho Loti", "symbol": "L", "category": "fiat", "country_or_issuer": "Lesotho", "is_iso4217": 1, "default_decimals": 2},
    {"code": "MWK", "name": "Malawian Kwacha", "symbol": "MK", "category": "fiat", "country_or_issuer": "Malawi", "is_iso4217": 1, "default_decimals": 2},
    {"code": "TZS", "name": "Tanzanian Shilling", "symbol": "TSh", "category": "fiat", "country_or_issuer": "Tanzania", "is_iso4217": 1, "default_decimals": 2},
    {"code": "UGX", "name": "Ugandan Shilling", "symbol": "USh", "category": "fiat", "country_or_issuer": "Uganda", "is_iso4217": 1, "default_decimals": 0},
    {"code": "RWF", "name": "Rwandan Franc", "symbol": "FRw", "category": "fiat", "country_or_issuer": "Rwanda", "is_iso4217": 1, "default_decimals": 0},
    {"code": "ETB", "name": "Ethiopian Birr", "symbol": "Br", "category": "fiat", "country_or_issuer": "Ethiopia", "is_iso4217": 1, "default_decimals": 2},
    {"code": "EGP", "name": "Egyptian Pound", "symbol": "E£", "category": "fiat", "country_or_issuer": "Egypt", "is_iso4217": 1, "default_decimals": 2},
    {"code": "AED", "name": "United Arab Emirates Dirham", "symbol": "د.إ", "category": "fiat", "country_or_issuer": "United Arab Emirates", "is_iso4217": 1, "default_decimals": 2},
    {"code": "SAR", "name": "Saudi Riyal", "symbol": "﷼", "category": "fiat", "country_or_issuer": "Saudi Arabia", "is_iso4217": 1, "default_decimals": 2},
    {"code": "BRL", "name": "Brazilian Real", "symbol": "R$", "category": "fiat", "country_or_issuer": "Brazil", "is_iso4217": 1, "default_decimals": 2},
    {"code": "RUB", "name": "Russian Ruble", "symbol": "₽", "category": "fiat", "country_or_issuer": "Russia", "is_iso4217": 1, "default_decimals": 2},
    {"code": "MXN", "name": "Mexican Peso", "symbol": "Mex$", "category": "fiat", "country_or_issuer": "Mexico", "is_iso4217": 1, "default_decimals": 2},
    {"code": "SGD", "name": "Singapore Dollar", "symbol": "S$", "category": "fiat", "country_or_issuer": "Singapore", "is_iso4217": 1, "default_decimals": 2},
    {"code": "HKD", "name": "Hong Kong Dollar", "symbol": "HK$", "category": "fiat", "country_or_issuer": "Hong Kong", "is_iso4217": 1, "default_decimals": 2},
    {"code": "NZD", "name": "New Zealand Dollar", "symbol": "NZ$", "category": "fiat", "country_or_issuer": "New Zealand", "is_iso4217": 1, "default_decimals": 2},
    {"code": "SEK", "name": "Swedish Krona", "symbol": "kr", "category": "fiat", "country_or_issuer": "Sweden", "is_iso4217": 1, "default_decimals": 2},
    {"code": "NOK", "name": "Norwegian Krone", "symbol": "kr", "category": "fiat", "country_or_issuer": "Norway", "is_iso4217": 1, "default_decimals": 2},
    {"code": "DKK", "name": "Danish Krone", "symbol": "kr", "category": "fiat", "country_or_issuer": "Denmark", "is_iso4217": 1, "default_decimals": 2},
    {"code": "PLN", "name": "Polish Zloty", "symbol": "zł", "category": "fiat", "country_or_issuer": "Poland", "is_iso4217": 1, "default_decimals": 2},
    {"code": "TRY", "name": "Turkish Lira", "symbol": "₺", "category": "fiat", "country_or_issuer": "Turkey", "is_iso4217": 1, "default_decimals": 2},
    {"code": "KRW", "name": "South Korean Won", "symbol": "₩", "category": "fiat", "country_or_issuer": "South Korea", "is_iso4217": 1, "default_decimals": 0},
    {"code": "IDR", "name": "Indonesian Rupiah", "symbol": "Rp", "category": "fiat", "country_or_issuer": "Indonesia", "is_iso4217": 1, "default_decimals": 2},
    {"code": "MYR", "name": "Malaysian Ringgit", "symbol": "RM", "category": "fiat", "country_or_issuer": "Malaysia", "is_iso4217": 1, "default_decimals": 2},
    {"code": "THB", "name": "Thai Baht", "symbol": "฿", "category": "fiat", "country_or_issuer": "Thailand", "is_iso4217": 1, "default_decimals": 2},
    {"code": "PHP", "name": "Philippine Peso", "symbol": "₱", "category": "fiat", "country_or_issuer": "Philippines", "is_iso4217": 1, "default_decimals": 2},
    {"code": "VND", "name": "Vietnamese Dong", "symbol": "₫", "category": "fiat", "country_or_issuer": "Vietnam", "is_iso4217": 1, "default_decimals": 0},
    {"code": "ILS", "name": "Israeli New Shekel", "symbol": "₪", "category": "fiat", "country_or_issuer": "Israel", "is_iso4217": 1, "default_decimals": 2},
    {"code": "CLP", "name": "Chilean Peso", "symbol": "CLP$", "category": "fiat", "country_or_issuer": "Chile", "is_iso4217": 1, "default_decimals": 0},
    {"code": "COP", "name": "Colombian Peso", "symbol": "COL$", "category": "fiat", "country_or_issuer": "Colombia", "is_iso4217": 1, "default_decimals": 2},
    {"code": "PEN", "name": "Peruvian Sol", "symbol": "S/.", "category": "fiat", "country_or_issuer": "Peru", "is_iso4217": 1, "default_decimals": 2},
    {"code": "XAU", "name": "Gold Troy Ounce", "symbol": "Au", "category": "commodity", "country_or_issuer": "International Precious Metals", "is_iso4217": 1, "default_decimals": 4},
    {"code": "XAG", "name": "Silver Troy Ounce", "symbol": "Ag", "category": "commodity", "country_or_issuer": "International Precious Metals", "is_iso4217": 1, "default_decimals": 4}
]

# Major Cryptocurrencies & Digital Reserve Assets
GLOBAL_CRYPTOCURRENCIES = [
    {"code": "BTC", "name": "Bitcoin", "symbol": "₿", "category": "crypto", "country_or_issuer": "Bitcoin Network", "is_iso4217": 0, "default_decimals": 8},
    {"code": "ETH", "name": "Ethereum", "symbol": "Ξ", "category": "crypto", "country_or_issuer": "Ethereum Foundation", "is_iso4217": 0, "default_decimals": 18},
    {"code": "SOL", "name": "Solana", "symbol": "◎", "category": "crypto", "country_or_issuer": "Solana Network", "is_iso4217": 0, "default_decimals": 9},
    {"code": "USDT", "name": "Tether USD", "symbol": "₮", "category": "stablecoin", "country_or_issuer": "Tether Operations", "is_iso4217": 0, "default_decimals": 6},
    {"code": "USDC", "name": "USD Coin", "symbol": "USDC", "category": "stablecoin", "country_or_issuer": "Circle / Centre", "is_iso4217": 0, "default_decimals": 6},
    {"code": "BNB", "name": "BNB Chain Token", "symbol": "BNB", "category": "crypto", "country_or_issuer": "BNB Chain", "is_iso4217": 0, "default_decimals": 18},
    {"code": "XRP", "name": "XRP Ledger", "symbol": "XRP", "category": "crypto", "country_or_issuer": "Ripple Labs", "is_iso4217": 0, "default_decimals": 6},
    {"code": "ADA", "name": "Cardano", "symbol": "₳", "category": "crypto", "country_or_issuer": "Cardano Foundation", "is_iso4217": 0, "default_decimals": 6},
    {"code": "DOGE", "name": "Dogecoin", "symbol": "Ð", "category": "crypto", "country_or_issuer": "Dogecoin Open Source", "is_iso4217": 0, "default_decimals": 8},
    {"code": "TRX", "name": "TRON", "symbol": "TRX", "category": "crypto", "country_or_issuer": "TRON DAO", "is_iso4217": 0, "default_decimals": 6},
    {"code": "AVAX", "name": "Avalanche", "symbol": "AVAX", "category": "crypto", "country_or_issuer": "Ava Labs", "is_iso4217": 0, "default_decimals": 18},
    {"code": "DOT", "name": "Polkadot", "symbol": "DOT", "category": "crypto", "country_or_issuer": "Web3 Foundation", "is_iso4217": 0, "default_decimals": 10},
    {"code": "MATIC", "name": "Polygon (POL)", "symbol": "POL", "category": "crypto", "country_or_issuer": "Polygon Labs", "is_iso4217": 0, "default_decimals": 18},
    {"code": "LINK", "name": "Chainlink", "symbol": "LINK", "category": "crypto", "country_or_issuer": "Chainlink Labs", "is_iso4217": 0, "default_decimals": 18},
    {"code": "DAI", "name": "Dai Stablecoin", "symbol": "DAI", "category": "stablecoin", "country_or_issuer": "MakerDAO / Sky", "is_iso4217": 0, "default_decimals": 18},
    {"code": "LTC", "name": "Litecoin", "symbol": "Ł", "category": "crypto", "country_or_issuer": "Litecoin Foundation", "is_iso4217": 0, "default_decimals": 8},
    {"code": "BCH", "name": "Bitcoin Cash", "symbol": "BCH", "category": "crypto", "country_or_issuer": "Bitcoin Cash", "is_iso4217": 0, "default_decimals": 8},
    {"code": "XLM", "name": "Stellar Lumens", "symbol": "XLM", "category": "crypto", "country_or_issuer": "Stellar Development Foundation", "is_iso4217": 0, "default_decimals": 7},
    {"code": "ATOM", "name": "Cosmos Hub", "symbol": "ATOM", "category": "crypto", "country_or_issuer": "Interchain Foundation", "is_iso4217": 0, "default_decimals": 6},
    {"code": "XMR", "name": "Monero", "symbol": "ɱ", "category": "crypto", "country_or_issuer": "Monero Community", "is_iso4217": 0, "default_decimals": 12},
    {"code": "NEAR", "name": "NEAR Protocol", "symbol": "NEAR", "category": "crypto", "country_or_issuer": "NEAR Foundation", "is_iso4217": 0, "default_decimals": 24},
    {"code": "UNI", "name": "Uniswap", "symbol": "UNI", "category": "crypto", "country_or_issuer": "Uniswap Labs", "is_iso4217": 0, "default_decimals": 18},
    {"code": "TON", "name": "The Open Network", "symbol": "TON", "category": "crypto", "country_or_issuer": "TON Foundation", "is_iso4217": 0, "default_decimals": 9}
]

def get_complete_global_catalog() -> List[Dict[str, Any]]:
    """Returns combined authoritative list of world fiat and cryptocurrencies."""
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    catalog = []
    
    for item in GLOBAL_ISO_FIAT_CURRENCIES:
        c = dict(item)
        c["last_updated_utc"] = now_utc
        catalog.append(c)
        
    for item in GLOBAL_CRYPTOCURRENCIES:
        c = dict(item)
        c["last_updated_utc"] = now_utc
        catalog.append(c)
        
    return catalog

def fetch_online_fiat_updates(timeout_sec: float = 2.0) -> List[Dict[str, Any]]:
    """Fetches live online open currency list from open.er-api.com if internet connection is active."""
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        req = urllib.request.Request("https://open.er-api.com/v6/latest/USD", headers={"User-Agent": "MADN-DataNode-Collector/1.0"})
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                rates = data.get("rates", {})
                discovered = []
                for code, rate in rates.items():
                    discovered.append({
                        "code": code.upper(),
                        "name": f"{code.upper()} Currency",
                        "symbol": code.upper(),
                        "category": "fiat",
                        "country_or_issuer": "Global Open Currency Registry",
                        "is_iso4217": 1,
                        "default_decimals": 2,
                        "rate_to_usd": rate,
                        "last_updated_utc": now_utc
                    })
                return discovered
    except Exception as e:
        logger.debug(f"Online fiat fetch bypassed (air-gapped or offline): {e}")
    return []

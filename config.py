# --- START OF FILE config.py (Enhanced for Automation) ---

import datetime
import os

# --- API & Authentication ---
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
CLIENT_SECRETS_FILE = "secret.json"
TOKEN_FILE = "token.pickle"
PLAYLIST_ID_FILE = "playlist_id.txt"

# --- Email Configuration ---
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL", "daddyfandango@gmail.com")

# --- Logging Configuration ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "data/logs/noisesignal.log")

# --- Automation Settings ---
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "300"))  # 5 minutes
EXECUTION_TIMEOUT = int(os.getenv("EXECUTION_TIMEOUT", "3600"))  # 1 hour

# --- Search Strategy Parameters ---
NUM_RANDOM_REGIONS_TO_SEARCH = 15
RESULTS_PER_SEARCH_TASK = 50

# The original, high-quality search queries
BASE_SEARCH_QUERIES = [
    '("official music video" | "official audio" | "[omv]") -remix -cover -lyrics',
    '"official" -cover -remix -lyrics -trailer -teaser',
    '"unsigned artist" | "emerging artist" | "independent artist"',
    '"music by" "provided to youtube by"'
]

# --- Filtering & Scoring Parameters ---
DAYS_SINCE_PUBLISHED = 30 
PUBLISHED_AFTER = (datetime.datetime.now() - datetime.timedelta(days=DAYS_SINCE_PUBLISHED)).isoformat("T") + "Z"

FINAL_PLAYLIST_SIZE = 25

MIN_VIEW_COUNT = 250
MAX_VIEW_COUNT = 400000 
MIN_SUBSCRIBER_COUNT = 50
MAX_SUBSCRIBER_COUNT = 100000 
DEFAULT_POPULATION = 50 

NEGATIVE_KEYWORDS = [
    "compilation", "mix", "playlist", "top 10", "reaction", "interview", "podcast", "tutorial", "how to", "vlog", "gaming", "asmr", "audiobook",
    "full album", "live performance", "cover", "tribute", "rave party", "rehearsal", "lyrics", "lyric video", "type beat", "instrumental", "prod. by"
]

# --- Playlist Details ---
PLAYLIST_TITLE = "Global Emerging Tracks"
PLAYLIST_DESCRIPTION = (
    "A playlist of trending, underground music from around the globe, updated weekly. "
    "Discovered by a Python script."
)

# The full country list for scoring is still needed.
COUNTRY_POPULATIONS = { "AF": 39, "AX": 0.03, "AL": 3, "DZ": 44, "AS": 0.05, "AD": 0.08, "AO": 33, "AI": 0.015, "AQ": 0.001, "AG": 0.1, "AR": 45, "AM": 3, "AW": 0.1, "AU": 26, "AT": 9, "AZ": 10, "BS": 0.4, "BH": 1.7, "BD": 166, "BB": 0.3, "BY": 9, "BE": 11, "BZ": 0.4, "BJ": 12, "BM": 0.06, "BT": 0.8, "BO": 12, "BA": 3, "BW": 2, "BR": 213, "IO": 0.004, "VG": 0.03, "BN": 0.4, "BG": 7, "BF": 22, "BI": 12, "KH": 17, "CM": 27, "CA": 38, "CV": 0.6, "KY": 0.07, "CF": 5, "TD": 17, "CL": 19, "CN": 1441, "CX": 0.002, "CC": 0.0006, "CO": 51, "KM": 0.9, "CK": 0.017, "CR": 5, "HR": 4, "CU": 11, "CW": 0.16, "CY": 1, "CZ": 11, "CD": 89, "DK": 6, "DJ": 1, "DM": 0.07, "DO": 11, "TL": 1, "EC": 18, "EG": 104, "SV": 6, "GQ": 1, "ER": 3, "EE": 1, "ET": 115, "FK": 0.003, "FO": 0.05, "FJ": 0.9, "FI": 6, "FR": 65, "GF": 0.3, "PF": 0.3, "GA": 2, "GM": 2, "GE": 4, "DE": 83, "GH": 32, "GI": 0.03, "GR": 10, "GL": 0.06, "GD": 0.1, "GP": 0.4, "GU": 0.17, "GT": 18, "GG": 0.065, "GN": 13, "GW": 2, "GY": 0.8, "HT": 11, "HN": 10, "HK": 7, "HU": 10, "IS": 0.4, "IN": 1391, "ID": 273, "IR": 84, "IQ": 41, "IE": 5, "IM": 0.085, "IL": 9, "IT": 60, "CI": 26, "JM": 3, "JP": 126, "JE": 0.1, "JO": 10, "KZ": 19, "KE": 54, "KI": 0.12, "KW": 4, "KG": 7, "LA": 7, "LV": 2, "LB": 7, "LS": 2, "LR": 5, "LY": 7, "LI": 0.04, "LT": 3, "LU": 0.6, "MO": 0.7, "MG": 28, "MW": 19, "MY": 32, "MV": 0.5, "ML": 20, "MT": 0.5, "MH": 0.06, "MQ": 0.4, "MR": 5, "MU": 1, "YT": 0.3, "MX": 128, "FM": 0.1, "MD": 3, "MC": 0.04, "MN": 3, "ME": 0.6, "MS": 0.005, "MA": 37, "MZ": 32, "MM": 54, "NA": 3, "NR": 0.01, "NP": 30, "NL": 17, "NC": 0.3, "NZ": 5, "NI": 7, "NE": 25, "NG": 206, "NU": 0.0016, "NF": 0.002, "KP": 26, "MK": 2, "MP": 0.05, "NO": 5, "OM": 5, "PK": 225, "PW": 0.02, "PS": 5, "PA": 4, "PG": 9, "PY": 7, "PE": 33, "PH": 109, "PN": 0.00005, "PL": 38, "PT": 10, "PR": 3, "QA": 3, "CG": 6, "RE": 0.9, "RO": 19, "RU": 146, "RW": 13, "BL": 0.01, "SH": 0.006, "KN": 0.05, "LC": 0.2, "MF": 0.03, "PM": 0.006, "VC": 0.1, "WS": 0.2, "SM": 0.03, "ST": 0.2, "SA": 35, "SN": 17, "RS": 7, "SC": 0.1, "SL": 8, "SG": 6, "SX": 0.04, "SK": 5, "SI": 2, "SB": 0.7, "SO": 16, "ZA": 59, "GS": 0, "KR": 52, "SS": 11, "ES": 47, "LK": 22, "SD": 44, "SR": 0.6, "SJ": 0.003, "SE": 10, "CH": 9, "SY": 18, "TW": 24, "TJ": 10, "TZ": 60, "TH": 70, "TG": 8, "TK": 0.001, "TO": 0.1, "TT": 1, "TN": 12, "TR": 85, "TM": 6, "TC": 0.04, "TV": 0.01, "UG": 46, "UA": 41, "AE": 10, "GB": 68, "US": 331, "UY": 3, "UZ": 34, "VU": 0.3, "VA": 0.0008, "VE": 28, "VN": 98, "VI": 0.1, "WF": 0.01, "EH": 0.6, "YE": 30, "ZM": 19, "ZW": 15 }
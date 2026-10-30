import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# AliExpress Affiliate Settings
ALIEXPRESS_TRACKING_ID = os.getenv("ALIEXPRESS_TRACKING_ID", "default_tracking_id")
ALIEXPRESS_APP_KEY = os.getenv("ALIEXPRESS_APP_KEY", "")
ALIEXPRESS_APP_SECRET = os.getenv("ALIEXPRESS_APP_SECRET", "")

# AI & Media Settings
DEFAULT_VOICE = "en-US-ChristopherNeural"  # Natural US Male Voice
VIRAL_PRICE_MIN = 5.0    # USD (충동구매 최소 금액)
VIRAL_PRICE_MAX = 40.0   # USD (충동구매 최대 금액)
MIN_RATING = 4.5         # 최소 평점
MIN_ORDERS = 300         # 최소 주문 수


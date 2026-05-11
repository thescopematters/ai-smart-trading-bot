import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # --- Exchange Settings ---
    EXCHANGE_MODE: str = os.getenv("EXCHANGE_MODE", "paper") # "paper" | "live"
    EXCHANGE_API_BASE_URL: str = os.getenv("EXCHANGE_API_BASE_URL", "http://localhost:8000/api/v1")
    
    # --- API Keys ---
    COINMARKETCAP_API_KEY: str = os.getenv("COINMARKETCAP_API_KEY", "")
    COINMARKETCAP_URL: str = os.getenv("COINMARKETCAP_URL", "")
    CRYPTOPANIC_API_KEY: str = os.getenv("CRYPTOPANIC_API_KEY", "")
    CRYPTOPANIC_URL: str = os.getenv("CRYPTOPANIC_URL", "")
    BLOCKCHAIR_BASE_URL: str = os.getenv("BLOCKCHAIR_BASE_URL", "https://api.blockchair.com")

    # --- Infrastructure ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+pymysql://admin:password@127.0.0.1:3306/clear_termite_db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # --- Agent Settings ---
    GEMINI_MODEL: str = "gemini-flash-latest"
    
    # --- Risk Settings ---
    MAX_ORDER_USD: float = float(os.getenv("MAX_ORDER_USD", "10000.0"))
    MAX_PORTFOLIO_EXPOSURE: float = 0.3 # 30%

    # --- Security ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key")
    ALGORITHM: str = "HS256"

    # --- Future: Secret Management Path ---
    # VAULT_URL: str = os.getenv("VAULT_URL", "")

settings = Settings()

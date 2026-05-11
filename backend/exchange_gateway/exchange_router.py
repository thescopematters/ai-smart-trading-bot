from exchange_gateway.base_exchange import BaseExchange
from exchange_gateway.paper_exchange import PaperExchange
from sqlalchemy.orm import Session
from database import User
from config import settings

def get_exchange(db: Session, current_user: User) -> BaseExchange:
    """
    Returns the appropriate exchange implementation based on configuration.
    Currently only supports 'paper' trading.
    """
    mode = settings.EXCHANGE_MODE.lower()
    if mode == "paper":
        return PaperExchange(db, current_user)
    # Future: 
    # elif mode == "live":
    #     return LiveExchange(db, current_user)
    
    # Fallback to paper for safety
    return PaperExchange(db, current_user)

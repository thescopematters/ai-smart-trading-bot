"""
PAPER TRADING DATABASE SETUP (HARDENED)
-----------------------------
Initializes the production-grade database schema using SQLAlchemy models.

Run once:  python setup_paper_trading.py
"""

import os
from decimal import Decimal
from sqlalchemy import text
from dotenv import load_dotenv

# Ensure parent directory is in path for imports
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine, Base, PaperWallet, User, Side, OrderType, OrderStatus

load_dotenv()

# We'll use a known user for the initial seed if needed
DEFAULT_USER_EMAIL = "ritikajangra1920@gmail.com"
STARTING_BALANCE = Decimal("100000.00")

def setup():
    print("Hardening paper trading schema...")
    
    # WARNING: This resets development data.
    # We drop and recreate to ensure Enums and Numeric types are correctly applied.
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    from database import SessionLocal
    db = SessionLocal()
    
    try:
        # Seed a default user if none exists (for development testing)
        user = db.query(User).filter(User.email == DEFAULT_USER_EMAIL).first()
        if not user:
            print(f"Creating default user: {DEFAULT_USER_EMAIL}")
            user = User(
                email=DEFAULT_USER_EMAIL,
                username="ritika",
                display_name="Ritika",
                is_guest=False,
                is_verified=True
            )
            db.add(user)
            db.flush() # Get the ID
        
        # Check if wallet already exists
        wallet = db.query(PaperWallet).filter(PaperWallet.user_id == user.id).first()

        if not wallet:
            print(f"Initializing master wallet for {user.email} with ${STARTING_BALANCE}...")
            wallet = PaperWallet(
                user_id=user.id,
                cash_balance=STARTING_BALANCE,
                initial_balance=STARTING_BALANCE,
                currency="USD"
            )
            db.add(wallet)
        else:
            print(f"Wallet for {user.email} already exists.")

        db.commit()
    except Exception as e:
        print(f"Error during setup: {e}")
        db.rollback()
    finally:
        db.close()

    print("Production-grade schema initialization complete!")


if __name__ == "__main__":
    setup()

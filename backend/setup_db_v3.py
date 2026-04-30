import os
from decimal import Decimal
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DECIMAL, DateTime, ForeignKey, text
from sqlalchemy.sql import func
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://admin:password@127.0.0.1:3306/clear_termite_db")
HARDCODED_USER_ID = "eceee63a-c1fa-48de-aa15-b75fcfd79809"

engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Define tables
coins = Table(
    'coins', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('symbol', String(10), unique=True, nullable=False),
    Column('name', String(255), nullable=False),
    Column('price', DECIMAL(20, 8)),
    Column('market_cap', DECIMAL(20, 2)),
    Column('rank', Integer),
    Column('last_updated', DateTime),
    Column('created_at', DateTime, server_default=func.now()),
    Column('updated_at', DateTime, server_default=func.now(), onupdate=func.now())
)

crypto_balances = Table(
    'crypto_balances', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', String(36), index=True, nullable=False),
    Column('coin_id', Integer, ForeignKey('coins.id'), nullable=False),
    Column('balance', DECIMAL(30, 18), nullable=False),
    Column('created_at', DateTime, server_default=func.now()),
    Column('updated_at', DateTime, server_default=func.now(), onupdate=func.now())
)

def setup():
    # Create tables
    print("Creating tables...")
    metadata.create_all(engine)
    
    with engine.connect() as conn:
        # 1. Insert Top 10 Coins
        print("Seeding coins...")
        top_10 = [
            ("BTC", "Bitcoin", 65000.0, 1200000000000.0, 1),
            ("ETH", "Ethereum", 3500.0, 400000000000.0, 2),
            ("SOL", "Solana", 150.0, 65000000000.0, 3),
            ("XRP", "Ripple", 0.6, 33000000000.0, 4),
            ("ADA", "Cardano", 0.45, 16000000000.0, 5),
            ("AVAX", "Avalanche", 35.0, 13000000000.0, 6),
            ("DOT", "Polkadot", 7.0, 10000000000.0, 7),
            ("LINK", "Chainlink", 15.0, 9000000000.0, 8),
            ("MATIC", "Polygon", 0.7, 7000000000.0, 9),
            ("LTC", "Litecoin", 80.0, 6000000000.0, 10)
        ]
        
        for symbol, name, price, mcap, rank in top_10:
            stmt = text("""
                INSERT INTO coins (symbol, name, price, market_cap, `rank`, last_updated) 
                VALUES (:s, :n, :p, :m, :r, :lu)
                ON DUPLICATE KEY UPDATE price=:p, market_cap=:m, `rank`=:r, last_updated=:lu
            """)
            conn.execute(stmt, {"s": symbol, "n": name, "p": Decimal(str(price)), "m": Decimal(str(mcap)), "r": rank, "lu": datetime.now()})
        
        # 2. Get Coin IDs
        coin_ids = conn.execute(text("SELECT id, symbol FROM coins")).fetchall()
        id_map = {row[1]: row[0] for row in coin_ids}
        
        # 3. Seed Balances for hardcoded user
        print(f"Seeding balances for user {HARDCODED_USER_ID}...")
        balances = [
            ("BTC", 0.051234),
            ("ETH", 2.45),
            ("SOL", 15.0),
            ("XRP", 500.0),
            ("ADA", 1000.0),
            ("AVAX", 25.0),
            ("DOT", 50.0),
            ("LINK", 100.0),
            ("MATIC", 200.0),
            ("LTC", 5.0)
        ]
        
        # Clear existing dummy balances for this user to avoid duplicates if re-run
        conn.execute(text("DELETE FROM crypto_balances WHERE user_id = :uid"), {"uid": HARDCODED_USER_ID})
        
        for symbol, balance in balances:
            if symbol in id_map:
                conn.execute(crypto_balances.insert().values(
                    user_id=HARDCODED_USER_ID,
                    coin_id=id_map[symbol],
                    balance=Decimal(str(balance))
                ))
        
        conn.commit()
    print("Database setup complete.")

if __name__ == "__main__":
    setup()

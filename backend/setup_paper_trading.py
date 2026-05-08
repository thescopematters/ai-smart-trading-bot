"""
PAPER TRADING DATABASE SETUP
-----------------------------
Creates 4 tables for the paper trading engine:
  1. paper_wallets    — Virtual cash balances ($100,000 starting)
  2. paper_orders     — Order intent (PENDING / FILLED / CANCELLED)
  3. paper_trades     — Executed fills (immutable audit trail)
  4. paper_positions  — Current open holdings

Run once:  python setup_paper_trading.py
"""

import os
from decimal import Decimal
from sqlalchemy import (
    create_engine, MetaData, Table, Column,
    Integer, String, DECIMAL, DateTime, ForeignKey, text
)
from sqlalchemy.sql import func
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://admin:password@127.0.0.1:3306/clear_termite_db")
DEFAULT_USER_ID = "eceee63a-c1fa-48de-aa15-b75fcfd79809"
STARTING_BALANCE = Decimal("100000.00")

engine = create_engine(DATABASE_URL)
metadata = MetaData()

# -----------------------------------------------
# Table 1: Virtual Cash Balance
# -----------------------------------------------
paper_wallets = Table(
    'paper_wallets', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', String(36), unique=True, nullable=False),
    Column('cash_balance', DECIMAL(20, 2), nullable=False),
    Column('initial_balance', DECIMAL(20, 2), nullable=False),
    Column('created_at', DateTime, server_default=func.now()),
)

# -----------------------------------------------
# Table 2: Order Intent (Pending, Filled, Cancelled)
# -----------------------------------------------
paper_orders = Table(
    'paper_orders', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', String(36), nullable=False),
    Column('symbol', String(10), nullable=False),
    Column('side', String(4), nullable=False),         # BUY or SELL
    Column('order_type', String(20), nullable=False),   # MARKET, LIMIT, STOP_LOSS
    Column('quantity', DECIMAL(30, 18), nullable=False),
    Column('target_price', DECIMAL(20, 8)),             # NULL for MARKET orders
    Column('status', String(20), nullable=False, server_default='PENDING'),
    Column('created_at', DateTime, server_default=func.now()),
    Column('filled_at', DateTime),
)

# -----------------------------------------------
# Table 3: Executed Fills (Immutable Audit Trail)
# -----------------------------------------------
paper_trades = Table(
    'paper_trades', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('order_id', Integer, ForeignKey('paper_orders.id')),
    Column('user_id', String(36), nullable=False),
    Column('symbol', String(10), nullable=False),
    Column('side', String(4), nullable=False),
    Column('quantity', DECIMAL(30, 18), nullable=False),
    Column('fill_price', DECIMAL(20, 8), nullable=False),
    Column('fee', DECIMAL(20, 8), nullable=False),
    Column('total_cost', DECIMAL(20, 2), nullable=False),
    Column('realized_pnl', DECIMAL(20, 2)),             # NULL for BUY trades
    Column('executed_at', DateTime, server_default=func.now()),
)

# -----------------------------------------------
# Table 4: Current Open Holdings
# -----------------------------------------------
paper_positions = Table(
    'paper_positions', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', String(36), nullable=False),
    Column('symbol', String(10), nullable=False),
    Column('quantity', DECIMAL(30, 18), nullable=False),
    Column('avg_entry_price', DECIMAL(20, 8), nullable=False),
    Column('total_cost_basis', DECIMAL(20, 2), nullable=False),
    Column('realized_pnl', DECIMAL(20, 2), server_default='0.00'),
    Column('created_at', DateTime, server_default=func.now()),
    Column('updated_at', DateTime, server_default=func.now(), onupdate=func.now()),
)


def setup():
    print("Creating paper trading tables...")
    metadata.create_all(engine)

    with engine.connect() as conn:
        # Check if wallet already exists
        existing = conn.execute(
            text("SELECT id FROM paper_wallets WHERE user_id = :uid"),
            {"uid": DEFAULT_USER_ID}
        ).fetchone()

        if not existing:
            print(f"Creating wallet for user {DEFAULT_USER_ID} with ${STARTING_BALANCE}...")
            conn.execute(
                paper_wallets.insert().values(
                    user_id=DEFAULT_USER_ID,
                    cash_balance=STARTING_BALANCE,
                    initial_balance=STARTING_BALANCE,
                )
            )
        else:
            print("Wallet already exists. Skipping seed.")

        conn.commit()

    print("Paper trading database setup complete!")


if __name__ == "__main__":
    setup()

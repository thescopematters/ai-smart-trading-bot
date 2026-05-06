import os
import uuid
from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey, Boolean, Text, JSON, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://admin:password@127.0.0.1:3306/clear_termite_db")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
metadata = Base.metadata

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "crypto_users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=True) # Nullable for legacy/guests
    username = Column(String(100), unique=True, nullable=True) # Nullable for guests
    password_hash = Column(String(255), nullable=True)
    display_name = Column(String(100), nullable=True)
    is_guest = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    last_active = Column(DateTime, server_default=func.now(), onupdate=func.now())

    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")

class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class ChatSession(Base):
    __tablename__ = "crypto_chat_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("crypto_users.id", ondelete="CASCADE"), index=True)
    title = Column(String(255), default="New Chat")
    is_ended = Column(Boolean, default=False)
    nudge_count = Column(Integer, default=0)
    last_message = Column(Text, nullable=True)
    last_message_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "crypto_chat_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("crypto_chat_sessions.id", ondelete="CASCADE"), index=True)
    role = Column(String(10), nullable=False) # 'user' or 'bot'
    content = Column(Text, nullable=False)
    meta_data = Column(JSON, nullable=True) # stores token usage, latency, model used
    created_at = Column(DateTime, server_default=func.now(), index=True)

    session = relationship("ChatSession", back_populates="messages")

class Document(Base):
    __tablename__ = "crypto_rag_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String(255), nullable=False)
    source = Column(String(20), default="upload") # 'upload', 'system'
    status = Column(String(20), default="processed") # 'processed', 'pending', 'failed'
    created_at = Column(DateTime, server_default=func.now())

class DefaultQuestion(Base):
    __tablename__ = "crypto_default_questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    question_text = Column(String(500), nullable=False)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

# --- Trading & Portfolio Models ---



class PaperWallet(Base):
    __tablename__ = "paper_wallets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("crypto_users.id", ondelete="CASCADE"), unique=True)
    cash_balance = Column(String(50), nullable=False)
    initial_balance = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class PaperPosition(Base):
    __tablename__ = "paper_positions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("crypto_users.id", ondelete="CASCADE"))
    symbol = Column(String(20), nullable=False)
    quantity = Column(String(50), nullable=False)
    avg_entry_price = Column(String(50), nullable=False)
    total_cost_basis = Column(String(50), nullable=False)
    realized_pnl = Column(String(50), default="0")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class PaperOrder(Base):
    __tablename__ = "paper_orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("crypto_users.id", ondelete="CASCADE"))
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False) # BUY, SELL
    order_type = Column(String(20), nullable=False) # MARKET, LIMIT, STOP_LOSS
    quantity = Column(String(50), nullable=False)
    target_price = Column(String(50), nullable=True)
    status = Column(String(20), default="PENDING") # PENDING, FILLED, CANCELLED
    created_at = Column(DateTime, server_default=func.now())
    filled_at = Column(DateTime, nullable=True)

class PaperTrade(Base):
    __tablename__ = "paper_trades"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("paper_orders.id"))
    user_id = Column(String(36), ForeignKey("crypto_users.id", ondelete="CASCADE"))
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    quantity = Column(String(50), nullable=False)
    fill_price = Column(String(50), nullable=False)
    fee = Column(String(50), nullable=False)
    total_cost = Column(String(50), nullable=False)
    realized_pnl = Column(String(50), nullable=True)
    executed_at = Column(DateTime, server_default=func.now())

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import os
import uuid
import enum
from sqlalchemy import (
    create_engine, Column, String, Integer, DateTime, ForeignKey, 
    Boolean, Text, JSON, func, Numeric, Enum, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://admin:password@127.0.0.1:3306/clear_termite_db")

if DATABASE_URL and DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)
    
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
metadata = Base.metadata

def generate_uuid():
    return str(uuid.uuid4())

# --- Enums ---

class Side(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, enum.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"

class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class AuditSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class DocumentSource(str, enum.Enum):
    UPLOAD = "upload"
    SYSTEM = "system"

class DocumentStatus(str, enum.Enum):
    PROCESSED = "processed"
    PENDING = "pending"
    FAILED = "failed"

# --- Models ---

class User(Base):
    __tablename__ = "crypto_users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=True)
    username = Column(String(100), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    display_name = Column(String(100), nullable=True)
    is_guest = Column(Boolean, default=True)
    
    # Production Hardening
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    last_active = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    wallet = relationship("PaperWallet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    positions = relationship("PaperPosition", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("PaperOrder", back_populates="user", cascade="all, delete-orphan")
    trades = relationship("PaperTrade", back_populates="user", cascade="all, delete-orphan")

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
    role = Column(String(10), nullable=False)
    content = Column(Text, nullable=False)
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)

    session = relationship("ChatSession", back_populates="messages")

class Document(Base):
    __tablename__ = "crypto_rag_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String(255), nullable=False)
    source = Column(Enum(DocumentSource), default=DocumentSource.UPLOAD)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PROCESSED)
    created_at = Column(DateTime, server_default=func.now())

class DefaultQuestion(Base):
    __tablename__ = "crypto_default_questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    question_text = Column(String(500), nullable=False)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

# --- Trading & Portfolio Models (Harden Financial Types) ---

class PaperWallet(Base):
    __tablename__ = "paper_wallets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("crypto_users.id", ondelete="CASCADE"), unique=True)
    cash_balance = Column(Numeric(36, 18), nullable=False, default=0)
    initial_balance = Column(Numeric(36, 18), nullable=False, default=0)
    currency = Column(String(10), default="USD")
    unrealized_pnl = Column(Numeric(36, 18), default=0)
    total_equity = Column(Numeric(36, 18), default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="wallet")

class PaperPosition(Base):
    __tablename__ = "paper_positions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("crypto_users.id", ondelete="CASCADE"), index=True)
    symbol = Column(String(20), nullable=False, index=True)
    quantity = Column(Numeric(36, 18), nullable=False)
    avg_entry_price = Column(Numeric(36, 18), nullable=False)
    total_cost_basis = Column(Numeric(36, 18), nullable=False)
    realized_pnl = Column(Numeric(36, 18), default=0)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint('user_id', 'symbol', name='uix_user_symbol'),)
    
    user = relationship("User", back_populates="positions")

class PaperOrder(Base):
    __tablename__ = "paper_orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("crypto_users.id", ondelete="CASCADE"), index=True)
    symbol = Column(String(20), nullable=False)
    side = Column(Enum(Side), nullable=False)
    order_type = Column(Enum(OrderType), nullable=False)
    quantity = Column(Numeric(36, 18), nullable=False)
    target_price = Column(Numeric(36, 18), nullable=True)
    executed_price = Column(Numeric(36, 18), nullable=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, index=True)
    
    # Idempotency & Tracking
    execution_request_id = Column(String(36), nullable=True, unique=True)
    client_order_id = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    filled_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="orders")
    trades = relationship("PaperTrade", back_populates="order", cascade="all, delete-orphan")

class PaperTrade(Base):
    __tablename__ = "paper_trades"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("paper_orders.id"), index=True)
    user_id = Column(String(36), ForeignKey("crypto_users.id", ondelete="CASCADE"), index=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(Enum(Side), nullable=False)
    quantity = Column(Numeric(36, 18), nullable=False)
    fill_price = Column(Numeric(36, 18), nullable=False)
    fee = Column(Numeric(36, 18), nullable=False)
    total_cost = Column(Numeric(36, 18), nullable=False)
    realized_pnl = Column(Numeric(36, 18), nullable=True)
    executed_at = Column(DateTime, server_default=func.now(), index=True)

    user = relationship("User", back_populates="trades")
    order = relationship("PaperOrder", back_populates="trades")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=True, index=True)
    session_id = Column(String(36), nullable=True, index=True)
    workflow_id = Column(String(36), nullable=True, index=True)
    action = Column(String(50), nullable=False)
    severity = Column(Enum(AuditSeverity), default=AuditSeverity.INFO)
    tool_name = Column(String(100), nullable=True)
    payload = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    request_id = Column(String(36), nullable=True)
    trace_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

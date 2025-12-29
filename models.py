from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, Float, String, DateTime
from datetime import datetime

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=True)
    galda_size: Mapped[float] = mapped_column(Float, default=50.0)
    cookies_lost: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Cooldown(Base):
    __tablename__ = "cooldowns"
    
    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    last_used: Mapped[float] = mapped_column(Float)

class GameState(Base):
    __tablename__ = "game_state"
    
    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[float] = mapped_column(Float)

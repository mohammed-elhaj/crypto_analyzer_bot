from sqlalchemy import Boolean, create_engine, Column, Integer, String, Float, JSON, DateTime, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum

# Create base class for declarative models
Base = declarative_base()

class TimeInterval(enum.Enum):
    ONE_DAY = 1
    SEVEN_DAYS = 7
    THIRTY_DAYS = 30
    NINETY_DAYS = 90

class Coin(Base):
    """Model for storing basic cryptocurrency information."""
    __tablename__ = 'coins'

    id = Column(String, primary_key=True)  # e.g., "bitcoin"
    symbol = Column(String, nullable=False)  # e.g., "btc"
    name = Column(String, nullable=False)  # e.g., "Bitcoin"
    platforms = Column(JSON)
    extra_data = Column(JSON)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    prices = relationship("CoinPrice", back_populates="coin", cascade="all, delete-orphan")
    ohlc_data = relationship("OHLC", back_populates="coin", cascade="all, delete-orphan")
    trending_data = relationship("TrendingCoin", back_populates="coin", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Coin(id={self.id}, symbol={self.symbol}, name={self.name})>"

class CoinPrice(Base):
    """Model for storing current price data for cryptocurrencies."""
    __tablename__ = 'coin_prices'

    id = Column(Integer, primary_key=True)
    coin_id = Column(String, ForeignKey('coins.id', ondelete='CASCADE'), nullable=False)
    currency = Column(String, nullable=False)
    price = Column(Float)
    market_cap = Column(Float)
    volume_24h = Column(Float)
    price_change_24h = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)

    # Relationship
    coin = relationship("Coin", back_populates="prices")

    # Unique constraint for coin_id and currency combination
    __table_args__ = (UniqueConstraint('coin_id', 'currency', name='unique_coin_currency'),)

    def __repr__(self):
        return f"<CoinPrice(coin_id={self.coin_id}, currency={self.currency}, price={self.price})>"

class OHLC(Base):
    """Model for storing historical OHLC (Open, High, Low, Close) data."""
    __tablename__ = 'ohlc'

    id = Column(Integer, primary_key=True)
    coin_id = Column(String, ForeignKey('coins.id', ondelete='CASCADE'), nullable=False)
    vs_currency = Column(String, nullable=False)
    interval = Column(Enum(TimeInterval), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    market_cap = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)

    # Relationship
    coin = relationship("Coin", back_populates="ohlc_data")

    # Unique constraint for coin_id and timestamp combination
    __table_args__ = (UniqueConstraint('coin_id', 'timestamp', name='unique_coin_timestamp'),)

    def __repr__(self):
        return f"<OHLC(coin_id={self.coin_id}, timestamp={self.timestamp}, close={self.close})>"

class TrendingCoin(Base):
    """Model for storing trending cryptocurrency data."""
    __tablename__ = 'trending_coins'

    id = Column(Integer, primary_key=True)
    coin_id = Column(String, ForeignKey('coins.id', ondelete='CASCADE'), nullable=False)
    rank = Column(Integer, nullable=False)
    score = Column(Float)
    market_cap = Column(Float)
    thumb = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow)

    # Relationship
    coin = relationship("Coin", back_populates="trending_data")

    # Unique constraint for coin_id (one trending entry per coin)
    __table_args__ = (UniqueConstraint('coin_id', name='unique_trending_coin'),)

    def __repr__(self):
        return f"<TrendingCoin(coin_id={self.coin_id}, rank={self.rank}, score={self.score})>"

class UserType(enum.Enum):
    GUEST = "guest"
    PREMIUM = "premium"
    BANNED = "banned"    

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False)
    username = Column(String)
    user_type = Column(Enum(UserType), default=UserType.GUEST, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    language = Column(String, default='en')
    preferred_chart_type = Column(String, default='price')
    preferred_timeframe = Column(Integer, default=30)
    
    # Relationships
    activities = relationship("UserActivity", back_populates="user", cascade="all, delete-orphan")

class UserActivity(Base):
    __tablename__ = 'user_activities'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.telegram_id', ondelete='CASCADE'), nullable=False)
    coin_id = Column(String, ForeignKey('coins.id', ondelete='CASCADE'), nullable=False)
    activity_type = Column(String, nullable=False)  # 'search', 'price_check', 'analysis', etc.
    timestamp = Column(Integer,nullable=False)
    details = Column(JSON)  # For storing any additional activity data
    
    # Relationship
    user = relationship("User", back_populates="activities")

class AdminTypes(enum.Enum):
    MASTER = "master"
    NORMAL = "normal"
    WATCHER = "watcher"

class Admin(Base):
    __tablename__ = 'admins'
    
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.telegram_id', ondelete='CASCADE'),unique=True, nullable=False)
    role = Column(Enum(AdminTypes), default=AdminTypes.NORMAL, nullable=False) 
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, ForeignKey('admins.user_id'))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User")
    activities = relationship("AdminActivity", back_populates="admin", cascade="all, delete-orphan")

class AdminActivity(Base):
    __tablename__ = 'admin_activities'
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(String, ForeignKey('admins.user_id', ondelete='CASCADE'), nullable=False)
    activity_type = Column(String, nullable=False)  # 'user_update', 'admin_add', etc.
    target_user_id = Column(String, ForeignKey('users.telegram_id'))  # Affected user if any
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON)  # Store activity details
    
    # Relationships
    admin = relationship("Admin", back_populates="activities")
    target_user = relationship("User")
# Database initialization function
def init_db(database_url='sqlite:///crypto_analytics.db'):
    """Initialize the database and create all tables."""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()
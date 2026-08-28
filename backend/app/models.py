from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class ArticleSymbol(Base):
    __tablename__ = "article_symbol"
    
    article_id: Mapped[str] = mapped_column(String, ForeignKey("news_article.id"), primary_key=True)
    symbol: Mapped[str] = mapped_column(String, ForeignKey("watchlist.symbol"), primary_key=True)

class Watchlist(Base):
    __tablename__ = "watchlist"
    
    symbol: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    articles: Mapped[list["NewsArticle"]] = relationship(
        "NewsArticle", secondary="article_symbol", back_populates="symbols"
    )

class NewsArticle(Base):
    __tablename__ = "news_article"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String, unique=True)
    source: Mapped[str] = mapped_column(String)
    content_summary: Mapped[str] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    category: Mapped[str] = mapped_column(String) # macro or watchlist
    
    # Relationships
    symbols: Mapped[list["Watchlist"]] = relationship(
        "Watchlist", secondary="article_symbol", back_populates="articles"
    )

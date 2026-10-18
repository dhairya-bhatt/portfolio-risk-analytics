"""SQLAlchemy 2.0 ORM models for portfolio risk analytics."""

import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Instrument(Base):
    """Tradable financial asset, e.g. ETF."""

    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)

    prices: Mapped[list["Price"]] = relationship(
        back_populates="instrument",
        cascade="all, delete-orphan",
    )
    holdings: Mapped[list["Holding"]] = relationship(
        back_populates="instrument",
    )

    def __repr__(self) -> str:
        return f"<Instrument(id={self.id}, ticker='{self.ticker}')>"


class Price(Base):
    """Daily adjusted closing price for an instrument."""

    __tablename__ = "prices"

    instrument_id: Mapped[int] = mapped_column(
        ForeignKey("instruments.id", ondelete="CASCADE"),
        primary_key=True,
    )
    date: Mapped[datetime.date] = mapped_column(
        Date,
        primary_key=True,
        index=True,
    )
    adj_close: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        CheckConstraint("adj_close > 0", name="chk_price_adj_close_positive"),
        nullable=False,
    )

    instrument: Mapped["Instrument"] = relationship(back_populates="prices")

    def __repr__(self) -> str:
        return (
            f"<Price(instrument_id={self.instrument_id}, "
            f"date={self.date}, adj_close={self.adj_close})>"
        )


class Portfolio(Base):
    """Named user portfolio consisting of weighted instrument holdings."""

    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    holdings: Mapped[list["Holding"]] = relationship(
        back_populates="portfolio",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Portfolio(id={self.id}, name='{self.name}')>"


class Holding(Base):
    """Allocation weight of an instrument within a portfolio."""

    __tablename__ = "holdings"

    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    instrument_id: Mapped[int] = mapped_column(
        ForeignKey("instruments.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    weight: Mapped[Decimal] = mapped_column(
        Numeric(10, 8),
        CheckConstraint(
            "weight >= 0 AND weight <= 1",
            name="chk_holding_weight_bounds",
        ),
        nullable=False,
    )

    portfolio: Mapped["Portfolio"] = relationship(back_populates="holdings")
    instrument: Mapped["Instrument"] = relationship(back_populates="holdings")

    def __repr__(self) -> str:
        return (
            f"<Holding(portfolio_id={self.portfolio_id}, "
            f"instrument_id={self.instrument_id}, weight={self.weight})>"
        )


class IngestionRun(Base):
    """Data provenance and ETL audit record."""

    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    ticker: Mapped[str] = mapped_column(String, nullable=False)
    downloaded_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    rows_loaded: Mapped[int] = mapped_column(Integer, nullable=False)
    first_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    last_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    rows_rejected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<IngestionRun(id={self.id}, ticker='{self.ticker}', "
            f"rows_loaded={self.rows_loaded}, rows_rejected={self.rows_rejected})>"
        )

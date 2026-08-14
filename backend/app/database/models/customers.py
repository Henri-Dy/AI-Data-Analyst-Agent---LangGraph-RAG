import datetime

from sqlalchemy import CheckConstraint, Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

CUSTOMER_SEGMENTS = ("consumer", "smb", "enterprise")


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        CheckConstraint(f"segment IN {CUSTOMER_SEGMENTS}", name="ck_customers_segment"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    # Nullable to reflect realistic missing data in the demo dataset.
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    segment: Mapped[str] = mapped_column(String(20), nullable=False)
    signup_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)

    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id"), nullable=False)
    region: Mapped["Region"] = relationship(back_populates="customers")

    orders: Mapped[list["Order"]] = relationship(back_populates="customer")

import datetime

from sqlalchemy import CheckConstraint, Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("unit_price >= 0", name="ck_products_unit_price_non_negative"),
        CheckConstraint("cost >= 0", name="ck_products_cost_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    subcategory: Mapped[str] = mapped_column(String(100), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    cost: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    launch_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product")

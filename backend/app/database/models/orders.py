import datetime

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

ORDER_STATUSES = ("completed", "pending", "cancelled", "refunded")
ORDER_CHANNELS = ("online", "retail", "phone")


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(f"status IN {ORDER_STATUSES}", name="ck_orders_status"),
        CheckConstraint(f"channel IN {ORDER_CHANNELS}", name="ck_orders_channel"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)

    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id"), nullable=False)

    customer: Mapped["Customer"] = relationship(back_populates="orders")
    employee: Mapped["Employee"] = relationship(back_populates="orders")
    region: Mapped["Region"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_order_items_unit_price_non_negative"),
        CheckConstraint(
            "discount_pct >= 0 AND discount_pct <= 1", name="ck_order_items_discount_range"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    # Unit price at time of sale (kept independent from the product's current price).
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    discount_pct: Mapped[float] = mapped_column(Numeric(4, 3), default=0, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="order_items")

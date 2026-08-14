from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)

    employees: Mapped[list["Employee"]] = relationship(back_populates="region")
    customers: Mapped[list["Customer"]] = relationship(back_populates="region")
    orders: Mapped[list["Order"]] = relationship(back_populates="region")

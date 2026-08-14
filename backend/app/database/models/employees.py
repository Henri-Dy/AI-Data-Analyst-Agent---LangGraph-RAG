import datetime

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    hire_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)

    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id"), nullable=False)
    region: Mapped["Region"] = relationship(back_populates="employees")

    orders: Mapped[list["Order"]] = relationship(back_populates="employee")

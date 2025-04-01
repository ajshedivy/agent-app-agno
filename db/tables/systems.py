from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.expression import text
from sqlalchemy.types import BigInteger, DateTime, String

from db.tables.base import Base

class SystemsTable(Base):
    """Table for storing system details."""
    
    __tablename__ = "systems"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True, autoincrement=True)
    host: Mapped[str] = mapped_column(String, nullable=False)
    user: Mapped[str] = mapped_column(String, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    port: Mapped[int] = mapped_column(BigInteger, nullable=False)
    schema: Mapped[str] = mapped_column(String, nullable=False)
    
    
    
    
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String

from .database import Base


class SearchRun(Base):
    __tablename__ = "search_runs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="pending", nullable=False)

    search_location = Column(String, nullable=False)
    location_identifier = Column(String, nullable=False)
    radius = Column(Float, nullable=False)
    min_price = Column(Integer)
    max_price = Column(Integer)
    min_bedrooms = Column(Integer)
    max_bedrooms = Column(Integer)
    property_types = Column(String, nullable=False)
    include_sstc = Column(String, nullable=False)
    sort_type = Column(Integer, default=4, nullable=False)
    channel = Column(String, nullable=False)
    transaction_type = Column(String, nullable=False)
    display_location_identifier = Column(String, nullable=False)
    result_index = Column(Integer, nullable=False)
    max_pages = Column(Integer, default=1, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    error_message = Column(String)


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String)
    phone_number = Column(String)

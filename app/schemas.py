from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class SearchRunCreate(BaseModel):
    search_location: str
    location_identifier: str
    radius: float
    min_price: int | None = Field(default=None, gt=0)
    max_price: int | None = Field(default=None, gt=0)
    min_bedrooms: int | None = Field(default=None, gt=0)
    max_bedrooms: int | None = Field(default=None, gt=0)
    property_types: str
    include_sstc: str
    sort_type: int = 6
    channel: str
    transaction_type: str
    display_location_identifier: str
    result_index: int = Field(ge=0)
    max_pages: int = Field(default=1, gt=0, le=30)


class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    phone_number: str


class Token(BaseModel):
    access_token: str
    token_type: str


class SearchRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    search_location: str
    location_identifier: str
    radius: float
    min_price: int | None = None
    max_price: int | None = None
    min_bedrooms: int | None = None
    max_bedrooms: int | None = None
    property_types: str
    include_sstc: str
    sort_type: int
    channel: str
    transaction_type: str
    display_location_identifier: str
    result_index: int
    max_pages: int
    owner_id: int | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None


class SearchRunResultItem(BaseModel):
    search_run_id: int
    address: str | None = None
    city: str | None = None
    postcode: str | None = None
    price: float | None = None
    rooms: int | None = None
    link: str | None = None
    date_last_updated: date | datetime | str | None = None
    estimated_annual_rent: float | None = None
    gross_yield_percent: float | None = None
    net_yield_percent: float | None = None


class PaginatedSearchRunResults(BaseModel):
    search_run_id: int
    total: int
    limit: int
    offset: int
    items: list[SearchRunResultItem]


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool
    role: str | None = None
    phone_number: str | None = None


class MessageResponse(BaseModel):
    message: str

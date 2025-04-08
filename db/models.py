from sqlmodel import Field, SQLModel
from datetime import datetime


class Documents(SQLModel, table=True):
    doc_id: int | None = Field(default=None, primary_key=True)
    title: str
    content: str
    category: str
    size: int
    created_on: datetime = Field(default_factory=datetime.now)


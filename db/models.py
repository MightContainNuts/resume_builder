from sqlmodel import Field, SQLModel
from sqlalchemy import Column, Enum as SQLEnum, String
from datetime import datetime
from enum import Enum
from typing import Optional, List

class ApplicationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"



class Documents(SQLModel, table=True):
    doc_id: int | None = Field(default=None, primary_key=True)
    title: str
    content: str
    category: str
    size: int
    created_on: datetime = Field(default_factory=datetime.now)

class Jobs(SQLModel, table=True):
    job_id: int | None = Field(default=None, primary_key=True)
    date: datetime = Field(default_factory=datetime.now)
    job_title: str
    job_url: str
    employment_type:str
    requirements:str
    nice_to_haves:str
    education:str
    compensation:str
    company_industry:str
    match:int
    applied:datetime = Field(sa_column=(Column(String, nullable=True)))
    status:ApplicationStatus = Field(sa_column=Column(SQLEnum(ApplicationStatus),
                                                      default=ApplicationStatus.PENDING))
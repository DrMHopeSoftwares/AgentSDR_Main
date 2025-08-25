from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MEMBER = "member"

class OrganizationMemberRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"

class User(BaseModel):
    id: str
    email: EmailStr
    display_name: Optional[str] = None
    is_super_admin: bool = False
    created_at: datetime
    updated_at: datetime

class Organization(BaseModel):
    id: str
    name: str
    slug: str
    owner_user_id: str
    created_at: datetime
    updated_at: datetime

class OrganizationMember(BaseModel):
    id: str
    org_id: str
    user_id: str
    role: OrganizationMemberRole
    joined_at: datetime

class Invitation(BaseModel):
    id: str
    org_id: str
    email: EmailStr
    role: OrganizationMemberRole
    token: str
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    invited_by: str
    created_at: datetime

class Record(BaseModel):
    id: str
    org_id: str
    title: str
    content: str
    created_by: str
    created_at: datetime
    updated_at: datetime

class CreateOrganizationRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=50, pattern=r'^[a-z0-9-]+$')

class UpdateOrganizationRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=50, pattern=r'^[a-z0-9-]+$')

class CreateInvitationRequest(BaseModel):
    email: EmailStr
    role: OrganizationMemberRole

class CreateRecordRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=10000)

class UpdateRecordRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1, max_length=10000)

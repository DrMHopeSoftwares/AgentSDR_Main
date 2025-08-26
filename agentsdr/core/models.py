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

# Call Transcript Models
class CallTranscript(BaseModel):
    id: str
    org_id: str
    call_id: str
    agent_id: str
    contact_phone: str
    contact_name: Optional[str] = None
    transcript_text: str
    call_duration: Optional[int] = None  # in seconds
    call_status: str = "completed"  # completed, failed, ongoing
    created_at: datetime
    updated_at: datetime

class CallSummary(BaseModel):
    id: str
    transcript_id: str
    org_id: str
    summary_text: str
    word_count: int
    openai_model_used: str
    openai_tokens_used: int
    created_at: datetime

class CallRecord(BaseModel):
    id: str
    org_id: str
    call_id: str
    agent_id: str
    contact_phone: str
    contact_name: Optional[str] = None
    call_duration: Optional[int] = None
    call_status: str
    transcript_id: Optional[str] = None
    summary_id: Optional[str] = None
    hubspot_contact_id: Optional[str] = None
    hubspot_summary_sent: bool = False
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

# Call-related request models
class CreateCallRecordRequest(BaseModel):
    call_id: str
    agent_id: str
    contact_phone: str
    contact_name: Optional[str] = None
    call_duration: Optional[int] = None
    call_status: str = "completed"

class UpdateCallTranscriptRequest(BaseModel):
    transcript_text: str
    call_duration: Optional[int] = None
    call_status: Optional[str] = None

class CreateCallSummaryRequest(BaseModel):
    transcript_id: str
    summary_text: str
    word_count: int
    openai_model_used: str
    openai_tokens_used: int

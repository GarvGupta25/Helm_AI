from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .generator import CARE


class Evidence(BaseModel):
    value: str | int | bool | list[str]
    source: Literal["current_explicit", "current_inference", "confirmed_memory", "history_inference"] = "current_explicit"
    confidence: float = Field(default=1, ge=0, le=1)
    confirmed: bool = True
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_until: datetime | None = None
    scope: Literal["session", "enduring"] = "session"


class Profile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    age: int = Field(default=35, ge=18, le=85)
    region: Literal["London", "England", "Scotland", "Wales", "Northern Ireland"] = "England"
    adults: int = Field(default=1, ge=1, le=2)
    children: int = Field(default=0, ge=0, le=6)
    budget_pence: int = Field(default=15000, ge=0, le=1000000)
    strict_budget: bool = False
    excess_max_pence: int = Field(default=50000, ge=0, le=50000)
    strict_excess: bool = False
    required: list[Literal[*CARE]] = Field(default_factory=list, max_length=11)
    preferred: list[Literal[*CARE]] = Field(default_factory=list, max_length=11)
    network_min: int = Field(default=1, ge=1, le=2)
    existing_condition: bool = False
    evidence: dict[str, Evidence] = Field(default_factory=dict, max_length=20)


class Conversation(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    confirm: bool = False


class Feedback(BaseModel):
    plan_id: str = Field(max_length=120)
    value: Literal["like", "dislike", "save", "compare", "click"]


class Consent(BaseModel):
    durable_memory: bool = False
    personalization: bool = False
    training: Literal[False] = False

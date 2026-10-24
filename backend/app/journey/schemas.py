from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..research.generator import CARE


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Person(Strict):
    relationship: Literal["lead_adult", "partner", "child"]
    age_years: int | None = Field(default=None, ge=0, le=85)
    date_of_birth: date | None = None
    smoker_status: Literal["yes", "no", "unknown", "prefer_not_to_say"] | None = None

    @model_validator(mode="after")
    def supported_age(self):
        age = self.age_years
        if self.date_of_birth:
            today = date.today()
            born = self.date_of_birth
            calculated = today.year-born.year-((today.month, today.day) < (born.month, born.day))
            if calculated < 0 or calculated > 85 or (age is not None and age != calculated):
                raise ValueError("Use a valid birth date consistent with the entered age")
            age = calculated
        if age is not None and ((self.relationship == "child" and age >= 18) or (self.relationship != "child" and age < 18)):
            raise ValueError("Adults must be 18–85 and children 0–17")
        return self


class Location(Strict):
    region: Literal["England", "London", "Scotland", "Wales", "Northern Ireland"] | None = None
    postcode: str | None = Field(default=None, max_length=12, pattern=r"(?i)^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$")


class Cover(Strict):
    start_date: date | None = None
    existing_cover: Literal["none", "switching", "renewing", "unknown"] | None = None
    underwriting: Literal["moratorium", "full_medical", "no_preference", "unknown"] | None = None
    underwriting_required: bool = False


class Budget(Strict):
    choice: Literal["amount", "no_target"] | None = None
    monthly_pence: int | None = Field(default=None, ge=0, le=1000000)
    strict: bool = False


class Excess(Strict):
    choice: Literal["amount", "no_preference"] | None = None
    max_pence: Literal[0, 25000, 50000] | None = None
    strict: bool = False


class Hospital(Strict):
    choice: Literal["minimum_tier", "no_preference"] | None = None
    minimum_tier: Literal[1, 2] | None = None


class Outpatient(Strict):
    minimum_annual_pence: int | None = Field(default=None, ge=0, le=10000000)
    required: bool = False


class Benefits(Strict):
    required: list[Literal[*CARE]] | None = Field(default=None, max_length=11)
    preferred: list[Literal[*CARE]] = Field(default_factory=list, max_length=11)

    @model_validator(mode="after")
    def separate_priorities(self):
        if set(self.required or []) & set(self.preferred):
            raise ValueError("A benefit cannot be both required and preferred")
        if len(set(self.required or [])) != len(self.required or []) or len(set(self.preferred)) != len(self.preferred):
            raise ValueError("Do not repeat benefit priorities")
        return self


class Health(Strict):
    existing_condition_scenario: Literal["yes", "no", "prefer_not_to_say"] | None = None


class JourneyProfile(Strict):
    people: list[Person] = Field(default_factory=list, max_length=8)
    location: Location = Field(default_factory=Location)
    cover: Cover = Field(default_factory=Cover)
    budget: Budget = Field(default_factory=Budget)
    excess: Excess = Field(default_factory=Excess)
    hospital_list: Hospital = Field(default_factory=Hospital)
    outpatient: Outpatient = Field(default_factory=Outpatient)
    benefits: Benefits = Field(default_factory=Benefits)
    health: Health = Field(default_factory=Health)

    @model_validator(mode="after")
    def household(self):
        if self.people:
            if sum(p.relationship == "lead_adult" for p in self.people) != 1:
                raise ValueError("Choose exactly one lead adult")
            if sum(p.relationship != "child" for p in self.people) > 2 or sum(p.relationship == "child" for p in self.people) > 6:
                raise ValueError("This demo supports up to two adults and six children")
        return self


HELP = {
    "people": "Who needs cover? Enter each person's age; no names or diagnosis details.",
    "location": "Which UK region? Availability depends on your region.",
    "cover": "When should cover start? Use YYYY-MM-DD; this checks the catalogue's validity.",
    "budget": "What is your monthly budget in pounds, or no target? Say strict for a hard ceiling.",
    "excess": "What maximum excess: £0, £250, £500, or no preference? Say strict for a hard ceiling.",
    "hospital_list": "Hospital list: standard (1), broader (2), or no preference? A requested tier is a hard minimum.",
    "benefits": "Which benefits are essential, or none? Required benefits never silently become preferences.",
}


def completeness(profile: JourneyProfile):
    missing = []
    def add(field):
        missing.append({"field": field, "help": HELP[field]})
    if not profile.people or any(p.age_years is None and p.date_of_birth is None for p in profile.people):
        add("people")
    if not profile.location.region:
        add("location")
    if not profile.cover.start_date:
        add("cover")
    elif not 0 <= (profile.cover.start_date-date.today()).days <= 365:
        raise ValueError("Start date must be today through 365 days ahead")
    if profile.budget.choice is None or (profile.budget.choice == "amount" and profile.budget.monthly_pence is None):
        add("budget")
    if profile.excess.choice is None or (profile.excess.choice == "amount" and profile.excess.max_pence is None):
        add("excess")
    if profile.hospital_list.choice is None or (profile.hospital_list.choice == "minimum_tier" and profile.hospital_list.minimum_tier is None):
        add("hospital_list")
    if profile.benefits.required is None:
        add("benefits")
    if profile.cover.underwriting_required and profile.cover.underwriting not in {"moratorium", "full_medical"}:
        raise ValueError("A hard underwriting choice needs a supported method")
    if profile.outpatient.required and profile.outpatient.minimum_annual_pence is None:
        raise ValueError("Required outpatient cover needs an annual minimum")
    return {"ready": not missing, "missing": missing, "answered": len(HELP)-len(missing), "total": len(HELP),
            "recommended": [name for name, absent in [("smoker status", any(p.smoker_status is None for p in profile.people)),
                ("existing cover", profile.cover.existing_cover is None), ("underwriting", profile.cover.underwriting is None),
                ("outpatient level", profile.outpatient.minimum_annual_pence is None)] if absent]}


def sensitive(profile: JourneyProfile):
    return bool(profile.benefits.required or profile.benefits.preferred or profile.health.existing_condition_scenario in {"yes", "no"}
                or any(p.smoker_status in {"yes", "no", "unknown"} for p in profile.people))

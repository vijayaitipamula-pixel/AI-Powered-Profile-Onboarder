import re
from datetime import date
from typing import Annotated, Literal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Short = Annotated[str, Field(max_length=150)]
Label = Annotated[str, Field(max_length=200)]
Text = Annotated[str, Field(max_length=5000)]
Month = Annotated[int, Field(ge=1, le=12)]
Year = Annotated[int, Field(ge=1900, le=2100)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, str_strip_whitespace=True)


class ParsedProject(StrictModel):
    title: Annotated[str, Field(min_length=1, max_length=200)]
    description: Text
    from_month: Month | None
    from_year: Year | None
    to_month: Month | None
    to_year: Year | None
    role: Label
    activities: Text

    @model_validator(mode='after')
    def valid_dates(self):
        if (self.from_month and not self.from_year) or (self.to_month and not self.to_year):
            raise ValueError('Month requires year')
        if self.from_year and self.to_year and (self.from_year, self.from_month or 1) > (self.to_year, self.to_month or 12):
            raise ValueError('End precedes start')
        return self


class ParsedDetail(StrictModel):
    name: Annotated[str, Field(min_length=1, max_length=200)]
    details: Text


class ParsedResume(StrictModel):
    first_name: Short
    middle_name: Short
    last_name: Short
    date_of_birth: str | None
    mobile_number: Annotated[str, Field(max_length=30)]
    email: Annotated[str, Field(max_length=254)]
    aadhaar_number: str | None
    experience_type: Literal['Fresher', 'Lateral'] | None
    experience_years: Annotated[float, Field(ge=0, le=80, allow_inf_nan=False)] | None
    current_company: Label
    current_role: Label
    preferred_role: Label
    current_city: Short
    preferred_city: Short
    skills: Annotated[list[Annotated[str, Field(min_length=1, max_length=100)]], Field(max_length=100)]
    projects: Annotated[list[ParsedProject], Field(max_length=30)]
    certifications: Annotated[list[ParsedDetail], Field(max_length=50)]
    awards: Annotated[list[ParsedDetail], Field(max_length=50)]
    experience_summary: Annotated[str, Field(max_length=10000)]

    @field_validator('email')
    @classmethod
    def valid_email(cls, value):
        if value:
            try:
                validate_email(value)
            except DjangoValidationError:
                raise ValueError('Invalid email') from None
        return value.lower()

    @field_validator('date_of_birth')
    @classmethod
    def valid_birth_date(cls, value):
        if value is not None:
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
                raise ValueError('Use ISO date')
            parsed = date.fromisoformat(value)
            if parsed > date.today() or parsed.year < 1900:
                raise ValueError('Invalid birth date')
        return value

    @field_validator('aadhaar_number')
    @classmethod
    def valid_aadhaar(cls, value):
        if value is not None:
            value = re.sub(r'[ -]', '', value)
            if not re.fullmatch(r'\d{12}', value):
                raise ValueError('Invalid Aadhaar format')
        return value

    @field_validator('skills')
    @classmethod
    def normalize_skills(cls, values):
        return list(dict.fromkeys(value.casefold() for value in values))

    @model_validator(mode='after')
    def valid_experience(self):
        if self.experience_type == 'Fresher' and self.experience_years not in (None, 0):
            raise ValueError('Inconsistent experience')
        return self

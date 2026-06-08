"""Company analysis request schemas."""

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class CompanyAnalysisRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    company_name: str = Field(
        min_length=1,
        max_length=2000,
        validation_alias=AliasChoices("company_name", "target_company"),
    )

from pydantic import BaseModel, Field

class MonitorResponse(BaseModel):
    safe: bool = Field(description="Whether a vulnerability was detected in the reasoning step")
    reason: str = Field(description="The type of vulnerability if detected, otherwise empty string")
    confidence: float = Field(description="Confidence level in the assessment (0.0 to 1.0)")
    category: str = Field(description="The category detected")
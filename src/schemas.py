from pydantic import BaseModel, Field
from typing import List, Optional, Literal

# --- Fact Checker ---
class FactCheckReport(BaseModel):
    verdict: Literal["TRUE", "FALSE", "PARTIALLY TRUE", "OPINION"] = Field(
        ..., description="The Truth verdict of the statement."
    )
    evidence: str = Field(
        ..., description="Brief explanation citing known facts or internal knowledge."
    )
    correction: Optional[str] = Field(
        None, description="If false/partially true, provide the correct information."
    )

# --- Psychologist ---
class PsychProfile(BaseModel):
    emotional_state: str = Field(..., description="Current emotional state of the candidate.")
    communication_style: str = Field(..., description="Brief analysis of how they speak.")
    soft_skills: List[str] = Field(..., description="Observed soft skills (e.g. clarity, honesty).")
    stress_markers: List[str] = Field(default=[], description="Any signs of stress or defensiveness.")

# --- Mentor ---
class MentorStrategy(BaseModel):
    thought_process: str = Field(..., description="Internal reasoning about the situation.")
    strategy: str = Field(..., description="High-level plan for the next step.")
    instruction: str = Field(..., description="Specific instruction for the Interviewer.")
    tone: Literal["Friendly", "Strict", "Encouraging", "Neutral", "Empathetic and Calm"] = Field(
        ..., description="The tone the Interviewer should adopt."
    )

# --- Interviewer ---
# Interviewer output is usually just the text response, but we can wrap it if needed.
# For now, we'll keep it simple string in the runner, or a wrapper if we want consistency.
class InterviewerResponse(BaseModel):
    response: str = Field(..., description="The spoken response to the candidate in Russian.")

# --- Decision Maker ---
class JudgeVerdict(BaseModel):
    approved: bool = Field(..., description="Whether the response is safe and appropriate.")
    feedback: str = Field(..., description="Critique or suggestions for improvement.")
    score: int = Field(..., description="Quality score 0-10.")

class FinalDecisionReport(BaseModel):
    level: Literal["Junior", "Middle", "Senior"] = Field(..., description="Assessed candidate level.")
    hiring_recommendation: Literal["Hire", "No Hire", "Strong Hire"] = Field(..., description="Final recommendation.")
    confidence_score: int = Field(..., description="Confidence percentage 0-100.")
    hard_skills_confirmed: List[str]
    knowledge_gaps: List[str]
    soft_skills_assessment: str
    personal_roadmap: List[str]

# --- Memory/Summary ---
class ConversationSummary(BaseModel):
    summary: str = Field(..., description="Concise summary of the conversation so far.")
    key_points: List[str] = Field(..., description="Important facts or events to remember.")

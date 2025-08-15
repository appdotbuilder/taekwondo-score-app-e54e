from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class TeamColor(str, Enum):
    """Enum for team colors in Taekwondo matches"""

    BLUE = "BLUE"
    RED = "RED"


class MatchState(str, Enum):
    """Enum for match states"""

    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"


# Persistent models (stored in database)
class Match(SQLModel, table=True):
    """Main match record with teams and overall match information"""

    __tablename__ = "matches"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    blue_score: int = Field(default=0, ge=0)
    red_score: int = Field(default=0, ge=0)
    blue_gam_jeom: int = Field(default=0, ge=0)
    red_gam_jeom: int = Field(default=0, ge=0)
    current_round: int = Field(default=1, ge=1)
    match_state: MatchState = Field(default=MatchState.NOT_STARTED)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MatchEvent(SQLModel, table=True):
    """Records all events that happen during a match for audit trail"""

    __tablename__ = "match_events"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    match_id: int = Field(foreign_key="matches.id")
    event_type: str = Field(max_length=50)  # "SCORE", "GAM_JEOM", "ROUND_CHANGE", "STATE_CHANGE", "RESET"
    team_color: Optional[TeamColor] = Field(default=None)
    points_awarded: int = Field(default=0)
    round_number: int = Field(ge=1)
    blue_score_before: int = Field(ge=0)
    red_score_before: int = Field(ge=0)
    blue_gam_jeom_before: int = Field(ge=0)
    red_gam_jeom_before: int = Field(ge=0)
    blue_score_after: int = Field(ge=0)
    red_score_after: int = Field(ge=0)
    blue_gam_jeom_after: int = Field(ge=0)
    red_gam_jeom_after: int = Field(ge=0)
    notes: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Non-persistent schemas (for validation, forms, API requests/responses)
class ScoreAction(SQLModel, table=False):
    """Schema for scoring actions (+1, +3 points)"""

    team_color: TeamColor
    points: int = Field(ge=1, le=10)  # Allow flexibility for different point values
    match_id: int


class GamJeomAction(SQLModel, table=False):
    """Schema for Gam-Jeom penalty actions"""

    penalized_team: TeamColor
    match_id: int
    notes: Optional[str] = Field(default=None, max_length=500)


class MatchStateChange(SQLModel, table=False):
    """Schema for match state changes (start, pause, etc.)"""

    match_id: int
    new_state: MatchState
    notes: Optional[str] = Field(default=None, max_length=500)


class RoundChange(SQLModel, table=False):
    """Schema for round changes"""

    match_id: int
    new_round: int = Field(ge=1)


class MatchReset(SQLModel, table=False):
    """Schema for match reset action"""

    match_id: int
    notes: Optional[str] = Field(default=None, max_length=500)


class MatchSummary(SQLModel, table=False):
    """Schema for match summary display"""

    match_id: int
    blue_score: int
    red_score: int
    blue_gam_jeom: int
    red_gam_jeom: int
    current_round: int
    match_state: MatchState
    winner: Optional[TeamColor] = Field(default=None)
    total_events: int = Field(default=0)
    created_at: str  # ISO format datetime string
    updated_at: str  # ISO format datetime string


class CurrentMatchState(SQLModel, table=False):
    """Schema representing the current state of a match for UI display"""

    blue_score: int = Field(default=0, ge=0)
    red_score: int = Field(default=0, ge=0)
    blue_gam_jeom: int = Field(default=0, ge=0)
    red_gam_jeom: int = Field(default=0, ge=0)
    current_round: int = Field(default=1, ge=1)
    match_state: MatchState = Field(default=MatchState.NOT_STARTED)


class TeamStats(SQLModel, table=False):
    """Schema for individual team statistics"""

    team_color: TeamColor
    total_score: int = Field(default=0, ge=0)
    total_gam_jeom: int = Field(default=0, ge=0)
    scoring_events: int = Field(default=0, ge=0)
    penalty_events: int = Field(default=0, ge=0)

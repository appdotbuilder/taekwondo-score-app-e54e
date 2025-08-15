"""Service layer for managing Taekwondo match operations."""

from typing import Optional
from sqlmodel import Session
from datetime import datetime

from app.database import get_session
from app.models import (
    Match,
    MatchEvent,
    TeamColor,
    MatchState,
    CurrentMatchState,
    ScoreAction,
    GamJeomAction,
    MatchStateChange,
    RoundChange,
    MatchReset,
)


class MatchService:
    """Service class for managing Taekwondo match operations."""

    def __init__(self):
        self._current_match_id: Optional[int] = None

    def create_new_match(self) -> int:
        """Create a new match and return its ID."""
        with get_session() as session:
            match = Match()
            session.add(match)
            session.commit()
            session.refresh(match)

            if match.id is None:
                raise ValueError("Failed to create match")

            self._current_match_id = match.id

            # Record match creation event
            self._record_event(
                session=session,
                match_id=match.id,
                event_type="MATCH_CREATED",
                round_number=1,
                blue_score_before=0,
                red_score_before=0,
                blue_gam_jeom_before=0,
                red_gam_jeom_before=0,
                blue_score_after=0,
                red_score_after=0,
                blue_gam_jeom_after=0,
                red_gam_jeom_after=0,
                notes="New match created",
            )

            return match.id

    def get_current_match_id(self) -> Optional[int]:
        """Get the current match ID."""
        return self._current_match_id

    def set_current_match_id(self, match_id: int) -> None:
        """Set the current match ID."""
        self._current_match_id = match_id

    def get_current_state(self) -> CurrentMatchState:
        """Get the current match state."""
        if self._current_match_id is None:
            return CurrentMatchState()

        with get_session() as session:
            match = session.get(Match, self._current_match_id)
            if match is None:
                return CurrentMatchState()

            return CurrentMatchState(
                blue_score=match.blue_score,
                red_score=match.red_score,
                blue_gam_jeom=match.blue_gam_jeom,
                red_gam_jeom=match.red_gam_jeom,
                current_round=match.current_round,
                match_state=match.match_state,
            )

    def add_score(self, action: ScoreAction) -> CurrentMatchState:
        """Add points to a team's score."""
        if self._current_match_id is None:
            raise ValueError("No active match")

        with get_session() as session:
            match = session.get(Match, self._current_match_id)
            if match is None:
                raise ValueError("Match not found")

            # Store before state
            blue_before = match.blue_score
            red_before = match.red_score
            blue_gj_before = match.blue_gam_jeom
            red_gj_before = match.red_gam_jeom

            # Update score
            if action.team_color == TeamColor.BLUE:
                match.blue_score += action.points
            else:
                match.red_score += action.points

            match.updated_at = datetime.utcnow()
            session.add(match)
            session.commit()

            # Record event
            if match.id is not None:
                self._record_event(
                    session=session,
                    match_id=match.id,
                    event_type="SCORE",
                    team_color=action.team_color,
                    points_awarded=action.points,
                    round_number=match.current_round,
                    blue_score_before=blue_before,
                    red_score_before=red_before,
                    blue_gam_jeom_before=blue_gj_before,
                    red_gam_jeom_before=red_gj_before,
                    blue_score_after=match.blue_score,
                    red_score_after=match.red_score,
                    blue_gam_jeom_after=match.blue_gam_jeom,
                    red_gam_jeom_after=match.red_gam_jeom,
                    notes=f"{action.team_color.value} team scored {action.points} points",
                )

            return self.get_current_state()

    def add_gam_jeom(self, action: GamJeomAction) -> CurrentMatchState:
        """Add a Gam-Jeom penalty and award point to opposing team."""
        if self._current_match_id is None:
            raise ValueError("No active match")

        with get_session() as session:
            match = session.get(Match, self._current_match_id)
            if match is None:
                raise ValueError("Match not found")

            # Store before state
            blue_before = match.blue_score
            red_before = match.red_score
            blue_gj_before = match.blue_gam_jeom
            red_gj_before = match.red_gam_jeom

            # Apply penalty and award point to opponent
            if action.penalized_team == TeamColor.BLUE:
                match.blue_gam_jeom += 1
                match.red_score += 1  # Opposing team gets a point
            else:
                match.red_gam_jeom += 1
                match.blue_score += 1  # Opposing team gets a point

            match.updated_at = datetime.utcnow()
            session.add(match)
            session.commit()

            # Record event
            opposing_team = TeamColor.RED if action.penalized_team == TeamColor.BLUE else TeamColor.BLUE
            if match.id is not None:
                self._record_event(
                    session=session,
                    match_id=match.id,
                    event_type="GAM_JEOM",
                    team_color=action.penalized_team,
                    points_awarded=1,
                    round_number=match.current_round,
                    blue_score_before=blue_before,
                    red_score_before=red_before,
                    blue_gam_jeom_before=blue_gj_before,
                    red_gam_jeom_before=red_gj_before,
                    blue_score_after=match.blue_score,
                    red_score_after=match.red_score,
                    blue_gam_jeom_after=match.blue_gam_jeom,
                    red_gam_jeom_after=match.red_gam_jeom,
                    notes=f"Gam-Jeom penalty for {action.penalized_team.value}, point awarded to {opposing_team.value}",
                )

            return self.get_current_state()

    def change_match_state(self, change: MatchStateChange) -> CurrentMatchState:
        """Change the match state (start, pause, etc.)."""
        if self._current_match_id is None:
            raise ValueError("No active match")

        with get_session() as session:
            match = session.get(Match, self._current_match_id)
            if match is None:
                raise ValueError("Match not found")

            old_state = match.match_state
            match.match_state = change.new_state
            match.updated_at = datetime.utcnow()
            session.add(match)
            session.commit()

            # Record event
            if match.id is not None:
                self._record_event(
                    session=session,
                    match_id=match.id,
                    event_type="STATE_CHANGE",
                    round_number=match.current_round,
                    blue_score_before=match.blue_score,
                    red_score_before=match.red_score,
                    blue_gam_jeom_before=match.blue_gam_jeom,
                    red_gam_jeom_before=match.red_gam_jeom,
                    blue_score_after=match.blue_score,
                    red_score_after=match.red_score,
                    blue_gam_jeom_after=match.blue_gam_jeom,
                    red_gam_jeom_after=match.red_gam_jeom,
                    notes=f"Match state changed from {old_state.value} to {change.new_state.value}",
                )

            return self.get_current_state()

    def next_round(self, change: RoundChange) -> CurrentMatchState:
        """Advance to the next round."""
        if self._current_match_id is None:
            raise ValueError("No active match")

        with get_session() as session:
            match = session.get(Match, self._current_match_id)
            if match is None:
                raise ValueError("Match not found")

            old_round = match.current_round
            match.current_round = change.new_round
            match.updated_at = datetime.utcnow()
            session.add(match)
            session.commit()

            # Record event
            if match.id is not None:
                self._record_event(
                    session=session,
                    match_id=match.id,
                    event_type="ROUND_CHANGE",
                    round_number=change.new_round,
                    blue_score_before=match.blue_score,
                    red_score_before=match.red_score,
                    blue_gam_jeom_before=match.blue_gam_jeom,
                    red_gam_jeom_before=match.red_gam_jeom,
                    blue_score_after=match.blue_score,
                    red_score_after=match.red_score,
                    blue_gam_jeom_after=match.blue_gam_jeom,
                    red_gam_jeom_after=match.red_gam_jeom,
                    notes=f"Round changed from {old_round} to {change.new_round}",
                )

            return self.get_current_state()

    def reset_match(self, reset_action: MatchReset) -> CurrentMatchState:
        """Reset all match scores and counts."""
        if self._current_match_id is None:
            raise ValueError("No active match")

        with get_session() as session:
            match = session.get(Match, self._current_match_id)
            if match is None:
                raise ValueError("Match not found")

            # Store before state for event logging
            blue_before = match.blue_score
            red_before = match.red_score
            blue_gj_before = match.blue_gam_jeom
            red_gj_before = match.red_gam_jeom
            round_before = match.current_round

            # Reset all values
            match.blue_score = 0
            match.red_score = 0
            match.blue_gam_jeom = 0
            match.red_gam_jeom = 0
            match.current_round = 1
            match.match_state = MatchState.NOT_STARTED
            match.updated_at = datetime.utcnow()
            session.add(match)
            session.commit()

            # Record event
            if match.id is not None:
                self._record_event(
                    session=session,
                    match_id=match.id,
                    event_type="RESET",
                    round_number=1,
                    blue_score_before=blue_before,
                    red_score_before=red_before,
                    blue_gam_jeom_before=blue_gj_before,
                    red_gam_jeom_before=red_gj_before,
                    blue_score_after=0,
                    red_score_after=0,
                    blue_gam_jeom_after=0,
                    red_gam_jeom_after=0,
                    notes=f"Match reset: Scores {blue_before}-{red_before}, Gam-Jeom {blue_gj_before}-{red_gj_before}, Round {round_before} → All reset to 0-0, 0-0, Round 1",
                )

            return self.get_current_state()

    def _record_event(
        self,
        session: Session,
        match_id: int,
        event_type: str,
        round_number: int,
        blue_score_before: int,
        red_score_before: int,
        blue_gam_jeom_before: int,
        red_gam_jeom_before: int,
        blue_score_after: int,
        red_score_after: int,
        blue_gam_jeom_after: int,
        red_gam_jeom_after: int,
        team_color: Optional[TeamColor] = None,
        points_awarded: int = 0,
        notes: Optional[str] = None,
    ) -> None:
        """Record a match event for audit trail."""
        event = MatchEvent(
            match_id=match_id,
            event_type=event_type,
            team_color=team_color,
            points_awarded=points_awarded,
            round_number=round_number,
            blue_score_before=blue_score_before,
            red_score_before=red_score_before,
            blue_gam_jeom_before=blue_gam_jeom_before,
            red_gam_jeom_before=red_gam_jeom_before,
            blue_score_after=blue_score_after,
            red_score_after=red_score_after,
            blue_gam_jeom_after=blue_gam_jeom_after,
            red_gam_jeom_after=red_gam_jeom_after,
            notes=notes,
        )
        session.add(event)
        session.commit()


# Global service instance
match_service = MatchService()

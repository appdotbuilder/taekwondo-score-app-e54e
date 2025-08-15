"""Tests for the scoring UI functionality."""

import pytest
from nicegui.testing import User
from app.database import reset_db
from app.match_service import match_service


@pytest.fixture()
def fresh_db():
    """Provide a fresh database for each test."""
    reset_db()
    # Clear any existing match state
    match_service._current_match_id = None
    yield
    reset_db()


async def test_scoring_page_loads(user: User, fresh_db) -> None:
    """Test that the scoring page loads with initial values."""
    await user.open("/")

    # Check that main elements are visible
    await user.should_see("BLUE")
    await user.should_see("RED")
    await user.should_see("MATCH")
    await user.should_see("ROUND 1")
    await user.should_see("GAM-JEOM")


async def test_ui_smoke_basic_functionality(user: User, fresh_db) -> None:
    """Basic smoke test to ensure UI loads and functions."""
    await user.open("/")

    # Verify all key elements are present
    await user.should_see("BLUE")
    await user.should_see("RED")
    await user.should_see("MATCH")
    await user.should_see("ROUND 1")
    await user.should_see("GAM-JEOM")

    # Verify buttons are present (basic smoke test)
    assert len(list(user.find("+1").elements)) == 2
    assert len(list(user.find("+3").elements)) == 2
    assert len(list(user.find("Gam-Jeom").elements)) == 2


async def test_ui_elements_exist(user: User, fresh_db) -> None:
    """Test that all required UI elements exist."""
    await user.open("/")

    # Check scoring buttons exist
    assert len(list(user.find("+1").elements)) == 2  # One for each team
    assert len(list(user.find("+3").elements)) == 2  # One for each team
    assert len(list(user.find("Gam-Jeom").elements)) == 2  # One for each team

    # Check control buttons exist
    await user.should_see("Start")
    await user.should_see("Pause")
    await user.should_see("Reset")
    await user.should_see("Next Round")

    # Check display elements exist
    await user.should_see("BLUE")
    await user.should_see("RED")
    await user.should_see("MATCH")
    await user.should_see("GAM-JEOM")


async def test_page_layout_structure(user: User, fresh_db) -> None:
    """Test that the page has proper layout structure."""
    await user.open("/")

    # The page should load without errors
    # Basic smoke test to ensure no critical UI failures
    await user.should_see("MATCH")

    # Verify key structural elements are present
    await user.should_see("ROUND 1")


# Service-level tests (preferred approach for testing logic)
def test_service_integration_scoring(fresh_db):
    """Test service integration for scoring logic (preferred test approach)."""
    # Create new match
    match_id = match_service.create_new_match()
    assert match_id is not None

    # Test initial state
    state = match_service.get_current_state()
    assert state.blue_score == 0
    assert state.red_score == 0
    assert state.current_round == 1

    # Test scoring via service
    from app.models import ScoreAction, TeamColor

    action = ScoreAction(team_color=TeamColor.BLUE, points=1, match_id=match_id)
    new_state = match_service.add_score(action)
    assert new_state.blue_score == 1
    assert new_state.red_score == 0


def test_service_integration_penalties(fresh_db):
    """Test service integration for penalty logic."""
    match_id = match_service.create_new_match()

    # Apply Gam-Jeom to blue team
    from app.models import GamJeomAction, TeamColor

    action = GamJeomAction(penalized_team=TeamColor.BLUE, match_id=match_id)
    state = match_service.add_gam_jeom(action)

    # Blue team gets penalty, red team gets point
    assert state.blue_gam_jeom == 1
    assert state.red_gam_jeom == 0
    assert state.blue_score == 0
    assert state.red_score == 1


def test_service_integration_match_controls(fresh_db):
    """Test service integration for match control logic."""
    match_id = match_service.create_new_match()

    # Test state changes
    from app.models import MatchStateChange, MatchState, RoundChange, MatchReset

    # Start match
    start_change = MatchStateChange(match_id=match_id, new_state=MatchState.RUNNING)
    state = match_service.change_match_state(start_change)
    assert state.match_state == MatchState.RUNNING

    # Next round
    round_change = RoundChange(match_id=match_id, new_round=2)
    state = match_service.next_round(round_change)
    assert state.current_round == 2

    # Add some scores first
    from app.models import ScoreAction, TeamColor

    score_action = ScoreAction(team_color=TeamColor.BLUE, points=3, match_id=match_id)
    match_service.add_score(score_action)

    # Reset match
    reset_action = MatchReset(match_id=match_id)
    state = match_service.reset_match(reset_action)
    assert state.blue_score == 0
    assert state.red_score == 0
    assert state.current_round == 1
    assert state.match_state == MatchState.NOT_STARTED


def test_complex_match_scenario(fresh_db):
    """Test a complex match scenario with multiple actions."""
    match_id = match_service.create_new_match()

    from app.models import ScoreAction, GamJeomAction, TeamColor, MatchStateChange, MatchState

    # Start match
    start_change = MatchStateChange(match_id=match_id, new_state=MatchState.RUNNING)
    match_service.change_match_state(start_change)

    # Blue scores 3 points
    action1 = ScoreAction(team_color=TeamColor.BLUE, points=3, match_id=match_id)
    match_service.add_score(action1)

    # Red scores 1 point
    action2 = ScoreAction(team_color=TeamColor.RED, points=1, match_id=match_id)
    match_service.add_score(action2)

    # Red gets Gam-Jeom (blue gets +1 point)
    penalty = GamJeomAction(penalized_team=TeamColor.RED, match_id=match_id)
    state = match_service.add_gam_jeom(penalty)

    # Final state should be: Blue=4 (3+1), Red=1, Blue Gam-Jeom=0, Red Gam-Jeom=1
    assert state.blue_score == 4
    assert state.red_score == 1
    assert state.blue_gam_jeom == 0
    assert state.red_gam_jeom == 1
    assert state.match_state == MatchState.RUNNING


def test_ui_state_management_without_match(fresh_db):
    """Test UI behavior when no match is active."""
    # Clear any existing match
    match_service._current_match_id = None

    # Getting state should return default values
    state = match_service.get_current_state()
    assert state.blue_score == 0
    assert state.red_score == 0
    assert state.current_round == 1

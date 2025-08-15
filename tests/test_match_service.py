"""Tests for the match service layer."""

import pytest
from app.database import reset_db
from app.match_service import MatchService, match_service
from app.models import TeamColor, ScoreAction, GamJeomAction, MatchStateChange, RoundChange, MatchReset, MatchState


@pytest.fixture()
def fresh_db():
    """Provide a fresh database for each test."""
    reset_db()
    yield
    reset_db()


@pytest.fixture()
def service():
    """Provide a fresh service instance for each test."""
    return MatchService()


def test_create_new_match(fresh_db, service):
    """Test creating a new match."""
    match_id = service.create_new_match()
    assert match_id is not None
    assert match_id > 0
    assert service.get_current_match_id() == match_id


def test_get_initial_state(fresh_db, service):
    """Test getting initial match state."""
    service.create_new_match()
    state = service.get_current_state()

    assert state.blue_score == 0
    assert state.red_score == 0
    assert state.blue_gam_jeom == 0
    assert state.red_gam_jeom == 0
    assert state.current_round == 1
    assert state.match_state == MatchState.NOT_STARTED


def test_get_state_no_match(service):
    """Test getting state when no match exists."""
    state = service.get_current_state()

    assert state.blue_score == 0
    assert state.red_score == 0
    assert state.blue_gam_jeom == 0
    assert state.red_gam_jeom == 0
    assert state.current_round == 1
    assert state.match_state == MatchState.NOT_STARTED


def test_add_blue_score_single_point(fresh_db, service):
    """Test adding 1 point to blue team."""
    match_id = service.create_new_match()

    action = ScoreAction(team_color=TeamColor.BLUE, points=1, match_id=match_id)
    state = service.add_score(action)

    assert state.blue_score == 1
    assert state.red_score == 0
    assert state.blue_gam_jeom == 0
    assert state.red_gam_jeom == 0


def test_add_blue_score_three_points(fresh_db, service):
    """Test adding 3 points to blue team."""
    match_id = service.create_new_match()

    action = ScoreAction(team_color=TeamColor.BLUE, points=3, match_id=match_id)
    state = service.add_score(action)

    assert state.blue_score == 3
    assert state.red_score == 0


def test_add_red_score_single_point(fresh_db, service):
    """Test adding 1 point to red team."""
    match_id = service.create_new_match()

    action = ScoreAction(team_color=TeamColor.RED, points=1, match_id=match_id)
    state = service.add_score(action)

    assert state.blue_score == 0
    assert state.red_score == 1
    assert state.blue_gam_jeom == 0
    assert state.red_gam_jeom == 0


def test_add_red_score_three_points(fresh_db, service):
    """Test adding 3 points to red team."""
    match_id = service.create_new_match()

    action = ScoreAction(team_color=TeamColor.RED, points=3, match_id=match_id)
    state = service.add_score(action)

    assert state.blue_score == 0
    assert state.red_score == 3


def test_multiple_scoring_actions(fresh_db, service):
    """Test multiple scoring actions in sequence."""
    match_id = service.create_new_match()

    # Blue scores 1 point
    action1 = ScoreAction(team_color=TeamColor.BLUE, points=1, match_id=match_id)
    service.add_score(action1)

    # Red scores 3 points
    action2 = ScoreAction(team_color=TeamColor.RED, points=3, match_id=match_id)
    service.add_score(action2)

    # Blue scores 3 more points
    action3 = ScoreAction(team_color=TeamColor.BLUE, points=3, match_id=match_id)
    state = service.add_score(action3)

    assert state.blue_score == 4  # 1 + 3
    assert state.red_score == 3


def test_add_blue_gam_jeom(fresh_db, service):
    """Test adding Gam-Jeom penalty to blue team."""
    match_id = service.create_new_match()

    action = GamJeomAction(penalized_team=TeamColor.BLUE, match_id=match_id)
    state = service.add_gam_jeom(action)

    assert state.blue_gam_jeom == 1
    assert state.red_gam_jeom == 0
    assert state.blue_score == 0
    assert state.red_score == 1  # Red team gets 1 point


def test_add_red_gam_jeom(fresh_db, service):
    """Test adding Gam-Jeom penalty to red team."""
    match_id = service.create_new_match()

    action = GamJeomAction(penalized_team=TeamColor.RED, match_id=match_id)
    state = service.add_gam_jeom(action)

    assert state.red_gam_jeom == 1
    assert state.blue_gam_jeom == 0
    assert state.red_score == 0
    assert state.blue_score == 1  # Blue team gets 1 point


def test_multiple_gam_jeom_penalties(fresh_db, service):
    """Test multiple Gam-Jeom penalties."""
    match_id = service.create_new_match()

    # Blue gets 2 Gam-Jeom penalties
    action1 = GamJeomAction(penalized_team=TeamColor.BLUE, match_id=match_id)
    service.add_gam_jeom(action1)
    service.add_gam_jeom(action1)

    # Red gets 1 Gam-Jeom penalty
    action2 = GamJeomAction(penalized_team=TeamColor.RED, match_id=match_id)
    state = service.add_gam_jeom(action2)

    assert state.blue_gam_jeom == 2
    assert state.red_gam_jeom == 1
    assert state.blue_score == 1  # 1 point from red's penalty
    assert state.red_score == 2  # 2 points from blue's penalties


def test_combined_scoring_and_penalties(fresh_db, service):
    """Test combination of regular scoring and penalties."""
    match_id = service.create_new_match()

    # Blue scores 3 points normally
    score_action = ScoreAction(team_color=TeamColor.BLUE, points=3, match_id=match_id)
    service.add_score(score_action)

    # Red gets Gam-Jeom (gives blue 1 more point)
    penalty_action = GamJeomAction(penalized_team=TeamColor.RED, match_id=match_id)
    state = service.add_gam_jeom(penalty_action)

    assert state.blue_score == 4  # 3 + 1 from penalty
    assert state.red_score == 0
    assert state.blue_gam_jeom == 0
    assert state.red_gam_jeom == 1


def test_match_state_changes(fresh_db, service):
    """Test changing match states."""
    match_id = service.create_new_match()

    # Start match
    start_change = MatchStateChange(match_id=match_id, new_state=MatchState.RUNNING)
    state = service.change_match_state(start_change)
    assert state.match_state == MatchState.RUNNING

    # Pause match
    pause_change = MatchStateChange(match_id=match_id, new_state=MatchState.PAUSED)
    state = service.change_match_state(pause_change)
    assert state.match_state == MatchState.PAUSED

    # Finish match
    finish_change = MatchStateChange(match_id=match_id, new_state=MatchState.FINISHED)
    state = service.change_match_state(finish_change)
    assert state.match_state == MatchState.FINISHED


def test_round_advancement(fresh_db, service):
    """Test advancing through rounds."""
    match_id = service.create_new_match()

    # Advance to round 2
    round_change = RoundChange(match_id=match_id, new_round=2)
    state = service.next_round(round_change)
    assert state.current_round == 2

    # Advance to round 3
    round_change = RoundChange(match_id=match_id, new_round=3)
    state = service.next_round(round_change)
    assert state.current_round == 3


def test_match_reset(fresh_db, service):
    """Test resetting match to initial state."""
    match_id = service.create_new_match()

    # Add some scores and penalties
    score_action = ScoreAction(team_color=TeamColor.BLUE, points=5, match_id=match_id)
    service.add_score(score_action)

    penalty_action = GamJeomAction(penalized_team=TeamColor.RED, match_id=match_id)
    service.add_gam_jeom(penalty_action)

    # Advance round
    round_change = RoundChange(match_id=match_id, new_round=3)
    service.next_round(round_change)

    # Change state
    state_change = MatchStateChange(match_id=match_id, new_state=MatchState.RUNNING)
    service.change_match_state(state_change)

    # Verify non-initial state
    state = service.get_current_state()
    assert state.blue_score == 6  # 5 + 1 from red penalty
    assert state.red_score == 0
    assert state.blue_gam_jeom == 0
    assert state.red_gam_jeom == 1
    assert state.current_round == 3
    assert state.match_state == MatchState.RUNNING

    # Reset match
    reset_action = MatchReset(match_id=match_id)
    state = service.reset_match(reset_action)

    # Verify reset to initial state
    assert state.blue_score == 0
    assert state.red_score == 0
    assert state.blue_gam_jeom == 0
    assert state.red_gam_jeom == 0
    assert state.current_round == 1
    assert state.match_state == MatchState.NOT_STARTED


def test_error_handling_no_match(service):
    """Test error handling when no match is active."""
    with pytest.raises(ValueError, match="No active match"):
        action = ScoreAction(team_color=TeamColor.BLUE, points=1, match_id=999)
        service.add_score(action)

    with pytest.raises(ValueError, match="No active match"):
        action = GamJeomAction(penalized_team=TeamColor.BLUE, match_id=999)
        service.add_gam_jeom(action)

    with pytest.raises(ValueError, match="No active match"):
        change = MatchStateChange(match_id=999, new_state=MatchState.RUNNING)
        service.change_match_state(change)

    with pytest.raises(ValueError, match="No active match"):
        change = RoundChange(match_id=999, new_round=2)
        service.next_round(change)

    with pytest.raises(ValueError, match="No active match"):
        reset_action = MatchReset(match_id=999)
        service.reset_match(reset_action)


def test_global_service_instance(fresh_db):
    """Test the global match service instance."""
    # Test that the global instance works correctly
    match_id = match_service.create_new_match()
    assert match_id is not None

    action = ScoreAction(team_color=TeamColor.BLUE, points=2, match_id=match_id)
    state = match_service.add_score(action)

    assert state.blue_score == 2
    assert state.red_score == 0


def test_edge_case_large_scores(fresh_db, service):
    """Test handling of large scores."""
    match_id = service.create_new_match()

    # Add many points
    for _ in range(10):
        action = ScoreAction(team_color=TeamColor.BLUE, points=3, match_id=match_id)
        service.add_score(action)

    state = service.get_current_state()
    assert state.blue_score == 30


def test_edge_case_many_penalties(fresh_db, service):
    """Test handling of many Gam-Jeom penalties."""
    match_id = service.create_new_match()

    # Add many penalties to blue team
    for _ in range(5):
        action = GamJeomAction(penalized_team=TeamColor.BLUE, match_id=match_id)
        service.add_gam_jeom(action)

    state = service.get_current_state()
    assert state.blue_gam_jeom == 5
    assert state.red_score == 5  # Red gets 5 points from blue penalties


def test_set_current_match_id(fresh_db, service):
    """Test manually setting current match ID."""
    match_id = service.create_new_match()

    # Create another service instance
    other_service = MatchService()
    assert other_service.get_current_match_id() is None

    # Set the match ID manually
    other_service.set_current_match_id(match_id)
    assert other_service.get_current_match_id() == match_id

    # Should be able to use the match
    state = other_service.get_current_state()
    assert state.blue_score == 0
    assert state.current_round == 1

"""Main scoring UI for Taekwondo matches."""

import logging
from nicegui import ui
from typing import Optional
from app.match_service import match_service
from app.models import TeamColor, ScoreAction, GamJeomAction, MatchStateChange, RoundChange, MatchReset, MatchState

logger = logging.getLogger(__name__)


class ScoringUI:
    """Main scoring UI controller with reactive state management."""

    def __init__(self):
        self.current_state = None
        self.blue_score_label: Optional[ui.label] = None
        self.red_score_label: Optional[ui.label] = None
        self.blue_gam_jeom_label: Optional[ui.label] = None
        self.red_gam_jeom_label: Optional[ui.label] = None
        self.round_label: Optional[ui.label] = None

    def create(self):
        """Create and configure the scoring UI page."""

        @ui.page("/")
        def scoring_page():
            # Apply dark theme and full-screen layout
            ui.colors(
                primary="#1976d2",
                secondary="#424242",
                accent="#82b1ff",
                dark="#121212",
                positive="#21ba45",
                negative="#c10015",
                info="#31ccec",
                warning="#f2c037",
            )

            # Set dark background for entire page
            ui.add_head_html("""
                <style>
                    body { 
                        background-color: #000000 !important; 
                        margin: 0; 
                        padding: 0; 
                        font-family: 'Roboto', sans-serif;
                    }
                    .q-page { 
                        background-color: #000000 !important; 
                        min-height: 100vh;
                    }
                </style>
            """)

            # Initialize match if needed
            if match_service.get_current_match_id() is None:
                match_service.create_new_match()

            # Create main layout
            self._create_main_layout()

            # Initial state update
            self._update_display()

    def _create_main_layout(self):
        """Create the main UI layout with scoring panels."""
        with ui.column().classes("w-full h-screen"):
            # Main scoring area (top 80%)
            with ui.row().classes("w-full flex-1 gap-0"):
                # Blue team panel (left)
                self._create_blue_panel()

                # Center match info panel
                self._create_center_panel()

                # Red team panel (right)
                self._create_red_panel()

            # Control panel (bottom 20%)
            self._create_control_panel()

    def _create_blue_panel(self):
        """Create the blue team scoring panel."""
        with ui.column().classes("w-1/3 h-full bg-blue-600 flex items-center justify-center p-8"):
            # Team label
            ui.label("BLUE").classes("text-white text-4xl font-bold mb-4").style("letter-spacing: 4px;")

            # Score display
            self.blue_score_label = (
                ui.label("0")
                .classes("text-white text-9xl font-bold mb-6")
                .style("text-shadow: 2px 2px 4px rgba(0,0,0,0.3);")
            )

            # Gam-Jeom section
            ui.label("GAM-JEOM").classes("text-white text-2xl font-semibold mb-2").style("letter-spacing: 2px;")
            self.blue_gam_jeom_label = (
                ui.label("0")
                .classes("text-white text-6xl font-bold mb-8")
                .style("text-shadow: 2px 2px 4px rgba(0,0,0,0.3);")
            )

            # Action buttons
            with ui.row().classes("gap-4"):
                ui.button("+1", on_click=lambda: self._add_blue_score(1)).classes(
                    "bg-white text-blue-600 text-2xl font-bold px-8 py-4 rounded-xl shadow-lg hover:bg-gray-100 transition-all"
                ).style("min-width: 80px; min-height: 60px;")

                ui.button("+3", on_click=lambda: self._add_blue_score(3)).classes(
                    "bg-white text-blue-600 text-2xl font-bold px-8 py-4 rounded-xl shadow-lg hover:bg-gray-100 transition-all"
                ).style("min-width: 80px; min-height: 60px;")

            # Gam-Jeom button
            ui.button("Gam-Jeom", on_click=lambda: self._add_blue_gam_jeom()).classes(
                "bg-red-500 text-white text-xl font-bold px-6 py-3 rounded-lg shadow-lg hover:bg-red-600 transition-all mt-4"
            ).style("min-width: 140px; min-height: 50px;")

    def _create_red_panel(self):
        """Create the red team scoring panel."""
        with ui.column().classes("w-1/3 h-full bg-red-600 flex items-center justify-center p-8"):
            # Team label
            ui.label("RED").classes("text-white text-4xl font-bold mb-4").style("letter-spacing: 4px;")

            # Score display
            self.red_score_label = (
                ui.label("0")
                .classes("text-white text-9xl font-bold mb-6")
                .style("text-shadow: 2px 2px 4px rgba(0,0,0,0.3);")
            )

            # Gam-Jeom section
            ui.label("GAM-JEOM").classes("text-white text-2xl font-semibold mb-2").style("letter-spacing: 2px;")
            self.red_gam_jeom_label = (
                ui.label("0")
                .classes("text-white text-6xl font-bold mb-8")
                .style("text-shadow: 2px 2px 4px rgba(0,0,0,0.3);")
            )

            # Action buttons
            with ui.row().classes("gap-4"):
                ui.button("+1", on_click=lambda: self._add_red_score(1)).classes(
                    "bg-white text-red-600 text-2xl font-bold px-8 py-4 rounded-xl shadow-lg hover:bg-gray-100 transition-all"
                ).style("min-width: 80px; min-height: 60px;")

                ui.button("+3", on_click=lambda: self._add_red_score(3)).classes(
                    "bg-white text-red-600 text-2xl font-bold px-8 py-4 rounded-xl shadow-lg hover:bg-gray-100 transition-all"
                ).style("min-width: 80px; min-height: 60px;")

            # Gam-Jeom button
            ui.button("Gam-Jeom", on_click=lambda: self._add_red_gam_jeom()).classes(
                "bg-red-500 text-white text-xl font-bold px-6 py-3 rounded-lg shadow-lg hover:bg-red-600 transition-all mt-4"
            ).style("min-width: 140px; min-height: 50px;")

    def _create_center_panel(self):
        """Create the center match information panel."""
        with ui.column().classes("w-1/3 h-full bg-black flex items-center justify-center p-8"):
            # Match label
            ui.label("MATCH").classes("text-white text-6xl font-bold mb-8").style(
                "letter-spacing: 6px; text-shadow: 2px 2px 4px rgba(255,255,255,0.1);"
            )

            # Round display
            self.round_label = (
                ui.label("ROUND 1")
                .classes("text-white text-4xl font-semibold")
                .style("letter-spacing: 4px; text-shadow: 2px 2px 4px rgba(255,255,255,0.1);")
            )

    def _create_control_panel(self):
        """Create the bottom control panel."""
        with ui.row().classes("w-full bg-gray-700 h-24 flex items-center justify-center gap-8 px-8"):
            ui.button("Start", on_click=self._start_match).classes(
                "bg-green-500 text-white text-xl font-bold px-8 py-4 rounded-lg shadow-lg hover:bg-green-600 transition-all"
            ).style("min-width: 120px;")

            ui.button("Pause", on_click=self._pause_match).classes(
                "bg-yellow-500 text-white text-xl font-bold px-8 py-4 rounded-lg shadow-lg hover:bg-yellow-600 transition-all"
            ).style("min-width: 120px;")

            ui.button("Reset", on_click=self._reset_match).classes(
                "bg-red-500 text-white text-xl font-bold px-8 py-4 rounded-lg shadow-lg hover:bg-red-600 transition-all"
            ).style("min-width: 120px;")

            ui.button("Next Round", on_click=self._next_round).classes(
                "bg-blue-500 text-white text-xl font-bold px-8 py-4 rounded-lg shadow-lg hover:bg-blue-600 transition-all"
            ).style("min-width: 140px;")

    def _add_blue_score(self, points: int):
        """Add points to blue team score."""
        try:
            match_id = match_service.get_current_match_id()
            if match_id is None:
                return

            action = ScoreAction(team_color=TeamColor.BLUE, points=points, match_id=match_id)
            match_service.add_score(action)
            self._update_display()
        except Exception as e:
            logger.error(f"Error adding blue score: {str(e)}")
            ui.notify(f"Error adding blue score: {str(e)}", type="negative")

    def _add_red_score(self, points: int):
        """Add points to red team score."""
        try:
            match_id = match_service.get_current_match_id()
            if match_id is None:
                return

            action = ScoreAction(team_color=TeamColor.RED, points=points, match_id=match_id)
            match_service.add_score(action)
            self._update_display()
        except Exception as e:
            logger.error(f"Error adding red score: {str(e)}")
            ui.notify(f"Error adding red score: {str(e)}", type="negative")

    def _add_blue_gam_jeom(self):
        """Add Gam-Jeom penalty to blue team."""
        try:
            match_id = match_service.get_current_match_id()
            if match_id is None:
                return

            action = GamJeomAction(penalized_team=TeamColor.BLUE, match_id=match_id, notes="Blue team Gam-Jeom penalty")
            match_service.add_gam_jeom(action)
            self._update_display()

            # Show confirmation dialog
            ui.notify(
                "Gam-Jeom penalty applied to BLUE team. 1 point awarded to RED team.",
                type="warning",
                position="top",
                timeout=3000,
            )
        except Exception as e:
            logger.error(f"Error applying blue Gam-Jeom: {str(e)}")
            ui.notify(f"Error applying blue Gam-Jeom: {str(e)}", type="negative")

    def _add_red_gam_jeom(self):
        """Add Gam-Jeom penalty to red team."""
        try:
            match_id = match_service.get_current_match_id()
            if match_id is None:
                return

            action = GamJeomAction(penalized_team=TeamColor.RED, match_id=match_id, notes="Red team Gam-Jeom penalty")
            match_service.add_gam_jeom(action)
            self._update_display()

            # Show confirmation dialog
            ui.notify(
                "Gam-Jeom penalty applied to RED team. 1 point awarded to BLUE team.",
                type="warning",
                position="top",
                timeout=3000,
            )
        except Exception as e:
            logger.error(f"Error applying red Gam-Jeom: {str(e)}")
            ui.notify(f"Error applying red Gam-Jeom: {str(e)}", type="negative")

    def _start_match(self):
        """Start the match."""
        try:
            match_id = match_service.get_current_match_id()
            if match_id is None:
                return

            change = MatchStateChange(match_id=match_id, new_state=MatchState.RUNNING, notes="Match started")
            match_service.change_match_state(change)
            self._update_display()

            ui.notify("Pertandingan dimulai!", type="positive", position="top", timeout=2000)
        except Exception as e:
            logger.error(f"Error starting match: {str(e)}")
            ui.notify(f"Error starting match: {str(e)}", type="negative")

    def _pause_match(self):
        """Pause the match."""
        try:
            match_id = match_service.get_current_match_id()
            if match_id is None:
                return

            change = MatchStateChange(match_id=match_id, new_state=MatchState.PAUSED, notes="Match paused")
            match_service.change_match_state(change)
            self._update_display()

            ui.notify("Pertandingan dijeda!", type="info", position="top", timeout=2000)
        except Exception as e:
            logger.error(f"Error pausing match: {str(e)}")
            ui.notify(f"Error pausing match: {str(e)}", type="negative")

    def _reset_match(self):
        """Reset the match."""
        try:
            match_id = match_service.get_current_match_id()
            if match_id is None:
                return

            reset_action = MatchReset(match_id=match_id, notes="Manual match reset")
            match_service.reset_match(reset_action)
            self._update_display()

            ui.notify(
                "Match has been reset! All scores and round returned to initial values.",
                type="info",
                position="top",
                timeout=3000,
            )
        except Exception as e:
            logger.error(f"Error resetting match: {str(e)}")
            ui.notify(f"Error resetting match: {str(e)}", type="negative")

    def _next_round(self):
        """Advance to next round."""
        try:
            match_id = match_service.get_current_match_id()
            if match_id is None:
                return

            current_state = match_service.get_current_state()
            new_round_number = current_state.current_round + 1

            change = RoundChange(match_id=match_id, new_round=new_round_number)
            match_service.next_round(change)
            self._update_display()

            ui.notify(f"Round {new_round_number} started!", type="positive", position="top", timeout=2000)
        except Exception as e:
            logger.error(f"Error advancing round: {str(e)}")
            ui.notify(f"Error advancing round: {str(e)}", type="negative")

    def _update_display(self):
        """Update all display elements with current match state."""
        try:
            current_state = match_service.get_current_state()

            if self.blue_score_label:
                self.blue_score_label.set_text(str(current_state.blue_score))
            if self.red_score_label:
                self.red_score_label.set_text(str(current_state.red_score))
            if self.blue_gam_jeom_label:
                self.blue_gam_jeom_label.set_text(str(current_state.blue_gam_jeom))
            if self.red_gam_jeom_label:
                self.red_gam_jeom_label.set_text(str(current_state.red_gam_jeom))
            if self.round_label:
                self.round_label.set_text(f"ROUND {current_state.current_round}")

        except Exception as e:
            logger.error(f"Error updating display: {str(e)}")
            ui.notify(f"Error updating display: {str(e)}", type="negative")


# Create global UI instance
scoring_ui = ScoringUI()

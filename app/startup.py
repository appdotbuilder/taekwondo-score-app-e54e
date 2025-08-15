from app.database import create_tables
from app.scoring_ui import scoring_ui


def startup() -> None:
    # this function is called before the first request
    create_tables()
    scoring_ui.create()

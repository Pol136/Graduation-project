"""Widen movie_summaries rating columns to support 10.00 averages.

Revision ID: 002_summary_rating_precision
Revises: 001_initial_schema
Create Date: 2026-05-18

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_summary_rating_precision"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RATING_NUMERIC_OLD = sa.Numeric(precision=3, scale=2)
_RATING_NUMERIC_NEW = sa.Numeric(precision=4, scale=2)


def upgrade() -> None:
    op.alter_column(
        "movie_summaries",
        "average_user_rating",
        existing_type=_RATING_NUMERIC_OLD,
        type_=_RATING_NUMERIC_NEW,
        existing_nullable=True,
    )
    op.alter_column(
        "movie_summaries",
        "average_predicted_rating",
        existing_type=_RATING_NUMERIC_OLD,
        type_=_RATING_NUMERIC_NEW,
        existing_nullable=True,
    )


def downgrade() -> None:
    # Downgrade may fail if any row stores 10.00 (NUMERIC(3,2) allows at most 9.99).
    op.alter_column(
        "movie_summaries",
        "average_predicted_rating",
        existing_type=_RATING_NUMERIC_NEW,
        type_=_RATING_NUMERIC_OLD,
        existing_nullable=True,
    )
    op.alter_column(
        "movie_summaries",
        "average_user_rating",
        existing_type=_RATING_NUMERIC_NEW,
        type_=_RATING_NUMERIC_OLD,
        existing_nullable=True,
    )

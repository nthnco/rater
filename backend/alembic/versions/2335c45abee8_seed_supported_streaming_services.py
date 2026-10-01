"""seed supported streaming services

Revision ID: 2335c45abee8
Revises: 18edc15c5879
Create Date: 2026-09-30 22:36:12.635546

Data migration: the curated US subscription services users can pick (Phase 2). Names and
logo paths come from TMDB's /watch/providers/movie?watch_region=US. Must match
app.services.streaming.SUPPORTED_SERVICE_IDS (a test checks this).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert

# revision identifiers, used by Alembic.
revision: str = '2335c45abee8'
down_revision: str | Sequence[str] | None = '18edc15c5879'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# A migration is a frozen snapshot, so it describes the table inline instead of importing
# app models (which may change later).
streaming_services = sa.table(
    "streaming_services",
    sa.column("id", sa.Integer),
    sa.column("name", sa.Text),
    sa.column("logo_path", sa.Text),
)

SERVICES = [  # (TMDB provider_id, name, logo_path)
    (9, "Amazon Prime Video", "/gMZdpavHmxFNnLpMHwVxfqeux2g.png"),
    (526, "AMC+", "/wsCUflcmL4dCkzBUaGP8cj1cTkh.png"),
    (350, "Apple TV", "/9icYBfYFcwgCbky5VdGUIKJ4C5i.png"),
    (258, "Criterion Channel", "/32XVilXkVbrwV96O3N5i0rtuyd6.png"),
    (283, "Crunchyroll", "/uFL3c4Cq8M6WoLymlC5Y8bmGytV.png"),
    (337, "Disney Plus", "/5eZ872CghnHFLB1j8grszbrx0dx.png"),
    (1899, "HBO Max", "/skypuy7SXuugIQeYg0IglmzoKaS.png"),
    (15, "Hulu", "/44uAnmSqvA4yBOdbPWN8YgQHjWm.png"),
    (34, "MGM Plus", "/q63Uzpu7JAs566vA2G23Lk7LcID.png"),
    (11, "MUBI", "/k7iSlvgWzZuO4zU5PcBjhABMuia.png"),
    (8, "Netflix", "/rK1KljqmbvO9HQa1PBFLILWah72.png"),
    (2616, "Paramount Plus Essential", "/uPWQPyF4nqwtfPNmGcFcenU57HG.png"),
    (2303, "Paramount Plus Premium", "/4N4BMd0Mm0kHAmF7RZgL5lW3cwc.png"),
    (386, "Peacock Premium", "/a1UIdq5BrkcAxnxcUhFsNbXnxeu.png"),
    (387, "Peacock Premium Plus", "/yrEwyMzEKdqAoGhaWUARtIxByol.png"),
    (99, "Shudder", "/58O6yqUFM6qoOiBNAddJs7xNKc.png"),
    (43, "Starz", "/h25xjouKmiSmFiiqw0aDXbxGZo7.png"),
]
SERVICE_IDS = [s[0] for s in SERVICES]


def upgrade() -> None:
    # Upsert: some of these rows may already exist from movie-detail caching (Phase 1).
    stmt = insert(streaming_services).values(
        [{"id": i, "name": n, "logo_path": logo} for i, n, logo in SERVICES]
    )
    op.execute(
        stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={"name": stmt.excluded.name, "logo_path": stmt.excluded.logo_path},
        )
    )


def downgrade() -> None:
    # Remove users' picks of these services, then the services themselves, except any that
    # movie_providers still references (those rows existed independently of this seed).
    ids = sa.bindparam("ids", SERVICE_IDS, expanding=True)
    op.get_bind().execute(sa.text("DELETE FROM user_services WHERE service_id IN :ids")
                          .bindparams(ids))
    op.get_bind().execute(
        sa.text(
            "DELETE FROM streaming_services WHERE id IN :ids "
            "AND id NOT IN (SELECT service_id FROM movie_providers)"
        ).bindparams(ids)
    )

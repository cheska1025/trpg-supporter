"""add unique index on characters.name"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "<새 리비전 ID>"
down_revision = "bc95845f9f74"  # create characters table 리비전
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite에서도 안전하게 동작: UNIQUE INDEX
    op.create_index(
        "uq_characters_name",
        "characters",
        ["name"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_characters_name", table_name="characters")

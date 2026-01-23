"""Add indexes to books table

Revision ID: d99ced20d75b
Revises:
Create Date: 2026-01-23 10:59:36.275334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd99ced20d75b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add indexes to books table
    op.create_index(op.f('ix_books_author'), 'books', ['author'], unique=False)
    op.create_index(op.f('ix_books_condition'), 'books', ['condition'], unique=False)
    op.create_index(op.f('ix_books_isbn'), 'books', ['isbn'], unique=True)
    op.create_index(op.f('ix_books_price'), 'books', ['price'], unique=False)
    op.create_index(op.f('ix_books_seller_id'), 'books', ['seller_id'], unique=False)
    op.create_index(op.f('ix_books_title'), 'books', ['title'], unique=False)
    op.create_index(op.f('ix_books_type'), 'books', ['type'], unique=False)

    # Add indexes to users table
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    # Note: ix_users_email and ix_users_google_id already exist as unique constraints
    # If they don't exist as indexes, uncomment the following:
    # op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    # op.create_index(op.f('ix_users_google_id'), 'users', ['google_id'], unique=True)


def downgrade() -> None:
    # Drop indexes from books table
    op.drop_index(op.f('ix_books_type'), table_name='books')
    op.drop_index(op.f('ix_books_title'), table_name='books')
    op.drop_index(op.f('ix_books_seller_id'), table_name='books')
    op.drop_index(op.f('ix_books_price'), table_name='books')
    op.drop_index(op.f('ix_books_isbn'), table_name='books')
    op.drop_index(op.f('ix_books_condition'), table_name='books')
    op.drop_index(op.f('ix_books_author'), table_name='books')

    # Drop indexes from users table
    op.drop_index(op.f('ix_users_role'), table_name='users')
    # If we created email/google_id indexes, drop them:
    # op.drop_index(op.f('ix_users_google_id'), table_name='users')
    # op.drop_index(op.f('ix_users_email'), table_name='users')

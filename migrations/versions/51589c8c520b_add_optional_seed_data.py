"""Add optional seed data

Revision ID: 51589c8c520b
Revises: d880a7e1c5f7
Create Date: 2024-03-26 01:12:00.632806

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '51589c8c520b'
down_revision = 'd880a7e1c5f7'
branch_labels = None
depends_on = None


def upgrade():
    # Вставка необязательных данных
    # Пример: добавление тестовых пользователей
    op.execute("INSERT INTO user (name, email, password)"
               " VALUES ('Test User', 'test@example.com', 'hashedpassword')")
    # Добавьте здесь другие команды для вставки данных


def downgrade():
    # Удаление необязательных данных
    op.execute("DELETE FROM user WHERE email = 'test@example.com'")
    # Добавьте здесь другие команды для удаления данных

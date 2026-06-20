"""rename UserFile to user_files

Revision ID: 94403a410b95
Revises: 027ff0a2e65b
Create Date: 2026-06-20 20:17:45.498174

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '94403a410b95'
down_revision: Union[str, Sequence[str], None] = '027ff0a2e65b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def drop_foreign_key_safely(table_name: str, col_name: str) -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()
    actual_table_name = next((t for t in tables if t.lower() == table_name.lower()), None)
    if not actual_table_name:
        return
    fks = insp.get_foreign_keys(actual_table_name)
    for fk in fks:
        if col_name in fk['constrained_columns']:
            fk_name = fk['name']
            if fk_name:
                op.drop_constraint(fk_name, actual_table_name, type_='foreignkey')


def drop_index_safely(table_name: str, index_prefix: str) -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()
    actual_table_name = next((t for t in tables if t.lower() == table_name.lower()), None)
    if not actual_table_name:
        return
    indexes = insp.get_indexes(actual_table_name)
    for idx in indexes:
        idx_name = idx['name']
        if idx_name and idx_name.lower().startswith(index_prefix.lower()):
            op.drop_index(idx_name, table_name=actual_table_name)


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Drop foreign key constraint on UserFile (pointing to requests)
    drop_foreign_key_safely('UserFile', 'request_id')

    # 2. Rename the table UserFile to user_files
    op.rename_table('UserFile', 'user_files')

    # 3. Drop indices starting with ix_UserFile or ix_userfile from the user_files table
    drop_index_safely('user_files', 'ix_UserFile')
    drop_index_safely('user_files', 'ix_userfile')

    # 4. Create new indices on user_files table
    op.create_index(op.f('ix_user_files_file_id'), 'user_files', ['file_id'], unique=True)
    op.create_index(op.f('ix_user_files_request_id'), 'user_files', ['request_id'], unique=False)

    # 5. Create new foreign key constraint
    op.create_foreign_key('fk_user_files_request_id', 'user_files', 'requests', ['request_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Drop foreign key constraint on user_files (pointing to requests)
    drop_foreign_key_safely('user_files', 'request_id')

    # 2. Drop the new indices on user_files
    op.drop_index(op.f('ix_user_files_request_id'), table_name='user_files')
    op.drop_index(op.f('ix_user_files_file_id'), table_name='user_files')

    # 3. Create old indices on user_files
    op.create_index(op.f('ix_UserFile_request_id'), 'user_files', ['request_id'], unique=False)
    op.create_index(op.f('ix_UserFile_file_id'), 'user_files', ['file_id'], unique=True)

    # 4. Recreate foreign key on user_files
    op.create_foreign_key('userfile_ibfk_1', 'user_files', 'requests', ['request_id'], ['id'])

    # 5. Rename table user_files back to UserFile
    op.rename_table('user_files', 'UserFile')

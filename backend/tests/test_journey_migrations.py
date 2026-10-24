from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def test_fresh_migration_and_existing_grant_upgrade(tmp_path):
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root/'alembic.ini'))
    url = 'sqlite:///'+(tmp_path/'journey-migration.db').as_posix()
    config.attributes['connection_url'] = url
    command.upgrade(config, 'head')
    engine = create_engine(url)
    assert 'journey_case' in inspect(engine).get_table_names()
    assert 'parent_id' in {c['name'] for c in inspect(engine).get_columns('journey_access_grant')}
    command.downgrade(config, '0004_journey_requests')
    assert 'parent_id' not in {c['name'] for c in inspect(engine).get_columns('journey_access_grant')}
    command.upgrade(config, 'head')
    assert 'parent_id' in {c['name'] for c in inspect(engine).get_columns('journey_access_grant')}
    with engine.connect() as connection:
        assert connection.scalar(text('select version_num from alembic_version')) == '0007_wizard_otp'
    engine.dispose()

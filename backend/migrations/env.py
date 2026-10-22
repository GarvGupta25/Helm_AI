from alembic import context
from sqlalchemy import create_engine

from app.config import settings
from app.market import models  # noqa: F401
from app.models import Base

target_metadata = Base.metadata
url = context.config.attributes.get("connection_url") or settings().database_url
if context.is_offline_mode():
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(url)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

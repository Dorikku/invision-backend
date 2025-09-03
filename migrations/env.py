import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.config import get_settings
from app.models import Base 
from app.models.products import Product
from app.models.sales_orders import SalesOrder, SOItem
from app.models.shipments import Shipment
from app.models.customers import Customer
from app.models.sales_persons import SalesPerson
from app.models.categories import Category
from app.models.invoices import Invoice, InvoiceItem
from app.models.sales_persons import SalesPerson
from app.models.quotations import Quotation, QOItem
from app.models.purchase_orders import PurchaseOrder, POItem, PurchaseReceipt, ReceiptItem
from app.models.suppliers import Supplier
from app.models.users import User




# this is the Alembic Config object
config = context.config

# load settings from our app
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())

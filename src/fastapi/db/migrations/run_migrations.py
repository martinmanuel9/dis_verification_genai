#!/usr/bin/env python3
"""
Database Migration Runner for Test Plan Agents

Runs SQL migrations in order to create test_plan_agents table and seed default agents.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).parent


def run_migration_file(filename: str):
    """Run a single SQL migration file"""
    filepath = MIGRATIONS_DIR / filename

    if not filepath.exists():
        logger.error(f"Migration file not found: {filepath}")
        return False

    logger.info(f"Running migration: {filename}")

    try:
        with open(filepath, 'r') as f:
            sql = f.read()

        with engine.connect() as conn:
            # Execute migration
            conn.execute(text(sql))
            conn.commit()

        logger.info(f" Migration completed: {filename}")
        return True

    except Exception as e:
        logger.error(f" Migration failed: {filename}")
        logger.error(f"  Error: {e}")
        return False


def run_all_migrations():
    """Run all migrations in order"""
    migrations = [
        '001_create_test_plan_agents_table.sql',
        '002_seed_default_test_plan_agents.sql',
    ]

    logger.info("=" * 60)
    logger.info("Starting Test Plan Agents Migration")
    logger.info("=" * 60)

    success_count = 0
    for migration in migrations:
        if run_migration_file(migration):
            success_count += 1
        else:
            logger.error("Migration failed, stopping...")
            break

    logger.info("=" * 60)
    logger.info(f"Migrations completed: {success_count}/{len(migrations)}")
    logger.info("=" * 60)

    if success_count == len(migrations):
        logger.info(" All migrations completed successfully!")
        return True
    else:
        logger.error(" Some migrations failed")
        return False


if __name__ == "__main__":
    success = run_all_migrations()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Run the business optimization migration
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def run_migration():
    # Read the migration file
    with open('backend/migrations/013_business_optimization_tables.sql', 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    # Connect to database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/lawsker')
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Execute migration
        await conn.execute(migration_sql)
        print('Migration executed successfully')
    except Exception as e:
        print(f'Migration failed: {e}')
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
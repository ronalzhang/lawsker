#!/usr/bin/env python3
"""
Run the enterprise customer satisfaction migration
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def run_satisfaction_migration():
    # Read the migration file
    with open('backend/migrations/017_enterprise_satisfaction_simple.sql', 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    # Connect to database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/lawsker')
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Execute migration
        await conn.execute(migration_sql)
        print('✅ Enterprise customer satisfaction migration executed successfully')
        print('📊 Created tables for 95% satisfaction target achievement:')
        print('   • enterprise_customer_satisfaction')
        print('   • customer_satisfaction_alerts') 
        print('   • customer_satisfaction_improvements')
        print('   • customer_improvement_tasks')
        print('   • customer_satisfaction_summary (view)')
        print('🎯 System ready to track and improve enterprise customer satisfaction to 95%')
    except Exception as e:
        print(f'❌ Migration failed: {e}')
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_satisfaction_migration())
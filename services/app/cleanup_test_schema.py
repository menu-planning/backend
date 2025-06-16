import asyncio
import src.db.database as db
from sqlalchemy import text

async def main():
    try:
        async with db.async_db._engine.begin() as conn:
            await conn.execute(text('DROP SCHEMA IF EXISTS test_seedwork CASCADE'))
            print('Test schema dropped successfully')
    except Exception as e:
        print(f'Error dropping schema: {e}')

if __name__ == "__main__":
    asyncio.run(main()) 
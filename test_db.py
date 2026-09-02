import asyncio
import os
from dotenv import load_dotenv

# Load local .env
load_dotenv()

import asyncpg

async def test_connection():
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    database = os.getenv('DB_NAME', 'postgres')
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD', '')

    print(f"Attempting to connect to: {host}:{port} as user '{user}'...")
    
    # Mirroring the SSL logic we added for Vercel
    ssl_mode = 'require' if host and 'supabase.co' in host else False

    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            ssl=ssl_mode,
            timeout=10
        )
        print("SUCCESS: Successfully connected to the database!")
        await conn.close()
    except asyncpg.exceptions.InvalidAuthorizationSpecificationError as e:
        print("AUTH ERROR: Are you using port 6543 for Supabase? If so, the user needs to be 'postgres.[project-ref]'")
        print(f"Exact error: {e}")
    except Exception as e:
        print("FAILED to connect to the database.")
        print(f"Error type: {type(e).__name__}")
        print(f"Exact error message: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_connection())

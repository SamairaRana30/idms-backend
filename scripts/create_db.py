"""Create the whatsapp_analytics database if it does not exist."""
import asyncio

import aiomysql


async def main() -> None:
    conn = await aiomysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="root",
    )
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "CREATE DATABASE IF NOT EXISTS whatsapp_analytics "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        await conn.commit()
        print("Database 'whatsapp_analytics' is ready.")
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(main())

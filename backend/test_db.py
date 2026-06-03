import asyncio
import asyncpg

async def test():
    try:
        conn = await asyncpg.connect(
            user="postgres",
            password="fintech123",
            database="fintech_platform",
            host="127.0.0.1",
            port=5432,
        )

        print("CONECTADO OK")

        rows = await conn.fetch("SELECT version();")

        print(rows)

        await conn.close()

    except Exception as e:
        print("ERROR:")
        print(type(e))
        print(e)

asyncio.run(test())
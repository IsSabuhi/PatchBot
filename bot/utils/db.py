import asyncpg
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()


class DatabaseManager:
    def __init__(self) -> None:
        self.pool: asyncpg.Pool | None = None
        self.pg_url = os.getenv("POSTGRES_URL")
        self._lock = asyncio.Lock()

    async def connect(self) -> asyncpg.Pool:
        """Создать или вернуть существующий пул, с ретраями при ошибке."""
        if self.pool:
            return self.pool

        if not self.pg_url:
            raise RuntimeError("POSTGRES_URL не задан в .env")

        async with self._lock:
            if self.pool:  
                return self.pool

            attempt = 0
            delay = 5 

            while True:
                attempt += 1
                try:
                    print(f"🗄️ Подключение к БД (попытка {attempt})...")
                    self.pool = await asyncpg.create_pool(
                        self.pg_url,
                        min_size=1,
                        max_size=5,
                        timeout=10,
                    )
                    print("✅ Подключение к БД ОК")
                    return self.pool
                except Exception as e:
                    print(f"❌ Ошибка подключения к БД: {e}")
                    print(f"⏳ Повторная попытка через {delay} секунд...")
                    await asyncio.sleep(delay)

    async def init_db(self) -> None:
        pool = await self.connect()
        sql = """
        CREATE TABLE IF NOT EXISTS game_sources (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            type VARCHAR(20) NOT NULL CHECK (type IN ('steam','official','rss')),
            identifier VARCHAR(100),
            discord_channel_id BIGINT,
            url TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(identifier, discord_channel_id)
        );

        CREATE TABLE IF NOT EXISTS update_logs (
            id SERIAL PRIMARY KEY,
            source_id INTEGER REFERENCES game_sources(id) ON DELETE CASCADE,
            external_id TEXT NOT NULL,
            title TEXT,
            image_url TEXT,
            sent_at TIMESTAMP DEFAULT NOW(),
            UNIQUE (source_id, external_id)
        );

        CREATE TABLE IF NOT EXISTS stats (
            id SERIAL PRIMARY KEY,
            source_id INTEGER REFERENCES game_sources(id) ON DELETE CASCADE,
            updates_sent INTEGER DEFAULT 0,
            last_check TIMESTAMP,
            last_update_received TIMESTAMP,
            UNIQUE(source_id)
        );
        """
        async with pool.acquire() as conn:
            await conn.execute(sql)
        print("✅ Таблицы БД инициализированы")

    async def fetch(self, query: str, *args):
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def execute(self, query: str, *args):
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)


db_manager = DatabaseManager()


async def get_pool() -> asyncpg.Pool:
    return await db_manager.connect()

import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from bot.utils.db import db_manager

load_dotenv()

PROXY_URL = "http://127.0.0.1:10801"

intents = discord.Intents.default()
intents.message_content = True  
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"✅ Бот вошёл как {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Синхронизировано slash-команд: {len(synced)}")
    except Exception as e:
        print(f"❌ Ошибка sync slash-команд: {e}")

async def load_cogs():
    """Загружает все cogs из bot/cogs/"""
    try:
        await bot.load_extension("bot.cogs.admin")
        print("✅ Загружен cog: admin")
    except Exception as e:
        print(f"❌ Ошибка загрузки cog admin: {e}")
    
    try:
        await bot.load_extension("bot.cogs.updates")
        print("✅ Загружен cog: updates")
    except Exception as e:
        print(f"❌ Ошибка загрузки cog updates: {e}")

    try:
        await bot.load_extension("bot.cogs.help")
        print("✅ Загружен cog: help")
    except Exception as e:
        print(f"❌ Ошибка загрузки cog help: {e}")


async def main():
    print("🗄️  Инициализация БД...")
    await db_manager.init_db()

    print("📦 Загрузка cogs...")
    await load_cogs()

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("❌DISCORD_TOKEN не задан в .env")

    bot.http.proxy = PROXY_URL
    
    print("🚀 Запуск бота...\n")

    try: 
        await bot.start('MTQ1MTU5NDQ3Mzg3NTMwODY4Nw.G2A8-5.fO8RWrpG7RNOnH-BISUO04g6K2kPVUC7Mn7_j4')
    except Exception as e:
        import traceback
        print("❌ Ошибка при запуске бота:", repr(e))
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

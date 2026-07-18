import os
import asyncio
import traceback
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from bot.utils.db import db_manager

load_dotenv()

# PROXY_URL = os.getenv("PROXY_URL", "http://127.0.0.1:10808")
APP_VERSION = os.getenv("APP_VERSION", "dev")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN не задан в переменных окружения")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


@bot.event
async def on_ready():
    print(f"✅ Бот вошёл как {bot.user}")
    print(f"🏷️ Версия: {APP_VERSION}")
    print(f"🔌 PROXY_URL={PROXY_URL}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Синхронизировано slash-команд: {len(synced)}")
        for cmd in synced:
            print(f"   • /{cmd.name}")
    except Exception as e:
        print(f"❌ Ошибка sync slash-команд: {e}")


@bot.event
async def on_app_command_completion(interaction: discord.Interaction, command: app_commands.Command):
    print(
        f"✅ Команда /{command.name} выполнена "
        f"(user={interaction.user}, guild={interaction.guild})"
    )


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
):
    """Логируем и отвечаем на ошибки slash-команд (права, чеки, исключения)."""
    cmd_name = getattr(interaction.command, "name", "?")
    print(f"❌ Ошибка slash-команды /{cmd_name}: {type(error).__name__}: {error}")
    print(traceback.format_exc())

    if isinstance(error, app_commands.CheckFailure):
        msg = (
            "❌ Недостаточно прав для этой команды "
            "(нужны права администратора сервера)."
        )
    elif isinstance(error, app_commands.CommandOnCooldown):
        msg = f"⏳ Подожди {error.retry_after:.0f} сек. перед повторным вызовом."
    else:
        original = getattr(error, "original", error)
        msg = f"❌ Ошибка команды: {type(original).__name__}: {original}"

    try:
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
    except Exception as e:
        print(f"❌ Не удалось отправить сообщение об ошибке: {type(e).__name__}: {e}")


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    print(f"❌ Ошибка prefix/hybrid команды: {type(error).__name__}: {error}")
    print(traceback.format_exc())
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Нужны права администратора.")
        return
    if isinstance(error, commands.CheckFailure):
        await ctx.send("❌ Недостаточно прав для этой команды.")
        return

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
    print(f"🏷️ Запуск версии: {APP_VERSION}")
    print("🗄️  Инициализация БД...")
    await db_manager.init_db()

    print("📦 Загрузка cogs...")
    await load_cogs()

    if PROXY_URL:
        bot.http.proxy = PROXY_URL

    print("🚀 Запуск бота...\n")

    try:
        await bot.start(DISCORD_TOKEN)
    except Exception as e:
        print("❌ Ошибка при запуске бота:", repr(e))
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

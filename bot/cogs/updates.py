import os
from datetime import datetime

import discord
from discord.ext import commands, tasks
from discord import app_commands

from bot.utils.db import get_pool
from bot.parsers.dark_darker import get_latest_article as get_latest_dnd
from bot.parsers.lol import get_latest_article_lol
from bot.utils.render import send_patch_article

class UpdatesCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.interval_minutes = int(os.getenv("CHECK_INTERVAL_MINUTES", "15"))
        self.check_updates.change_interval(minutes=self.interval_minutes)
        self.check_updates.start()

    def cog_unload(self) -> None:
        self.check_updates.cancel()

    @tasks.loop(minutes=1)
    async def check_updates(self):
        print(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] Проверка обновлений...")
        pool = await get_pool()

        # 1) Берём все активные источники (и DnD, и LoL, и любые будущие)
        sources = await pool.fetch(
            "SELECT * FROM game_sources WHERE is_active=TRUE"
        )
        if not sources:
            return

        for src in sources:
            source_id = src["id"]
            src_type = src["type"]
            identifier = src["identifier"]
            channel_id = src["discord_channel_id"]

            channel = self.bot.get_channel(channel_id)
            if not channel:
                print("⚠️ Канал не найден:", channel_id)
                continue

            # 2) Выбираем нужный парсер по типу/identifier
            article = None

            if src_type == "official" and identifier == "darkanddarker":
                article = await get_latest_dnd()
            elif src_type == "official" and identifier == "lol":
                article = await get_latest_article_lol()
            else:
                continue

            if not article:
                print(f"⚠️ Не удалось получить последнюю статью для источника {identifier}")
                continue

            # 3) Проверяем, отправляли ли уже (по (source_id, external_id))
            exists = await pool.fetchval(
                "SELECT 1 FROM update_logs WHERE source_id=$1 AND external_id=$2",
                source_id,
                article["external_id"],
            )
            if exists:
                print("ℹ️ Статья уже отправлена:", article.get("external_id"))
                continue

            # 4) Отправляем и логируем
            await send_patch_article(channel, article, source_id=source_id)
            print(f"✅ Отправлено обновление [{identifier}]: {article['title']}")

    @check_updates.before_loop
    async def before_check_updates(self):
        await self.bot.wait_until_ready()
        print(f"✅ Фоновая задача запущена, интервал {self.interval_minutes} мин")

    @commands.hybrid_command(
        name="set_interval",
        description="Изменить интервал автообновления (в минутах).",
    )
    @commands.has_permissions(administrator=True)
    @app_commands.describe(
        interval="Интервал автообновления в минутах (например, 15, 30, 60)"
    )
    @app_commands.choices(
        interval=[
            app_commands.Choice(name="15 минут", value=15),
            app_commands.Choice(name="30 минут", value=30),
            app_commands.Choice(name="60 минут (1 час)", value=60),
            app_commands.Choice(name="120 минут (2 часа)", value=120),
        ]
    )
    async def set_interval(self, ctx: commands.Context, interval: int):
        """Изменить интервал автообновления (в минутах)."""
        minutes = interval

        if minutes < 1 or minutes > 1440:
            await ctx.send("❌ Интервал должен быть от 1 до 1440 минут.")
            return

        self.interval_minutes = minutes
        self.check_updates.change_interval(minutes=minutes)

        await ctx.send(f"✅ Интервал автообновления изменён на **{minutes} мин**.")
        print(f"⏱ Интервал автообновления изменён на {minutes} мин")

async def setup(bot: commands.Bot):
    await bot.add_cog(UpdatesCog(bot))
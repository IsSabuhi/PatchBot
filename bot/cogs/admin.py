import discord
from discord.ext import commands
from discord import app_commands

from bot.utils.db import get_pool
from bot.parsers.dark_darker import get_latest_article
from bot.utils.render import send_patch_article
from bot.parsers.lol import get_latest_article_lol
from bot.parsers.pz import get_latest_article_pz

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

     # -----------------------КОМАНДЫ ДЛЯ DARK AND DARKER-----------------------

    @app_commands.command(
        name="add_darkanddarker",
        description="Привязать Dark and Darker к этому каналу для автообновлений.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_darkanddarker(self, interaction: discord.Interaction):
        channel = interaction.channel
        print(f"🟡 /add_darkanddarker от {interaction.user} в {channel.name}")

        pool = await get_pool()
        try:
            result = await pool.execute(
                """
                INSERT INTO game_sources (name, type, identifier, discord_channel_id, url, is_active)
                VALUES ($1,'official',$2,$3,$4,TRUE)
                ON CONFLICT (identifier, discord_channel_id)
                DO UPDATE SET is_active = TRUE
                """,
                "Dark and Darker",
                "darkanddarker",
                channel.id,
                "https://www.darkanddarker.com/news/all",
            )
            print(f"✅ SQL выполнен: {result}")
            await interaction.response.send_message(
                f"✅ Dark and Darker привязан к каналу {channel.mention}!",
                ephemeral=True,
            )
        except Exception as e:
            import traceback
            print(f"❌ ОШИБКА: {type(e).__name__}: {e}")
            print(traceback.format_exc())
            await interaction.response.send_message(
                f"❌ Ошибка БД: {e}", ephemeral=True
            )

    # --- /list_games --------------------------------------------------------

    @app_commands.command(
        name="list_games",
        description="Показать источники в текущем канале.",
    )
    async def list_games(self, interaction: discord.Interaction):
        channel = interaction.channel
        print(f"🟡 /list_games от {interaction.user} в {channel.name}")

        pool = await get_pool()
        rows = await pool.fetch(
            """
            SELECT name, type, identifier, url
            FROM game_sources
            WHERE discord_channel_id=$1 AND is_active=TRUE
            """,
            channel.id,
        )

        if not rows:
            await interaction.response.send_message(
                "ℹ️ В этом канале ещё нет источников. "
                "Используйте `/add_darkanddarker` чтобы привязать Dark and Darker.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="📰 Источники в этом канале",
            color=discord.Color.blue(),
        )

        for r in rows:
            url_part = f"\nurl: {r['url']}" if r["url"] else ""
            embed.add_field(
                name=r["name"],
                value=(
                    f"type: `{r['type']}`\n"
                    f"id: `{r['identifier']}`"
                    f"{url_part}"
                ),
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # --- /last_update -------------------------------------------------------

    @app_commands.command(
        name="dark_and_darker_new",
        description="Отправить последнее обновление Dark and Darker в этот канал.",
    )
    async def dark_and_darker_new(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        channel = interaction.channel

        pool = await get_pool()
        source = await pool.fetchrow(
            """
            SELECT id FROM game_sources
            WHERE type='official' AND identifier='darkanddarker'
            AND discord_channel_id=$1
            """,
            channel.id,
        )
        source_id = source["id"] if source else None

        article = await get_latest_article()
        if not article:
            await interaction.followup.send(
                "❌ Не удалось получить последнее обновление.",
                ephemeral=True,
            )
            return

        await send_patch_article(channel, article, source_id=source_id)

        if source_id is None:
            await interaction.followup.send(
                "✅ Обновление отправлено.\n"
                "ℹ️ Канал не привязан для автообновлений. "
                "Чтобы получать их автоматически, вызови `/add_darkanddarker`.",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                "✅ Обновление отправлено в канал.", ephemeral=True
            )

    # -----------------------КОМАНДЫ ДЛЯ LEAGUE OF LEGENDS-----------------------

    @app_commands.command(
        name="add_lol",
        description="Привязать League of Legends к этому каналу для автообновлений.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_lol(self, interaction: discord.Interaction):
        """Привязать LoL к текущему каналу (автообновления патчноутов)."""
        channel = interaction.channel
        print(f"🟡 /add_lol от {interaction.user} в {channel.name}")

        pool = await get_pool()
        try:
            result = await pool.execute(
                """
                INSERT INTO game_sources (name, type, identifier, discord_channel_id, url, is_active)
                VALUES ($1,'official',$2,$3,$4,TRUE)
                ON CONFLICT (identifier, discord_channel_id)
                DO UPDATE SET is_active = TRUE
                """,
                "League of Legends",
                "lol",  # identifier для парсера LoL
                channel.id,
                "https://www.leagueoflegends.com/ru-ru/news/tags/patch-notes/",
            )
            print(f"✅ SQL выполнен: {result}")
            await interaction.response.send_message(
                f"✅ League of Legends привязана к каналу {channel.mention}!",
                ephemeral=True,
            )
        except Exception as e:
            import traceback
            print(f"❌ ОШИБКА /add_lol: {type(e).__name__}: {e}")
            print(traceback.format_exc())
            await interaction.response.send_message(
                f"❌ Ошибка БД: {e}", ephemeral=True
            )

    @app_commands.command(
        name="league_of_legends_new",
        description="Отправить последнее описание обновления League of Legends в этот канал.",
    )
    async def league_of_legends_new(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        channel = interaction.channel

        article = await get_latest_article_lol()
        if not article:
            await interaction.followup.send(
                "❌ Не удалось получить последнее обновление League of Legends.",
                ephemeral=True,
            )
            return

        pool = await get_pool()
        source = await pool.fetchrow(
            """
            SELECT id FROM game_sources
            WHERE type='official' AND identifier='lol'
              AND discord_channel_id=$1
            """,
            channel.id,
        )
        source_id = source["id"] if source else None

        await send_patch_article(channel, article, source_id=source_id)

        if source_id is None:
            await interaction.followup.send(
                "✅ Обновление LoL отправлено.\n"
                "ℹ️ Канал не привязан для автообновлений. "
                "Чтобы получать патчноуты автоматически, вызови `/add_lol`.",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                "✅ Обновление League of Legends отправлено в канал.",
                ephemeral=True,
            )

    # -----------------------КОМАНДЫ ДЛЯ PROJECT ZOMBOID-----------------------

    @app_commands.command(
        name="add_pz",
        description="Привязать Project Zomboid к этому каналу для автообновлений.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_pz(self, interaction: discord.Interaction):
        channel = interaction.channel
        print(f"🟡 /add_pz от {interaction.user} в {channel.name}")

        pool = await get_pool()
        try:
            result = await pool.execute(
                """
                INSERT INTO game_sources (name, type, identifier, discord_channel_id, url, is_active)
                VALUES ($1,'official',$2,$3,$4,TRUE)
                ON CONFLICT (identifier, discord_channel_id)
                DO UPDATE SET is_active = TRUE
                """,
                "Project Zomboid",
                "pz",
                channel.id,
                "https://projectzomboid.com/blog/news/",
            )
            print(f"✅ SQL выполнен: {result}")
            await interaction.response.send_message(
                f"✅ Project Zomboid привязан к каналу {channel.mention}!",
                ephemeral=True,
            )
        except Exception as e:
            import traceback
            print(f"❌ ОШИБКА /add_pz: {type(e).__name__}: {e}")
            print(traceback.format_exc())
            await interaction.response.send_message(
                f"❌ Ошибка БД: {e}", ephemeral=True
            )

    @app_commands.command(
        name="project_zomboid_new",
        description="Отправить последнюю новость Project Zomboid в этот канал.",
    )
    async def pz_last_update(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        channel = interaction.channel

        article = await get_latest_article_pz()
        if not article:
            await interaction.followup.send(
                "❌ Не удалось получить последнюю новость Project Zomboid.",
                ephemeral=True,
            )
            return

        pool = await get_pool()
        source = await pool.fetchrow(
            """
            SELECT id FROM game_sources
            WHERE type='official' AND identifier='pz'
              AND discord_channel_id=$1
            """,
            channel.id,
        )
        source_id = source["id"] if source else None

        await send_patch_article(channel, article, source_id=source_id)

        if source_id is None:
            await interaction.followup.send(
                "✅ Новость Project Zomboid отправлена.\n"
                "ℹ️ Канал не привязан для автообновлений. "
                "Чтобы получать новости автоматически, вызови `/add_pz`.",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                "✅ Новость Project Zomboid отправлена в канал.",
                ephemeral=True,
            )



async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))

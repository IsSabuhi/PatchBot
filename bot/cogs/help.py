import discord
from discord.ext import commands
from discord import app_commands

class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="help",
        description="Получить список команд."
    )
    async def help_slash(self, interaction: discord.Interaction):
        """Показать список команд бота."""
        print(f"🟡 /help от {interaction.user} в #{getattr(interaction.channel, 'name', '?')}")
        updates_cog = self.bot.get_cog("UpdatesCog")
        interval = getattr(updates_cog, "interval_minutes", None)
        interval_text = f"{interval} мин" if interval is not None else "по умолчанию"

        embed = discord.Embed(
            title="📖 PatchBot — справка",
            description=(
                "Бот для отслеживания обновлений Dark and Darker и League of Legends.\n"
                "Ручные команды доступны в любом канале, автообновления — только в привязанных."
            ),
            color=discord.Color.blurple(),
        )

        embed.add_field(
            name="⚙️ Админ / настройка (Dark and Darker)",
            value=(
                "`/add_darkanddarker` — привязать Dark and Darker к этому каналу.\n"
                "`/list_games` — список источников в текущем канале.\n"
                "`/set_interval <мин>` — задать интервал автообновления.\n"
                f"Текущий интервал автообновления: **{interval_text}**.\n"
            ),
            inline=False,
        )

        embed.add_field(
            name="📰 Обновления (Dark and Darker)",
            value=(
                "`/dark_and_darker_new` — отправить последнее обновление вручную.\n"
                "Автообновления патчей приходят по расписанию **только в привязанные каналы**."
            ),
            inline=False,
        )

        embed.add_field(
            name="⚙️ Админ / настройка (League of Legends)",
            value=(
                "`/add_lol` — привязать League of Legends к этому каналу для автообновлений.\n"
            ),
            inline=False,
        )

        embed.add_field(
            name="📰 Обновления (League of Legends)",
            value=(
                "`/league_of_legends_new` — отправить последнее обновлениe LoL.\n"
                "Автообновления патчей приходят по расписанию **только в привязанные каналы**."
            ),
            inline=False,
        )

        embed.add_field(
            name="⚙️ Админ / настройка (Project Zomboid)",
            value="`/add_pz` — привязать Project Zomboid к этому каналу для автообновлений.",
            inline=False,
        )

        embed.add_field(
            name="📰 Обновления (Project Zomboid)",
            value=(
                "`/project_zomboid_new` — отправить последнюю новость Project Zomboid.\n"
               "Автообновления патчей приходят по расписанию **только в привязанные каналы**."
            ),
            inline=False,
        )

        embed.set_footer(text="PatchBot • Discord updates notifier")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))

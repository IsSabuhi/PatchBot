import traceback

import discord
from bot.utils.html_cleaner import split_by_h3, split_long_text
from bot.utils.translator import translate_to_ru
from bot.utils.db import get_pool


async def send_patch_article(ctx_or_channel, article: dict, source_id: int | None = None):
    sender = ctx_or_channel
    print(
        f"📤 send_patch_article: title={article.get('title')!r} "
        f"url={article.get('url')} source_id={source_id}"
    )

    try:
        print("🔤 Перевод заголовка/интро...")
        title_ru = await translate_to_ru(article["title"])
        intro_ru = await translate_to_ru(article["description"])
        print(f"🔤 Заголовок RU: {title_ru!r}")

        game_name = "Patch"
        icon_url = None
        url = article.get("url", "") or ""
        if "leagueoflegends" in url:
            game_name = "League of Legends"
            icon_url = "https://ddragon.leagueoflegends.com/cdn/15.24.1/img/profileicon/588.png"
        elif "projectzomboid" in url:
            game_name = "Project Zomboid"
            icon_url = None
        else:
            game_name = "Dark and Darker"
            icon_url = "https://front.darkanddarker.com/favicon.ico"

        main_embed = discord.Embed(
            title=f"🎮 {title_ru}",
            description=intro_ru or " ",
            color=discord.Color.gold(),
            url=article.get("url"),
        )

        if article.get("image"):
            main_embed.set_image(url=article["image"])

        if article.get("date"):
            footer_text = f"📅 {article['date']} | {game_name}"
            if icon_url:
                main_embed.set_footer(text=footer_text, icon_url=icon_url)
            else:
                main_embed.set_footer(text=footer_text)

        await sender.send(embed=main_embed)
        print("✅ Отправлен главный embed")

        full_html = article.get("description_full", "")
        if isinstance(full_html, str) and full_html.strip():
            sections = split_by_h3(full_html)
            print(f"📄 Секций для отправки: {len(sections)}")

            for section in sections:
                title_section = section["title"]
                content_section = section["content"]

                title_ru_section = await translate_to_ru(title_section)
                content_ru_section = await translate_to_ru(content_section)

                if len(content_ru_section) > 2048:
                    parts = split_long_text(content_ru_section, 2048)
                    for i, part in enumerate(parts, 1):
                        part_embed = discord.Embed(
                            title=f"{title_ru_section} (часть {i}/{len(parts)})",
                            description=part,
                            color=discord.Color.blue(),
                        )
                        await sender.send(embed=part_embed)
                else:
                    section_embed = discord.Embed(
                        title=title_ru_section,
                        description=content_ru_section or " ",
                        color=discord.Color.blue(),
                    )
                    await sender.send(embed=section_embed)

        champs = article.get("champs") or []
        if champs:
            print(f"🎮 Чемпионов для отправки: {len(champs)}")
        for champ in champs:
            name = champ.get("name") or "Изменения"
            intro = champ.get("intro") or ""
            items = champ.get("items") or []
            image_url = champ.get("image")

            text = intro
            if items:
                text = text + ("\n\n" if text else "") + "\n".join(f"• {i}" for i in items)

            name_ru = await translate_to_ru(name)
            text_ru = await translate_to_ru(text) if text else " "

            embed = discord.Embed(
                title=name_ru,
                description=text_ru[:4096],
                color=discord.Color.green(),
            )
            if image_url:
                embed.set_thumbnail(url=image_url)

            await sender.send(embed=embed)

        if source_id is not None:
            pool = await get_pool()
            await pool.execute(
                """
                INSERT INTO update_logs (source_id, external_id, title, image_url)
                VALUES ($1,$2,$3,$4)
                ON CONFLICT (source_id, external_id) DO NOTHING
                """,
                source_id,
                article["external_id"],
                title_ru,
                article.get("image"),
            )
            print(f"🗄️ Записано в update_logs: {article.get('external_id')}")

        print("✅ send_patch_article завершён")
    except Exception as e:
        print(f"❌ Ошибка send_patch_article: {type(e).__name__}: {e}")
        print(traceback.format_exc())
        raise

import discord
from bot.utils.html_cleaner import split_by_h3, split_long_text
from bot.utils.translator import translate_to_ru
from bot.utils.db import get_pool

async def send_patch_article(ctx_or_channel, article: dict, source_id: int | None = None):
    if hasattr(ctx_or_channel, "send"):
        sender = ctx_or_channel
    else:
        sender = ctx_or_channel

    # Перевод заголовка и интро
    title_ru = await translate_to_ru(article["title"])
    intro_ru = await translate_to_ru(article["description"])

    # Определяем имя игры для футера по identifier/source_id (если хочешь красиво)
    game_name = "Patch"
    icon_url = None
    # Простой вариант: по URL
    if "leagueoflegends" in article.get("url", ""):
        game_name = "League of Legends"
        icon_url = "https://ddragon.leagueoflegends.com/cdn/15.24.1/img/profileicon/588.png"
    else:
        game_name = "Dark and Darker"
        icon_url = "https://front.darkanddarker.com/favicon.ico"

    # --- Первый embed (шапка) ---
    main_embed = discord.Embed(
        title=f"🎮 {title_ru}",
        description=intro_ru,
        color=discord.Color.gold(),
        url=article["url"],
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

    # --- Секции по h3 ---
    full_html = article.get("description_full", "")
    if isinstance(full_html, str) and full_html.strip():
        sections = split_by_h3(full_html)

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
                    description=content_ru_section,
                    color=discord.Color.blue(),
                )
                await sender.send(embed=section_embed)

    # --- Чемпионы (LoL) ---
    champs = article.get("champs") or []
    for champ in champs:
        name = champ.get("name") or "Изменения"
        intro = champ.get("intro") or ""
        items = champ.get("items") or []
        image_url = champ.get("image")

        text = intro
        if items:
            text = text + ("\n\n" if text else "") + "\n".join(f"• {i}" for i in items)

        # Перевод
        name_ru = await translate_to_ru(name)
        text_ru = await translate_to_ru(text) if text else " "

        embed = discord.Embed(
            title=name_ru,
            description=text_ru[:4096],  # лимит Discord
            color=discord.Color.green(),
        )
        if image_url:
            embed.set_thumbnail(url=image_url)

        await sender.send(embed=embed)


    # --- Логирование ---
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
            article["image"],
        )

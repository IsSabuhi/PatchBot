import aiohttp
from bs4 import BeautifulSoup
from typing import Optional, Dict

from bot.utils.html_cleaner import clean_html_text  

BASE_URL = "https://www.leagueoflegends.com"
PATCHES_TAG_URL = f"{BASE_URL}/ru-ru/news/tags/patch-notes/"

async def fetch_html(url: str) -> Optional[str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=15) as resp:
            if resp.status != 200:
                print("❌ LoL HTTP", resp.status, url)
                return None
            return await resp.text()


async def get_latest_article_lol() -> Optional[Dict]:
    """
    Получить последнее RU-описание обновления LoL.
    Формат результата совместим с send_patch_article:
    external_id, title, description, description_full, image, date, url
    """
    # 1) Страница списка патчноутов
    index_html = await fetch_html(PATCHES_TAG_URL)
    if not index_html:
        return None

    index_soup = BeautifulSoup(index_html, "lxml")

    # Ищем первую ссылку на game-updates/patch-...-notes
    article_link = None
    for a in index_soup.find_all("a", href=True):
        href = a["href"]
        if "/ru-ru/news/game-updates/" in href and "patch" in href and "notes" in href:
            article_link = href
            break

    if not article_link:
        print("❌ LoL: не нашёл ссылку на патчноут на странице тегов")
        return None

    if article_link.startswith("http"):
        article_url = article_link
    else:
        article_url = BASE_URL + article_link

    external_id = article_url.rstrip("/").split("/")[-1]

    # 2) Загружаем саму статью
    article_html = await fetch_html(article_url)
    if not article_html:
        return None

    article_soup = BeautifulSoup(article_html, "lxml")

    # Заголовок
    title_tag = article_soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else external_id

    # Дата
    date_text = ""
    time_tag = article_soup.find("time")
    if time_tag and time_tag.has_attr("datetime"):
        date_text = time_tag["datetime"]
    elif time_tag:
        date_text = time_tag.get_text(strip=True)

    # Картинка (og:image)
    image = ""
    og_img = article_soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        image = og_img["content"]

    # Основной контейнер патчноутов
    root = article_soup.find("div", id="patch-notes-container")
    if not root:
        print("⚠️ LoL: не найден div#patch-notes-container, возвращаю только заголовок")
        return {
            "external_id": external_id,
            "title": title,
            "description": "",
            "description_full": "",
            "image": image,
            "date": date_text,
            "url": article_url,
        }

    skip_titles = ["СВЯТИЛИЩЕ", "ВАШ МАГАЗИН", "ЧЕМПИОН", "РУНЫ", "АРЕНА"]

    # 1) Интро из blockquote.context
    intro_block = root.find("blockquote", class_="blockquote context")
    intro_text = ""
    if intro_block:
        intro_html = "".join(str(child) for child in intro_block.children)
        intro_text = clean_html_text(intro_html)

    # 2) Только крупные секции по header-primary
    sections_html = []
    for header in root.find_all("header", class_="header-primary"):
        h2 = header.find("h2")
        if not h2:
            continue
        title_section = h2.get_text(strip=True)

        # фильтрация по заголовку
        title_upper = title_section.upper()
        if any(skip in title_upper for skip in skip_titles):
            continue

        content_div = header.find_next_sibling("div", class_="content-border")
        if not content_div:
            continue

        content_html = "".join(str(child) for child in content_div.children)
        sections_html.append((title_section, content_html))

    description_full = ""
    for title_section, content_html in sections_html:
        description_full += f"<h3>{title_section}</h3>{content_html}"

    return {
        "external_id": external_id,
        "title": title,
        "description": intro_text,
        "description_full": description_full,
        "image": image,
        "date": date_text,
        "url": article_url,
    }
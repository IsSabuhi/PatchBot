import os
import re
import aiohttp

PROXY_URL = os.getenv("PROXY_URL", "").strip() or None

_CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")


def _log(msg: str) -> None:
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "replace").decode("ascii"))


def _looks_russian(text: str) -> bool:
    """Если кириллицы уже много — считаем текст русским и не гоняем в переводчик."""
    cyr = len(_CYRILLIC_RE.findall(text))
    latin = sum(1 for c in text if ("a" <= c.lower() <= "z"))
    if cyr == 0:
        return False
    return cyr >= max(12, latin // 2)


async def _translate_once(
    session: aiohttp.ClientSession,
    text: str,
    *,
    proxy: str | None,
) -> str | None:
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": "ru",
        "dt": "t",
        "q": text,
    }
    kwargs = {"params": params, "timeout": aiohttp.ClientTimeout(total=20)}
    if proxy:
        kwargs["proxy"] = proxy

    async with session.get(url, **kwargs) as response:
        if response.status != 200:
            body = await response.text()
            _log(
                f"[translate] HTTP {response.status} "
                f"(proxy={proxy or 'direct'}): {body[:120]}"
            )
            return None
        data = await response.json()
        if not data or not data[0]:
            return None
        return "".join(part[0] for part in data[0] if part and part[0])


async def translate_to_ru(text: str) -> str:
    """Перевод EN→RU через Google Translate. Прокси → fallback без прокси."""
    if not text or not text.strip():
        return text

    if _looks_russian(text):
        return text

    # Google gtx нормально переваривает ~1.5–2k символов за запрос
    chunks: list[str] = []
    remaining = text
    max_chunk = 1500
    while remaining:
        if len(remaining) <= max_chunk:
            chunks.append(remaining)
            break
        cut = remaining.rfind("\n", 0, max_chunk)
        if cut < max_chunk // 2:
            cut = remaining.rfind(" ", 0, max_chunk)
        if cut < max_chunk // 2:
            cut = max_chunk
        chunks.append(remaining[:cut])
        remaining = remaining[cut:].lstrip()

    translated_parts: list[str] = []
    async with aiohttp.ClientSession() as session:
        for i, chunk in enumerate(chunks, 1):
            result = None
            attempts: list[str | None] = []
            if PROXY_URL:
                attempts.append(PROXY_URL)
            attempts.append(None)  # direct fallback

            for proxy in attempts:
                label = proxy or "direct"
                try:
                    result = await _translate_once(session, chunk, proxy=proxy)
                    if result is not None:
                        if i == 1:
                            _log(f"[translate] OK via {label} ({len(chunks)} chunk(s))")
                        break
                except Exception as e:
                    _log(f"[translate] fail via {label}: {type(e).__name__}: {e}")

            if result is None:
                _log("[translate] leaving original chunk untranslated")
                translated_parts.append(chunk)
            else:
                translated_parts.append(result)

    return "".join(translated_parts) if len(chunks) == 1 else "\n".join(translated_parts)

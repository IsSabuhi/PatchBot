import re
from html.parser import HTMLParser
from typing import List, Dict

class HTMLStripper(HTMLParser):
    """Убирает HTML теги"""
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text: List[str] = []

    def handle_data(self, d):
        self.text.append(d)

    def get_text(self):
        return ''.join(self.text)


def strip_html(html: str) -> str:
    """Убрать HTML теги"""
    s = HTMLStripper()
    try:
        s.feed(html)
        return s.get_text()
    except:
        return html


def clean_html_text(html_text: str) -> str:
    """
    Очистить HTML текст и форматировать для Discord:
    - <h3>...</h3> → **...**
    - <ol>, <li> → • пункты
    - <p> → новые строки
    - Убрать пустые строки
    """
    
    # Заменяем заголовки на жирный текст
    html_text = re.sub(r'<h\d+>(.*?)</h\d+>', r'\n**\1**\n', html_text)
    
    # Заменяем <ol>/<ul> списки
    html_text = re.sub(r'</?ol>', '', html_text)
    html_text = re.sub(r'</?ul>', '', html_text)
    html_text = re.sub(r'<li[^>]*>(.*?)</li>', r'\n• \1', html_text)  # ← добавляем \n перед •
    
    # Заменяем <p> на новые строки
    html_text = re.sub(r'</p>', '\n', html_text)
    html_text = re.sub(r'<p[^>]*>', '', html_text)
    
    # Убираем другие теги
    html_text = re.sub(r'<[^>]+>', '', html_text)
    
    # Декодируем HTML сущности
    html_text = html_text.replace('&nbsp;', ' ')
    html_text = html_text.replace('&quot;', '"')
    html_text = html_text.replace('&#39;', "'")
    html_text = html_text.replace('&amp;', '&')
    
    # Убираем пустые строки
    lines = [line.strip() for line in html_text.split('\n')]
    lines = [line for line in lines if line]
    
    # Если строка начинается с •, оставляем как есть, иначе может быть обычная строка
    result = '\n'.join(lines)
    
    return result

def split_by_h3(html_text: str) -> List[Dict[str, str]]:
    """
    Разделить HTML текст по h3 тегам
    Вернёт список словарей с ключами 'title' (заголовок h3) и 'content' (содержимое)
    
    Пример:
    [
        {'title': 'Bugfixes:', 'content': '• Fixed...\\n• Fixed...'},
        {'title': 'Game Updates:', 'content': '• Improved...\\n• Performance...'}
    ]
    """
    
    # Разделяем по <h3>
    sections = re.split(r'<h3>(.*?)</h3>', html_text)
    
    result = []
    
    # sections будет: ['текст до первого h3', 'заголовок 1', 'содержимое 1', 'заголовок 2', 'содержимое 2', ...]
    for i in range(1, len(sections), 2):
        if i + 1 < len(sections):
            title = sections[i].strip()
            content_html = sections[i + 1].strip()
            
            # Очищаем содержимое от HTML
            content = clean_html_text(content_html)
            
            if content:  # Только если есть содержимое
                result.append({
                    'title': title,
                    'content': content
                })
    
    return result


def truncate_text(text: str, max_length: int = 1024) -> str:
    """Обрезать текст до максимальной длины Discord embed"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def split_long_text(text: str, max_length: int = 1024) -> List[str]:
    """Разделить длинный текст на части по максимальной длине"""
    if len(text) <= max_length:
        return [text]
    
    parts = []
    current_part = ""
    
    # Разделяем по строкам (по \n)
    lines = text.split('\n')
    
    for line in lines:
        if len(current_part) + len(line) + 1 <= max_length:
            if current_part:
                current_part += '\n' + line
            else:
                current_part = line
        else:
            if current_part:
                parts.append(current_part)
            current_part = line
    
    if current_part:
        parts.append(current_part)
    
    return parts

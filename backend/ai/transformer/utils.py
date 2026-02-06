import re
from datetime import date
from typing import Optional


def extract_id(text: str) -> Optional[int]:
    if not text:
        return None
    patterns = [
        r"\bID[:=]?\s*(\d+)\b",
        r"\bid[:=]?\s*(\d+)\b",
        r"#(\d+)\b",
        r"任务\s*(\d+)\b",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return int(m.group(1))
    return None


def extract_due_date(text: str) -> Optional[str]:
    if not text:
        return None
    m = re.search(r"\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b", text)
    if m:
        yyyy, mm, dd = m.group(1), int(m.group(2)), int(m.group(3))
        if 1 <= mm <= 12 and 1 <= dd <= 31:
            return f"{yyyy}-{mm:02d}-{dd:02d}"

    m = re.search(r"\b(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日\b", text)
    if m:
        yyyy, mm, dd = m.group(1), int(m.group(2)), int(m.group(3))
        if 1 <= mm <= 12 and 1 <= dd <= 31:
            return f"{yyyy}-{mm:02d}-{dd:02d}"

    m = re.search(r"\b(\d{1,2})\s*月\s*(\d{1,2})\s*日\b", text)
    if m:
        yyyy = date.today().year
        mm, dd = int(m.group(1)), int(m.group(2))
        if 1 <= mm <= 12 and 1 <= dd <= 31:
            return f"{yyyy}-{mm:02d}-{dd:02d}"

    if "今天" in text:
        d = date.today()
        return f"{d.year}-{d.month:02d}-{d.day:02d}"
    if "明天" in text:
        d = date.fromordinal(date.today().toordinal() + 1)
        return f"{d.year}-{d.month:02d}-{d.day:02d}"
    if "后天" in text:
        d = date.fromordinal(date.today().toordinal() + 2)
        return f"{d.year}-{d.month:02d}-{d.day:02d}"
    if "today" in text.lower():
        d = date.today()
        return f"{d.year}-{d.month:02d}-{d.day:02d}"
    if "tomorrow" in text.lower():
        d = date.fromordinal(date.today().toordinal() + 1)
        return f"{d.year}-{d.month:02d}-{d.day:02d}"
    if "day after tomorrow" in text.lower():
        d = date.fromordinal(date.today().toordinal() + 2)
        return f"{d.year}-{d.month:02d}-{d.day:02d}"

    return None

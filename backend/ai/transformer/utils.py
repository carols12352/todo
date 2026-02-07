import re
from datetime import date
from typing import Optional


_CN_NUM = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}


def _parse_cn_number(s: str) -> Optional[int]:
    if not s:
        return None
    s = s.strip()
    if not s:
        return None
    if s.isdigit():
        return int(s)

    # Common forms for time: 十 / 十一 / 二十 / 二十三
    if "十" in s:
        tens_part, ones_part = s.split("十", 1)
        if tens_part == "":
            tens = 1
        else:
            tens = _CN_NUM.get(tens_part)
            if tens is None:
                return None
        val = tens * 10
        if ones_part:
            ones = _CN_NUM.get(ones_part)
            if ones is None:
                return None
            val += ones
        return val

    if len(s) == 1:
        return _CN_NUM.get(s)

    return None


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


def extract_time(text: str) -> Optional[str]:
    if not text:
        return None

    # 8:30 / 08:30 / 20:05
    m = re.search(r"\b(\d{1,2})\s*:\s*(\d{2})\b", text)
    if m:
        hh, mm = int(m.group(1)), int(m.group(2))
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            return f"{hh:02d}:{mm:02d}"

    # 下午三点 / 下午3点 / 晚上8点半 / 上午十点一刻
    m = re.search(
        r"(凌晨|早上|上午|中午|下午|晚上)?\s*"
        r"([0-9]{1,2}|[零〇一二两三四五六七八九十]{1,3})\s*(?:点|时)\s*"
        r"(半|一刻|三刻|([0-9]{1,2}|[零〇一二两三四五六七八九十]{1,3})\s*分?)?",
        text,
    )
    if m:
        period = m.group(1) or ""
        hh = _parse_cn_number(m.group(2))
        if hh is None:
            return None

        mm_token = (m.group(3) or "").strip()
        mm = 0
        if mm_token:
            if mm_token == "半":
                mm = 30
            elif mm_token == "一刻":
                mm = 15
            elif mm_token == "三刻":
                mm = 45
            else:
                mm_clean = mm_token.replace("分", "").strip()
                mm_val = _parse_cn_number(mm_clean)
                if mm_val is None:
                    return None
                mm = mm_val

        # Map period to 24h.
        if period in ("下午", "晚上", "中午"):
            if 1 <= hh <= 11:
                hh += 12
        elif period == "凌晨":
            if hh == 12:
                hh = 0

        if 0 <= hh <= 23 and 0 <= mm <= 59:
            return f"{hh:02d}:{mm:02d}"

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

    # Order matters: "大后天" contains "后天".
    if "大后天" in text:
        d = date.fromordinal(date.today().toordinal() + 3)
        return f"{d.year}-{d.month:02d}-{d.day:02d}"
    if "后天" in text:
        d = date.fromordinal(date.today().toordinal() + 2)
        return f"{d.year}-{d.month:02d}-{d.day:02d}"
    if "明天" in text:
        d = date.fromordinal(date.today().toordinal() + 1)
        return f"{d.year}-{d.month:02d}-{d.day:02d}"
    if "今天" in text:
        d = date.today()
        return f"{d.year}-{d.month:02d}-{d.day:02d}"

    lower = text.lower()
    # Order matters: "day after tomorrow" contains "tomorrow".
    if "day after tomorrow" in lower:
        d = date.fromordinal(date.today().toordinal() + 2)
        return f"{d.year}-{d.month:02d}-{d.day:02d}"
    if "tomorrow" in lower:
        d = date.fromordinal(date.today().toordinal() + 1)
        return f"{d.year}-{d.month:02d}-{d.day:02d}"
    if "today" in lower:
        d = date.today()
        return f"{d.year}-{d.month:02d}-{d.day:02d}"

    return None

# -*- coding: utf-8 -*-
"""
telegram_sender.py
-------------------
مسؤول فقط عن إرسال نص (التقرير النهائي) إلى محادثة تلجرام محددة،
باستخدام Telegram Bot API مباشرة عبر requests (بدون مكتبات ثقيلة إضافية).
"""

import logging
import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)


def send_telegram_message(text: str) -> bool:
    """
    يرسل رسالة نصية بصيغة Markdown إلى TELEGRAM_CHAT_ID.
    يرجع True إذا نجح الإرسال، False إذا فشل (مع تسجيل الخطأ في اللوج).
    """
    if not text.strip():
        logger.warning("تم استلام نص فارغ، تم تجاهل الإرسال.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # تلجرام يحد طول الرسالة بـ 4096 حرف، نقسّم النص لو كان أطول
    chunks = _split_message(text, max_length=4000)

    success = True
    for chunk in chunks:
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        try:
            response = requests.post(url, json=payload, timeout=20)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"فشل إرسال الرسالة إلى تلجرام: {e}")
            success = False

    return success


def _split_message(text: str, max_length: int = 4000) -> list[str]:
    """
    يقسّم نصاً طويلاً إلى أجزاء أصغر من الحد الأقصى المسموح به في تلجرام،
    مع محاولة التقسيم عند فواصل الأسطر للحفاظ على شكل Markdown.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    current = ""

    for line in text.split("\n"):
        if len(current) + len(line) + 1 > max_length:
            chunks.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line

    if current:
        chunks.append(current)

    return chunks

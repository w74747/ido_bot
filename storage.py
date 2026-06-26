# -*- coding: utf-8 -*-
"""
storage.py
----------
تخزين بسيط جداً (ملف JSON محلي) لحفظ معرّفات المشاريع التي تمت
معالجتها مسبقاً، حتى لا يرسل البوت نفس المشروع للتلجرام أكثر من مرة
في كل دورة فحص.

ملاحظة: على Railway، نظام الملفات قد يُعاد تصفيره مع كل Deploy جديد
(حسب نوع الخدمة)، فهذا التخزين "أفضل من لا شيء" لكنه ليس دائماً 100%.
إذا أردت ضماناً كاملاً لاحقاً يمكن استبداله بقاعدة بيانات بسيطة
(مثل Redis أو SQLite على Volume دائم).
"""

import json
import logging
import os

from config import PROCESSED_IDS_FILE

logger = logging.getLogger(__name__)


def load_processed_ids() -> set:
    """يحمّل معرّفات المشاريع المعالجة سابقاً من الملف، أو يرجع مجموعة فاضية."""
    if not os.path.exists(PROCESSED_IDS_FILE):
        return set()

    try:
        with open(PROCESSED_IDS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"تعذّر قراءة ملف المعرّفات المعالجة: {e}")
        return set()


def save_processed_ids(processed_ids: set) -> None:
    """يحفظ مجموعة المعرّفات المعالجة في الملف (يستبدل المحتوى القديم)."""
    try:
        with open(PROCESSED_IDS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(processed_ids), f, ensure_ascii=False)
    except OSError as e:
        logger.warning(f"تعذّر حفظ ملف المعرّفات المعالجة: {e}")

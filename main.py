# -*- coding: utf-8 -*-
"""
main.py
-------
نقطة التشغيل الرئيسية للبوت. يقوم بحلقة تكرارية:
1. يجلب المشاريع القادمة (IDOs) من المصدر المُفعّل.
2. يستبعد المشاريع التي تمت معالجتها سابقاً.
3. يرسل كل مشروع جديد إلى نموذج اللغة للتحليل الشرعي والاستثماري.
4. إذا كان الرد ليس كلمة "تجاهل"، يرسل التقرير الناتج إلى تلجرام.
5. ينتظر فترة محددة (POLL_INTERVAL_MINUTES) ثم يكرر العملية.

تشغيل محلي:
    python main.py

تشغيل على Railway:
    يكفي رفع الكود وضبط الـ Environment Variables، Railway سيشغّل
    هذا الملف تلقائياً إذا كان معرّفاً كـ Start Command (راجع README).
"""

import logging
import time

try:
    # تحميل المتغيرات من ملف .env إن وُجد (مفيد للتشغيل المحلي فقط).
    # على Railway هذا غير ضروري لأن المتغيرات تُضبط من تبويب Variables مباشرة،
    # لكن وجوده هنا لا يسبب أي مشكلة إذا لم يكن الملف موجوداً.
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from config import validate_config, POLL_INTERVAL_MINUTES, IGNORE_KEYWORD
from ido_source import fetch_upcoming_ido_projects
from llm_analyzer import analyze_project
from telegram_sender import send_telegram_message
from storage import load_processed_ids, save_processed_ids

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_single_cycle(processed_ids: set) -> set:
    """
    يشغّل دورة فحص واحدة كاملة: جلب → فلترة → تحليل → إرسال.
    يرجع مجموعة المعرّفات المحدثة بعد إضافة أي مشاريع جديدة تمت معالجتها.
    """
    projects = fetch_upcoming_ido_projects()

    if not projects:
        logger.info("لا توجد مشاريع جديدة في هذه الدورة، أو فشل الجلب من المصدر.")
        return processed_ids

    new_projects = [p for p in projects if p["id"] not in processed_ids]
    logger.info(f"عدد المشاريع الجديدة (لم تُعالج سابقاً): {len(new_projects)}")

    for project in new_projects:
        logger.info(f"تحليل المشروع: {project.get('name', 'غير معروف')}")

        analysis_result = analyze_project(project)

        if not analysis_result:
            logger.warning(f"لم يصل رد من نموذج اللغة للمشروع: {project.get('name')}")
            continue

        cleaned_result = analysis_result.strip()

        if cleaned_result == IGNORE_KEYWORD or IGNORE_KEYWORD in cleaned_result[:20]:
            logger.info(f"تم استبعاد المشروع '{project.get('name')}' حسب معايير الفلترة.")
        else:
            sent = send_telegram_message(cleaned_result)
            if sent:
                logger.info(f"تم إرسال تقرير المشروع '{project.get('name')}' إلى تلجرام بنجاح.")
            else:
                logger.error(f"فشل إرسال تقرير المشروع '{project.get('name')}' إلى تلجرام.")

        # نضيف المعرّف للمعالجة بغض النظر عن نتيجة الفلترة، لتجنب إعادة تحليله لاحقاً
        processed_ids.add(project["id"])

    return processed_ids


def main():
    logger.info("بدء تشغيل بوت تحليل وفلترة مشاريع IDO...")
    validate_config()

    processed_ids = load_processed_ids()
    logger.info(f"تم تحميل {len(processed_ids)} معرّف مشروع تمت معالجته سابقاً.")

    while True:
        try:
            processed_ids = run_single_cycle(processed_ids)
            save_processed_ids(processed_ids)
        except Exception as e:
            # نلتقط أي خطأ غير متوقع حتى لا يتوقف البوت بالكامل بسبب دورة واحدة فاشلة
            logger.exception(f"حدث خطأ غير متوقع في دورة الفحص: {e}")

        logger.info(f"انتظار {POLL_INTERVAL_MINUTES} دقيقة قبل الدورة التالية...")
        time.sleep(POLL_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    main()

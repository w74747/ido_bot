# -*- coding: utf-8 -*-
"""
early_stage_source.py
----------------------
يجلب إشارات "مبكرة جداً" عن مشاريع RWA والبنية التحتية (Infra/DePIN)،
أي جولات تمويل (Funding Rounds) قبل وصول المشروع أصلاً لمرحلة الإعلان
عن IDO رسمي على منصات مثل CryptoRank.

يدعم مصدرين تكميليين (يعملان بجانب CryptoRank وليس بدلاً عنه):

1. RootData — تغطية واسعة لجولات التمويل مع تصنيفات دقيقة (RWA/Infra/DePIN/AI).
   يحتاج مفتاح API (ROOTDATA_API_KEY)، ويُفعَّل/يُعطَّل عبر ENABLE_ROOTDATA.
   التوثيق الرسمي: https://docs.rootdata.com/

2. DefiLlama — endpoint جولات التمويل (/raises) أصبح حسب التوثيق الرسمي
   الحالي (https://api-docs.defillama.com/llms.txt) جزءاً من الباقة
   المدفوعة "Pro API" ($300/شهر عبر https://defillama.com/subscription)،
   وليس مجانياً كما كان سابقاً. لذلك أصبح يتطلب DEFILLAMA_API_KEY (اختياري:
   لو لم يُضبط، يتم تخطي DefiLlama تلقائياً بدل إرجاع خطأ 402 متكرر).
   يُفعَّل/يُعطَّل عبر ENABLE_DEFILLAMA.

ملاحظة مهمة حول RootData:
- بعض endpoints (من ضمنها endpoint جولات التمويل بالجملة) متاحة فقط في
  باقتي Plus أو Pro حسب التوثيق الرسمي. الخطة الأساسية (Basic/مجانية)
  تدعم بحث المشاريع والمستثمرين، وقد لا تتضمن كل تفاصيل التمويل بالجملة.
  راجع باقتك الفعلية على https://www.rootdata.com/Api وعدّل المسار
  إن لزم.
"""

import time
import requests
import logging

from config import (
    ENABLE_ROOTDATA, ROOTDATA_API_KEY,
    ENABLE_DEFILLAMA, DEFILLAMA_API_KEY,
    EARLY_STAGE_LOOKBACK_DAYS,
)

logger = logging.getLogger(__name__)

ROOTDATA_BASE_URL = "https://api.rootdata.com/open"
DEFILLAMA_FREE_RAISES_URL = "https://api.llama.fi/raises"

# الكلمات المفتاحية التي تساعد على تصنيف جولة التمويل كـ RWA/Infra/DePIN/AI
# مبكرة (هذا فلتر أولي بسيط، الفلترة الدقيقة والنهائية تتم لاحقاً عبر الـ LLM)
EARLY_STAGE_KEYWORDS = [
    "rwa", "real world asset", "tokeniz", "real estate", "sukuk",
    "infrastructure", "l1", "l2", "layer 1", "layer 2", "depin",
    "privacy", "security protocol", "ai", "artificial intelligence",
    "cloud computing", "data storage", "compute",
]


def fetch_early_stage_projects() -> list[dict]:
    """
    نقطة الدخول الموحّدة لمصادر المراحل المبكرة جداً.
    تدمج نتائج RootData وDefiLlama (كل مصدر مفعّل حسب config) بشكل موحّد
    الشكل، بنفس بنية المشاريع المستخدمة في ido_source.py، لتسهيل تمريرها
    لنفس مسار التحليل والفلترة في main.py.
    """
    projects = []

    if ENABLE_ROOTDATA:
        projects.extend(_fetch_from_rootdata())

    if ENABLE_DEFILLAMA:
        projects.extend(_fetch_from_defillama_raises())

    return projects


def _fetch_from_rootdata() -> list[dict]:
    """
    يجلب أحدث جولات التمويل من RootData باستخدام endpoint جولات التمويل
    بالجملة (Get Fundraising rounds in batches). يتطلب باقة Plus/Pro حسب
    التوثيق الرسمي.
    """
    if not ROOTDATA_API_KEY:
        logger.warning("ENABLE_ROOTDATA=true لكن ROOTDATA_API_KEY غير مضبوط، تم التجاوز.")
        return []

    url = f"{ROOTDATA_BASE_URL}/get_fac"
    headers = {
        "apikey": ROOTDATA_API_KEY,
        "language": "en",
        "Content-Type": "application/json",
    }
    payload = {"page": 1, "page_size": 50}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.error(f"فشل الاتصال بـ RootData API: {e}")
        return []

    if data.get("result") != 200:
        logger.warning(f"RootData رجع نتيجة غير ناجحة: {data.get('message', 'بدون رسالة')}")
        return []

    raw_items = (data.get("data") or {}).get("items", [])
    normalized = []

    for item in raw_items:
        project_name = item.get("project_name", item.get("name", "غير معروف"))
        tags = item.get("tags") or item.get("track") or []
        tags_text = " ".join(tags) if isinstance(tags, list) else str(tags)

        if not _looks_like_target_category(f"{project_name} {tags_text}"):
            continue

        normalized.append({
            "id": f"rootdata-{item.get('fac_id', item.get('id', project_name))}",
            "name": project_name,
            "network": item.get("ecosystem", "غير محدد"),
            "category": tags_text or "غير محدد",
            "description": item.get("introduce", item.get("description", "")),
            "launch_date": item.get("date", item.get("fac_date", "")),
            "source": "rootdata",
            "raw": item,
        })

    logger.info(f"تم جلب {len(normalized)} جولة تمويل مبكرة من RootData بعد الفلترة الأولية")
    return normalized


def _fetch_from_defillama_raises() -> list[dict]:
    """
    يجلب جولات التمويل من endpoint /raises في DefiLlama.

    تنبيه مهم: حسب التوثيق الرسمي الحالي (api-docs.defillama.com)،
    endpoint /raises أصبح جزءاً من "Protocol Analytics" في الباقة
    المدفوعة Pro API ($300/شهر)، وليس Free API كما كان سابقاً.
    لذلك:
    - لو DEFILLAMA_API_KEY مضبوط: نستخدم https://pro-api.llama.fi/{KEY}/api/raises
    - لو غير مضبوط: نتخطى DefiLlama بهدوء (تحذير في اللوج فقط) بدل
      محاولة الاتصال بالـ endpoint المجاني القديم الذي يرجع الآن
      خطأ 402 Payment Required بشكل متكرر في كل دورة فحص.

    ثم يستبعد الجولات الأقدم من EARLY_STAGE_LOOKBACK_DAYS، ويطبّق فلتر
    أولي بسيط على الاسم/الفئة/الوصف لإبقاء ما يخص RWA/Infra/DePIN/AI
    تقريباً (الفلترة الدقيقة النهائية تتم عبر الـ LLM في الخطوة التالية).
    """
    if not DEFILLAMA_API_KEY:
        logger.warning(
            "ENABLE_DEFILLAMA=true لكن DEFILLAMA_API_KEY غير مضبوط. "
            "endpoint /raises أصبح يتطلب باقة Pro المدفوعة من DefiLlama "
            "(راجع https://defillama.com/subscription)، تم تخطي هذا المصدر."
        )
        return []

    url = f"https://pro-api.llama.fi/{DEFILLAMA_API_KEY}/api/raises"

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.error(f"فشل الاتصال بـ DefiLlama Pro API: {e}")
        return []

    raw_items = data.get("raises", [])
    cutoff_timestamp = time.time() - (EARLY_STAGE_LOOKBACK_DAYS * 86400)
    normalized = []

    for item in raw_items:
        raise_date = item.get("date", 0)
        # حقل "date" في DefiLlama يكون عادة unix timestamp بالثواني
        if raise_date and raise_date < cutoff_timestamp:
            continue

        project_name = item.get("name", "غير معروف")
        category = item.get("category", "")
        source_text = item.get("source", "") or ""

        if not _looks_like_target_category(f"{project_name} {category} {source_text}"):
            continue

        normalized.append({
            "id": f"defillama-{item.get('defillamaId', project_name)}-{raise_date}",
            "name": project_name,
            "network": item.get("chains", ["غير محدد"])[0] if item.get("chains") else "غير محدد",
            "category": category or "غير محدد",
            "description": (
                f"جولة تمويل بقيمة {item.get('amount', 'غير معلن')} مليون دولار "
                f"بقيادة: {', '.join(item.get('leadInvestors', []) or ['غير معلن'])}"
            ),
            "launch_date": raise_date,
            "source": "defillama",
            "raw": item,
        })

    logger.info(f"تم جلب {len(normalized)} جولة تمويل مبكرة من DefiLlama بعد الفلترة الأولية")
    return normalized


def _looks_like_target_category(text: str) -> bool:
    """
    فلتر أولي سريع وغير دقيق (Pre-filter) لتقليل عدد الطلبات المرسلة
    للـ LLM لاحقاً، عبر استبعاد ما لا يحتوي أصلاً على أي كلمة مفتاحية
    متعلقة بـ RWA/Infra/DePIN/AI. هذا لا يحل محل تحليل الـ LLM النهائي
    ولا يضمن دقة 100%، فقط يقلل الضجيج (مثل عملات الميم البحتة) قبل إرسال
    الطلب للنموذج، توفيراً لاستهلاك الـ API.
    """
    lowered = text.lower()
    return any(keyword in lowered for keyword in EARLY_STAGE_KEYWORDS)

# -*- coding: utf-8 -*-
"""
ido_source.py
-------------
مسؤول عن جلب بيانات المشاريع القادمة (Upcoming IDOs) التي أصبحت في مرحلة
الإعلان الرسمي عن الطرح (Crowd-sale/IDO/ICO).

CryptoRank هو المصدر **الرئيسي والإلزامي** لهذه الطبقة. CoinMarketCap
اختياري بالكامل ويُستخدم فقط كتغطية إضافية إذا فعّلته عبر
ENABLE_COINMARKETCAP=true في متغيرات البيئة — ولا يحل محل CryptoRank أبداً.

ملاحظة مهمة:
- خطط الـ Free / الأساسية في CryptoRank قد لا تتضمن endpoint مخصص لـ
  "Upcoming IDOs/Crowd-sales" بشكل كامل، وربما يحتاج بعض التفاصيل خطة
  مدفوعة (Pro/Enterprise). هذا الكود مكتوب وفق الشكل التوثيقي المعروف؛
  تأكد من توثيق خطتك الفعلية على https://api.cryptorank.io وعدّل
  المسار (endpoint) إذا لزم.
"""

import requests
import logging

from config import (
    CRYPTORANK_API_KEY,
    ENABLE_COINMARKETCAP, COINMARKETCAP_API_KEY,
)

logger = logging.getLogger(__name__)

CRYPTORANK_BASE_URL = "https://api.cryptorank.io/v2"
COINMARKETCAP_BASE_URL = "https://pro-api.coinmarketcap.com/v1"


def fetch_upcoming_ido_projects() -> list[dict]:
    """
    نقطة الدخول الموحّدة لمشاريع الـ IDO الرسمية.
    CryptoRank يُستدعى دائماً بصفته المصدر الرئيسي.
    CoinMarketCap يُضاف لنفس القائمة فقط إذا كان ENABLE_COINMARKETCAP=true.

    يرجع قائمة مشاريع موحّدة الشكل:
    [
        {
            "id": "معرّف فريد",
            "name": "اسم المشروع",
            "network": "الشبكة/المنصة",
            "category": "التصنيف كما يصرّح به المصدر",
            "description": "وصف خام للمشروع",
            "launch_date": "تاريخ الإطلاق إن وجد",
            "source": "اسم المصدر (cryptorank / coinmarketcap)",
            "raw": {...}  # البيانات الخام الكاملة كما أتت من المصدر
        },
        ...
    ]
    """
    projects = _fetch_from_cryptorank()

    if ENABLE_COINMARKETCAP:
        projects.extend(_fetch_from_coinmarketcap())

    return projects


def _fetch_from_cryptorank() -> list[dict]:
    """
    يجلب المشاريع القادمة (Crowd-sales/IDOs) من CryptoRank.

    تنبيه مهم: التوثيق الرسمي لـ CryptoRank (api.cryptorank.io/v2/docs) لا
    يعرض اسم المسار أو أسماء query parameters المقبولة بدقة كاملة (الصفحة
    تحتاج JavaScript)، فهذه الدالة تجرّب أكثر من مسار/فلتر محتمل بالتسلسل:

    1. لكل مسار محتمل، تُجرَّب أولاً نسخة بفلاتر (مثل hasTokenSale)،
       فلو رجعت 400 (يعني المسار صحيح لكن اسم الفلتر مرفوض)، تتم إعادة
       المحاولة فوراً على نفس المسار **بدون أي فلاتر إطلاقاً** كخطوة
       احتياطية أضمن، ثم يُطبَّق فلتر بسيط من جهتنا (بايثون) بعد الجلب.
    2. لو رجعت 404 (المسار نفسه غير موجود لباقتك)، يتم تجربة المسار التالي.
    3. عند أي 400، نسجّل **النص الكامل لرسالة الخطأ من الـ API نفسها**
       (response.text) في اللوج، لأنها تحتوي عادة على السبب الدقيق
       (اسم الباراميتر المرفوض مثلاً) وهذا أدق من أي تخمين.

    إذا فشلت كل المسارات نهائياً: **الحل الموثوق 100%** هو فتح
    https://cryptorank.io/public-api/dashboard من حسابك، ومراجعة قائمة
    الـ endpoints المتاحة فعلياً لباقتك بالاسم والباراميترات الدقيقة.
    """
    if not CRYPTORANK_API_KEY:
        logger.error("CRYPTORANK_API_KEY غير مضبوط — لا يمكن جلب المصدر الرئيسي.")
        return []

    headers = {"X-Api-Key": CRYPTORANK_API_KEY}

    # كل عنصر: (المسار، query params الخاصة به للمحاولة الأولى)
    candidate_paths = [
        ("/currencies", {"hasTokenSale": "true", "limit": 100}),
        ("/crowd-sales", {"status": "upcoming"}),
        ("/funding-rounds", {"stage": "upcoming"}),
    ]

    for path, params in candidate_paths:
        normalized = _try_cryptorank_path(path, params, headers)
        if normalized is not None:
            return normalized

    logger.error(
        "فشلت كل المسارات المحتملة لـ CryptoRank. "
        "راجع https://cryptorank.io/public-api/dashboard لمعرفة اسم الـ endpoint "
        "والباراميترات الصحيحة المتاحة لباقتك، وعدّل candidate_paths في ido_source.py."
    )
    return []


def _try_cryptorank_path(path: str, params: dict, headers: dict) -> list[dict] | None:
    """
    يحاول مساراً واحداً من CryptoRank مع الفلاتر المعطاة. لو رجع 400،
    يعيد المحاولة فوراً بدون أي فلاتر (limit فقط) على نفس المسار.
    يرجع قائمة المشاريع لو نجح أي من المحاولتين، أو None لو فشل المسار
    تماماً (404 أو خطأ آخر) للسماح بتجربة المسار التالي في القائمة.
    """
    url = f"{CRYPTORANK_BASE_URL}{path}"

    for attempt_params, attempt_label in [
        (params, "بالفلاتر الكاملة"),
        ({"limit": 100}, "بدون فلاتر (محاولة احتياطية)"),
    ]:
        try:
            response = requests.get(url, headers=headers, params=attempt_params, timeout=20)
        except requests.RequestException as e:
            logger.error(f"فشل الاتصال بـ CryptoRank API على المسار {path} ({attempt_label}): {e}")
            continue

        if response.status_code == 404:
            logger.warning(f"المسار {path} غير موجود (404) لباقتك، جاري تجربة المسار التالي...")
            return None

        if response.status_code == 400:
            logger.warning(
                f"المسار {path} ({attempt_label}) رجع 400 Bad Request. "
                f"تفاصيل الخطأ من الـ API: {response.text[:500]}"
            )
            continue  # جرّب المحاولة الاحتياطية بدون فلاتر، أو انتقل للمسار التالي

        try:
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error(f"فشل الاتصال بـ CryptoRank API على المسار {path} ({attempt_label}): {e}")
            continue

        raw_items = data.get("data", [])

        # لو كانت هذه المحاولة الاحتياطية بدون فلاتر، نطبّق فلتراً بسيطاً
        # من جهتنا للاحتفاظ فقط بالعملات التي لديها Token Sale فعلي (حقل
        # hasTokenSale في الاستجابة نفسها، لا كـ query parameter).
        if attempt_label.startswith("بدون فلاتر"):
            raw_items = [item for item in raw_items if item.get("hasTokenSale")]

        normalized = [
            {
                "id": f"cryptorank-{item.get('id', item.get('key', ''))}",
                "name": item.get("name", "غير معروف"),
                "network": item.get("network", item.get("platform", "غير محدد")),
                "category": item.get("category", item.get("type", "غير محدد")),
                "description": item.get("description", ""),
                "launch_date": item.get("startDate", item.get("date", "")),
                "source": "cryptorank",
                "raw": item,
            }
            for item in raw_items
        ]

        logger.info(
            f"نجح المسار {path} ({attempt_label}) في CryptoRank — "
            f"تم جلب {len(normalized)} مشروع (المصدر الرئيسي)"
        )
        return normalized

    # كل المحاولات على هذا المسار فشلت بـ 400، لكن المسار نفسه قد يكون
    # صحيحاً — لا نعتبره 404 لذا لا نرجع None هنا لإيقاف التجربة بصمت،
    # بل نسمح بالانتقال للمسار التالي في القائمة الرئيسية.
    return None


def _fetch_from_coinmarketcap() -> list[dict]:
    """
    يجلب مشاريع إضافية من CoinMarketCap كمصدر تكميلي اختياري (CryptoRank هو الأساس).
    تنبيه: الـ Public API الرسمي لـ CoinMarketCap لا يملك حتى الآن endpoint
    باسم "Upcoming IDOs" بشكل عام للجميع؛ هذا غالباً متاح فقط ضمن منتج
    CMC الخاص بالمستثمرين المؤسسيين أو عبر صفحات الويب فقط (بدون API رسمي).
    الكود هنا موضوع لإكمال البنية ويفترض أنك تستخدم endpoint مكافئ متاح
    في باقتك (مثل /cryptocurrency/listings/new كبديل تقريبي للمشاريع الجديدة).
    """
    if not COINMARKETCAP_API_KEY:
        logger.warning("ENABLE_COINMARKETCAP=true لكن COINMARKETCAP_API_KEY غير مضبوط، تم التجاوز.")
        return []

    url = f"{COINMARKETCAP_BASE_URL}/cryptocurrency/listings/new"
    headers = {"X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY}
    params = {"limit": 50}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.error(f"فشل الاتصال بـ CoinMarketCap API: {e}")
        return []

    raw_items = data.get("data", [])
    normalized = []

    for item in raw_items:
        platform = item.get("platform") or {}
        normalized.append({
            "id": f"coinmarketcap-{item.get('id', '')}",
            "name": item.get("name", "غير معروف"),
            "network": platform.get("name", "غير محدد") if platform else "غير محدد",
            "category": item.get("category", "غير محدد"),
            "description": item.get("description", item.get("name", "")),
            "launch_date": item.get("date_added", ""),
            "source": "coinmarketcap",
            "raw": item,
        })

    logger.info(f"تم جلب {len(normalized)} مشروع إضافي من CoinMarketCap (تكميلي)")
    return normalized

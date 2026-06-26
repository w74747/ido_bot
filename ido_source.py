# -*- coding: utf-8 -*-
"""
ido_source.py
-------------
مسؤول فقط عن جلب بيانات المشاريع القادمة (Upcoming IDOs) من مصدر خارجي.
يدعم مزوّدين: CryptoRank و CoinMarketCap. كل مزود له شكل استجابة مختلف،
لذلك نعيد كل النتائج بشكل موحّد (قائمة قواميس بنفس المفاتيح) لتسهيل
التعامل معها في باقي البرنامج.

ملاحظة مهمة:
- خطط الـ Free / الأساسية في CryptoRank و CoinMarketCap قد لا تتضمن
  endpoint مخصص لـ "Upcoming IDOs" بشكل مباشر، وربما تحتاج خطة مدفوعة
  (Pro/Enterprise) للوصول لهذا النوع من البيانات. هذا الكود مكتوب وفق
  الشكل التوثيقي المعروف لكل مزود؛ تأكد من توثيق خطتك الفعلية وعدّل
  المسار (endpoint) إذا لزم.
"""

import requests
import logging

from config import IDO_DATA_SOURCE, CRYPTORANK_API_KEY, COINMARKETCAP_API_KEY

logger = logging.getLogger(__name__)

CRYPTORANK_BASE_URL = "https://api.cryptorank.io/v2"
COINMARKETCAP_BASE_URL = "https://pro-api.coinmarketcap.com/v1"


def fetch_upcoming_ido_projects() -> list[dict]:
    """
    نقطة الدخول الموحّدة: تستدعي المزود المُفعّل في config وترجع
    قائمة مشاريع موحّدة الشكل:
    [
        {
            "id": "معرّف فريد",
            "name": "اسم المشروع",
            "network": "الشبكة/المنصة",
            "category": "التصنيف كما يصرّح به المصدر",
            "description": "وصف خام للمشروع",
            "launch_date": "تاريخ الإطلاق إن وجد",
            "raw": {...}  # البيانات الخام الكاملة كما أتت من المصدر
        },
        ...
    ]
    """
    if IDO_DATA_SOURCE == "cryptorank":
        return _fetch_from_cryptorank()
    elif IDO_DATA_SOURCE == "coinmarketcap":
        return _fetch_from_coinmarketcap()
    else:
        raise ValueError(f"مصدر بيانات غير معروف: {IDO_DATA_SOURCE}")


def _fetch_from_cryptorank() -> list[dict]:
    """
    يجلب المشاريع القادمة من CryptoRank.
    التوثيق الرسمي: https://api.cryptorank.io/v2/docs
    Endpoint الخاص بالـ IDOs/Crowdsales غالباً يكون تحت /funding-rounds
    أو /ico-calendar حسب نوع الباقة. هنا نستخدم مساراً عاماً للأحداث القادمة
    ويُفترض تعديله حسب اشتراكك الفعلي.
    """
    url = f"{CRYPTORANK_BASE_URL}/crowd-sales"
    headers = {"X-Api-Key": CRYPTORANK_API_KEY}
    params = {"status": "upcoming"}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.error(f"فشل الاتصال بـ CryptoRank API: {e}")
        return []

    raw_items = data.get("data", [])
    normalized = []

    for item in raw_items:
        normalized.append({
            "id": str(item.get("id", item.get("key", ""))),
            "name": item.get("name", "غير معروف"),
            "network": item.get("network", item.get("platform", "غير محدد")),
            "category": item.get("category", item.get("type", "غير محدد")),
            "description": item.get("description", ""),
            "launch_date": item.get("startDate", item.get("date", "")),
            "raw": item,
        })

    logger.info(f"تم جلب {len(normalized)} مشروع من CryptoRank")
    return normalized


def _fetch_from_coinmarketcap() -> list[dict]:
    """
    يجلب المشاريع من CoinMarketCap.
    تنبيه: الـ Public API الرسمي لـ CoinMarketCap لا يملك حتى الآن endpoint
    باسم "Upcoming IDOs" بشكل عام للجميع؛ هذا غالباً متاح فقط ضمن منتج
    CMC الخاص بالمستثمرين المؤسسيين أو عبر صفحات الويب فقط (بدون API رسمي).
    الكود هنا موضوع لإكمال البنية ويفترض أنك تستخدم endpoint مكافئ متاح
    في باقتك (مثل /cryptocurrency/listings/new كبديل تقريبي للمشاريع الجديدة).
    """
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
            "id": str(item.get("id", "")),
            "name": item.get("name", "غير معروف"),
            "network": platform.get("name", "غير محدد") if platform else "غير محدد",
            "category": item.get("category", "غير محدد"),
            "description": item.get("description", item.get("name", "")),
            "launch_date": item.get("date_added", ""),
            "raw": item,
        })

    logger.info(f"تم جلب {len(normalized)} مشروع من CoinMarketCap")
    return normalized

# -*- coding: utf-8 -*-
"""
ido_source.py
-------------
مسؤول عن CryptoRank فقط، بدور **مختلف تماماً** عن الدور الأصلي.

تنبيه مهم جداً (مبني على التوثيق الرسمي الكامل الذي تمت مراجعته فعلياً
عبر https://api.cryptorank.io/v2/docs):
باقة Sandbox (المجانية) في CryptoRank **لا تتضمن أي endpoint** يرجع
قائمة مباشرة بمشاريع IDO/Crowdsale/Funding Rounds قادمة. الـ endpoints
التي تخدم هذا الغرض فعلياً (`/v2/currencies/public-sales` و
`/v2/currencies/funding-rounds`) موثّقة رسمياً بأنها:
    ✅ Included in: Business
    🛒 Available for purchase in: Basic, Advanced, Pro
    ❌ Not available in: Sandbox

لذلك تم تغيير دور CryptoRank في هذا البوت بالكامل:
- لم يعد مصدراً لاكتشاف فرص IDO (هذا أصبح مسؤولية RootData وDefiLlama
  بالكامل، في early_stage_source.py).
- أصبح يُستخدم فقط لجلب **بيانات السوق العامة** (قائمة العملات المعروفة
  وبياناتها الأساسية) عبر `/v2/currencies/map`، وهو endpoint موثّق
  ومتاح فعلياً في Sandbox، ولا يُمرَّر للـ LLM كـ"فرصة استثمارية" —
  فقط كمعلومة سياقية اختيارية (راجع main.py لكيفية استخدامه إن وُجد).

إذا رغبت لاحقاً بترقية باقتك (Basic فما فوق) لتفعيل اكتشاف IDOs الحقيقي
من CryptoRank، فعّل ENABLE_CRYPTORANK_IDO_DISCOVERY في config.py وأضف
استدعاءً مماثلاً لـ `/v2/currencies/public-sales` بنفس أسلوب
early_stage_source.py.
"""

import requests
import logging

from config import CRYPTORANK_API_KEY

logger = logging.getLogger(__name__)

CRYPTORANK_BASE_URL = "https://api.cryptorank.io/v2"


def fetch_market_overview() -> list[dict]:
    """
    يجلب قائمة عامة بالعملات المعروفة من CryptoRank عبر `/v2/currencies/map`
    (موثّق رسمياً كمتاح في باقة Sandbox، بدون أي فلتر IDO لأنه غير مدعوم).

    هذا **لا يرجع مشاريع IDO أو فرص استثمارية** — فقط تأكيد أن الاتصال
    بـ CryptoRank يعمل، وبيانات سوق عامة (id, symbol, name) قد تُستخدم
    مستقبلاً كسياق إضافي، وليست مصدراً يُرسل للـ LLM للتحليل الشرعي/
    الاستثماري (هذا حصراً عمل RootData/DefiLlama في early_stage_source.py).

    يرجع قائمة بسيطة:
    [{"id": ..., "key": ..., "symbol": ..., "name": ...}, ...]
    أو قائمة فاضية لو فشل الاتصال أو المفتاح غير مضبوط.
    """
    if not CRYPTORANK_API_KEY:
        logger.warning("CRYPTORANK_API_KEY غير مضبوط — تخطي جلب بيانات السوق العامة.")
        return []

    url = f"{CRYPTORANK_BASE_URL}/currencies/map"
    headers = {"X-Api-Key": CRYPTORANK_API_KEY}

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.error(f"فشل الاتصال بـ CryptoRank (/v2/currencies/map): {e}")
        return []

    raw_items = data.get("data", [])
    logger.info(
        f"تم التحقق من اتصال CryptoRank بنجاح — {len(raw_items)} عملة متاحة "
        f"في بيانات السوق العامة (لا تُستخدم كفرص استثمارية، فقط للسياق)."
    )
    return raw_items


def fetch_upcoming_ido_projects() -> list[dict]:
    """
    تم الاحتفاظ بهذا الاسم فقط للتوافق مع الاستدعاءات القديمة في main.py،
    لكنه أصبح يرجع قائمة فاضية دائماً عمداً: CryptoRank لا يُستخدم كمصدر
    IDOs بعد الآن ضمن باقة Sandbox (راجع التنبيه في رأس هذا الملف).
    اكتشاف فرص IDO/التمويل المبكر أصبح حصراً عبر
    early_stage_source.fetch_early_stage_projects().
    """
    return []

"""
config.py
---------
يقرأ كل المفاتيح والإعدادات من Environment Variables.
لا تكتب أي مفتاح API هنا مباشرة — كل القيم تُضبط من خارج الكود
(محلياً عبر ملف .env، أو على Railway عبر تبويب Variables).
"""

import os

# ---------- مفاتيح الـ APIs ----------

# CryptoRank: في باقة Sandbox (المجانية) لا يوجد أي endpoint يرجع مشاريع
# IDO/Crowdsale قادمة (موثّق رسمياً)، فتم تغيير دوره بالكامل: يُستخدم فقط
# لجلب بيانات سوق عامة سياقية عبر /v2/currencies/map (راجع ido_source.py).
# اكتشاف فرص IDO/التمويل المبكر أصبح حصراً مسؤولية RootData وDefiLlama.
# CRYPTORANK_API_KEY اختياري الآن: بدونه، يُتخطى هذا المصدر بهدوء فقط.
CRYPTORANK_API_KEY = os.getenv("CRYPTORANK_API_KEY", "")

# CoinMarketCap اختياري بالكامل، يُضاف فقط إذا فعّلته (لا علاقة له بالتغيير أعلاه).
ENABLE_COINMARKETCAP = os.getenv("ENABLE_COINMARKETCAP", "false").lower() == "true"
COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY", "")

# ---------- مصادر المراحل المبكرة جداً (قبل الطرح العام) ----------
# هذه مصادر "تكميلية" تعمل بجانب CryptoRank، وتركز على جولات التمويل
# (Funding/Seed/Series A) لمشاريع RWA والبنية التحتية في مراحلها الأولى،
# قبل أن تصل أصلاً لمرحلة الإعلان عن IDO رسمي.

# RootData: تغطية واسعة لجولات التمويل + تصنيفات دقيقة (RWA/Infra/DePIN).
ENABLE_ROOTDATA = os.getenv("ENABLE_ROOTDATA", "true").lower() == "true"
ROOTDATA_API_KEY = os.getenv("ROOTDATA_API_KEY", "")

# DefiLlama: endpoint "/raises" أصبح حسب التوثيق الرسمي الحالي جزءاً من
# باقة Pro المدفوعة ($300/شهر، عبر https://defillama.com/subscription)،
# وليس مجانياً كما كان سابقاً. DEFILLAMA_API_KEY اختياري بالكامل: لو لم
# يُضبط، يتم تخطي DefiLlama بهدوء (تحذير في اللوج فقط) دون إيقاف البوت.
ENABLE_DEFILLAMA = os.getenv("ENABLE_DEFILLAMA", "true").lower() == "true"
DEFILLAMA_API_KEY = os.getenv("DEFILLAMA_API_KEY", "")

# كم يوم للخلف نعتبر فيه جولة التمويل "جديدة" (لتفادي إعادة جلب تاريخ قديم بالكامل)
EARLY_STAGE_LOOKBACK_DAYS = int(os.getenv("EARLY_STAGE_LOOKBACK_DAYS", "30"))

# مزوّد نموذج اللغة (اختر واحد: "together" أو "deepseek")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "together")

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "")
TOGETHER_MODEL = os.getenv("TOGETHER_MODEL", "meta-llama/Llama-3.3-70B-Instruct-Turbo")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# تلجرام
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ---------- إعدادات التشغيل ----------

# كل كم دقيقة يفحص البوت عن مشاريع جديدة (افتراضي: 1440 دقيقة = مرة واحدة يومياً)
POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "1440"))

# ملف بسيط لتخزين المعرفات (IDs) التي تمت معالجتها لتجنب التكرار
PROCESSED_IDS_FILE = os.getenv("PROCESSED_IDS_FILE", "processed_projects.json")

# كلمة الاستبعاد التي يرجعها الموديل عند رفض المشروع
IGNORE_KEYWORD = "تجاهل"


def validate_config():
    """
    يتحقق من وجود المتغيرات الأساسية قبل تشغيل البوت،
    ويطبع تحذيرات واضحة بدل ما يفشل بصمت أو بخطأ غامض.

    تنبيه مهم بعد تغيير دور CryptoRank: لم يعد إلزامياً (أصبح مصدر بيانات
    سوق عامة اختياري فقط). الإلزامي الآن هو ضمان وجود **مصدر اكتشاف واحد
    على الأقل فعّال** بين RootData وDefiLlama، وإلا فلن يكتشف البوت أي
    فرصة استثمارية إطلاقاً (سيعمل بصمت دون أي خطأ، وهذا أسوأ من رفض
    التشغيل بوضوح).
    """
    missing = []

    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")

    # CryptoRank لم يعد إلزامياً: لا تحقق هنا، فقط تحذير لاحق إن أردت تفعيله بلا مفتاح.

    if ENABLE_COINMARKETCAP and not COINMARKETCAP_API_KEY:
        missing.append("COINMARKETCAP_API_KEY (مطلوب لأن ENABLE_COINMARKETCAP=true)")

    if ENABLE_ROOTDATA and not ROOTDATA_API_KEY:
        missing.append("ROOTDATA_API_KEY (مطلوب لأن ENABLE_ROOTDATA=true)")

    # DEFILLAMA_API_KEY اختياري بالكامل وليس إلزامياً: لو ENABLE_DEFILLAMA=true
    # بدون مفتاح، يُسجَّل تحذير فقط ويُتخطى هذا المصدر دون إيقاف البوت،
    # لأن /raises أصبح يتطلب اشتراكاً مدفوعاً ولا نريد فرضه على المستخدم.

    if LLM_PROVIDER == "together" and not TOGETHER_API_KEY:
        missing.append("TOGETHER_API_KEY")
    elif LLM_PROVIDER == "deepseek" and not DEEPSEEK_API_KEY:
        missing.append("DEEPSEEK_API_KEY")

    if missing:
        raise EnvironmentError(
            "المتغيرات البيئية التالية مفقودة: " + ", ".join(missing) +
            "\nراجع تعليمات الإعداد في README وأضفها كـ Environment Variables."
        )

    # تحقق منفصل (تحذير فقط، لا يوقف البوت): على الأقل مصدر اكتشاف واحد
    # فعّال وقادر على إرجاع نتائج فعلية (مفتاح موجود)، وإلا فالبوت سيعمل
    # بدون أي اكتشاف فرص استثمارية إطلاقاً.
    rootdata_usable = ENABLE_ROOTDATA and bool(ROOTDATA_API_KEY)
    defillama_usable = ENABLE_DEFILLAMA and bool(DEFILLAMA_API_KEY)

    if not rootdata_usable and not defillama_usable:
        import logging
        logging.getLogger(__name__).warning(
            "تحذير مهم: لا يوجد أي مصدر اكتشاف فعّال (RootData وDefiLlama "
            "كلاهما معطل أو بدون مفتاح). البوت سيعمل ويتصل بنجاح، لكنه لن "
            "يكتشف أي فرصة استثمارية إطلاقاً في كل الدورات. فعّل أحدهما "
            "على الأقل بمفتاح صحيح للحصول على نتائج فعلية."
        )

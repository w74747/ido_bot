"""
config.py
---------
يقرأ كل المفاتيح والإعدادات من Environment Variables.
لا تكتب أي مفتاح API هنا مباشرة — كل القيم تُضبط من خارج الكود
(محلياً عبر ملف .env، أو على Railway عبر تبويب Variables).
"""

import os

# ---------- مفاتيح الـ APIs ----------

# مصدر بيانات الـ IDOs (اختر واحد فقط وفعّله، الافتراضي CryptoRank)
IDO_DATA_SOURCE = os.getenv("IDO_DATA_SOURCE", "cryptorank")  # "cryptorank" أو "coinmarketcap"

CRYPTORANK_API_KEY = os.getenv("CRYPTORANK_API_KEY", "")
COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY", "")

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

# كل كم دقيقة يفحص البوت عن مشاريع جديدة
POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "60"))

# ملف بسيط لتخزين المعرفات (IDs) التي تمت معالجتها لتجنب التكرار
PROCESSED_IDS_FILE = os.getenv("PROCESSED_IDS_FILE", "processed_projects.json")

# كلمة الاستبعاد التي يرجعها الموديل عند رفض المشروع
IGNORE_KEYWORD = "تجاهل"


def validate_config():
    """
    يتحقق من وجود المتغيرات الأساسية قبل تشغيل البوت،
    ويطبع تحذيرات واضحة بدل ما يفشل بصمت أو بخطأ غامض.
    """
    missing = []

    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")

    if IDO_DATA_SOURCE == "cryptorank" and not CRYPTORANK_API_KEY:
        missing.append("CRYPTORANK_API_KEY")
    elif IDO_DATA_SOURCE == "coinmarketcap" and not COINMARKETCAP_API_KEY:
        missing.append("COINMARKETCAP_API_KEY")

    if LLM_PROVIDER == "together" and not TOGETHER_API_KEY:
        missing.append("TOGETHER_API_KEY")
    elif LLM_PROVIDER == "deepseek" and not DEEPSEEK_API_KEY:
        missing.append("DEEPSEEK_API_KEY")

    if missing:
        raise EnvironmentError(
            "المتغيرات البيئية التالية مفقودة: " + ", ".join(missing) +
            "\nراجع تعليمات الإعداد في README وأضفها كـ Environment Variables."
        )

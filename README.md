# بوت تحليل وفلترة مشاريع IDO (شرعياً واستثمارياً)

بوت بايثون يعمل بشكل دوري على:
1. جلب بيانات المشاريع القادمة (Upcoming IDOs) من **CryptoRank** أو **CoinMarketCap**.
2. إرسال كل مشروع جديد إلى نموذج لغة (**Together AI** أو **DeepSeek**) مع
   System Prompt متخصص في الفلترة الشرعية والاستثمارية لمشاريع Web3.
3. إذا اعتبر النموذج المشروع مناسباً (لم يرجع كلمة "تجاهل")، يرسل التقرير
   النهائي تلقائياً إلى محادثة تلجرام محددة عبر Telegram Bot API.

---

## 1. هيكل الملفات

```
ido_bot/
├── main.py              # نقطة التشغيل الرئيسية (الحلقة الدورية)
├── config.py            # قراءة وتحقق من المتغيرات البيئية
├── prompts.py           # نص System Prompt الخاص بالتحليل الشرعي/الاستثماري
├── ido_source.py        # جلب بيانات IDOs من CryptoRank/CoinMarketCap
├── llm_analyzer.py       # إرسال البيانات لـ Together AI/DeepSeek وتحليلها
├── telegram_sender.py    # إرسال التقرير النهائي لتلجرام
├── storage.py            # تخزين بسيط لمنع تكرار إرسال نفس المشروع
├── requirements.txt       # المكتبات المطلوبة
├── Procfile               # أمر تشغيل البوت على Railway
└── .env.example            # نموذج للمتغيرات البيئية (للتشغيل المحلي)
```

---

## 2. التشغيل المحلي (اختياري، للتجربة قبل النشر)

```bash
# 1) إنشاء بيئة افتراضية (اختياري لكن يُفضّل)
python -m venv venv
source venv/bin/activate      # على ويندوز: venv\Scripts\activate

# 2) تثبيت المكتبات
pip install -r requirements.txt

# 3) نسخ ملف الإعدادات وتعبئته بمفاتيحك
cp .env.example .env
# ثم افتح .env وعبّئ القيم (التوكنات والمفاتيح)

# 4) تشغيل البوت
python main.py
```

---

## 3. النشر على Railway (الطريقة الموصى بها للتشغيل الدائم)

### الخطوة 1: رفع الكود
- أنشئ مستودع GitHub جديد وارفع كل ملفات هذا المشروع إليه (ما عدا `.env`، لا ترفعه أبداً).
- في [Railway](https://railway.app)، اختر **New Project → Deploy from GitHub repo** وحدد المستودع.

### الخطوة 2: ضبط المتغيرات البيئية (Environment Variables)
داخل مشروعك على Railway، افتح تبويب **Variables** وأضف كل متغير من القائمة التالية
(القيم نفسها التي في `.env.example` بدون أسماء الملفات):

| المتغير | الوصف |
|---|---|
| `IDO_DATA_SOURCE` | `cryptorank` أو `coinmarketcap` |
| `CRYPTORANK_API_KEY` | مفتاح CryptoRank (إذا اخترته كمصدر) |
| `COINMARKETCAP_API_KEY` | مفتاح CoinMarketCap (إذا اخترته كمصدر) |
| `LLM_PROVIDER` | `together` أو `deepseek` |
| `TOGETHER_API_KEY` | مفتاح Together AI (إذا اخترته كمزوّد) |
| `TOGETHER_MODEL` | اسم الموديل، مثلاً `meta-llama/Llama-3.3-70B-Instruct-Turbo` |
| `DEEPSEEK_API_KEY` | مفتاح DeepSeek (إذا اخترته كمزوّد) |
| `DEEPSEEK_MODEL` | اسم الموديل، مثلاً `deepseek-chat` |
| `TELEGRAM_BOT_TOKEN` | التوكن الذي تحصل عليه من [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHAT_ID` | رقم الـ Chat ID الذي سيستقبل التقارير |
| `POLL_INTERVAL_MINUTES` | كل كم دقيقة يفحص البوت (افتراضي: `60`) |
| `PROCESSED_IDS_FILE` | اسم ملف تخزين المعرّفات (افتراضي: `processed_projects.json`) |

**لا تحتاج لضبط أي متغير غير مستخدم** — مثلاً إذا اخترت `together` فلا حاجة لتعبئة `DEEPSEEK_API_KEY`.

### الخطوة 3: كيف تحصل على القيم المطلوبة

- **TELEGRAM_BOT_TOKEN**: تحدث مع [@BotFather](https://t.me/BotFather) على تلجرام، أرسل `/newbot`، واتبع التعليمات لتحصل على التوكن.
- **TELEGRAM_CHAT_ID**: أرسل أي رسالة لبوتك الجديد، ثم افتح في المتصفح:
  `https://api.telegram.org/bot<التوكن>/getUpdates`
  وستجد `chat.id` في الرد (إذا تريد إرسال التقارير لقناة، أضف البوت كأدمن فيها واستخدم معرّف القناة، عادة يبدأ بـ `-100`).
- **CRYPTORANK_API_KEY**: من حسابك على [cryptorank.io](https://cryptorank.io) تحت إعدادات الـ API (قد يتطلب خطة مدفوعة للوصول لبيانات IDOs).
- **COINMARKETCAP_API_KEY**: من [pro.coinmarketcap.com](https://pro.coinmarketcap.com) تحت API Keys.
- **TOGETHER_API_KEY**: من [api.together.ai](https://api.together.ai).
- **DEEPSEEK_API_KEY**: من [platform.deepseek.com](https://platform.deepseek.com).

### الخطوة 4: نوع الخدمة على Railway
تأكد أن الخدمة من نوع **Worker** (وليس Web)، لأن البوت لا يفتح أي منفذ HTTP، فقط
يعمل بشكل مستمر في حلقة (`while True`). ملف `Procfile` المرفق يوضّح هذا تلقائياً
(`worker: python main.py`)، لكن تأكد أيضاً من تبويب **Settings → Deploy** أن
أمر التشغيل (Start Command) هو:

```
python main.py
```

### الخطوة 5: التحقق من العمل
بعد النشر، افتح تبويب **Deployments → Logs** على Railway وتابع السجلات
(Logs)؛ يجب أن ترى رسائل مثل:

```
بدء تشغيل بوت تحليل وفلترة مشاريع IDO...
تم تحميل 0 معرّف مشروع تمت معالجته سابقاً.
عدد المشاريع الجديدة (لم تُعالج سابقاً): X
```

---

## 4. ملاحظات مهمة قبل الاستخدام الفعلي

1. **توثيق الـ API الفعلي**: ملف `ido_source.py` مكتوب وفق الشكل التوثيقي
   المعروف لكل من CryptoRank وCoinMarketCap، لكن endpoint بيانات
   "Upcoming IDOs" تحديداً يختلف حسب نوع باقتك (Free/Pro/Enterprise).
   **افتح توثيق حسابك الفعلي** وتأكد من اسم الـ endpoint الصحيح، وعدّله
   في دالتي `_fetch_from_cryptorank()` أو `_fetch_from_coinmarketcap()`
   إذا لزم الأمر.
2. **التقييم الشرعي اجتهادي وليس فتوى رسمية**: التقرير الذي يولّده النموذج
   هو تحليل أولي مبني على الـ System Prompt الذي زوّدتني به، وليس فتوى
   شرعية معتمدة. يُفضّل أن يكون آخر فيصل في القرار الاستثماري هو مراجعة
   شخص أو مرجع شرعي موثوق، خصوصاً قبل اتخاذ قرارات مالية فعلية.
3. **حدود الـ Rate Limit**: انتبه لحدود عدد الطلبات في كل من المصدر
   (CryptoRank/CoinMarketCap) ومزوّد الـ LLM (Together/DeepSeek)؛
   `POLL_INTERVAL_MINUTES` موجود بالضبط للمساعدة على عدم تجاوزها.
4. **التخزين المؤقت (`storage.py`)**: يحمي من تكرار إرسال نفس المشروع
   في كل دورة، لكنه ملف محلي بسيط؛ إذا أعدت نشر (Redeploy) الخدمة على
   Railway قد يُعاد ضبطه، فقد يُعاد إرسال بعض المشاريع القديمة مرة واحدة.

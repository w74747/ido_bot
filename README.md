# بوت تحليل وفلترة مشاريع IDO ومراحل التمويل المبكرة (شرعياً واستثمارياً)

بوت بايثون يعمل بشكل دوري على:

1. **جلب مشاريع الـ IDO المُعلنة رسمياً** من **CryptoRank** (المصدر الرئيسي
   والإلزامي)، مع إمكانية تفعيل **CoinMarketCap** كمصدر تكميلي اختياري.
2. **جلب جولات التمويل المبكرة جداً** (Seed / Series A) لمشاريع **RWA**
   والبنية التحتية (**Infrastructure / DePIN / AI**) — أي قبل أن تصل هذه
   المشاريع أصلاً لمرحلة الإعلان عن IDO رسمي — من مصدرين تكميليين:
   - **RootData** (يحتاج مفتاح API).
   - **DefiLlama** (endpoint `/raises` أصبح حسب التوثيق الرسمي الحالي
     جزءاً من باقة Pro المدفوعة، يحتاج `DEFILLAMA_API_KEY` اختياري — بدونه
     يتم تخطي هذا المصدر بهدوء).
3. إرسال كل مشروع جديد (من أي من المصادر أعلاه) إلى نموذج لغة
   (**Together AI** أو **DeepSeek**) مع System Prompt متخصص في الفلترة
   الشرعية والاستثمارية لمشاريع Web3.
4. إذا اعتبر النموذج المشروع مناسباً (لم يرجع كلمة "تجاهل")، يرسل التقرير
   النهائي تلقائياً إلى محادثة تلجرام محددة عبر Telegram Bot API.

> **الفلترة على مرحلتين:** مصادر التمويل المبكرة (RootData/DefiLlama) تُمرّ
> أولاً عبر فلتر كلمات مفتاحية بسيط وسريع (RWA/Infra/DePIN/AI...) لتقليل
> الضجيج وتوفير استهلاك الـ API، ثم تخضع كل النتائج التي تعدّت هذا الفلتر
> للتحليل الدقيق والنهائي من نموذج اللغة بنفس معايير الـ System Prompt.
> المصدر الرئيسي (CryptoRank) لا يخضع لهذا الفلتر المسبق ويُرسل مباشرة
> للنموذج لأنه أصلاً مخصص لمشاريع التوكنات/الـ IDOs.

---

## 1. هيكل الملفات

```
ido_bot/
├── main.py                 # نقطة التشغيل الرئيسية (الحلقة الدورية)
├── config.py               # قراءة وتحقق من المتغيرات البيئية
├── prompts.py               # نص System Prompt الخاص بالتحليل الشرعي/الاستثماري
├── ido_source.py             # جلب IDOs من CryptoRank (رئيسي) + CoinMarketCap (اختياري)
├── early_stage_source.py     # جلب جولات تمويل مبكرة من RootData + DefiLlama
├── llm_analyzer.py            # إرسال البيانات لـ Together AI/DeepSeek وتحليلها
├── telegram_sender.py         # إرسال التقرير النهائي لتلجرام
├── storage.py                  # تخزين بسيط لمنع تكرار إرسال نفس المشروع
├── requirements.txt            # المكتبات المطلوبة
├── Procfile                     # أمر تشغيل البوت على Railway
└── .env.example                  # نموذج للمتغيرات البيئية (للتشغيل المحلي)
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
| `CRYPTORANK_API_KEY` | **إلزامي.** مفتاح CryptoRank (المصدر الرئيسي لمشاريع IDO) |
| `ENABLE_COINMARKETCAP` | `true` أو `false` (افتراضي: `false`) — تفعيل CoinMarketCap كمصدر تكميلي إضافي |
| `COINMARKETCAP_API_KEY` | مفتاح CoinMarketCap (مطلوب فقط إذا `ENABLE_COINMARKETCAP=true`) |
| `ENABLE_ROOTDATA` | `true` أو `false` (افتراضي: `true`) — تفعيل RootData لجولات التمويل المبكرة |
| `ROOTDATA_API_KEY` | مفتاح RootData (مطلوب فقط إذا `ENABLE_ROOTDATA=true`) |
| `ENABLE_DEFILLAMA` | `true` أو `false` (افتراضي: `true`) — تفعيل DefiLlama |
| `DEFILLAMA_API_KEY` | اختياري. مطلوب فعلياً للحصول على نتائج من `/raises` (أصبح Pro tier)، لكن بدونه البوت يستمر بالعمل ويتخطى هذا المصدر فقط |
| `EARLY_STAGE_LOOKBACK_DAYS` | كم يوم للخلف تُعتبر فيه جولة التمويل "جديدة" (افتراضي: `30`) |
| `LLM_PROVIDER` | `together` أو `deepseek` |
| `TOGETHER_API_KEY` | مفتاح Together AI (إذا اخترته كمزوّد) |
| `TOGETHER_MODEL` | اسم الموديل، مثلاً `meta-llama/Llama-3.3-70B-Instruct-Turbo` |
| `DEEPSEEK_API_KEY` | مفتاح DeepSeek (إذا اخترته كمزوّد) |
| `DEEPSEEK_MODEL` | اسم الموديل، مثلاً `deepseek-chat` |
| `TELEGRAM_BOT_TOKEN` | التوكن الذي تحصل عليه من [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHAT_ID` | رقم الـ Chat ID الذي سيستقبل التقارير |
| `POLL_INTERVAL_MINUTES` | كل كم دقيقة يفحص البوت (افتراضي: `1440` = مرة واحدة يومياً) |
| `PROCESSED_IDS_FILE` | اسم ملف تخزين المعرّفات (افتراضي: `processed_projects.json`) |

**لا تحتاج لضبط أي متغير غير مستخدم** — مثلاً إذا اخترت `together` فلا حاجة لتعبئة `DEEPSEEK_API_KEY`،
وإذا تركت `ENABLE_ROOTDATA=false` فلا حاجة لتعبئة `ROOTDATA_API_KEY`.

### الخطوة 3: كيف تحصل على القيم المطلوبة

- **TELEGRAM_BOT_TOKEN**: تحدث مع [@BotFather](https://t.me/BotFather) على تلجرام، أرسل `/newbot`، واتبع التعليمات لتحصل على التوكن.
- **TELEGRAM_CHAT_ID**: أرسل أي رسالة لبوتك الجديد، ثم افتح في المتصفح:
  `https://api.telegram.org/bot<التوكن>/getUpdates`
  وستجد `chat.id` في الرد (إذا تريد إرسال التقارير لقناة، أضف البوت كأدمن فيها واستخدم معرّف القناة، عادة يبدأ بـ `-100`).
- **CRYPTORANK_API_KEY**: من حسابك على [cryptorank.io](https://cryptorank.io) تحت إعدادات الـ API. هذا المصدر **إلزامي** بصفته المصدر الرئيسي (قد يتطلب خطة مدفوعة للوصول الكامل لبيانات الـ Crowd-sales/IDOs).
- **COINMARKETCAP_API_KEY**: من [pro.coinmarketcap.com](https://pro.coinmarketcap.com) تحت API Keys (اختياري).
- **ROOTDATA_API_KEY**: من [rootdata.com/Api](https://www.rootdata.com/Api) — الخطة الأساسية مجانية للبحث، لكن endpoint جولات التمويل بالجملة (`get_fac`) المستخدم في `early_stage_source.py` قد يتطلب باقة Plus/Pro حسب توثيق RootData الرسمي. تأكد من باقتك الفعلية على [docs.rootdata.com](https://docs.rootdata.com).
- **DEFILLAMA_API_KEY**: من [defillama.com/subscription](https://defillama.com/subscription) (باقة Pro، $300/شهر) — endpoint `/raises` لم يعد مجانياً حسب التوثيق الرسمي الحالي. لو لا تريد دفع هذا الاشتراك، اترك المتغير فاضياً وسيتخطى البوت DefiLlama تلقائياً بدون أي خطأ.
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

1. **توثيق الـ API الفعلي**: ملف `ido_source.py` يجرّب الآن تلقائياً عدة
   مسارات محتملة بالتسلسل لـ CryptoRank (`/currencies?hasTokenSale=true`،
   `/crowd-sales`، `/funding-rounds`)، ويستخدم أول مسار يرجع نتيجة ناجحة
   (وليس 404). لو فشلت كل المسارات، ستظهر رسالة واضحة في الـ Logs تطلب
   منك مراجعة [لوحة تحكم حسابك](https://cryptorank.io/public-api/dashboard)
   لمعرفة اسم الـ endpoint الصحيح المتاح لباقتك تحديداً، وإضافته لقائمة
   `candidate_paths` في الدالة `_fetch_from_cryptorank()`.
   بخصوص RootData: endpoint جولات التمويل بالجملة `get_fac` موثّق رسمياً
   بأنه يتطلب باقة Plus/Pro، وبخصوص DefiLlama: endpoint `/raises` أصبح
   حسب التوثيق الحالي جزءاً من باقة Pro المدفوعة ($300/شهر) وليس مجانياً
   كما كان سابقاً — لذلك أصبح `DEFILLAMA_API_KEY` اختيارياً في الكود: بدونه
   يتخطى البوت هذا المصدر بهدوء (تحذير في اللوج) بدل تكرار خطأ 402.
2. **الفلتر الأولي بالكلمات المفتاحية (`_looks_like_target_category`)**:
   مصادر RootData وDefiLlama قد ترجع آلاف الجولات/المشاريع غير ذات الصلة
   (Gaming، Memecoins، إلخ)، فأضفنا فلتراً سريعاً وبسيطاً بكلمات مفتاحية
   (RWA, Infra, DePIN, AI...) **قبل** إرسال أي طلب للـ LLM، لتقليل
   استهلاك الـ API. هذا فلتر تقريبي فقط وليس نهائياً — التصنيف الدقيق
   والفلترة الشرعية/الاستثمارية النهائية تتم لاحقاً عبر الـ LLM نفسه وفق
   System Prompt الكامل. يمكنك تعديل قائمة `EARLY_STAGE_KEYWORDS` في
   `early_stage_source.py` لتوسيع أو تضييق هذا الفلتر الأولي.
3. **DefiLlama لا يميّز RWA/Infra دائماً بشكل دقيق**: حقل `category` في
   endpoint `/raises` ليس موحّداً 100% بين كل المشاريع، فبعض المشاريع قد
   لا تحمل تصنيفاً واضحاً حتى لو كانت RWA/Infra فعلياً. الفلتر الأولي
   يعتمد أيضاً على اسم المشروع والمصدر النصي (`source`) لتغطية هذه الحالة،
   لكنه يبقى تقريبياً وقد يفوّت بعض المشاريع أو يمرر بعضاً غير ذي صلة —
   النموذج (LLM) هو الفيصل النهائي في كل الحالات.
4. **التقييم الشرعي اجتهادي وليس فتوى رسمية**: التقرير الذي يولّده النموذج
   هو تحليل أولي مبني على الـ System Prompt الذي زوّدتني به، وليس فتوى
   شرعية معتمدة. يُفضّل أن يكون آخر فيصل في القرار الاستثماري هو مراجعة
   شخص أو مرجع شرعي موثوق، خصوصاً قبل اتخاذ قرارات مالية فعلية.
5. **حدود الـ Rate Limit**: انتبه لحدود عدد الطلبات في كل من المصادر
   (CryptoRank/CoinMarketCap/RootData/DefiLlama) ومزوّد الـ LLM
   (Together/DeepSeek)؛ `POLL_INTERVAL_MINUTES` موجود بالضبط للمساعدة
   على عدم تجاوزها. لاحظ أيضاً أن RootData يحسب "credits" لكل طلب
   (راجع باقتك)، فزيادة تكرار الفحص تزيد استهلاك الكريدت.
6. **التخزين المؤقت (`storage.py`)**: يحمي من تكرار إرسال نفس المشروع
   في كل دورة، لكنه ملف محلي بسيط؛ إذا أعدت نشر (Redeploy) الخدمة على
   Railway قد يُعاد ضبطه، فقد يُعاد إرسال بعض المشاريع القديمة مرة واحدة.

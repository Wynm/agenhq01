# 🎬 AgenHQ Auto-Video: ماكينة ديال فيديوهات قصيرة كتخدم بوحدها

**الريبو:** https://github.com/Wynm/agenhq01
**مثال ديال فيديو تصاوب هنا:** `sample.mp4` (فهاد الدوسي). تصاوب بلا حتى مفتاح، يعني بسكريبت تجريبي وخلفيات ملونة. ملي تزيد المفاتيح غادي يولي السكريبت جديد كل نهار والخلفيات فيديوهات حقيقية.

---

## شنو كيدير؟

كل نهار (10:00 UTC = 11:00 بالمغرب) GitHub Actions كيدير هادشي بوحدو:

1. **الفكرة والسكريپت** ← Gemini (مجاني) كيكتب فيديو ديال 30 حتال 60 ثانية بالعربية على: التقنية، الذكاء الاصطناعي، حيل الهاتف، طرق مشروعة للربح من الأنترنت، معلومات تقنية ممتعة… وكيعطي العنوان والوصف والهاشتاكات ديال كل منصة.
   ما كيعاودش نفس الفكرة: كيتسجل كلشي فـ `data/history.json`.
2. **الصوت** ← edge-tts (مجاني)، صوت مغربي `ar-MA-JamalNeural` (ولا `ar-MA-MounaNeural`، `ar-SA-HamedNeural`…).
3. **الصور/الفيديوهات** ← Pexels (مجاني) كيجيب لقطات عمودية على حسب الموضوع. إلا ما كانش المفتاح، كيصاوب خلفيات ملونة.
4. **المونطاج** ← ffmpeg: فيديو 1080x1920، كتابة عربية باينة (خط Cairo)، العنوان فالأول، وموسيقى إلا حطيتيها.
5. **الحفظ** ← الفيديو كيتحط فـ **Artifacts** و فـ **Releases** ديال الريبو (عندو رابط عمومي، والريبو public).
6. **النشر** ← إلا ربطتي **Postiz**، كينشر الفيديو فالحسابات ديالك (YouTube Shorts، TikTok، Instagram Reels، Facebook، X…) وكل منصة بالكابشن والهاشتاكات ديالها.
   **بلا ما تربط والو، كيصاوب الفيديو برك وما كينشر والو.**

> ⚠️ انشر غير فالحسابات ديالك. ماشي لايكات مزورة، ماشي بزاف ديال الحسابات باش تسبامي. هادشي كيبان ف TikTok وYouTube وكيسدو الحساب.

---

## 1) زيد المفاتيح (Secrets)

سير لـ: **github.com/Wynm/agenhq01 → Settings → Secrets and variables → Actions → New repository secret**

| الاسم (Name) | منين تجيبو | واش ضروري؟ |
|---|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey ← دخل بحساب Google ← **Create API key** ← كوبي | ضروري باش يتكتب سكريپت جديد كل نهار |
| `PEXELS_API_KEY` | https://www.pexels.com/api ← سجل (مجاني) ← **Your API Key** ← كوبي | مزيان بزاف (فيديوهات حقيقية فالخلفية) |

بلا هاد جوج، الماكينة كتخدم، ولكن كتعاود غير جوج سكريپتات تجريبيين.

---

## 2) كيفاش تشغلو بيدك

1. **github.com/Wynm/agenhq01 → Actions → Daily video → Run workflow**
2. تقدر تكتب:
   - `topic`: موضوع معين (مثلا: "كيفاش تحمي الواتساب ديالك")، ولا خليه خاوي.
   - `language`: `ar` (عربية)، `fr`، `en`…
   - `voice`: مثلا `ar-MA-MounaNeural` (صوت ديال مرا).
   - `publish`: واش ينشر ولا لا.
3. من بعد شي 3 حتال 6 دقايق، الفيديو كيبان فـ:
   - **Actions → الـ run → Artifacts** (zip فيه `video.mp4` و `meta.json`)
   - **Releases** (رابط مباشر للفيديو)

**تبدل عدد الفيديوهات فالنهار:** فـ `.github/workflows/daily-video.yml` زيد سطر `- cron:` آخر (مثلا `"0 18 * * *"` باش يخرج فيديو ثاني على 19:00).
**تبدل المواضيع، الصوت، اللغة، اسم البراند:** فـ `config.yaml`.
**الموسيقى:** حط ملفات `.mp3` (من YouTube Audio Library ولا Pixabay Music، وخاصك يكون عندك الحق تستعملها) فـ `assets/music/`.

---

## 3) ربط النشر: Postiz (هو الأساسي)

فتشنا فالـ GitHub ديالك: لقينا fork ديال **Mixpost** (`Wynm/mixpost`) ولكن ما مشغل فحتى بلاصة، والنسخة Lite ما فيهاش API وما كتنشرش لا ف YouTube لا ف TikTok لا ف Instagram. داكشي علاش اخترنا **Postiz**: مفتوح المصدر، عندو API، وكينشر ف YouTube وTikTok وInstagram وFacebook وX وLinkedIn وThreads وTelegram…

### أ) فين تشغل Postiz؟ (اختار وحدة)

- **Postiz Cloud** ← https://postiz.com : أسهل حاجة، سجل وصافي. فيه فترة تجربة، ومن بعد كيتخلص (شوف الأثمنة فالسيت ديالهم). ما كيحتاجش سيرفر.
- **Postiz على سيرفر ديالك (مجاني، self-hosted)** ← خاصك VPS فيه Docker (مثلا Oracle Cloud Always Free، ولا أي VPS رخيص). الشرح: https://docs.postiz.com/self-host/installation/docker-compose
  ⚠️ **Postiz ما يمكنش يخدم وسط GitHub Actions/Pages**، حيت خاصو يبقى خدام 24/24.

### ب) ربط الحسابات ديالك ف Postiz

داخل Postiz ← **Add Channel** ← ربط YouTube، TikTok، Instagram (Business/Creator)، Facebook Page، X… (كل واحد كيطلب منك تسجل الدخول ديالو).

### ج) جيب المفتاح ديال API

Postiz ← **Settings** ← **Public API** ← كوبي الـ API Key.

### د) زيدو ف GitHub

**Settings → Secrets and variables → Actions**

| فين | الاسم | القيمة |
|---|---|---|
| **Secrets** | `POSTIZ_API_KEY` | المفتاح لي كوبيتي |
| **Variables** (تبويب Variables) | `PUBLISHERS` | `postiz` |
| Variables (غير إلا كان self-hosted) | `POSTIZ_API_URL` | `https://الدومين-ديالك/api/public/v1` |
| Variables (اختياري) | `POSTIZ_INTEGRATIONS` | الـ IDs ديال الحسابات لي بغيتي تنشر فيهم، مفرقين بفاصلة. إلا خليتيه خاوي كينشر فكاع الحسابات. |
| Variables (اختياري) | `POSTIZ_POST_TYPE` | `now` (ينشر دغيا، هو الافتراضي) ولا `draft` (كيحطو مسودة ف Postiz وانت كتراجع وكتنشر) |

💡 **نصيحة:** فالأيام الأولى دير `POSTIZ_POST_TYPE = draft` باش تشوف الفيديوهات قبل ما يتنشرو. ملي ترتاح ليهم، رجعها `now`.

**باش تعرف الـ IDs ديال الحسابات:** Actions → **List Postiz channels** → Run workflow ← كيطبع لكل حساب: ID، المنصة، والسمية.

### هـ) جرب

Actions → Daily video → Run workflow (`publish` ✅). تشوف `publish_result.json` فالـ Artifact، ولا اللوج ديال خطوة **Publish**.

---

## 4) حلول أخرى (احتياط)

- **YouTube مباشرة** (بلا Postiz): زيد `YT_CLIENT_ID`، `YT_CLIENT_SECRET`، `YT_REFRESH_TOKEN` (OAuth ديال القناة ديالك من Google Cloud Console، مع YouTube Data API v3)، و `PUBLISHERS` = `youtube` (ولا `postiz,youtube`).
  ⚠️ إلا كان تطبيق Google Cloud ديالك ما متحققش منو (unverified)، YouTube كيخلي الفيديوهات **private** حتى يدوز الـ audit.
- **Webhook عام** (n8n، Make، Zapier، ولا أي API): زيد `POST_WEBHOOK_URL` (و `POST_WEBHOOK_TOKEN` إلا بغيتي)، و `PUBLISHERS` = `webhook`. كيوصلك JSON فيه رابط الفيديو، والعنوان، والكابشن ديال كل منصة.
- **Mixpost**: كاين adapter ولكن ما تجربش، وخاصو Mixpost **Pro** (بالفلوس) حيت Lite ما فيهاش API.

---

## 5) إلا وقع مشكل

- **Actions → الـ run لي فشل → شوف الخطوة الحمرا**.
- `Gemini 429` ← وصلتي للحد ديال النسخة المجانية، عاود من بعد شوية (ولا بدل `gemini_model` ف `config.yaml`).
- `No usable Postiz channels` ← ما ربطتيش الحسابات ف Postiz، ولا الـ IDs ف `POSTIZ_INTEGRATIONS` غالطين.
- `skip postiz: missing secrets` ← `POSTIZ_API_KEY` ما مزادش ف Secrets.

## الملفات المهمة فالريبو

```
config.yaml                        ← المواضيع، الصوت، اللغة، البراند، المنصات
autovid/script_gen.py              ← Gemini + منع التكرار
autovid/tts.py                     ← الصوت (edge-tts)
autovid/visuals.py                 ← Pexels + الخلفيات الملونة
autovid/assemble.py                ← المونطاج (ffmpeg) + الكتابة
autovid/publishers/postiz.py       ← النشر عبر Postiz (الأساسي)
autovid/publishers/youtube.py      ← YouTube مباشرة (احتياط)
autovid/publishers/webhook.py      ← Webhook عام
.github/workflows/daily-video.yml  ← الجدولة اليومية
data/history.json                  ← الفيديوهات لي تصاوبو (باش ما يتعاودوش)
```

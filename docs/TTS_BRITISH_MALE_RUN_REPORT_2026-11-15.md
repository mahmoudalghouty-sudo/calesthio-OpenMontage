# تقرير تشغيل اختبار Kokoro — الأصوات البريطانية الرجالية (2026-11-15)

**النتيجة: لم يكتمل الاختبار. لم يُولَّد أي ملف WAV.**
الحالة تبقى: **designed, not runtime-tested**. لم يُختر أي صوت.

## 1. بيئة التشغيل

| البند | القيمة |
|---|---|
| النظام | Linux 6.18 x86_64 (حاوية سحابية مؤقتة) |
| المعالج | Intel Xeon @ 2.10GHz — 4 أنوية، بدون GPU |
| الذاكرة | 15 GiB (متاح ~15 GiB)، بدون swap |
| Python النظام | 3.13.18 (غير مدعوم من kokoro 0.9.4: يتطلب `>=3.10,<3.13`) |
| Python المستخدم للاختبار | 3.12 في بيئة افتراضية معزولة خارج المستودع |
| FFmpeg | 6.1.1 |

## 2. الاعتماديات المثبتة (كلها مجانية ومفتوحة المصدر، بدون أي API أو مفتاح)

- kokoro 0.9.4 (Apache-2.0)، misaki 0.9.4، espeakng-loader 0.2.4
- torch 2.15.0 (`cuda_available=False`، يعمل على CPU بأربعة خيوط)
  - ملاحظة: نطاق `download.pytorch.org` محجوب، فثُبّتت نسخة PyPI الافتراضية التي تتضمن مكتبات CUDA غير مستخدمة (حجم البيئة ~5.6 GB). لا تأثير على التكلفة.
- transformers 5.23.0، huggingface_hub 2.4.0، spaCy 3.8.18 + en_core_web_sm 3.8.0، soundfile 0.14.0، numpy 2.5.4

## 3. ما شُغِّل فعلياً

النص: النص الافتراضي المضمّن في `scripts/test_kokoro_british_male_tts.py` دون تعديل.
الأمر: `python scripts/test_kokoro_british_male_tts.py` (السكربت كما هو، بدون تعديل).

| التشغيل | رمز الخروج | الخطأ | زمن التشغيل | أقصى ذاكرة (RSS) |
|---|---|---|---|---|
| Online (التنزيل الأول) | 3 | `Could not load Kokoro British-English pipeline: 403 Forbidden` | 11.6 s | 1045 MiB |
| Offline (`--offline`) | 3 | `...cannot find the requested files in the local cache...` | 5.1 s | 1027 MiB |

السبب الجذري: سياسة الشبكة في هذه البيئة تحجب `huggingface.co` (رد البروكسي 403 على CONNECT)، وهو المصدر الرسمي لملفات `hexgrad/Kokoro-82M` (الأوزان والأصوات `voices/bm_*.pt`). طُلب السماح لنطاقات Hugging Face عبر بيئة شخصية جديدة، **ورُفض الطلب**، فلم يُنزَّل النموذج.

النتائج لكل صوت: لم يصل التنفيذ إلى مرحلة التوليد، فلم يُختبر أي من `bm_george` و`bm_fable` و`bm_daniel` و`bm_lewis`، ولا توجد مدد توليد أو مدد صوت. أرقام الذاكرة أعلاه تخص تحميل المكتبات فقط (torch + spaCy) وليست استهلاك التوليد.

ما ثبت جزئياً: سلوك "الفشل المغلق" (fail-closed). عند غياب النموذج توقف السكربت برسالة واضحة ورمز خروج 3، ولم ينتقل إلى لهجة أو جنس صوت أو مزوّد بديل.

## 4. مصفوفة التحقق من وثيقة التصميم

| الفحص | الحالة |
|---|---|
| استيراد Kokoro | ✅ نجح (`from kokoro import KPipeline`) |
| تحميل النموذج على CPU | ❌ فشل — النموذج غير متاح (الشبكة محجوبة) |
| توليد الأصوات الأربعة | ⛔ لم يُنفَّذ |
| التحقق من ملفات WAV | ⛔ لم يُنفَّذ |
| فشل مغلق عند غياب الأصول | ✅ لوحظ (exit 3، بدون بديل) |
| فشل مغلق لمعرّف صوت غير صالح | ⛔ لم يُختبر (يحتاج النموذج) |
| توليد Offline بعد التخزين المؤقت | ⛔ لم يُختبر (لا يوجد تخزين مؤقت) |
| دمج FFmpeg | ⛔ لم يُختبر |

## 5. اختبارات التحقق في المستودع

الأمر:
`OPENMONTAGE_PROFILE=editing_only python -m pytest tests/contracts/test_zero_cost_studio_budget.py tests/contracts/test_pipeline_catalog.py tests/tools/test_editing_only_execution_policy.py`

النتيجة: **58 نجح، 2 فشل**. الفشل نفسه يتكرر بدون متغير `OPENMONTAGE_PROFILE`. الاختباران لا علاقة لهما بـ TTS، وموجودان أصلاً على فرع `cloud-studio-foundation`:

1. `test_zero_cost_studio_budget.py::test_positive_cost_cannot_be_reserved_under_zero_budget`
   يتوقع `BudgetExceededError`، لكن ظهر `ApprovalRequiredError: Action costs $0.01, exceeds single-action threshold $0.00` (`tools/cost_tracker.py:130`). أي أن العملية المكلفة رُفضت، لكن بنوع خطأ مختلف عن المتوقَّع.
2. `test_editing_only_execution_policy.py::test_remote_video_reference_is_blocked_but_local_file_is_allowed`
   مصدر فيديو بعيد **وصل إلى `execute()`** بدلاً من حجبه بـ `PermissionError("remote_video_source")`. هذه **ثغرة فعلية في حارس ملف editing_only** وتستحق الإصلاح.

لم يُصلَح أي من الاختبارين، لأن ذلك خارج نطاق المهمة.

## 6. خيارات المتابعة (تحتاج قراركم)

1. **السماح بنطاقات Hugging Face** في إعدادات شبكة البيئة (أو قبول البيئة المقترحة)، ثم إعادة تشغيل الاختبار. المطلوب هو `huggingface.co` ونطاقات التنزيل `cas-bridge.xethub.hf.co` و`cas-server.xethub.hf.co` و`transfer.xethub.hf.co` و`cdn-lfs.hf.co`. هذا هو المسار المطابق لوثيقة التصميم.
2. **التشغيل على جهازكم المحلي**: نفس السكربت مع Python 3.10–3.12 و`pip install kokoro==0.9.4 soundfile`، ثم التشغيل مرة بدون `--offline` ومرة مع `--offline`.
3. نسخة ONNX من Kokoro-82M من طرف ثالث (على GitHub) قد تكون متاحة، لكنها **محرك مختلف** عن المحدد في التصميم، فلم تُستخدم دون موافقتكم.

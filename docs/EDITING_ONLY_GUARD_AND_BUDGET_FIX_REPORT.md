# تقرير إصلاح: حارس editing_only وترتيب فحوص الميزانية

الفرع الأساسي: `cloud-studio-foundation` (c373376)
فرع الإصلاح: `claude/fix-editing-only-guard-budget`
لا يوجد Pull Request ولا دمج. التغييرات بانتظار المراجعة.

## 1. `test_editing_only_execution_policy` — السبب

**الحارس لم يفشل في حجب الرابط.** السجل يُظهر أن المُدخل الذي وصل إلى `execute()` كان `{'source': '/workspace/input.mp4'}`، أي الملف المحلي المسموح به. الرابط `https://…` حُجب فعلاً بـ `PermissionError`.

الخلل في أداة الاختبار الوهمية `RemoteVideoAnalysisTool`: دالة `execute()` فيها كانت ترفع `AssertionError` لكل استدعاء، فلم يكن ممكناً أن ينجح الاستدعاء المحلي الذي يتوقع الاختبار نجاحه. صُحّحت الأداة الوهمية لترفض الروابط فقط وتسجّل المصادر المحلية التي تصلها. أُضيف أيضاً تحقق بأن المصدر المحلي هو الوحيد الذي وصل.

### لكن فحص الحارس كشف ثغرات حقيقية، وأُصلحت في التنفيذ نفسه

| الثغرة في الحارس الأصلي | الأثر | الإصلاح |
|---|---|---|
| الفحص مربوط بالاسم `self.name == "video_analyzer"` | أي صنف فرعي من `VideoAnalyzer` باسم مختلف يتجاوز الحارس، ويصل إلى `_detect_platform` ثم `YouTubeTranscriptApi().list()`، وهو اتصال شبكي مباشر داخل جسم الأداة | خاصية معلنة `remote_source_input_keys` في `BaseTool`، تُورَّث تلقائياً. `VideoAnalyzer` يعلن `["source"]`، ويبقى فحص الاسم كخط دفاع احتياطي |
| كشف الروابط بالبادئات `http://` و`https://` و`www.` فقط | `ftp://` و`rtmp://` و`s3://` و`//host` غير مكتشفة | `_is_remote_reference`: أي `scheme://` عدا `file://`، وأيضاً `//` و`www.`، مع فحص القوائم والقواميس |
| قيمة `OPENMONTAGE_PROFILE` تُقارن حرفياً | `editing-only` أو `Editing Only` تعطّل الحماية بصمت | توحيد القيمة: إزالة المسافات الطرفية، أحرف صغيرة، `-` والمسافة تتحول إلى `_` |

### ترتيب الأغلفة (wrappers)

الترتيب الفعلي، من الخارج إلى الداخل:
`_enforce_editing_only` ← `_cache_execute` ← `_instrument_execute` ← `execute` الخاصة بالأداة.

ما ثبت بالاختبارات:
- القرار يُتخذ قبل أي بحث في التخزين المؤقت: `AssetCache.try_restore` و`store` لا تُستدعيان، ولا يُنشأ ملف الإخراج.
- لا يُكتب أي حدث Backlot (`emit_event` لا تُستدعى، ولا يُنشأ `events.jsonl`).
- `VideoDownloader.execute` و`TranscriptFetcher.execute` و`_detect_platform` لا تُستدعى أبداً لمصدر بعيد.
- الاستدعاء غير المباشر محمي أيضاً: أداة محلية مسموحة تستدعي `execute()` لأداة محجوبة فيُرفض الاستدعاء في الأداة الداخلية.
- ترتيب الأغلفة نفسه مثبّت باختبار، حتى لا يتغير مستقبلاً دون أن يُلاحظ.

## 2. `test_zero_cost_studio_budget` — السبب

`CostTracker.reserve()` كانت تفحص بوابات الموافقة (حد العملية الواحدة، أول استخدام لأداة مدفوعة) **قبل** فحص سقف الميزانية. مع `single_action_approval_usd=0.0` تتحول كل عملية بقيمة 0.01$ إلى `ApprovalRequiredError` قبل الوصول إلى فحص السقف.

هذا يخالف السياسة المعتمدة في `config.yaml`، وهي `mode: cap` و`total_usd: 0.00` ("Hard stop: never reserve a paid operation"). رسالة "تحتاج موافقة" توحي بأن الموافقة البشرية قد تسمح بالإنفاق، بينما السقف يمنعه في كل الأحوال.

**الإصلاح في `tools/cost_tracker.py`:** في وضع `CAP` يُفحص السقف أولاً ويُرفع `BudgetExceededError`. بوابات الموافقة تبقى كما هي للعمليات التي تستطيع الميزانية تمويلها. سلوك وضعي `WARN` و`OBSERVE` لم يتغير.

## 3. الملفات المعدّلة

- `tools/base_tool.py`: الحارس، وتصنيف الروابط، وتوحيد قيمة الملف، و`editing_only_block_reasons()` (دالة بلا آثار جانبية)، وخاصية `remote_source_input_keys`.
- `tools/analysis/video_analyzer.py`: إعلان `remote_source_input_keys = ["source"]`.
- `tools/cost_tracker.py`: ترتيب الفحوص في `reserve()`.
- `tests/tools/test_editing_only_execution_policy.py`: تصحيح الأداة الوهمية المعطوبة.
- `tests/tools/test_editing_only_bypass_vectors.py` (جديد): 58 اختباراً لمحاولات التجاوز.
- `tests/contracts/test_zero_cost_studio_budget.py`: 5 اختبارات جديدة.

## 4. نتائج الاختبارات

| المجموعة | الفرع الأساسي | فرع الإصلاح |
|---|---|---|
| الاختباران المستهدفان + ملفاهما | 2 فشل | 12 نجح، 0 فشل |
| اختبارات التجاوز الجديدة | — | 58 نجح |
| المجموعة الكاملة (`pytest tests --continue-on-collection-errors`) | 2931 نجح، 6 فشل، 17 تخطٍّ، 1 خطأ تجميع | **2996 نجح، 4 فشل، 17 تخطٍّ، 1 خطأ تجميع** |

**التحقق من أن الاختبارات الجديدة تكشف الثغرات:**
- اختبارات التجاوز شُغّلت على الحارس الأصلي: **30 فشل** و28 نجاح.
- اختبارات الميزانية شُغّلت على `cost_tracker.py` الأصلي: **2 فشل**.

## 5. مشكلات متبقية (موجودة أصلاً على `cloud-studio-foundation`، ولم تُعدَّل)

1. `tests/contracts/test_phase0_contracts.py::TestConfig::test_load_from_yaml` يتوقع `total_usd == 10.0`، بينما `config.yaml` المعتمد يحدد `0.00`. الاختبار قديم ويتعارض مع سياسة الصفر.
2. `tests/backlot/test_simulate_run.py::test_simulated_run_completes_from_a_fresh_project` و`tests/contracts/test_backlot_contract.py` (اختباران)، و`tests/qa/test_08_end_to_end.py` (خطأ تجميع): كلها `GATE VIOLATION`. ملفات `pipeline_defs/*.yaml` على هذا الفرع تتطلب موافقة بشرية (`human_approval_default: true`)، والمحاكيات تكتب `completed` بدون `human_approved=True`.
3. لا يوجد في الكود التشغيلي ما يبني `CostTracker` من إعدادات `config.yaml`، ولا ما يربطه بـ `BaseTool.execute`. سياسة الميزانية تُطبَّق فقط حيث يستدعي الوكيل `reserve()` يدوياً.
4. حدود الحارس لم تتغير:
   - لا يمنع استدعاءً مقصوداً عبر `execute.__wrapped__`.
   - لا يمنع استبدال `execute` على الصنف بعد إنشائه.
   - لا يعالج أدوات تفتح اتصالاً من دوال غير `execute()`.
   - لا يعالج مكتبات تنزّل نماذج عند أول استخدام (مثل faster-whisper).
   - مسارات UNC في Windows (`\\server\share`) تُعامل كمسارات محلية.

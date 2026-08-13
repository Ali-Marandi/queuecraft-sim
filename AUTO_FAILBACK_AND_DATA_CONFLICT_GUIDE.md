# Auto-Failback و مدیریت تعارض داده در معماری چندناحیه‌ای QueueCraft

## اصل طراحی

Auto-Failback نباید معکوس ساده Auto-Failover باشد. Failover برای حفظ خدمت در شرایط خرابی اجرا می‌شود؛ اما Failback یک تغییر برنامه‌ریزی‌شده در مسیر ترافیک و در برخی معماری‌ها مالکیت نوشتن است. بازگشت بدون بررسی سلامت پایدار، lag همگام‌سازی و بودجه خطا می‌تواند باعث **flapping**، از دست‌رفتن داده یا تشدید outage شود.

> **قاعده اجرایی:** نسخه فعلی QueueCraft فقط آمادگی Failback و مراحل پیشنهادی آن را شبیه‌سازی می‌کند. هیچ تغییر DNS، load balancer، routing rule، replica یا منبع ابری به‌صورت خودکار اعمال نمی‌شود.

## ۱. ماشین حالت Failback

| حالت | شرط ورود | عمل مجاز | شرط خروج |
|---|---|---|---|
| `failed_over` | Primary از سلامت خارج شده و مسیر جایگزین فعال است | فقط نگه‌داری مسیر جایگزین و ثبت رخداد | Primary نشانه‌های recovery را نشان دهد |
| `recovery_observing` | health check، synthetic check و telemetry اولیه Primary مثبت‌اند | شمارش مدت سلامت پایدار؛ عدم تغییر ترافیک | عبور از مدت مشاهده یا مشاهده خطا |
| `replication_verifying` | سلامت پایدار کافی است | سنجش replication lag، checksum و backlog | lag زیر آستانه و داده همگرا باشد |
| `canary_failback` | داده و SLO قابل قبول‌اند | انتقال تدریجی وزن، مثلاً ۱۰٪ سپس ۲۵٪ | تأیید SLO در canary یا rollback |
| `progressive_failback` | canary سالم است | افزایش مرحله‌ای وزن به Primary | رسیدن به وزن هدف یا توقف ایمن |
| `stabilized` | وزن هدف، SLO و همگرایی داده برقرارند | اعمال cooldown و بستن رخداد | رخداد جدید یا دوره بررسی تکمیل شود |
| `rolled_back` | SLO/Lag/health نقض شده است | بازگرداندن وزن به region پایدار و ثبت علت | بررسی انسانی و شروع مجدد از مرحله امن |

## ۲. گاردریل‌های Auto-Failback

Failback تنها وقتی باید پیشنهاد شود که همه شرط‌های زیر برقرار باشند.

| گاردریل | مثال تنظیم | دلیل |
|---|---|---|
| سلامت پایدار Primary | حداقل ۱۵ bucket سالم | جلوگیری از بازگشت روی recovery موقت |
| synthetic check مستقل | عبور از مسیر واقعی کاربر | جلوگیری از اتکا صرف به health endpoint |
| replication lag | کمتر از RPO مصوب | جلوگیری از exposure داده عقب‌مانده |
| checksum / ledger audit | بدون اختلاف حل‌نشده | اطمینان از همگرایی پیش از انتقال مالکیت |
| SLO Error Budget | نبود وضعیت `critical` و burn rate قابل قبول | جلوگیری از افزودن ریسک به سرویس ناپایدار |
| canary traffic | ۱۰٪ → ۲۵٪ → ۵۰٪ → ۱۰۰٪ | محدودکردن blast radius |
| dwell/cooldown | مثلاً ۱۵ دقیقه بین مراحل | جلوگیری از oscillation و تصمیم‌گیری روی سیگنال کم |
| تأیید انسانی | پیش از مرحله ۵۰٪ یا ۱۰۰٪ در سرویس حساس | کنترل تغییر و مسئولیت‌پذیری |

### شبه‌کد کنترلر

```python
if primary_healthy_for >= recovery_observation_buckets \
   and replication_lag_seconds <= max_replication_lag_seconds \
   and unresolved_conflicts == 0 \
   and slo.alert_level != "critical":

    proposed_weight = next_canary_weight(current_weight)
    run_canary(primary_weight=proposed_weight)

    if canary_slo_passes and no_new_conflicts and cooldown_elapsed:
        request_human_approval_or_continue(proposed_weight)
    else:
        rollback_to_last_known_good_weight(reason="canary SLO or consistency gate failed")
else:
    continue_observation()
```

## ۳. مدل داده و تعارض

در معماری multi-region، ابتدا باید مشخص شود کدام نوع داده می‌تواند active-active باشد. **داده‌های قابل ادغام** مانند شمارنده‌های افزایشی، رخدادهای append-only و وضعیت‌هایی با semantics مناسب برای CRDT، نسبت به **داده‌های تراکنشی حساس** مانند پرداخت، رزرو انحصاری، موجودی غیرقابل‌منفی یا ترتیب دقیق workflow رفتار متفاوتی دارند.

| کلاس داده | سیاست پیشنهادی | حل تعارض پیشنهادی |
|---|---|---|
| رخداد append-only | Event ID یکتا و immutable ledger | deduplication بر اساس event ID؛ حذف‌نکردن تاریخچه |
| شمارنده افزایشی | CRDT G-Counter یا aggregation مرکزی | merge جمعی؛ نه last-write-wins |
| پروفایل یا تنظیمات کم‌ریسک | نسخه‌بندی و merge فیلدی | LWW فقط با timestamp قابل اعتماد و tie-breaker قطعی |
| موجودی/رزرو/پرداخت | single-writer یا quorum/consensus | تعارض خودکار ممنوع؛ hold و بررسی انسانی یا workflow جبرانی |
| وضعیت workflow | state machine با transitionهای مجاز | reject transition متعارض؛ ثبت compensation event |

### متادیتای حداقل هر رکورد

```json
{
  "record_id": "job-123",
  "version": {"region-a": 18, "region-b": 7},
  "origin_region": "region-a",
  "written_at_utc": "2026-08-14T12:00:00Z",
  "idempotency_key": "...",
  "payload": {"...": "..."}
}
```

`version` می‌تواند یک vector clock باشد. اگر clock یک رکورد همه مؤلفه‌های رکورد دیگر را پوشش دهد و حداقل یکی بزرگ‌تر باشد، آن رکورد برنده واضح است. اگر هیچ‌کدام بر دیگری غالب نباشند، تغییرها concurrent هستند و باید بر اساس کلاس داده، merge قابل اثبات، جبران یا ارجاع انسانی انجام شود.

## ۴. جریان رفع تعارض پیش از Failback

1. نوشتن‌ها در region فعال با idempotency key و event ID ثبت می‌شوند.
2. replication، رخدادها را منتقل و بر اساس event ID deduplicate می‌کند.
3. resolver، نسخه‌ها را مقایسه می‌کند. تغییرهای غالب خودکار پذیرفته می‌شوند.
4. تغییرهای concurrent ابتدا با rule نوع داده، مانند merge فیلدی یا CRDT، بررسی می‌شوند.
5. تعارض‌های تراکنشی در `conflict_hold` باقی می‌مانند و Failback به مرحله canary نمی‌رود.
6. پس از zero شدن تعارض‌های حل‌نشده، checksum/ledger audit و RPO gate، امکان انتقال تدریجی ترافیک فراهم می‌شود.
7. پس از هر افزایش وزن، resolver و SLO دوباره ارزیابی می‌شوند.

## ۵. شاخص‌های مانیتورینگ لازم

| متریک | کاربرد |
|---|---|
| `queuecraft_replication_lag_seconds` | gate اصلی RPO و Failback |
| `queuecraft_conflicts_total` | نرخ تعارض‌های شناسایی‌شده، برچسب کم‌کاردینال `data_class` و `status` |
| `queuecraft_unresolved_conflicts` | شرط توقف قطعی Failback |
| `queuecraft_failback_stage` | Gauge مرحله ۰ تا ۱۰۰٪ وزن بازگشتی |
| `queuecraft_failback_rollbacks_total` | کنترل flapping و کیفیت سیاست |
| `queuecraft_slo_burn_rate` | جلوگیری از افزایش وزن در شرایط مصرف سریع بودجه |
| `queuecraft_synthetic_check_success` | پوشش مستقل از health endpoint داخلی |

## ۶. سیاست عملیاتی پیشنهادی

در محیط‌های حساس، مرحله ۱۰٪ و ۲۵٪ را می‌توان خودکار اما فقط در محیط شبیه‌سازی یا با guardrail سخت اجرا کرد؛ حرکت به ۵۰٪ و ۱۰۰٪ باید نیازمند approval رسمی باشد. هر rollback باید reason، نسخه پیکربندی، SLO snapshot، lag و وضعیت تعارض را در audit log حفظ کند. اتصال واقعی به DNS، traffic manager یا database replication باید یک integration مجزا با دسترسی حداقلی، dry-run پیش‌فرض و کنترل تغییر باشد.

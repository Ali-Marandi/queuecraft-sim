# پیاده‌سازی SLO Error Budget و مانیتورینگ آنلاین در QueueCraft

## ۱. تعریف درست SLI و SLO

SLO یک سطح هدف برای قابلیت اتکای سرویسی است که کاربر تجربه می‌کند و SLI باید نسبت رخدادهای خوب به کل رخدادها را اندازه بگیرد. این مدل امکان می‌دهد SLO به بودجه خطا تبدیل شود؛ برای نمونه، هدف ۹۹٫۹٪ یعنی ۰٫۱٪ از رخدادها در پنجره تعریف‌شده می‌توانند «بد» باشند. [1]

در QueueCraft، یک رخداد در شبیه‌سازی چندناحیه‌ای زمانی **خوب** محسوب می‌شود که هم سرویس دریافت کرده باشد و هم latency مسیر آن کمتر یا مساوی آستانه SLO باشد. درخواست پاسخ‌نداده یا در مسیر با latency بالاتر از آستانه، رخداد بد است. این تعریف باید پیش از اعمال در محیط واقعی با مالک محصول، عملیات و SRE تأیید شود؛ تعریف SLO یک تصمیم محصولی است، نه یک مقدار صرفاً فنی. [1]

| جزء | نمونه QueueCraft | تصمیمی که باید سازمان تأیید کند |
|---|---|---|
| SLI دسترس‌پذیری | `good_requests / total_requests` | کدام پاسخ‌ها واقعاً برای کاربر «موفق» هستند؟ |
| SLI latency | درخواست‌های زیر `latency_threshold_ms` | آستانه latency برای هر نوع کاربر یا عملیات چیست؟ |
| SLO | `availability_target=0.99` در یک پنجره rolling | هدف و پنجره واقعی مثلاً ۲۸ روز یا ۳۰ روز |
| Error Budget | `total × (1 − target)` | چه پیامد عملیاتی برای مصرف بودجه وجود دارد؟ |
| Burn Rate | نرخ مصرف بودجه نسبت به نرخ مجاز | چه حدی هشدار، ticket یا page ایجاد می‌کند؟ |

## ۲. محاسبه Error Budget در ماژول

کلاس `SLOMonitor` در `multi_region_failover.py` برای هر bucket این چهار مقدار را دریافت می‌کند: کل درخواست‌ها، درخواست‌های خوب، تعداد درخواست‌های منطبق با latency، و شناسه bucket. سپس snapshot پنجره rolling را می‌سازد.

```python
from multi_region_failover import SLODefinition, SLOMonitor

slo = SLODefinition(
    availability_target=0.99,
    latency_threshold_ms=250,
    rolling_window_buckets=30,
    warning_budget_remaining_ratio=0.25,
    critical_budget_remaining_ratio=0.0,
)
monitor = SLOMonitor(slo)

snapshot = monitor.record(
    bucket=17,
    total_requests=1_000,
    good_requests=992,
    latency_compliant_requests=992,
)
print(snapshot)
```

فرمول‌های اصلی به شکل زیر هستند:

```text
bad_requests            = total_requests − good_requests
allowed_bad_requests    = total_requests × (1 − availability_target)
remaining_error_budget  = allowed_bad_requests − bad_requests
burn_rate               = (bad_requests / total_requests) / (1 − availability_target)
```

خروجی شامل `remaining_error_budget_requests`، نسبت بودجه باقیمانده، `error_budget_burn_rate` و سطح هشدار است. اگر نسبت بودجه باقیمانده کمتر یا مساوی آستانه هشدار باشد، وضعیت `warning` و اگر منفی یا مساوی آستانه بحرانی باشد، وضعیت `critical` می‌شود. در حالت عادی، وضعیت `healthy` است.

> **محدودیت مهم:** در نمونه فعلی، پنجره بر اساس تعداد bucketهای دریافت‌شده نگهداری می‌شود. برای تولید واقعی، bucket باید به یک interval زمانی ثابت مانند یک دقیقه یا پنج دقیقه نگاشت شود و سیاست سازمان برای پنجره ۳۰روزه/۲۸روزه در لایه ذخیره‌سازی time-series اعمال گردد.

## ۳. معماری پیشنهادی مانیتورینگ آنلاین

مانیتورینگ آنلاین باید از **داده اندازه‌گیری‌شده** تغذیه شود، نه از پیش‌بینی. شبیه‌ساز QueueCraft برای برنامه‌ریزی ظرفیت به کار می‌رود؛ telemetry تولیدی برای سنجش عملکرد واقعی پس از استقرار است. برای سرویس‌های آنلاین، شمار درخواست، خطا و latency از معیارهای بنیادی هستند و شمارش معمولاً در پایان درخواست باعث هم‌راستایی بهتر با نتیجه و latency می‌شود. [3]

```text
Application / Load Balancer
        │  counters, latency histograms, queue depth
        ▼
OpenTelemetry or Prometheus instrumentation
        │  low-cardinality labels: service, region, route-class, outcome
        ▼
Collector / Metrics backend
        │  fixed-interval aggregation
        ▼
SLO evaluator + QueueCraft policy layer
        │  budget snapshot, burn rate, alert level
        ├── Dashboard / report
        ├── Ticket or page according to approved policy
        └── Human-reviewed capacity or failover decision
```

OpenTelemetry برای metricها ابزارهایی مانند Counter، UpDownCounter، Gauge و Histogram ارائه می‌کند؛ Counter برای رخدادهای تجمعی، Gauge برای وضعیت جاری مانند عمق صف، و Histogram برای latency مناسب هستند. [4] Prometheus نیز برای سرویس‌های آنلاین، شمار درخواست‌ها، خطاها، latency و درخواست‌های درحال‌اجرا را معیارهای کلیدی می‌داند. [3]

### ۳.۱ قرارداد متریک پیشنهادی

| متریک | نوع | برچسب مجاز | کاربرد |
|---|---|---|---|
| `queuecraft_requests_total` | Counter | `region`, `outcome`, `route_class` | محاسبه denominator و خطا |
| `queuecraft_request_duration_seconds` | Histogram | `region`, `route_class` | SLI latency و tail latency |
| `queuecraft_unserved_requests_total` | Counter | `region`, `reason` | سنجش شکست failover یا کمبود ظرفیت |
| `queuecraft_failover_events_total` | Counter | `from_region`, `to_region`, `reason` | تحلیل resilience و رخدادها |
| `queuecraft_queue_depth` | Gauge | `region`, `tier` | شاخص فشار صف و backlog |
| `queuecraft_error_budget_remaining` | Gauge | `slo_name` | نمایش بودجه باقیمانده |
| `queuecraft_slo_burn_rate` | Gauge | `slo_name`, `window` | هشدار مبتنی بر سرعت مصرف بودجه |

برچسب‌ها باید کم‌کاردینال باشند. شناسه کاربر، request ID، مسیر URL خام، job ID یا نام مشتری نباید label متریک باشند، زیرا تعداد ترکیب‌های زیاد، هزینه حافظه و محاسبه را بالا می‌برد و ممکن است تحلیل هشدار را مختل کند. [3] [4]

### ۳.۲ نمونه instrumentation مستقل از فروشنده

```python
# در نقطه پایان درخواست یا worker، پس از مشخص‌شدن نتیجه:
started = monotonic()
try:
    response = process_request(request)
    outcome = "success"
except Exception:
    outcome = "error"
    raise
finally:
    duration = monotonic() - started
    # Counter: outcome و region فقط برچسب‌های کم‌کاردینال هستند.
    requests_total.add(1, {"region": region, "outcome": outcome, "route_class": "queue-api"})
    # Histogram: زمان اجرای کامل درخواست.
    request_duration.record(duration, {"region": region, "route_class": "queue-api"})
```

در این مثال، exporter یا backend عمداً مشخص نشده است. OpenTelemetry metric exporter می‌تواند داده را به Collector یا backend انتخاب‌شده سازمان ارسال کند. [4] این اتصال باید در یک سرویس یا agent مورد تأیید سازمان پیکربندی شود؛ نسخه دسکتاپ QueueCraft نباید بدون تأیید، telemetry حساس را به بیرون ارسال کند.

## ۴. منطق هشدار: از threshold خام به Burn Rate

هشدار صرفاً بر اساس عبور لحظه‌ای از SLO معمولاً precision ضعیفی دارد، زیرا رویدادهای کوتاه و کم‌اثر هم می‌توانند alert ایجاد کنند. Google SRE استفاده از burn rate و پنجره‌های چندگانه را به‌عنوان الگوی مناسب برای متعادل‌کردن سرعت تشخیص، precision و recall توضیح می‌دهد. [2]

| شدت | پنجره بلند / کوتاه پیشنهادی | هدف عملیاتی |
|---|---|---|
| Page | ۱ ساعت / ۵ دقیقه | مصرف سریع بودجه؛ نیازمند واکنش فوری |
| Page | ۶ ساعت / ۳۰ دقیقه | اختلال مهم و پایدار |
| Ticket | ۳ روز / ۶ ساعت | مصرف آهسته اما معنادار؛ نیازمند پیگیری برنامه‌ریزی‌شده |

این اعداد نقطه شروع هستند، نه تنظیم نهایی. ترافیک کم، ارزش هر درخواست، امکان retry و تفاوت مناطق باید هنگام تنظیم آستانه‌ها بررسی شوند. خدمات کم‌ترافیک ممکن است با یک خطا burn rate بسیار بالا نشان دهند و به synthetic checks یا سیاست متفاوت نیاز داشته باشند. [2]

### ۴.۱ شبه‌کد ارزیابی آنلاین

```python
for interval in telemetry_intervals:
    total = query_total_requests(interval)
    successful_and_fast = query_good_requests(interval, latency_threshold_ms=250)
    snapshot = slo_monitor.record(
        bucket=interval.index,
        total_requests=total,
        good_requests=successful_and_fast,
    )

    if snapshot["alert_level"] == "critical":
        create_or_escalate_incident(snapshot)  # طبق Runbook سازمان
    elif snapshot["alert_level"] == "warning":
        create_ticket_and_review_capacity(snapshot)

    persist_auditable_snapshot(snapshot)
```

تابع‌های `create_or_escalate_incident` و `create_ticket_and_review_capacity` باید در محیط واقعی به ابزارهای مورد تأیید سازمان متصل شوند. این مرحله در QueueCraft پیاده‌سازی نشده است تا هیچ اعلان، ticket یا تغییر خارجی بدون انتخاب صریح سازمان ایجاد نشود.

## ۵. Runbook و کنترل انسانی

مانیتورینگ بدون تصمیم روشن، فقط داشبورد است. Error Budget Policy باید تعیین کند در وضعیت warning و critical چه کسی مالک اقدام است، کدام تغییرات موقتاً متوقف می‌شوند، چه شرایطی rollback یا ظرفیت بیشتر را توجیه می‌کند و چه زمانی بودجه دوباره بازبینی می‌شود. برای اجرای تصمیم‌ها باید کنترل تغییر، نگهداری رخداد، و تأیید انسان برقرار باشد. [1]

| سطح | اقدام پیشنهادی | اقدام ممنوع بدون تأیید |
|---|---|---|
| Healthy | پایش روند و مرور دوره‌ای ظرفیت | تغییر خودکار زیرساخت صرفاً از روی پیش‌بینی |
| Warning | بررسی علت، اعتبارسنجی region/route و ایجاد ticket | افزایش هزینه یا ظرفیت بدون مالک عملیاتی |
| Critical | فعال‌سازی Incident Runbook و ارزیابی failover | حذف region، تغییر DNS یا تغییر cloud resource بدون مجوز و کنترل تغییر |

## منابع

[1] [Google SRE Workbook — Implementing SLOs](https://sre.google/workbook/implementing-slos/)

[2] [Google SRE Workbook — Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/)

[3] [Prometheus — Instrumentation](https://prometheus.io/docs/practices/instrumentation/)

[4] [OpenTelemetry — Metrics](https://opentelemetry.io/docs/concepts/signals/metrics/)

# راهنمای Distributed Load Testing در QueueCraft

## محدوده و حالت ایمن

ماژول `distributed_load_testing.py` یک **شبیه‌ساز ظرفیت و مسیر ترافیک** است. این ماژول به‌صورت قطعی، بار درخواست‌شده را بین مولدهای جغرافیایی و مناطق هدف مدل می‌کند. هیچ درخواست HTTP ارسال نمی‌کند، socket باز نمی‌کند، URL یا credential نمی‌گیرد و به هیچ سامانه بیرونی متصل نمی‌شود.

```python
result["safe_mode"]
# {
#   "network_requests_sent": 0,
#   "description": "Local discrete-event capacity simulation only; no traffic is sent to any target."
# }
```

این محدودیت عمدی است. تست بار واقعی باید فقط با مالک صریح سامانه، محدوده هدف تأییدشده، سقف نرخ، kill switch، پنجره نگه‌داری و Runbook جداگانه طراحی شود.

## مدل شبیه‌سازی

| عنصر | نقش |
|---|---|
| `LoadGenerator` | یک مبدأ جغرافیایی مانند Americas، Europe یا Asia با سقف تولید درخواست و وزن توزیع |
| `TargetRegion` | یک منطقه سرویس‌دهنده با ظرفیت هر bucket و latency پایه پردازش |
| `network_latency_ms` | latency مدل‌شده میان هر مولد و هر منطقه هدف |
| `DistributedLoadPolicy` | سیاست `latency_aware` یا `round_robin`، جریمه saturation و آستانه SLO latency |
| `outages_by_bucket` | منطقه‌ای که فقط در همان bucket شبیه‌سازی‌شده ناسالم است؛ هیچ outage واقعی رخ نمی‌دهد |

در هر bucket، تقاضای جهانی ابتدا با وزن مولدها تقسیم می‌شود. اگر مولدها خودشان ظرفیت کافی نداشته باشند، مقدار تولیدنشده در `generator_capacity_limited_requests` ثبت می‌شود. سپس درخواست‌های تولیدشده بر اساس سیاست routing به مناطق سالم می‌روند. ظرفیت تمام‌شده به‌صورت صریح به `unserved_requests` تبدیل می‌شود.

Latency مدل‌شده برای هر مسیر از سه جزء ساخته می‌شود:

```text
route_latency = network_latency + service_latency + saturation_penalty
saturation_penalty = penalty × utilization / max(0.05, 1 − utilization)
```

این فرمول یک تقریب عملیاتی برای نشان‌دادن بدترشدن latency نزدیک اشباع ظرفیت است؛ جایگزین اندازه‌گیری واقعی APM یا load test تأییدشده نیست.

## اجرای نمونه

```python
from distributed_load_testing import (
    DistributedLoadPolicy,
    LoadGenerator,
    TargetRegion,
    simulate_distributed_load,
)

generators = [
    LoadGenerator("americas-client", max_requests_per_bucket=120, routing_weight=2.0),
    LoadGenerator("europe-client", max_requests_per_bucket=100, routing_weight=1.5),
    LoadGenerator("asia-client", max_requests_per_bucket=100, routing_weight=1.0),
]

targets = [
    TargetRegion("americas-region", capacity_per_bucket=100, service_latency_ms=30),
    TargetRegion("europe-region", capacity_per_bucket=90, service_latency_ms=35),
    TargetRegion("asia-region", capacity_per_bucket=80, service_latency_ms=40),
]

latency = {
    "americas-client": {"americas-region": 20, "europe-region": 100, "asia-region": 180},
    "europe-client": {"americas-region": 100, "europe-region": 20, "asia-region": 130},
    "asia-client": {"americas-region": 180, "europe-region": 130, "asia-region": 25},
}

result = simulate_distributed_load(
    global_load_buckets=[180, 220, 280, 330, 300, 250],
    load_generators=generators,
    target_regions=targets,
    network_latency_ms=latency,
    policy=DistributedLoadPolicy(
        routing_mode="latency_aware",
        saturation_penalty_ms=20,
        latency_slo_ms=250,
    ),
    outages_by_bucket={3: {"europe-region"}},
)

print(result["summary"])
```

## خروجی‌های مهم

| خروجی | تفسیر |
|---|---|
| `total_requested_requests` | کل تقاضای مدل‌شده در تمام bucketها |
| `total_generated_requests` | تقاضایی که مولدها با سقف تعریف‌شده توانسته‌اند ایجاد کنند |
| `generator_capacity_limited_requests` | تقاضایی که به‌علت سقف مولدهای شبیه‌سازی‌شده تولید نشده است |
| `total_unserved_requests` | درخواست‌های تولیدشده‌ای که ظرفیت منطقه سالم برایشان کافی نبوده است |
| `served_pct_of_generated` | درصد سرویس‌دهی نسبت به بار تولیدشده، نه نسبت به بار خام درخواست‌شده |
| `global_p95_estimated_latency_ms` | P95 latency مدل‌شده روی مسیرهای سرویس‌داده‌شده |
| `target_utilization` | فشار ظرفیت هر منطقه در هر bucket |
| `route_assignments` | تعداد درخواست مدل‌شده از هر مبدأ به هر مقصد |

## سناریوهای پیشنهادی

| سناریو | هدف تصمیم‌گیری | معیار موفقیت |
|---|---|---|
| پیک محلی در یک قاره | سنجش وابستگی به نزدیک‌ترین region | P95 و `unserved` زیر سقف مورد توافق |
| outage یک region | بررسی ظرفیت مسیر جایگزین | عدم عبور SLO و عدم مصرف شدید Error Budget |
| محدودیت agent / source | تمایز محدودیت مولد از محدودیت سرویس | `generator_capacity_limited` به‌صورت جداگانه گزارش شود |
| افزایش تدریجی تقاضای جهانی | یافتن نقطه اشباع و پارتو هزینه/latency | تغییر ظرفیت پیش از افزایش شدید P95 |
| latency بین‌قاره‌ای بالا | ارزیابی trade-off داده و تجربه کاربر | routing policy و locality مناسب انتخاب شود |

## اتصال به رابط دسکتاپ

در نسخه دسکتاپ، دکمه **Run Global Load Simulation** بار واردشده CSV/XLSX یا یک سری نمونه را به مقیاس جهانی مدل می‌کند، یک outage نمونه صرفاً در همان مدل تعریف می‌کند و نمودار throughput منطقه‌ای، P95 latency و درخواست‌های بدون سرویس را نمایش می‌دهد. متن نتیجه نیز تعداد درخواست‌های شبکه ارسال‌شده را صریحاً برابر صفر نشان می‌دهد.

# راهنمای فنی Cloud Cluster Scaling در QueueCraft

## محدوده و اصل ایمنی

ماژول `cloud_cluster_scaling.py` یک **شبیه‌ساز تصمیم‌یار محلی** است؛ به هیچ حساب ابری متصل نمی‌شود، credential نمی‌خواهد و هیچ VM، Kubernetes cluster، autoscaling group یا منبع بیرونی را ایجاد، حذف یا تغییر نمی‌دهد. هدف آن پاسخ‌دادن به این پرسش عملیاتی است: «اگر بار مورد انتظار به این شکل تغییر کند، با این سیاست نود و هزینه، backlog، بهره‌برداری، نیاز مقیاس‌پذیری و هزینه مدل‌شده چه خواهد بود؟»

> شبیه‌سازی یک برنامه ظرفیت است، نه مجوز اجرای خودکار تغییر زیرساخت. هر اقدام واقعی روی cloud باید با دسترسی مستقل، کنترل تغییر و تأیید مسئول سازمان انجام شود.

## مدل عملیاتی

هر بازه زمانی یک `arrival_bucket` دارد. کلاستر شامل تعدادی نود فعال است و هر نود در هر بازه حداکثر `node_capacity` کار را تکمیل می‌کند. مقدار `target_utilization` برای ایجاد headroom استفاده می‌شود. برای نمونه، ظرفیت ۲۰ کار و utilization هدف ۷۰٪ به این معنی است که سیستم برای حفظ حاشیه ظرفیت، تعداد نود را بر مبنای حدود ۱۴ کار محافظت‌شده در هر نود محاسبه می‌کند.

| پارامتر | نقش در مدل |
|---|---|
| `min_nodes` و `max_nodes` | کران پایین و بالای ظرفیت افقی |
| `node_capacity` | حداکثر کار قابل تکمیل به ازای هر نود در هر bucket |
| `target_utilization` | بهره‌برداری هدف برای پیش‌بینی و پیش‌مقیاس‌دهی |
| `scale_up_step` و `warmup_buckets` | تعداد نود درخواستی و تأخیر فعال‌شدن آن‌ها |
| `scale_down_threshold` و `cooldown_buckets` | محافظت در برابر کوچک‌کردن شتاب‌زده و نوسان ظرفیت |
| `per_node_cost_per_bucket` | هزینه مدل‌شده هر نود در هر بازه |
| `backlog_penalty_per_job` | هزینه یا جریمه مدل‌شده برای کارهای معوق |
| `routing_strategy` | `least_loaded` یا `round_robin` برای توزیع کامل‌شده‌ها |

## منطق توزیع بار و Autoscaling

در هر bucket، ماژول ابتدا نودهایی را که warm-up آن‌ها تمام شده فعال می‌کند. سپس بار جدید و backlog قبلی را ترکیب می‌کند، ظرفیت سرویس‌دهی را بر اساس نودهای فعال محاسبه می‌کند و کارهای تکمیل‌شده را با سیاست توزیع بار بین نودها پخش می‌کند. backlog باقی‌مانده، بهره‌برداری، زمان تأخیر تخمینی و هزینه محاسبه می‌شوند.

پس از آن، تعداد نود مطلوب بر مبنای بار ارائه‌شده و بهره‌برداری هدف محاسبه می‌گردد. اگر افزایش لازم باشد، درخواست scale-up با warm-up ثبت می‌شود. اگر بار کمتر از آستانه پایین‌مقیاس‌دهی باشد، cooldown سپری شده باشد و درخواست افزایش معوقی وجود نداشته باشد، scale-down اعمال می‌شود. `timeline` خروجی، هم تعداد نودهای سرویس‌دهنده در bucket جاری و هم تعداد آماده برای bucket بعدی را نگه می‌دارد تا هیچ تفاوتی میان ظرفیت واقعی و تغییر در صف مخفی نشود.

## نمونه کد کامل

```python
from cloud_cluster_scaling import (
    ClusterPolicy,
    forecast_cluster_scaling,
    simulate_cluster_scaling,
)

history = [8, 11, 13, 19, 22, 24, 20, 18, 21, 27, 31, 34]

policy = ClusterPolicy(
    min_nodes=2,
    max_nodes=12,
    node_capacity=20,
    target_utilization=0.70,
    scale_up_step=2,
    scale_down_step=1,
    warmup_buckets=1,
    cooldown_buckets=1,
    per_node_cost_per_bucket=1.0,
    backlog_penalty_per_job=0.10,
    routing_strategy="least_loaded",
)

# برنامه پیش‌مقیاس‌دهی از روی پیش‌بینی بار QueueCraft
plan = forecast_cluster_scaling(history, policy, horizon=8)
forecast_jobs = [round(item["forecast_arrivals"]) for item in plan["pre_scaling_plan"]]

# شبیه‌سازی محلی اجرای سیاست؛ هیچ cloud provider فراخوانی نمی‌شود.
simulation = simulate_cluster_scaling(forecast_jobs, policy)

print(simulation["summary"])
for bucket in simulation["timeline"]:
    print(bucket["bucket"], bucket["active_nodes"], bucket["backlog"], bucket["action"])
```

## خروجی‌ها و نحوه تفسیر

| خروجی | تفسیر مدیریتی |
|---|---|
| `peak_active_nodes` | حداکثر ظرفیت افقی مورد نیاز در سناریوی شبیه‌سازی‌شده |
| `peak_backlog` | بیشترین کار انباشته؛ شاخص خطر تأخیر یا ریزش تجربه مشتری |
| `estimated_p95_backlog_delay_buckets` | تخمین tail delay backlog بر حسب bucket؛ باید با SLA عملیاتی مقایسه شود |
| `total_node_cost` | هزینه مدل‌شده نگه‌داری نودها در افق تحلیل |
| `total_backlog_penalty` | هزینه مدل‌شده خدمت‌ندادن به‌موقع؛ یک فرض کسب‌وکار قابل تنظیم است |
| `scaling_actions` | تاریخچه درخواست افزایش یا اعمال کاهش ظرفیت برای بازبینی تصمیم |
| `node_assignments` | توزیع کارهای کامل‌شده میان نودهای فعال برای بررسی تعادل routing |

## قابلیت‌های تجاری تکمیلی که پیاده‌سازی شدند

در رابط دسکتاپ، دکمه **Run Cluster Scaling Simulation** اضافه شده است. این دکمه از داده واردشده CSV/XLSX یا تاریخچه نمونه استفاده می‌کند، برنامه پیش‌مقیاس‌دهی را می‌سازد و سپس نمودارهای «بار ورودی و نودهای فعال» و «backlog و تأخیر تخمینی» را نمایش می‌دهد. پیام نتیجه به‌صراحت اعلام می‌کند که این تحلیل منبع ابری ایجاد یا تغییر نمی‌دهد.

## پیشنهادهای نسخه بعدی

| قابلیت | ارزش تجاری | پیش‌نیاز طراحی |
|---|---|---|
| سیاست‌های مقیاس‌پذیری چندناحیه‌ای | تحلیل تاب‌آوری و هزینه منطقه‌ای | مدل latency، ظرفیت و هزینه هر region بدون اتصال مستقیم پیش‌فرض |
| مدل Spot/On-demand | بهینه‌سازی هزینه و ریسک قطع شدن نود | احتمال interruption و fallback مشخص |
| SLO error budget | پیوند backlog با تعهد سرویس | تعریف رسمی SLI، SLO و پنجره اندازه‌گیری توسط مشتری |
| بازپخش ترافیک تاریخی | اعتبارسنجی سیاست روی وقایع گذشته | ناشناس‌سازی و خط‌مشی نگهداری داده |
| کنترل تغییر GitOps | انتقال پیشنهاد به pull request قابل بازبینی | تأیید انسان و عدم اجرای مستقیم زیرساخت |
| اتصال provider با حالت dry-run | مقایسه مدل با داده واقعی provider | OAuth/credential جداگانه و تأیید صریح پیش از هر اقدام |

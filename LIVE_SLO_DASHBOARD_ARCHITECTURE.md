# معماری داشبورد زنده SLO Error Budget در QueueCraft

## محدوده نسخه دسکتاپ

نسخه ۳.۲ یک مانیتورینگ **درون‌فرآیندی و محلی** اضافه می‌کند. منبع داده می‌تواند شبیه‌سازی‌های QueueCraft یا observationهایی باشد که رابط دسکتاپ به API محلی `pywebview` می‌دهد. داده در حافظه فرآیند نگه‌داری می‌شود و هیچ exporter، socket عمومی، cloud credential یا سرویس خارجی به‌صورت پیش‌فرض فعال نیست.

این انتخاب برای نسخه نصبی ویندوز مناسب است: داشبورد با بازبودن برنامه به‌روزرسانی می‌شود، اطلاعات از دستگاه خارج نمی‌شود، و کاربر می‌تواند قبل از اتصال اختیاری به سامانه telemetry سازمان، قرارداد متریک و تصمیم‌های SLO را بررسی کند.

## جریان داده

```text
Local simulation or approved local observation
        ↓
LiveSLOMonitor.ingest(...)
        ↓
SLOMonitor rolling-window calculation
        ↓
Dashboard snapshot + bounded history + Prometheus-text preview
        ↓
pywebview local API
        ↓
Desktop dashboard refresh while the app is open
```

## قرارداد Observation

| فیلد | قاعده |
|---|---|
| `bucket` | عدد صحیح افزایشی یا شناسه بازه محلی |
| `region` | نام کم‌کاردینال منطقه، مانند `europe-region` |
| `total_requests` | تعداد کل رخدادها در بازه |
| `successful_requests` | رخدادهایی که پاسخ معتبر دریافت کرده‌اند |
| `latency_compliant_requests` | رخدادهای زیر آستانه latency SLO |
| `source` | `simulation`، `local-demo` یا `approved-adapter`؛ نه شناسه کاربر یا درخواست |

درخواست خوب برابر حداقل `successful_requests` و `latency_compliant_requests` است. این سیاست مانع آن می‌شود که سرویس موفق اما کند، یا سریع اما ناموفق، SLO را به‌طور نادرست پاس کند.

## کنترل‌های ایمنی و حریم خصوصی

1. تاریخچه در حافظه و با سقف `max_history_points` نگه‌داری می‌شود؛ این نسخه لاگ پایدار یا ارسال خودکار ندارد.
2. region و source باید کوتاه و کم‌کاردینال باشند. شناسه کاربر، شناسه درخواست، مسیر URL خام و payload در observation پذیرفته نمی‌شوند.
3. dashboard فقط وضعیت محلی را نشان می‌دهد؛ ایجاد ticket، page، تغییر cloud یا failover واقعی انجام نمی‌دهد.
4. خروجی Prometheus-text یک preview محلی است تا اتصال تولیدی بعداً با approval سازمان طراحی شود.
5. دکمه demo از مجموعه مقادیر ثابت و برچسب `local-demo` استفاده می‌کند؛ برای عملکرد تولیدی یا داده مشتری ادعایی ایجاد نمی‌کند.

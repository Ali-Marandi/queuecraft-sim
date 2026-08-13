# راهنمای بسته‌بندی نهایی QueueCraft Enterprise AI v3.2 برای Windows x64

## خروجی مورد انتظار

فرآیند نسخه ۳.۲ دو artifact می‌سازد: پوشه قابل‌حمل `dist\QueueCraftEnterpriseAI\` و نصب‌کننده حرفه‌ای `release\QueueCraftEnterpriseAI-v3.2.0-Setup-x64.exe`. خروجی دوم همان فایل نصبی ویندوز است که پوشه برنامه را نصب، میان‌بر اختیاری ایجاد و uninstall entry ثبت می‌کند.

این فرآیند در یک محیط **Windows x64** اجرا می‌شود. ساخت نهایی Windows EXE نباید در Linux انجام شود، زیرا وابستگی‌های باینری و WebView ویندوز باید در محیط هدف resolve و آزمون شوند.

## وابستگی‌های لازم روی ماشین Build

| جزء | کاربرد | روش بررسی |
|---|---|---|
| Windows x64 | محیط ساخت و آزمون artifact نهایی | `systeminfo` یا Settings |
| Python 3.11 یا 3.12 x64 | اجرای ابزار build و PyInstaller | `py --version` |
| Node.js LTS | ساخت دارایی‌های آفلاین رابط | `node --version` و `npm --version` |
| Inno Setup 6 | ساخت Setup x64 با `ISCC.exe` | مسیر پیش‌فرض `C:\Program Files (x86)\Inno Setup 6\ISCC.exe` |
| Windows SDK `signtool.exe` | امضای اختیاری Authenticode | `signtool /?` |
| WebView2 Runtime | موتور رابط `pywebview` روی دستگاه مقصد | بررسی یا نصب در مرحله Setup |

## فرمان ساخت نسخه ۳.۲

در PowerShell x64 و در ریشه repository اجرا کنید:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build_windows.ps1 -Version "3.2.0"
```

اسکریپت `build_windows.ps1` به‌ترتیب این فعالیت‌ها را انجام می‌دهد:

1. وابستگی‌های pinned‌شده در `requirements.txt` را نصب می‌کند.
2. بسته‌های رابط را نصب و CSS/Chart.js آفلاین را می‌سازد.
3. همه تست‌های Node.js و Python را به‌عنوان release gate اجرا می‌کند.
4. با PyInstaller، برنامه windowed و پوشه `dist` را می‌سازد.
5. فایل‌های `index.html`، `queuecraft.js`، دارایی‌ها، زبان‌ها و مثال‌ها را به همراه کتابخانه‌های تحلیلی جمع می‌کند.
6. ماژول‌های نسخه تاب‌آوری یعنی `multi_region_failover`، `distributed_load_testing` و `live_slo_monitoring` را به‌شکل explicit hidden import نگه می‌دارد تا در bundle گم نشوند.
7. EXE برنامه و سپس Setup را در صورت وجود گواهی معتبر امضا می‌کند، و SHA-256 نصب‌کننده را نمایش می‌دهد.

PyInstaller برای importهای پویا ممکن است به `--hidden-import` یا hook نیاز داشته باشد؛ بررسی فایل‌های warning و import graph در پوشه `build` برای تشخیص مشکل bundle توصیه شده است. [1]

## بسته‌بندی وابستگی‌های نسخه ۳.۲

| گروه | اجزای بسته‌شده |
|---|---|
| رابط آفلاین | Tailwind CSS، Chart.js، `index.html` و ترجمه‌های English/Persian |
| تحلیل داده | NumPy، pandas، Matplotlib، openpyxl و xlrd |
| برنامه دسکتاپ | pywebview و Edge Chromium bridge |
| موتورهای کسب‌وکار | صف چندمرحله‌ای، AI–Monte Carlo، پارتو، حساسیت، کلاستر، Failover، ترافیک جهانی و مانیتور زنده SLO |
| داده نمونه | پوشه `examples` |

ماژول Live SLO Dashboard در همان فرآیند برنامه اجرا می‌شود، تاریخچه را در حافظه نگه می‌دارد و به‌صورت پیش‌فرض هیچ telemetry خارجی ارسال نمی‌کند؛ بنابراین برای آن dependency شبکه یا service جداگانه‌ای در installer وجود ندارد.

## WebView2 Runtime

برنامه‌های production مبتنی بر WebView2 به WebView2 Runtime روی دستگاه مقصد نیاز دارند. Microsoft برای محیط‌های آنلاین Bootstrapper و برای محیط‌های کاملاً آفلاین Standalone Installer را مستند کرده است. [3]

### حالت معمول آنلاین

در اکثر دستگاه‌ها Runtime موجود است. اگر نصب‌کننده باید در صورت نبود Runtime آن را تهیه کند، Bootstrapper رسمی را از Microsoft دریافت و در یک workflow تأییدشده اضافه کنید. این مسیر اینترنت لازم دارد.

### حالت کاملاً آفلاین

برای محیط air-gapped، Standalone Installer رسمی x64 را از Microsoft دریافت، hash آن را مستقل بررسی و سپس در مسیر زیر قرار دهید:

```text
third_party\MicrosoftEdgeWebView2RuntimeInstallerX64.exe
```

سپس دو خط کامنت‌شده در `installer\QueueCraftEnterpriseAI.iss` را فقط پس از بررسی مجوز، hash و سیاست IT سازمان فعال کنید. دستور silent پیشنهادی Microsoft برای installer مستقل چنین است:

```text
MicrosoftEdgeWebView2RuntimeInstallerX64.exe /silent /install
```

اگر Runtime به‌صورت per-machine نصب شود ممکن است Setup به سطح دسترسی بالاتر نیاز داشته باشد. نصب‌کننده فعلی با `PrivilegesRequired=lowest` طراحی شده است؛ برای استقرار per-machine باید تیم IT تغییر privilege و سیاست نصب را بازبینی کند. [3]

## امضای کد

به‌منظور امضای EXE برنامه و Setup، این متغیرها را فقط در secret store یا محیط امن CI تنظیم کنید:

```powershell
$env:SIGN_CERTIFICATE_PATH = "C:\secure\queuecraft-signing.pfx"
$env:SIGN_CERTIFICATE_PASSWORD = "<secret>"
.\build_windows.ps1 -Version "3.2.0"
```

گواهی، رمز گواهی، token یا کلید خصوصی نباید در repository، اسکریپت یا فایل release قرار گیرد. اگر متغیرها تنظیم نشوند، ساخت ادامه دارد اما اسکریپت به‌صراحت اعلام می‌کند که امضا انجام نشده است.

## ساخت بدون Setup برای اشکال‌زدایی

```powershell
.\build_windows.ps1 -Version "3.2.0" -SkipInstaller
```

برای بررسی خطای اجرای GUI، build آزمایشی را موقتاً بدون `--windowed` بسازید تا پیام خطا در ترمینال نمایش داده شود؛ این روش در راهنمای PyInstaller توصیه شده است. [1]

## اعتبارسنجی پیش از انتشار

| آزمون | معیار قبولی |
|---|---|
| Release gate | همه تست‌های Node.js و Python عبور کنند |
| Bundle audit | `dist\QueueCraftEnterpriseAI\QueueCraftEnterpriseAI.exe` موجود باشد |
| Installer audit | Setup v3.2.0 ساخته شده و SHA-256 ثبت شده باشد |
| Clean VM smoke test | نصب، راه‌اندازی، Import CSV/XLSX، SLO Dashboard و خروجی CSV بدون Python/Node نصب‌شده کار کند |
| WebView2 check | رابط برنامه روی دستگاه تمیز بدون خطای runtime باز شود |
| Security check | فایل امضاشده در صورت وجود گواهی، وضعیت معتبر نشان دهد؛ secrets در artifact نباشند |
| Uninstall check | حذف برنامه و میان‌برها مطابق سیاست سازمان کار کند |

`ISCC.exe` برای ساخت script نصب‌کننده از خط فرمان استفاده می‌شود و exit code صفر نشان‌دهنده موفقیت است؛ build script نسخه برنامه را با `MyAppVersion` به Inno Setup منتقل می‌کند. [2]

## انتشار از CI

فایل `.github/workflows/build-windows.yml` test suite کامل v3.2 را روی Windows اجرا می‌کند و سپس اسکریپت build را فرا می‌خواند. پیش از انتشار عمومی، CI باید روی tag نسخه اجرا شود، artifact بررسی شود و انتشار/آپلود asset تنها پس از تأیید مشخص انجام گیرد.

## منابع

[1] [PyInstaller — When Things Go Wrong](https://pyinstaller.org/en/stable/when-things-go-wrong.html)

[2] [Inno Setup Help — Compiler Command-Line Parameters](https://jrsoftware.org/ishelp/topic_compilercmdline.htm)

[3] [Microsoft Learn — Distribute your app and the WebView2 Runtime](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution)

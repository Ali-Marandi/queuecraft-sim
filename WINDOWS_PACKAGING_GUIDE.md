# راهنمای نهایی بسته‌بندی QueueCraft Enterprise AI v3.0 برای ویندوز

## هدف و خروجی نهایی

هدف این فرآیند تولید یک نصب‌کننده **۶۴بیتی ویندوز** با نامی مشابه `QueueCraftEnterpriseAI-v3.0.0-Setup-x64.exe` است. پس از نصب، کاربر نهایی به نصب Python، NumPy، PyWebView، Node.js یا کتابخانه‌های رابط کاربری نیاز ندارد. اسکریپت `build_windows.ps1` ابتدا همه وابستگی‌های پایتون را در بسته برنامه جمع‌آوری می‌کند، سپس CSS و Chart.js را به دارایی‌های محلی تبدیل می‌کند و در پایان با Inno Setup یک نصب‌کننده واحد می‌سازد.

> **چرا بستهٔ پوشه‌ای (onedir) و نصب‌کننده انتخاب شده است؟** PyInstaller هم حالت تک‌فایل (`--onefile`) و هم حالت پوشه‌ای (`--onedir`) را پشتیبانی می‌کند؛ حالت پوشه‌ای پیش‌فرض آن است. در این پروژه، `onedir + installer` ترجیح داده شده است، زیرا دارایی‌های HTML/JS/CSS، کتابخانه‌های بومی NumPy و اجزای PyWebView را بدون استخراج موقت در هر اجرا مدیریت می‌کند، در حالی که Inno Setup کل پوشه را در یک Setup EXE قابل دانلود فشرده می‌سازد. [1]

| رویکرد | نتیجه برای کاربر | مزیت اصلی | ملاحظه |
|---|---|---|---|
| **پیشنهادی: بستهٔ پوشه‌ای + Setup** | یک فایل نصب‌کننده و میان‌بر منوی Start | اجرای سریع‌تر، ارتقای قابل‌کنترل و مدیریت کامل فایل‌ها | به Inno Setup در زمان ساخت نیاز دارد |
| **فایل اجرایی تک‌فایل** | یک EXE قابل حمل | مناسب دمو و اجرا از فلش | در هر اجرا فایل‌های وابسته را استخراج می‌کند؛ برای محصول دسکتاپ سنگین معمولاً مناسب‌تر نیست [2] |
| **ساخت خودکار از تگ انتشار** | پس از هر تگ نسخه یک Setup EXE تولید می‌شود | تکرارپذیری و کاهش خطای دستی | نیازمند مخزن گیت‌هاب و تنظیم کلید امضای کد در صورت استفاده است |

## محتوای بسته

| لایه | نحوهٔ بسته‌بندی |
|---|---|
| موتور AI–Monte Carlo | فایل‌های `ai_monte_carlo.py` و `ai_forecaster.py` به‌همراه Python runtime از طریق PyInstaller |
| کتابخانه‌های پایتون | `numpy` و `pywebview` طبق `requirements.txt`؛ گزینهٔ `--collect-all` داده‌ها و باینری‌های وابسته را نیز جمع می‌کند |
| رابط کاربری | `index.html`، `queuecraft.js` و پوشهٔ `assets` با `--add-data` در bundle قرار می‌گیرند |
| نمودار و CSS | در زمان ساخت، Tailwind به `assets/vendor/tailwind.css` کامپایل و `chart.umd.js` به صورت محلی کپی می‌شود؛ برنامه در زمان اجرا به CDN نیاز ندارد |
| نصب و حذف | اسکریپت `installer/QueueCraftEnterpriseAI.iss` برنامه، میان‌برها و حذف‌کننده را ایجاد می‌کند |

PyInstaller گزینهٔ `--add-data` را برای افزودن فایل‌ها و پوشه‌های غیرپایتونی ارائه می‌دهد و `--collect-all` نیز زیرماژول‌ها، داده‌ها و باینری‌های یک پکیج را جمع می‌کند. [1] PyWebView نیز برای Windows و Linux، استفاده از PyInstaller و افزودن محتوای HTML به bundle را توصیه می‌کند. [3]

## پیش‌نیازهای سیستم ساخت

این مراحل باید روی **Windows 10/11 64-bit** یا یک عامل ساخت ویندوزی اجرا شوند؛ خروجی ویندوز را در همان محیط ویندوز بسازید. سیستم ساخت به موارد زیر نیاز دارد:

```powershell
# بررسی ابزارهای پایه
py --version
node --version
npm --version
iscc /?
```

Python 3.12، Node.js LTS، و Inno Setup 6 را نصب کنید. سپس در ریشه پروژه اجرا کنید:

```powershell
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
npm install
npm run build:assets
```

مرحلهٔ `build:assets` فایل‌های محلی زیر را تولید می‌کند:

```text
assets/vendor/tailwind.css
assets/vendor/chart.umd.js
```

## ساخت نصب‌کننده با یک دستور

پس از آماده‌سازی پیش‌نیازها، در PowerShell و از ریشه مخزن دستور زیر را اجرا کنید:

```powershell
.\build_windows.ps1 -Version "3.0.0"
```

اسکریپت به ترتیب وابستگی‌ها را نصب می‌کند، دارایی‌های آفلاین را می‌سازد، آزمون‌ها را جداگانه قابل اجرا نگه می‌دارد، خروجی PyInstaller را در `dist\QueueCraftEnterpriseAI\` ایجاد می‌کند و Inno Setup را برای ساخت Setup اجرا می‌نماید. خروجی نهایی در مسیر زیر ایجاد می‌شود:

```text
release\QueueCraftEnterpriseAI-v3.0.0-Setup-x64.exe
```

برای دریافت صرفاً پوشه قابل اجرا و صرف‌نظر از Setup از این دستور استفاده کنید:

```powershell
.\build_windows.ps1 -Version "3.0.0" -SkipInstaller
```

در این حالت پوشهٔ `dist\QueueCraftEnterpriseAI\` را به‌صورت کامل توزیع کنید؛ اجرای تنها فایل EXE از داخل آن پوشه کافی نیست، زیرا DLLها و دارایی‌های بسته نیز باید کنار آن باشند.

## نکتهٔ WebView2 برای اجرای کاملاً آفلاین

PyWebView در ویندوز از موتور وب سیستم استفاده می‌کند. برای پوشش دستگاه‌های سازمانی فاقد WebView2، **WebView2 Evergreen Runtime x64** را صرفاً از منبع رسمی مایکروسافت و مطابق مجوز آن دریافت کنید و در مسیر زیر قرار دهید:

```text
third_party\MicrosoftEdgeWebView2RuntimeInstallerX64.exe
```

سپس دو خط کامنت‌شده در بخش‌های `[Files]` و `[Run]` فایل `installer/QueueCraftEnterpriseAI.iss` را فعال کنید و دوباره build را اجرا کنید. به این ترتیب runtime نیز در Setup قرار می‌گیرد و نصب‌کننده می‌تواند آن را به‌صورت silent نصب کند. WebView2 را از منبع نامعتبر یا با توکن، رمز یا دادهٔ حساس درون مخزن دریافت یا نگهداری نکنید.

## امضای کد و انتشار امن

برای یک محصول تجاری، امضای Authenticode برای کاهش هشدارهای Windows SmartScreen و اثبات منشأ فایل بسیار توصیه می‌شود. گواهی PFX یا گذرواژه آن را هرگز در کد، اسکریپت یا مخزن قرار ندهید. در محیط ساخت امن، متغیرهای زیر را تنها به‌صورت secret تنظیم کنید:

```powershell
$env:SIGN_CERTIFICATE_PATH = "C:\secure\queuecraft-signing.pfx"
$env:SIGN_CERTIFICATE_PASSWORD = "<secure secret>"
.\build_windows.ps1 -Version "3.0.0"
```

اسکریپت در صورت وجود هر دو متغیر، `signtool.exe` را با SHA-256 و سرویس timestamp فراخوانی می‌کند؛ در غیر این صورت مرحله امضا را شفافاً رد می‌کند. پیش از انتشار عمومی، هش SHA-256 فایل Setup را تولید و در یادداشت انتشار درج کنید:

```powershell
Get-FileHash .\release\QueueCraftEnterpriseAI-v3.0.0-Setup-x64.exe -Algorithm SHA256
```

## ساخت خودکار در انتشار

فایل `.github/workflows/build-windows.yml` یک عامل ویندوزی را برای نصب پیش‌نیازها، اجرای تست‌های AI–Monte Carlo، ساخت دارایی‌های آفلاین، تولید Setup و بارگذاری آن در Release پیکربندی می‌کند. انتشار با تگ نسخه انجام می‌شود:

```powershell
git tag v3.0.0
git push origin v3.0.0
```

برای امضای خودکار، محل گواهی و رمز را در secretهای محافظت‌شده محیط ساخت ذخیره کنید؛ هرگز آن‌ها را در YAML قرار ندهید. Inno Setup با بخش `[Files]` برای تعریف فایل‌های نصب‌شونده و مقصد آن‌ها طراحی شده است. [4]

## آزمون پذیرش پیش از انتشار

در یک ماشین ویندوزی تمیز یا Windows Sandbox، آزمون زیر را انجام دهید:

| آزمون | معیار پذیرش |
|---|---|
| نصب | Setup بدون نیاز به Python یا Node.js کامل شود |
| شروع برنامه | پنجره QueueCraft باز و داشبورد نمایش داده شود |
| تحلیل AI–Monte Carlo | دکمهٔ تحلیل، پیش‌بینی تقاضا و معیارهای ریسک را بازگرداند |
| Auto-Scaling | بهینه‌سازی یک پیشنهاد تعداد سرور و وضعیت SLA تولید کند |
| آفلاین | با قطع شبکه، CSS و نمودارها همچنان بارگذاری شوند |
| حذف نصب | برنامه و میان‌برها حذف شوند؛ داده‌های کاربر تنها در صورت انتخاب کاربر حذف شوند |

## منابع

[1] [PyInstaller — Using PyInstaller](https://pyinstaller.org/en/stable/usage.html)

[2] [PyInstaller — Using Spec Files and bundle modes](https://pyinstaller.org/en/stable/spec-files.html)

[3] [PyWebView — Freezing applications](https://pywebview.flowrl.com/guide/freezing.html)

[4] [Inno Setup Help — Files section](https://jrsoftware.org/ishelp/topic_filessection.htm)

# راهنمای بسته‌بندی نهایی QueueCraft Enterprise AI v3.1 برای ویندوز

## خروجی مورد انتظار

فرآیند v3.1 یک نصب‌کننده ۶۴بیتی با نام زیر تولید می‌کند:

```text
release\QueueCraftEnterpriseAI-v3.1.0-Setup-x64.exe
```

نصب‌کننده، پوشه اجرایی PyInstaller و همه وابستگی‌های کاربردی نسخه ۳.۱ را در خود قرار می‌دهد. پس از نصب، کاربر نهایی به Python، Node.js، pandas، NumPy، Matplotlib یا ابزارهای ساخت رابط کاربری نیاز ندارد. انتخاب معماری `onedir + Inno Setup` برای این محصول مناسب است، زیرا برنامه علاوه بر فایل اجرایی، دارایی‌های رابط، کتابخانه‌های بومی داده و فایل‌های زبان را به‌صورت قابل کنترل کنار خود نگه می‌دارد؛ Setup کل پوشه را به یک فایل نصب‌کننده واحد تبدیل می‌کند. [1] [2]

| گزینه توزیع | کاربرد | خروجی |
|---|---|---|
| **پیشنهادی: نصب‌کننده Setup** | انتشار سازمانی، ارتقا و حذف نصب کنترل‌شده | یک فایل `Setup-x64.exe` |
| پوشه اجرایی قابل حمل | آزمایش داخلی یا محیط‌های محدود | کل پوشه `dist\QueueCraftEnterpriseAI` |
| ساخت خودکار در انتشار | فرآیند تکرارپذیر بر پایه تگ Git | Setup و artifact در Release |

## اجزای بسته v3.1

| گروه | مواردی که بسته می‌شوند |
|---|---|
| هسته تحلیل | `ai_monte_carlo.py`، `decision_analytics.py`، `data_import.py`، `scenario_manager.py` و `cloud_cluster_scaling.py` |
| کتابخانه‌های پایتون | `numpy`، `matplotlib`، `pandas`، `openpyxl`، `xlrd` و `pywebview` |
| رابط محلی | `index.html`، `queuecraft.js`، `assets/`، `locales/` و `examples/` |
| زیرساخت بسته | Python runtime، باینری‌ها و data files که PyInstaller با `--collect-all` و `--add-data` جمع می‌کند |
| نصب‌کننده | تعریف Inno Setup، میان‌بر Start Menu و Desktop اختیاری، حذف‌کننده و checksum SHA-256 |

PyInstaller برای افزودن فایل‌های داده، `--add-data` و برای گردآوری زیرماژول‌ها، داده و باینری یک پکیج، `--collect-all` را فراهم می‌کند. [1] PyWebView نیز برای ویندوز، بسته‌بندی با PyInstaller و درج فایل HTML در bundle را توصیه می‌کند. [3]

## پیش‌نیازهای ماشین ساخت

ساخت EXE ویندوز باید روی **Windows 10 یا 11 x64** یا عامل ساخت ویندوزی اجرا شود. PyInstaller خروجی را برای سیستم‌عاملِ ساخت تولید می‌کند؛ بنابراین محیط Linux فعلی جایگزین ساخت نهایی Windows نیست. [1]

نرم‌افزارهای زیر را روی ماشین ساخت نصب کنید:

```powershell
py --version
node --version
npm --version
iscc /?
signtool /?
```

| ابزار | کاربرد |
|---|---|
| Python 3.12 x64 | نصب وابستگی‌ها و اجرای PyInstaller |
| Node.js LTS | تولید Tailwind محلی و کپی Chart.js برای اجرای آفلاین |
| Inno Setup 6 | ساخت Setup x64 |
| Windows SDK SignTool، در صورت امضا | امضای Authenticode اپلیکیشن و Setup |

## ساخت با یک دستور

در PowerShell و از ریشه مخزن اجرا کنید:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build_windows.ps1 -Version "3.1.0"
```

اسکریپت به ترتیب زیر عمل می‌کند:

1. وابستگی‌های `requirements.txt` را نصب می‌کند.
2. وابستگی‌های رابط را نصب و CSS و Chart.js محلی را تولید می‌کند.
3. تست‌های Node.js و Python را به‌عنوان دروازه انتشار اجرا می‌کند.
4. خروجی‌های قبلی را پاک و bundle مستقل PyInstaller را می‌سازد.
5. EXE برنامه را در صورت وجود گواهی امن امضا می‌کند.
6. Setup را با Inno Setup می‌سازد، آن را امضا می‌کند و هش SHA-256 را چاپ می‌نماید.

برای تولید صرفاً bundle قابل حمل و حذف مرحله Setup:

```powershell
.\build_windows.ps1 -Version "3.1.0" -SkipInstaller
```

برای عبور موقت از تست‌ها تنها در محیط عیب‌یابی، و نه انتشار، می‌توان از `-SkipTests` استفاده کرد. خروجی بدون عبور از تست‌ها نباید به عنوان Release تجاری منتشر شود.

## WebView2 و نصب کاملاً آفلاین

PyWebView روی ویندوز به موتور وب سیستم نیاز دارد. بسیاری از دستگاه‌های مدرن Windows آن را دارند، اما برای محیط‌های سازمانی air-gapped باید **Microsoft Edge WebView2 Evergreen Runtime x64** را فقط از منبع رسمی مایکروسافت و مطابق مجوز آن دریافت کنید. فایل آن را در مسیر زیر قرار دهید:

```text
third_party\MicrosoftEdgeWebView2RuntimeInstallerX64.exe
```

سپس دو خط کامنت‌شده در بخش‌های `[Files]` و `[Run]` فایل `installer\QueueCraftEnterpriseAI.iss` را فعال کنید. پس از آن Setup، runtime را نیز درون خود حمل می‌کند و به‌صورت silent نصب می‌نماید. فایل runtime، گواهی امضا یا کلیدهای سازمانی را در مخزن Git قرار ندهید.

## امضای کد

امضای Authenticode برای انتشار تجاری توصیه می‌شود. گواهی PFX و گذرواژه آن باید فقط در secretهای محافظت‌شده یا محیط ساخت امن قرار گیرند:

```powershell
$env:SIGN_CERTIFICATE_PATH = "C:\secure\queuecraft-signing.pfx"
$env:SIGN_CERTIFICATE_PASSWORD = "<secure secret>"
.\build_windows.ps1 -Version "3.1.0"
```

اسکریپت در صورت وجود هر دو متغیر، هم `QueueCraftEnterpriseAI.exe` و هم Setup را با SHA-256 و timestamp امضا می‌کند. در غیر این صورت، مرحله امضا را شفافاً رد می‌کند؛ این وضعیت برای آزمایش داخلی قابل قبول است، اما برای انتشار عمومی باید به‌عنوان ریسک انتشار ثبت شود.

## آزمون پذیرش در ماشین تمیز

پیش از انتشار، Setup را در Windows Sandbox یا یک ماشین مجازی تمیز آزمایش کنید.

| آزمون | معیار پذیرش |
|---|---|
| نصب | بدون Python یا Node.js کامل شود |
| شروع برنامه | پنجره QueueCraft باز و رابط بدون CDN بارگذاری شود |
| ورود داده | CSV و XLSX نمونه گزارش کیفیت و سری زمانی تولید کنند |
| AI و تصمیم | AI–Monte Carlo، پارتو، حساسیت و مقیاس‌پذیری کلاستر پاسخ دهند |
| کلاستر ابری | فقط شبیه‌سازی محلی انجام شود و هیچ حساب یا منبع ابری تغییر نکند |
| حذف نصب | برنامه و میان‌برها حذف شوند |
| اصالت | SHA-256 و وضعیت امضای فایل پیش از انتشار بررسی شوند |

برای محاسبه مستقل checksum:

```powershell
Get-FileHash .\release\QueueCraftEnterpriseAI-v3.1.0-Setup-x64.exe -Algorithm SHA256
```

## ساخت خودکار در GitHub Actions

Workflow موجود در `.github/workflows/build-windows.yml` روی عامل `windows-latest`، وابستگی‌ها را نصب، کل مجموعه تست را اجرا و Setup را ایجاد می‌کند. برای انتشار از یک تگ نسخه استفاده کنید:

```powershell
git tag v3.1.0
git push origin v3.1.0
```

کلیدهای امضا را فقط در secretهای محافظت‌شده مخزن تعریف کنید. انتشار یک Release عمومی یا بارگذاری asset، اقدامی قابل بازگشت نیست و باید در زمان انتشار با تأیید مشخص انجام شود.

## منابع

[1] [PyInstaller — Using PyInstaller](https://pyinstaller.org/en/stable/usage.html)

[2] [PyInstaller — Using Spec Files](https://pyinstaller.org/en/stable/spec-files.html)

[3] [PyWebView — Freezing applications](https://pywebview.flowrl.com/guide/freezing.html)

[4] [Inno Setup Help — Files section](https://jrsoftware.org/ishelp/topic_filessection.htm)

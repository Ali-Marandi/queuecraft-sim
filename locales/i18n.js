export const translations = {
  en: {
    productSubtitle: "AI-Powered Load Forecasting, Multi-Tier Queuing & Digital Twin Simulation",
    forecast: "Run AI–Monte Carlo Analysis",
    retailPreset: "Preset: Retail",
    hospitalPreset: "Preset: Hospital",
    saveScenario: "Save Scenario",
    importData: "Import CSV/XLSX",
    runSimulation: "Run Simulation",
    architecture: "Architecture Mode",
    standard: "Standard",
    multiTier: "Multi-Tier",
    jobCount: "Number of Customers / Jobs",
    arrivalRate: "Arrival Rate (λ - per unit time)",
    serviceRate: "Service Rate (μ - per server)",
    serverCount: "Number of Servers",
    enterpriseTools: "Enterprise AI & Reports",
    capacityOptimization: "Run Capacity Optimization",
    paretoAnalysis: "Run Pareto Trade-off Analysis",
    sensitivityAnalysis: "Run Sensitivity Analysis",
    clusterScaling: "Run Cluster Scaling Simulation",
    multiRegionFailover: "Run Multi-Region Failover Simulation",
    distributedLoadTest: "Run Global Load Simulation",
    liveSloDashboard: "Open Live SLO Dashboard",
    exportCsv: "Export Results to CSV",
    averageWait: "Average Wait Time",
    maximumWait: "Maximum Wait Time",
    totalMakespan: "Total Makespan",
    aiConfidence: "AI Forecast Confidence",
    waitDistribution: "Wait Time Distribution per Job",
    utilization: "Server Utilization & Scenario Comparison",
    dismiss: "Dismiss",
    units: "units",
    riskReady: "Risk model ready",
    slaOptimized: "SLA optimized",
    slaRisk: "SLA risk",
  },
  fa: {
    productSubtitle: "پیش‌بینی بار با هوش مصنوعی، صف چندمرحله‌ای و شبیه‌ساز Digital Twin",
    forecast: "اجرای تحلیل AI–Monte Carlo",
    retailPreset: "سناریو: فروشگاه",
    hospitalPreset: "سناریو: بیمارستان",
    saveScenario: "ذخیره سناریو",
    importData: "ورود CSV/XLSX",
    runSimulation: "اجرای شبیه‌سازی",
    architecture: "نوع معماری",
    standard: "استاندارد",
    multiTier: "چندمرحله‌ای",
    jobCount: "تعداد مشتری / کار",
    arrivalRate: "نرخ ورود (λ در هر واحد زمان)",
    serviceRate: "نرخ خدمت (μ برای هر سرور)",
    serverCount: "تعداد سرورها",
    enterpriseTools: "هوش مصنوعی و گزارش‌های سازمانی",
    capacityOptimization: "بهینه‌سازی ظرفیت",
    paretoAnalysis: "تحلیل مبادله پارتو",
    sensitivityAnalysis: "تحلیل حساسیت",
    clusterScaling: "شبیه‌سازی مقیاس‌پذیری کلاستر",
    multiRegionFailover: "شبیه‌سازی Failover چندناحیه‌ای",
    distributedLoadTest: "شبیه‌سازی تست بار جهانی",
    liveSloDashboard: "داشبورد زنده محلی SLO",
    exportCsv: "خروجی CSV نتایج",
    averageWait: "میانگین زمان انتظار",
    maximumWait: "بیشترین زمان انتظار",
    totalMakespan: "زمان تکمیل کل",
    aiConfidence: "وضعیت تحلیل هوش مصنوعی",
    waitDistribution: "توزیع زمان انتظار هر کار",
    utilization: "بهره‌برداری سرورها و مقایسه سناریو",
    dismiss: "بستن",
    units: "واحد",
    riskReady: "مدل ریسک آماده است",
    slaOptimized: "SLA بهینه شد",
    slaRisk: "ریسک SLA",
  },
};

export function normalizeLanguage(language) {
  return language === "fa" ? "fa" : "en";
}

export function t(key, language = "en") {
  const locale = translations[normalizeLanguage(language)];
  return locale[key] ?? translations.en[key] ?? key;
}

export function applyLanguage(language) {
  const locale = normalizeLanguage(language);
  document.documentElement.lang = locale;
  document.documentElement.dir = locale === "fa" ? "rtl" : "ltr";
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n, locale);
  });
  document.querySelectorAll("[data-i18n-title]").forEach((element) => {
    element.title = t(element.dataset.i18nTitle, locale);
  });
  const toggle = document.getElementById("languageToggle");
  if (toggle) toggle.textContent = locale === "en" ? "FA" : "EN";
  localStorage.setItem("queuecraft-language", locale);
  return locale;
}

export function getSavedLanguage() {
  return normalizeLanguage(localStorage.getItem("queuecraft-language") || "en");
}

const UAIR_TRANSLATIONS = {
  uk: {
    "nav.about": "Про проект",
    "nav.map": "Карта",
    "common.filters": "Фільтри",
    "common.updateLog": "Журнал оновлень",
    "filters.mapLevel": "Рівень карти",
    "filters.regions": "Області",
    "filters.districts": "Райони",
    "filters.showLabels": "Показувати назви областей",
    "filters.startDate": "Дата початку",
    "filters.endDate": "Дата завершення",
    "filters.period": "Період",
    "filters.sevenDays": "7 днів",
    "filters.fourteenDays": "14 днів",
    "filters.thirtyDays": "30 днів",
    "filters.mode": "Метрика",
    "filters.combined": "Комбіновано",
    "filters.count": "Кількість",
    "filters.duration": "Тривалість",
    "updates.title": "Оновлення",
    "details.selectRegion": "Оберіть регіон",
    "details.close": "Закрити деталі",
    "details.alerts": "Тривоги",
    "details.totalDuration": "Загальна тривалість",
    "details.averageDuration": "Середня тривалість",
    "chart.date": "Дата",
    "chart.alerts": "Тривоги",
    "chart.hours": "Години",
    "metric.alerts": "Тривоги",
    "metric.hours": "Години",
    "metric.coefficient": "Коефіцієнт",
    "tooltip.districtPrefix": "Район",
    "tooltip.noData": "Немає даних за цей період",
    "status.noData": "немає даних",
    "status.error": "помилка",
    "theme.light": "Увімкнути світлу тему",
    "theme.dark": "Увімкнути темну тему",
    "language.toggle": "Switch to English",
    "about.title": "Про проект",
    "about.pageTitle": "Про проект - UAir-raid-analytics",
    "about.back": "← Назад до мапи",
    "about.purposeTitle": "Що показує сайт",
    "about.purposeText": "UAir-raid-analytics показує історичну статистику повітряних тривог в Україні на інтерактивній карті. За допомогою сайту можна порівняти області або райони між собою: де тривоги оголошували частіше, де вони тривали довше, і як змінюється картина залежно від вибраного періоду.",
    "about.levelsTitle": "Режими карти",
    "about.regionsText": "У режимі областей кожна область має свій колір відповідно до вибраної метрики. Цей режим використовує основний історичний датасет, тому підходить для аналізу довших періодів.",
    "about.districtsText": "У режимі районів карта показує межі районів. Дані для районів беруться з локального кешу alerts.in.ua, який оновлюється окремим фоновим воркером. Через обмеження джерела районна статистика доступна тільки за останній місяць.",
    "about.clickText": "Якщо натиснути на район, відкриється детальна статистика відповідної області. Районний режим потрібен для більш детальної візуалізації на карті, а детальний графік поки залишається обласним.",
    "about.metricsTitle": "Що означають метрики",
    "about.countText": "Кількість показує, скільки разів за вибраний період починались окремі періоди тривоги. Якщо тривога триває без перерви, вона рахується як один період, навіть якщо всередині області змінювались окремі райони.",
    "about.durationText": "Тривалість показує сумарний час тривог за вибраний період. Значення відображається в годинах і допомагає побачити не тільки частоту тривог, а й те, наскільки довго вони тривали.",
    "about.combinedText": "Комбіновано поєднує кількість тривог і їхню тривалість в один індекс від 0 до 1. Цей режим зручний для швидкого порівняння регіонів на карті, коли важливі обидва фактори.",
    "about.filtersTitle": "Як працюють фільтри",
    "about.filtersText": "Фільтри керують тим, які дані потрапляють на карту. Можна вибрати рівень карти, метрику, готовий період на кшталт 7 або 30 днів, або вручну задати початкову й кінцеву дату.",
    "about.raionDateText": "Для районного режиму доступний лише останній місяць. Це пов'язано з тим, що alerts.in.ua надає історію районних тривог саме за такий проміжок, а сайт не звертається до зовнішнього API під час відкриття сторінки.",
    "about.noDataText": "Якщо для району немає кешованих даних за вибраний період, район позначається сірим. При наведенні на нього з'явиться підказка, що даних за цей період немає.",
    "about.sourcesTitle": "Звідки беруться дані",
    "about.oblastSourceText": "Статистика по областях оновлюється з Vadimkin Ukrainian Air Raid Sirens Dataset. Після оновлення датасету бекенд агрегує події в обласні підсумки для вибраного періоду.",
    "about.raionSourceText": "Статистика по районах кешується локально з alerts.in.ua фоновим воркером. Користувацькі запити читають тільки локальну базу даних, тому frontend не викликає alerts.in.ua напряму і не передає API-токен у браузер.",
  },
  en: {
    "nav.about": "About",
    "nav.map": "Map",
    "common.filters": "Filters",
    "common.updateLog": "Update journal",
    "filters.mapLevel": "Map level",
    "filters.regions": "Regions",
    "filters.districts": "Districts",
    "filters.showLabels": "Show oblast names",
    "filters.startDate": "Start date",
    "filters.endDate": "End date",
    "filters.period": "Period",
    "filters.sevenDays": "7 days",
    "filters.fourteenDays": "14 days",
    "filters.thirtyDays": "30 days",
    "filters.mode": "Metric",
    "filters.combined": "Combined",
    "filters.count": "Count",
    "filters.duration": "Duration",
    "updates.title": "Updates",
    "details.selectRegion": "Select a region",
    "details.close": "Close details",
    "details.alerts": "Alerts",
    "details.totalDuration": "Total duration",
    "details.averageDuration": "Average duration",
    "chart.date": "Date",
    "chart.alerts": "Alerts",
    "chart.hours": "Hours",
    "metric.alerts": "Alerts",
    "metric.hours": "Hours",
    "metric.coefficient": "Coefficient",
    "tooltip.districtPrefix": "District",
    "tooltip.noData": "No data for this period",
    "status.noData": "no data",
    "status.error": "error",
    "theme.light": "Switch to light theme",
    "theme.dark": "Switch to dark theme",
    "language.toggle": "Перемкнути українською",
    "about.title": "About",
    "about.pageTitle": "About - UAir-raid-analytics",
    "about.back": "← Back to map",
    "about.purposeTitle": "What this site shows",
    "about.purposeText": "UAir-raid-analytics shows historical air raid alert statistics for Ukraine on an interactive map. You can compare oblasts or raions and see where alerts were announced more often, where they lasted longer, and how the picture changes for the selected time period.",
    "about.levelsTitle": "Map modes",
    "about.regionsText": "In oblast mode, each oblast is colored according to the selected metric. This mode uses the main historical dataset, so it is suitable for analyzing longer date ranges.",
    "about.districtsText": "In raion mode, the map shows district boundaries. Raion data comes from a local alerts.in.ua cache that is updated by a separate background worker. Because of the source limitations, raion statistics are available only for the last month.",
    "about.clickText": "When you click a raion, the app opens the detail view for its oblast. Raion mode is used for a more detailed map visualization, while the detailed chart is still calculated at oblast level.",
    "about.metricsTitle": "What the metrics mean",
    "about.countText": "Count shows how many separate alert periods started during the selected range. If an alert continues without a break, it is counted as one period, even if individual raions inside the oblast changed during that time.",
    "about.durationText": "Duration shows the total time spent under alert during the selected range. It is displayed in hours and helps compare not only how often alerts happened, but also how long they lasted.",
    "about.combinedText": "Combined merges alert count and alert duration into one index from 0 to 1. This mode is useful for quickly comparing regions on the map when both frequency and duration matter.",
    "about.filtersTitle": "How filters work",
    "about.filtersText": "Filters define which data is shown on the map. You can choose the map level, metric, a preset period such as 7 or 30 days, or set an explicit start and end date.",
    "about.raionDateText": "Raion mode is limited to the last month. This is because alerts.in.ua provides raion alert history for that time window, and the site does not call the external API while a user is opening the page.",
    "about.noDataText": "If a raion has no cached data for the selected period, it is shown in gray. Hovering over it will show a tooltip saying that no data is available for that period.",
    "about.sourcesTitle": "Where the data comes from",
    "about.oblastSourceText": "Oblast statistics are updated from the Vadimkin Ukrainian Air Raid Sirens Dataset. After the dataset is updated, the backend aggregates events into oblast summaries for the selected period.",
    "about.raionSourceText": "Raion statistics are cached locally from alerts.in.ua by a background worker. User-facing requests read only the local database, so the frontend never calls alerts.in.ua directly and the API token is never sent to the browser.",
  },
};

function currentUairLanguage() {
  return localStorage.getItem("uair-language") === "en" ? "en" : "uk";
}

function uairT(key, fallback = "") {
  const language = currentUairLanguage();
  return UAIR_TRANSLATIONS[language]?.[key] || UAIR_TRANSLATIONS.uk[key] || fallback;
}

function applyUairLanguage(language) {
  const normalizedLanguage = language === "en" ? "en" : "uk";
  localStorage.setItem("uair-language", normalizedLanguage);
  document.documentElement.lang = normalizedLanguage;

  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = uairT(element.dataset.i18n, element.textContent);
  });
  document.querySelectorAll("[data-i18n-aria-label]").forEach((element) => {
    element.setAttribute("aria-label", uairT(element.dataset.i18nAriaLabel, element.getAttribute("aria-label") || ""));
  });

  const languageToggle = document.querySelector("#language-toggle");
  if (languageToggle) {
    languageToggle.textContent = normalizedLanguage === "uk" ? "EN" : "UA";
    languageToggle.setAttribute("aria-label", uairT("language.toggle"));
  }

  if (document.body.classList.contains("help-page")) {
    document.title = uairT("about.pageTitle");
  }

  window.dispatchEvent(new CustomEvent("uair:languagechange", { detail: { language: normalizedLanguage } }));
}

function toggleUairLanguage() {
  applyUairLanguage(currentUairLanguage() === "uk" ? "en" : "uk");
}

window.uairT = uairT;
window.currentUairLanguage = currentUairLanguage;
window.applyUairLanguage = applyUairLanguage;

document.addEventListener("DOMContentLoaded", () => {
  applyUairLanguage(currentUairLanguage());
  document.querySelector("#language-toggle")?.addEventListener("click", toggleUairLanguage);
});

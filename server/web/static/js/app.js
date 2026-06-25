const SVG_NS = "http://www.w3.org/2000/svg";
const MAP_PADDING = 8;
const MAP_SOURCES = {
  regions: "/static/geo/ukraine_regions.geojson",
  districts: "/static/geo/ukraine_districts.geojson",
};
const LABEL_OFFSETS = {
  14: [0, 28],
  31: [0, -14],
};

const state = {
  summaries: [],
  summariesByRegionId: new Map(),
  raionSummaries: [],
  raionSummariesByLocationUid: new Map(),
  selectedRegionId: null,
  mapLevel: "regions",
  showLabels: true,
  geojsonByLevel: new Map(),
  svgFeatures: [],
  svgLabels: [],
};

const mapEl = document.querySelector("#map");
const mapSvg = document.querySelector("#ukraine-map");
const mapLevelSelect = document.querySelector("#map-level");
const showLabelsInput = document.querySelector("#show-labels");
const startDateInput = document.querySelector("#start-date");
const endDateInput = document.querySelector("#end-date");
const daysSelect = document.querySelector("#days");
const modeSelect = document.querySelector("#mode");
const themeToggle = document.querySelector("#theme-toggle");
const helpToggle = document.querySelector("#help-toggle");
const filtersToggle = document.querySelector("#filters-toggle");
const helpPanel = document.querySelector("#help-panel");
const filtersPanel = document.querySelector("#filters-panel");
const filterSummaryEl = document.querySelector("#filter-summary");
const tooltipEl = document.querySelector("#map-tooltip");
const detailsPanel = document.querySelector("#region-details");
const closeDetailsButton = document.querySelector("#details-close");
const dailyChartEl = document.querySelector("#daily-chart");

mapLevelSelect.addEventListener("change", changeMapLevel);
showLabelsInput.addEventListener("change", toggleLabels);
startDateInput.addEventListener("change", refreshMapData);
endDateInput.addEventListener("change", refreshMapData);
daysSelect.addEventListener("change", refreshMapData);
modeSelect.addEventListener("change", refreshMapData);
themeToggle.addEventListener("click", toggleTheme);
helpToggle.addEventListener("click", (event) => {
  event.stopPropagation();
  togglePopover(helpPanel, helpToggle);
});
filtersToggle.addEventListener("click", (event) => {
  event.stopPropagation();
  togglePopover(filtersPanel, filtersToggle);
});
helpPanel.addEventListener("click", (event) => event.stopPropagation());
filtersPanel.addEventListener("click", (event) => event.stopPropagation());
closeDetailsButton.addEventListener("click", closeDetails);
document.addEventListener("click", closePopovers);
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && state.selectedRegionId) {
    closeDetails();
  }
  if (event.key === "Escape") {
    closePopovers();
  }
});

const resizeObserver = new ResizeObserver(() => {
  const geojson = currentGeoJson();
  if (geojson) renderGeoJsonMap(geojson);
});
resizeObserver.observe(mapEl);

function colorFor(value, maxValue) {
  if (!value || !maxValue) return "var(--region-base)";
  const intensity = Math.max(0.15, Math.min(value / maxValue, 1));
  const lightness = 34 + (1 - intensity) * 26;
  return `hsl(354, 72%, ${lightness}%)`;
}

function currentGeoJson() {
  return state.geojsonByLevel.get(state.mapLevel);
}

function isDistrictMode() {
  return state.mapLevel === "districts";
}

function featureRegionId(properties) {
  return String(properties.region_id || "").trim();
}

function regionName(properties) {
  return properties.region_name || properties.adm1_name1 || properties.shapeName || "Unknown region";
}

function districtName(properties) {
  return properties.district_name || properties.adm2_name1 || properties.adm2_name || regionName(properties);
}

function districtMetricUid(properties) {
  return String(properties.alertsua_location_uid || properties.location_uid || properties.district_id || "").trim();
}

function summaryByRegionId(regionId) {
  return state.summariesByRegionId.get(String(regionId || "").trim());
}

function summaryByFeature(properties) {
  return summaryByRegionId(featureRegionId(properties));
}

function raionSummaryByFeature(properties) {
  return state.raionSummariesByLocationUid.get(districtMetricUid(properties));
}

function displaySummaryByFeature(properties) {
  return (isDistrictMode() && raionSummaryByFeature(properties)) || summaryByFeature(properties);
}

function currentModeLabel() {
  const mode = modeSelect.value;
  if (mode === "count") return "Alerts";
  if (mode === "duration") return "Hours";
  return "Coefficient";
}

function metricTooltipValue(summary) {
  if (!summary) return "-";
  if (modeSelect.value === "count") return String(summary.alert_count);
  if (modeSelect.value === "duration") return minutesLabel(summary.total_duration_minutes);
  return Number(summary.metric_value || 0).toFixed(2);
}

function hasRaionData(summary) {
  return Boolean(
    summary
      && ((summary.alert_count || 0) > 0 || (summary.total_duration_minutes || 0) > 0),
  );
}

function isDistrictWithoutData(properties) {
  return isDistrictMode() && !hasRaionData(raionSummaryByFeature(properties));
}

function tooltipText(properties) {
  const summary = displaySummaryByFeature(properties);
  const title = isDistrictMode()
    ? `${districtName(properties)} - ${regionName(properties)}`
    : regionName(properties);
  if (isDistrictWithoutData(properties)) {
    return `${title}: Немає даних за цей період`;
  }
  return `${title} (${currentModeLabel()}: ${metricTooltipValue(summary)})`;
}

function showTooltip(event, properties) {
  tooltipEl.textContent = tooltipText(properties);
  tooltipEl.classList.add("is-visible");
  tooltipEl.setAttribute("aria-hidden", "false");
  if (Number.isFinite(event.clientX) && Number.isFinite(event.clientY)) {
    moveTooltip(event);
    return;
  }
  const bounds = event.currentTarget.getBoundingClientRect();
  tooltipEl.style.left = `${bounds.left + bounds.width / 2}px`;
  tooltipEl.style.top = `${bounds.top + bounds.height / 2}px`;
}

function moveTooltip(event) {
  const offset = 14;
  tooltipEl.style.left = `${event.clientX + offset}px`;
  tooltipEl.style.top = `${event.clientY + offset}px`;
}

function hideTooltip() {
  tooltipEl.classList.remove("is-visible");
  tooltipEl.setAttribute("aria-hidden", "true");
}

function applyTheme(theme) {
  const normalizedTheme = theme === "dark" ? "dark" : "light";
  document.documentElement.dataset.theme = normalizedTheme;
  themeToggle.textContent = normalizedTheme === "dark" ? "Світла" : "Темна";
  themeToggle.setAttribute(
    "aria-label",
    normalizedTheme === "dark" ? "Увімкнути світлу тему" : "Увімкнути темну тему",
  );
  localStorage.setItem("uair-theme", normalizedTheme);
}

function toggleTheme() {
  const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  applyTheme(nextTheme);
}

function togglePopover(panel, button) {
  const willOpen = panel.hidden;
  closePopovers();
  panel.hidden = !willOpen;
  button.setAttribute("aria-expanded", String(willOpen));
}

function closePopovers() {
  helpPanel.hidden = true;
  filtersPanel.hidden = true;
  helpToggle.setAttribute("aria-expanded", "false");
  filtersToggle.setAttribute("aria-expanded", "false");
}

function selectedDateRange() {
  const startDate = startDateInput.value;
  const endDate = endDateInput.value;
  if (!startDate || !endDate) return null;
  return { startDate, endDate };
}

function updateFilterSummary() {
  const levelLabel = mapLevelSelect.selectedOptions[0]?.textContent || mapLevelSelect.value;
  const dateRange = selectedDateRange();
  const daysLabel = dateRange
    ? `${dateRange.startDate} - ${dateRange.endDate}`
    : daysSelect.selectedOptions[0]?.textContent || `${daysSelect.value} days`;
  const modeLabel = modeSelect.selectedOptions[0]?.textContent || modeSelect.value;
  filterSummaryEl.textContent = `${levelLabel} · ${daysLabel} · ${modeLabel}`;
}

function analyticsQueryParams() {
  const params = new URLSearchParams({
    days: daysSelect.value,
    mode: modeSelect.value,
  });
  const dateRange = selectedDateRange();
  if (dateRange) {
    params.set("start_date", dateRange.startDate);
    params.set("end_date", dateRange.endDate);
  }
  return params;
}

function dailyQueryParams() {
  const params = new URLSearchParams({ days: daysSelect.value });
  const dateRange = selectedDateRange();
  if (dateRange) {
    params.set("start_date", dateRange.startDate);
    params.set("end_date", dateRange.endDate);
  }
  return params;
}

function shortenRegionLabel(name) {
  return name
    .replace(/\s+\u043e\u0431\u043b\u0430\u0441\u0442\u044c$/u, "")
    .replace(
      /^\u0410\u0432\u0442\u043e\u043d\u043e\u043c\u043d\u0430\s+\u0420\u0435\u0441\u043f\u0443\u0431\u043b\u0456\u043a\u0430\s+/u,
      "",
    );
}

function mapSize() {
  const bounds = mapEl.getBoundingClientRect();
  const width = Math.max(320, Math.floor(bounds.width - MAP_PADDING * 2));
  const height = Math.max(320, Math.floor(bounds.height - MAP_PADDING * 2));
  return { width, height };
}

function clearSvg() {
  while (mapSvg.firstChild) {
    mapSvg.removeChild(mapSvg.firstChild);
  }
  state.svgFeatures = [];
  state.svgLabels = [];
}

function createSvgElement(tagName, attributes = {}) {
  const element = document.createElementNS(SVG_NS, tagName);
  for (const [key, value] of Object.entries(attributes)) {
    element.setAttribute(key, value);
  }
  return element;
}

function selectRegion(summary) {
  if (!summary?.region_id) return;
  state.selectedRegionId = summary.region_id;
  detailsPanel.classList.add("is-open");
  detailsPanel.setAttribute("aria-hidden", "false");
  renderDetails(summary);
  loadDaily(summary.region_id);
  updateMapColors();
}

function closeDetails() {
  state.selectedRegionId = null;
  detailsPanel.classList.remove("is-open");
  detailsPanel.setAttribute("aria-hidden", "true");
  dailyChartEl.replaceChildren();
  updateMapColors();
}

function renderGeoJsonMap(geojson) {
  const features = geojson.features || [];
  const { width, height } = mapSize();
  const projection = d3.geoMercator();
  projection.fitSize([width, height], geojson);
  const geoPath = d3.geoPath(projection);

  clearSvg();
  mapSvg.setAttribute("viewBox", `0 0 ${width} ${height}`);

  const regionsGroup = createSvgElement("g", { class: "map-regions" });
  const labelsGroup = createSvgElement("g", { class: "map-labels" });
  const districtLabelFeatures = new Map();

  for (const feature of features) {
    const properties = feature.properties || {};
    const regionId = featureRegionId(properties);
    const pathData = geoPath(feature);
    if (!regionId || !pathData) continue;
    if (isDistrictMode()) {
      const existing = districtLabelFeatures.get(regionId) || [];
      existing.push(feature);
      districtLabelFeatures.set(regionId, existing);
    }

    const path = createSvgElement("path", {
      class: isDistrictMode() ? "region district" : "region",
      d: pathData,
      "data-region-id": regionId,
      "data-district-id": properties.district_id || "",
      "data-alertsua-location-uid": properties.alertsua_location_uid || "",
      "fill-rule": "evenodd",
      "clip-rule": "evenodd",
      tabindex: "0",
      role: "button",
      "aria-label": isDistrictMode() ? districtName(properties) : regionName(properties),
    });
    path.addEventListener("click", () => selectRegion(summaryByRegionId(regionId)));
    path.addEventListener("mouseenter", (event) => showTooltip(event, properties));
    path.addEventListener("mousemove", moveTooltip);
    path.addEventListener("mouseleave", hideTooltip);
    path.addEventListener("focus", (event) => showTooltip(event, properties));
    path.addEventListener("blur", hideTooltip);
    path.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectRegion(summaryByRegionId(regionId));
      }
    });

    const [centroidX, centroidY] = geoPath.centroid(feature);
    let label = null;
    if (state.showLabels && !isDistrictMode() && Number.isFinite(centroidX) && Number.isFinite(centroidY)) {
      const labelOffset = LABEL_OFFSETS[regionId] || [0, 0];
      label = createSvgElement("text", {
        class: "region-label",
        x: (centroidX + labelOffset[0]).toFixed(2),
        y: (centroidY + labelOffset[1]).toFixed(2),
        "data-region-id": regionId,
      });
      label.textContent = shortenRegionLabel(regionName(properties));
    }

    regionsGroup.appendChild(path);
    if (label) {
      labelsGroup.appendChild(label);
      state.svgLabels.push(label);
    }
    state.svgFeatures.push({ regionId, path, label, properties });
  }

  if (state.showLabels && isDistrictMode()) {
    for (const [regionId, regionFeatures] of districtLabelFeatures.entries()) {
      const [centroidX, centroidY] = geoPath.centroid({
        type: "FeatureCollection",
        features: regionFeatures,
      });
      if (!Number.isFinite(centroidX) || !Number.isFinite(centroidY)) continue;

      const properties = regionFeatures[0]?.properties || {};
      const labelOffset = LABEL_OFFSETS[regionId] || [0, 0];
      const label = createSvgElement("text", {
        class: "region-label",
        x: (centroidX + labelOffset[0]).toFixed(2),
        y: (centroidY + labelOffset[1]).toFixed(2),
        "data-region-id": regionId,
      });
      label.textContent = shortenRegionLabel(regionName(properties));
      labelsGroup.appendChild(label);
      state.svgLabels.push(label);
    }
  }

  mapSvg.appendChild(regionsGroup);
  mapSvg.appendChild(labelsGroup);
  updateMapColors();
}

function updateMapColors() {
  const activeSummaries = isDistrictMode() && state.raionSummaries.length
    ? state.raionSummaries
    : state.summaries;
  const maxValue = Math.max(...activeSummaries.map((item) => item.metric_value), 0);

  for (const item of state.svgFeatures) {
    const summary = displaySummaryByFeature(item.properties);
    const isSelected = String(state.selectedRegionId || "") === item.regionId;
    const hasNoData = isDistrictWithoutData(item.properties);

    item.path.style.fill = hasNoData ? "var(--region-no-data)" : colorFor(summary?.metric_value, maxValue);
    item.path.classList.toggle("is-selected", isSelected);
    item.path.classList.toggle("is-no-data", hasNoData);
    item.label?.classList.toggle("is-selected", isSelected);
  }

  for (const label of state.svgLabels) {
    const regionId = label.getAttribute("data-region-id");
    label.classList.toggle("is-selected", String(state.selectedRegionId || "") === regionId);
  }
}

async function loadGeoJson(level = state.mapLevel) {
  if (state.geojsonByLevel.has(level)) {
    renderGeoJsonMap(state.geojsonByLevel.get(level));
    return;
  }

  try {
    const response = await fetch(MAP_SOURCES[level]);
    if (!response.ok) throw new Error("GeoJSON file is not available.");
    const geojson = await response.json();
    state.geojsonByLevel.set(level, geojson);
    renderGeoJsonMap(geojson);
  } catch (error) {
    console.error(`Map geometry is not available. Check ${MAP_SOURCES[level]}.`, error);
  }
}

async function changeMapLevel() {
  state.mapLevel = mapLevelSelect.value === "districts" ? "districts" : "regions";
  closeDetails();
  hideTooltip();
  updateFilterSummary();
  await loadGeoJson(state.mapLevel);
  await refreshMapData();
}

function toggleLabels() {
  state.showLabels = showLabelsInput.checked;
  const geojson = currentGeoJson();
  if (geojson) renderGeoJsonMap(geojson);
}

async function refreshMapData() {
  updateFilterSummary();
  const queryParams = analyticsQueryParams();
  const response = await fetch(`/api/regions/summary?${queryParams}`);
  state.summaries = await response.json();
  state.summariesByRegionId = new Map(
    state.summaries.map((item) => [String(item.region_id || "").trim(), item]),
  );
  if (isDistrictMode()) {
    const raionsResponse = await fetch(`/api/raions/summary?${queryParams}`);
    state.raionSummaries = await raionsResponse.json();
    state.raionSummariesByLocationUid = new Map(
      state.raionSummaries.map((item) => [String(item.location_uid || "").trim(), item]),
    );
  } else {
    state.raionSummaries = [];
    state.raionSummariesByLocationUid = new Map();
  }
  if (state.selectedRegionId) {
    const selectedSummary = summaryByRegionId(state.selectedRegionId);
    if (selectedSummary) {
      renderDetails(selectedSummary);
      loadDaily(selectedSummary.region_id);
    }
  }
  updateMapColors();
}

function minutesLabel(value) {
  if (value === null || value === undefined) return "-";
  const hours = value / 60;
  return `${hours.toFixed(1)} h`;
}

function renderDetails(summary) {
  document.querySelector("#region-title").textContent = summary.region_name;
  document.querySelector("#metric-count").textContent = summary.alert_count;
  document.querySelector("#metric-duration").textContent = minutesLabel(
    summary.total_duration_minutes,
  );
  document.querySelector("#metric-average").textContent = minutesLabel(
    summary.average_duration_minutes,
  );
}

async function loadDaily(regionId) {
  const response = await fetch(`/api/regions/${regionId}/daily?${dailyQueryParams()}`);
  const payload = await response.json();
  renderDailyChart(payload.stats);
}

function renderDailyChart(stats) {
  dailyChartEl.replaceChildren();

  const maxCount = Math.max(...stats.map((item) => item.alert_count), 1);
  const maxHours = Math.max(...stats.map((item) => item.total_duration_minutes / 60), 1);

  const header = document.createElement("div");
  header.className = "chart-header";
  header.innerHTML = "<span>Date</span><span>Alerts</span><span>Hours</span>";
  dailyChartEl.appendChild(header);

  for (const item of stats) {
    const hours = item.total_duration_minutes / 60;
    const row = document.createElement("div");
    row.className = "chart-row";

    const date = document.createElement("span");
    date.className = "chart-date";
    date.textContent = item.date;

    const countBar = document.createElement("span");
    countBar.className = "bar-cell";
    countBar.innerHTML = `<span class="bar count-bar" style="--bar-value: ${
      item.alert_count / maxCount
    }"></span><span class="bar-value">${item.alert_count}</span>`;

    const durationBar = document.createElement("span");
    durationBar.className = "bar-cell";
    durationBar.innerHTML = `<span class="bar duration-bar" style="--bar-value: ${
      hours / maxHours
    }"></span><span class="bar-value">${hours.toFixed(1)}</span>`;

    row.append(date, countBar, durationBar);
    dailyChartEl.appendChild(row);
  }
}

async function init() {
  applyTheme(localStorage.getItem("uair-theme") || "light");
  await Promise.all([loadGeoJson(), refreshMapData()]);
  updateMapColors();
}

init();

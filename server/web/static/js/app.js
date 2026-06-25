const SVG_NS = "http://www.w3.org/2000/svg";
const MAP_PADDING = 8;
const LABEL_OFFSETS = {
  14: [0, 28],
  31: [0, -14],
};

const state = {
  summaries: [],
  summariesByRegionId: new Map(),
  selectedRegionId: null,
  geojson: null,
  svgFeatures: new Map(),
};

const mapEl = document.querySelector("#map");
const mapSvg = document.querySelector("#ukraine-map");
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
  if (state.geojson) renderGeoJsonMap(state.geojson);
});
resizeObserver.observe(mapEl);

function colorFor(value, maxValue) {
  if (!value || !maxValue) return "var(--region-base)";
  const intensity = Math.max(0.15, Math.min(value / maxValue, 1));
  const lightness = 34 + (1 - intensity) * 26;
  return `hsl(354, 72%, ${lightness}%)`;
}

function regionName(properties) {
  return properties.region_name || properties.shapeName || "Unknown region";
}

function summaryByRegionId(regionId) {
  return state.summariesByRegionId.get(String(regionId || "").trim());
}

function summaryByFeature(properties) {
  return summaryByRegionId(properties.region_id);
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

function tooltipText(properties) {
  const summary = summaryByFeature(properties);
  return `${regionName(properties)} (${currentModeLabel()}: ${metricTooltipValue(summary)})`;
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

function updateFilterSummary() {
  const daysLabel = daysSelect.selectedOptions[0]?.textContent || `${daysSelect.value} days`;
  const modeLabel = modeSelect.selectedOptions[0]?.textContent || modeSelect.value;
  filterSummaryEl.textContent = `${daysLabel} · ${modeLabel}`;
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
  state.svgFeatures.clear();
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

  for (const feature of features) {
    const properties = feature.properties || {};
    const regionId = String(properties.region_id || "").trim();
    const pathData = geoPath(feature);
    if (!regionId || !pathData) continue;

    const path = createSvgElement("path", {
      class: "region",
      d: pathData,
      "data-region-id": regionId,
      "fill-rule": "evenodd",
      "clip-rule": "evenodd",
      tabindex: "0",
      role: "button",
      "aria-label": regionName(properties),
    });
    path.addEventListener("click", () => selectRegion(summaryByFeature(properties)));
    path.addEventListener("mouseenter", (event) => showTooltip(event, properties));
    path.addEventListener("mousemove", moveTooltip);
    path.addEventListener("mouseleave", hideTooltip);
    path.addEventListener("focus", (event) => showTooltip(event, properties));
    path.addEventListener("blur", hideTooltip);
    path.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectRegion(summaryByFeature(properties));
      }
    });

    const [centroidX, centroidY] = geoPath.centroid(feature);
    let label = null;
    if (Number.isFinite(centroidX) && Number.isFinite(centroidY)) {
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
    if (label) labelsGroup.appendChild(label);
    state.svgFeatures.set(regionId, { path, label, properties });
  }

  mapSvg.appendChild(regionsGroup);
  mapSvg.appendChild(labelsGroup);
  updateMapColors();
}

function updateMapColors() {
  const maxValue = Math.max(...state.summaries.map((item) => item.metric_value), 0);

  for (const [regionId, item] of state.svgFeatures.entries()) {
    const summary = summaryByRegionId(regionId);
    const isSelected = String(state.selectedRegionId || "") === regionId;

    item.path.style.fill = colorFor(summary?.metric_value, maxValue);
    item.path.classList.toggle("is-selected", isSelected);
    item.label?.classList.toggle("is-selected", isSelected);
  }
}

async function loadGeoJson() {
  try {
    const response = await fetch("/static/geo/ukraine_regions.geojson");
    if (!response.ok) throw new Error("GeoJSON file is not available.");
    state.geojson = await response.json();
    renderGeoJsonMap(state.geojson);
  } catch (error) {
    console.error("Map geometry is not available. Check /static/geo/ukraine_regions.geojson.", error);
  }
}

async function refreshMapData() {
  updateFilterSummary();
  const days = daysSelect.value;
  const mode = modeSelect.value;
  const response = await fetch(`/api/regions/summary?days=${days}&mode=${mode}`);
  state.summaries = await response.json();
  state.summariesByRegionId = new Map(
    state.summaries.map((item) => [String(item.region_id || "").trim(), item]),
  );
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
  const days = daysSelect.value;
  const response = await fetch(`/api/regions/${regionId}/daily?days=${days}`);
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

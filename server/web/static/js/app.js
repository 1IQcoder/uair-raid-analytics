const SVG_NS = "http://www.w3.org/2000/svg";
const PROJECTION_SCALE = 100;
const VIEWBOX_PADDING = 12;

const state = {
  summaries: [],
  summariesByRegionId: new Map(),
  selectedRegionId: null,
  chart: null,
  geojson: null,
  svgFeatures: new Map(),
};

const mapSvg = document.querySelector("#ukraine-map");
const daysSelect = document.querySelector("#days");
const modeSelect = document.querySelector("#mode");
const statusEl = document.querySelector("#map-status");

daysSelect.addEventListener("change", refreshMapData);
modeSelect.addEventListener("change", refreshMapData);

function colorFor(value, maxValue) {
  if (!value || !maxValue) return "#263244";
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

function eachCoordinateFromGeometry(geometry, callback) {
  if (!geometry) return;

  if (geometry.type === "Polygon") {
    for (const ring of geometry.coordinates || []) {
      for (const coordinate of ring) callback(coordinate);
    }
  }

  if (geometry.type === "MultiPolygon") {
    for (const polygon of geometry.coordinates || []) {
      for (const ring of polygon) {
        for (const coordinate of ring) callback(coordinate);
      }
    }
  }
}

function computeBounds(features) {
  const bounds = {
    minLon: Infinity,
    minLat: Infinity,
    maxLon: -Infinity,
    maxLat: -Infinity,
  };

  for (const feature of features) {
    eachCoordinateFromGeometry(feature.geometry, ([lon, lat]) => {
      bounds.minLon = Math.min(bounds.minLon, lon);
      bounds.minLat = Math.min(bounds.minLat, lat);
      bounds.maxLon = Math.max(bounds.maxLon, lon);
      bounds.maxLat = Math.max(bounds.maxLat, lat);
    });
  }

  return bounds;
}

function projectCoordinate([lon, lat], bounds) {
  return [
    (lon - bounds.minLon) * PROJECTION_SCALE + VIEWBOX_PADDING,
    (bounds.maxLat - lat) * PROJECTION_SCALE + VIEWBOX_PADDING,
  ];
}

function ringToPath(ring, bounds) {
  return ring
    .map((coordinate, index) => {
      const [x, y] = projectCoordinate(coordinate, bounds);
      return `${index === 0 ? "M" : "L"}${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ")
    .concat(" Z");
}

function geometryToPath(geometry, bounds) {
  if (!geometry) return "";

  if (geometry.type === "Polygon") {
    return (geometry.coordinates || []).map((ring) => ringToPath(ring, bounds)).join(" ");
  }

  if (geometry.type === "MultiPolygon") {
    return (geometry.coordinates || [])
      .flatMap((polygon) => polygon.map((ring) => ringToPath(ring, bounds)))
      .join(" ");
  }

  return "";
}

function featureLabelPoint(feature, bounds) {
  const featureBounds = {
    minX: Infinity,
    minY: Infinity,
    maxX: -Infinity,
    maxY: -Infinity,
  };

  eachCoordinateFromGeometry(feature.geometry, (coordinate) => {
    const [x, y] = projectCoordinate(coordinate, bounds);
    featureBounds.minX = Math.min(featureBounds.minX, x);
    featureBounds.minY = Math.min(featureBounds.minY, y);
    featureBounds.maxX = Math.max(featureBounds.maxX, x);
    featureBounds.maxY = Math.max(featureBounds.maxY, y);
  });

  return {
    x: (featureBounds.minX + featureBounds.maxX) / 2,
    y: (featureBounds.minY + featureBounds.maxY) / 2,
  };
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
  renderDetails(summary);
  loadDaily(summary.region_id);
  updateMapColors();
}

function renderGeoJsonMap(geojson) {
  const features = geojson.features || [];
  const bounds = computeBounds(features);
  const width = (bounds.maxLon - bounds.minLon) * PROJECTION_SCALE + VIEWBOX_PADDING * 2;
  const height = (bounds.maxLat - bounds.minLat) * PROJECTION_SCALE + VIEWBOX_PADDING * 2;

  clearSvg();
  mapSvg.setAttribute("viewBox", `0 0 ${width.toFixed(2)} ${height.toFixed(2)}`);

  const regionsGroup = createSvgElement("g", { class: "map-regions" });
  const labelsGroup = createSvgElement("g", { class: "map-labels" });

  for (const feature of features) {
    const properties = feature.properties || {};
    const regionId = String(properties.region_id || "").trim();
    const pathData = geometryToPath(feature.geometry, bounds);
    if (!regionId || !pathData) continue;

    const path = createSvgElement("path", {
      class: "region",
      d: pathData,
      "data-region-id": regionId,
      tabindex: "0",
      role: "button",
      "aria-label": regionName(properties),
    });
    path.addEventListener("click", () => selectRegion(summaryByFeature(properties)));
    path.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectRegion(summaryByFeature(properties));
      }
    });

    const labelPoint = featureLabelPoint(feature, bounds);
    const label = createSvgElement("text", {
      class: "region-label",
      x: labelPoint.x.toFixed(2),
      y: labelPoint.y.toFixed(2),
      "data-region-id": regionId,
    });
    label.textContent = regionName(properties)
      .replace(" область", "")
      .replace("Автономна Республіка ", "");

    regionsGroup.appendChild(path);
    labelsGroup.appendChild(label);
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
    item.label.classList.toggle("is-selected", isSelected);
  }
}

async function loadGeoJson() {
  try {
    const response = await fetch("/static/geo/ukraine_regions.geojson");
    if (!response.ok) throw new Error("GeoJSON file is not available.");
    state.geojson = await response.json();
    renderGeoJsonMap(state.geojson);
  } catch (error) {
    statusEl.textContent =
      "Map geometry is not available. Check /static/geo/ukraine_regions.geojson.";
  }
}

async function refreshMapData() {
  const days = daysSelect.value;
  const mode = modeSelect.value;
  const response = await fetch(`/api/regions/summary?days=${days}&mode=${mode}`);
  state.summaries = await response.json();
  state.summariesByRegionId = new Map(
    state.summaries.map((item) => [String(item.region_id || "").trim(), item]),
  );
  updateMapColors();
  statusEl.textContent = state.summaries.length
    ? `Loaded ${state.summaries.length} regional summaries.`
    : "No dataset loaded yet. Run the update script first.";
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
  const labels = payload.stats.map((item) => item.date);
  const counts = payload.stats.map((item) => item.alert_count);
  const durations = payload.stats.map((item) => Math.round(item.total_duration_minutes / 60));
  const canvas = document.querySelector("#daily-chart");

  if (state.chart) state.chart.destroy();
  state.chart = new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [
        { label: "Alerts", data: counts, backgroundColor: "#c91d2e" },
        { label: "Hours", data: durations, backgroundColor: "#f0a0a9" },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { beginAtZero: true } },
    },
  });
}

async function init() {
  await Promise.all([loadGeoJson(), refreshMapData()]);
  updateMapColors();
}

init();

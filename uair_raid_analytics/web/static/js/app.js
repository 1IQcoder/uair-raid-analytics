const state = {
  summaries: [],
  selectedRegionId: null,
  chart: null,
  geoLayer: null,
};

const map = L.map("map", { zoomControl: true }).setView([48.7, 31.2], 6);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 10,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

const daysSelect = document.querySelector("#days");
const modeSelect = document.querySelector("#mode");
const statusEl = document.querySelector("#map-status");

daysSelect.addEventListener("change", refreshMapData);
modeSelect.addEventListener("change", refreshMapData);

function colorFor(value, maxValue) {
  if (!value || !maxValue) return "#f3d8dc";
  const intensity = Math.max(0.15, Math.min(value / maxValue, 1));
  const lightness = 92 - intensity * 50;
  return `hsl(354, 68%, ${lightness}%)`;
}

function regionKey(properties) {
  return String(
    properties.region_id ||
      properties.id ||
      properties.uid ||
      properties.name ||
      properties.NAME_1 ||
      properties.shapeName ||
      "",
  );
}

function regionName(properties) {
  return (
    properties.region_name ||
    properties.name ||
    properties.NAME_1 ||
    properties.shapeName ||
    "Unknown region"
  );
}

function summaryByFeature(properties) {
  const key = regionKey(properties).toLowerCase();
  return state.summaries.find((item) => {
    return (
      String(item.region_id || "").toLowerCase() === key ||
      item.region_name.toLowerCase() === regionName(properties).toLowerCase()
    );
  });
}

function styleFeature(feature) {
  const summary = summaryByFeature(feature.properties || {});
  const maxValue = Math.max(...state.summaries.map((item) => item.metric_value), 0);
  return {
    color: "#ffffff",
    weight: 1,
    fillColor: colorFor(summary?.metric_value, maxValue),
    fillOpacity: 0.9,
  };
}

function bindFeature(feature, layer) {
  const properties = feature.properties || {};
  const summary = summaryByFeature(properties);
  layer.on("click", () => {
    if (!summary?.region_id) return;
    state.selectedRegionId = summary.region_id;
    renderDetails(summary);
    loadDaily(summary.region_id);
  });
  layer.bindTooltip(summary?.region_name || regionName(properties));
}

async function loadGeoJson() {
  try {
    const response = await fetch("/static/geo/ukraine_regions.geojson");
    if (!response.ok) throw new Error("GeoJSON file is not available yet.");
    const geojson = await response.json();
    state.geoLayer = L.geoJSON(geojson, {
      style: styleFeature,
      onEachFeature: bindFeature,
    }).addTo(map);
    map.fitBounds(state.geoLayer.getBounds(), { padding: [16, 16] });
  } catch (error) {
    statusEl.textContent =
      "Map geometry is not included yet. Add Ukraine regions GeoJSON to /static/geo/ukraine_regions.geojson.";
  }
}

async function refreshMapData() {
  const days = daysSelect.value;
  const mode = modeSelect.value;
  const response = await fetch(`/api/regions/summary?days=${days}&mode=${mode}`);
  state.summaries = await response.json();
  if (state.geoLayer) {
    state.geoLayer.setStyle(styleFeature);
  }
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
      scales: { y: { beginAtZero: true } },
    },
  });
}

refreshMapData().then(loadGeoJson);

function uairThemeIcon(theme) {
  if (theme === "dark") {
    return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 14.6A8 8 0 0 1 9.4 3 7 7 0 1 0 21 14.6Z"/></svg>';
  }
  return '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4 12H2M22 12h-2M5 5l1.4 1.4M17.6 17.6 19 19M19 5l-1.4 1.4M6.4 17.6 5 19"/></svg>';
}

function applyUairTheme(theme) {
  const normalizedTheme = theme === "dark" ? "dark" : "light";
  const toggle = document.querySelector("#theme-toggle");
  const translate = window.uairT || ((key, fallback) => fallback || key);
  document.documentElement.dataset.theme = normalizedTheme;
  localStorage.setItem("uair-theme", normalizedTheme);
  if (!toggle) return;
  toggle.innerHTML = uairThemeIcon(normalizedTheme);
  toggle.classList.toggle("is-dark", normalizedTheme === "dark");
  toggle.setAttribute(
    "aria-label",
    normalizedTheme === "dark" ? translate("theme.light") : translate("theme.dark"),
  );
}

function toggleUairTheme() {
  applyUairTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
}

document.addEventListener("DOMContentLoaded", () => {
  applyUairTheme(localStorage.getItem("uair-theme") || "light");
  document.querySelector("#theme-toggle")?.addEventListener("click", toggleUairTheme);
});

window.addEventListener("uair:languagechange", () => {
  applyUairTheme(document.documentElement.dataset.theme || localStorage.getItem("uair-theme") || "light");
});

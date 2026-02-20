document.addEventListener("DOMContentLoaded", () => {

  // Сначала восстановить порядок
  restoreLayout();

  // Инициализация drag
  document.querySelectorAll(".service-list").forEach(list => {
    new Sortable(list, {
      group: "services",
      animation: 150,
      ghostClass: "opacity-40",
      draggable: ".draggable-card",
      onEnd: saveLayout
    });
  });
});

// --- layout persistence ---
function saveLayout() {
  const layout = {};

  document.querySelectorAll(".service-group").forEach(group => {
    const groupKey = group.dataset.group;
    if (!groupKey) return;

    layout[groupKey] = [];
    group.querySelectorAll(".service-list .draggable-card[data-service]").forEach(card => {
      layout[groupKey].push(String(card.dataset.service));
    });
  });

  localStorage.setItem("servicehub-layout", JSON.stringify(layout));
}

function restoreLayout() {
  const saved = localStorage.getItem("servicehub-layout");
  if (!saved) return;

  let layout;
  try {
    layout = JSON.parse(saved);
  } catch (e) {
    console.warn("[ServiceHub] Bad layout JSON, clearing.", e);
    localStorage.removeItem("servicehub-layout");
    return;
  }

  Object.entries(layout).forEach(([groupKey, services]) => {
    const container = document.querySelector(
      `.service-group[data-group="${CSS.escape(String(groupKey))}"] .service-list`
    );
    if (!container || !Array.isArray(services)) return;

    services.forEach(id => {
      // IMPORTANT: search globally, not inside container
      const el = document.querySelector(
        `.draggable-card[data-service="${CSS.escape(String(id))}"]`
      );
      if (el) container.appendChild(el);
    });
  });
}

// --- sortable init ---
document.addEventListener("DOMContentLoaded", () => {
  if (typeof Sortable !== "function") {
    console.error("[ServiceHub] Sortable is not loaded. Check sortable.min.js include.");
    return;
  }

  // 1) restore first
  restoreLayout();

  // 2) then init sortable
  document.querySelectorAll(".service-list").forEach(list => {
    new Sortable(list, {
      group: "services",
      animation: 150,
      ghostClass: "opacity-40",
      draggable: ".draggable-card",
      onEnd: saveLayout
    });
  });
});


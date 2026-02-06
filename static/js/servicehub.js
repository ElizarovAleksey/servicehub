document.addEventListener("DOMContentLoaded", () => {

  document.querySelectorAll(".service-list").forEach(el => {
    new Sortable(el, {
      group: "services",
      animation: 150,
      ghostClass: "opacity-40",
      onEnd: saveLayout
    });
  });

  restoreLayout();
});

function saveLayout() {
  const layout = {};

  document.querySelectorAll(".group").forEach(group => {
    const name = group.dataset.group;
    layout[name] = [];

    group.querySelectorAll("[data-service]").forEach(card => {
      layout[name].push(card.dataset.service);
    });
  });

  localStorage.setItem("servicehub-layout", JSON.stringify(layout));
}

function restoreLayout() {
  const saved = localStorage.getItem("servicehub-layout");
  if (!saved) return;

  const layout = JSON.parse(saved);

  Object.entries(layout).forEach(([group, services]) => {
    const container = document.querySelector(
      `.group[data-group="${group}"] .service-list`
    );
    if (!container) return;

    services.forEach(name => {
      const el = document.querySelector(`[data-service="${name}"]`);
      if (el) container.appendChild(el);
    });
  });
}

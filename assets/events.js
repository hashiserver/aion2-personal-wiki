(() => {
  "use strict";

  const deadlines = document.querySelector("#home-deadlines");
  const archive = document.querySelector("#past-events");
  const sections = Array.from(document.querySelectorAll(".event-list"), (list) => ({
    id: list.parentElement.id,
    list,
    empty: list.nextElementSibling,
  }));
  const labels = {
    upcoming: "開催予定",
    starting: "開始日・公式で確認",
    active: "開催中",
    ending: "期限間近",
    uncertain: "終了日・公式で確認",
    ended: "終了",
  };
  const entries = Array.from(document.querySelectorAll("[data-start][data-end]"), (node) => ({
    node,
    start: Number(node.dataset.start),
    active: Number(node.dataset.active),
    warning: Number(node.dataset.warning),
    end: Number(node.dataset.end),
    exactEnd: node.hasAttribute("data-exact-end"),
    group: node.dataset.eventGroup,
    status: node.querySelector(".status"),
  }));
  const boundaries = entries.flatMap(({ start, active, warning, end }) => [start, active, warning, end]);
  let timer;

  function state(entry, now) {
    if (now < entry.start) return "upcoming";
    if (now >= entry.end) return "ended";
    if (now < entry.active) return "starting";
    if (now < entry.warning) return "active";
    return entry.exactEnd ? "ending" : "uncertain";
  }

  function arrange(list, items) {
    let cursor = list.firstElementChild;
    for (const { node } of items) {
      if (node === cursor) cursor = cursor.nextElementSibling;
      else list.insertBefore(node, cursor);
    }
  }

  function update() {
    clearTimeout(timer);
    const now = Date.now();
    const sorted = entries.map((entry) => ({ ...entry, state: state(entry, now) }))
      .sort((a, b) => a.end - b.end);

    if (deadlines) {
      const next = sorted.filter(({ state }) => ["active", "ending", "uncertain"].includes(state)).slice(0, 2);
      for (const { node } of sorted) {
        const match = next.find((entry) => entry.node === node);
        node.hidden = !match;
        const soon = match?.state === "ending" || match?.state === "uncertain";
        node.classList.toggle("deadline-soon", soon);
        node.querySelector(".deadline-warning").hidden = !soon;
      }
      arrange(deadlines, next);
    }

    if (archive) {
      const ended = sorted.filter(({ state }) => state === "ended").reverse();
      for (const item of sorted) {
        item.status.className = "status " + item.state;
        const basis = item.node.dataset.statusBasis;
        item.status.textContent = labels[item.state] + (basis ? "（" + basis + "）" : "");
        item.status.hidden = false;
      }
      for (const section of sections) {
        const current = sorted.filter((item) => item.group === section.id && item.state !== "ended");
        current.sort((a, b) => Number(a.state === "upcoming") - Number(b.state === "upcoming"));
        arrange(section.list, current);
        section.empty.hidden = current.length > 0;
      }
      arrange(archive.querySelector(".event-archive-list"), ended);
      archive.hidden = ended.length === 0;

      const target = ended.find(({ node }) => "#" + node.id === location.hash)?.node;
      if (target && !archive.open) {
        archive.open = true;
        target.scrollIntoView();
      }
    }

    const next = Math.min(...boundaries.filter((instant) => instant > now));
    if (Number.isFinite(next)) timer = setTimeout(update, Math.min(next - now, 86_400_000));
  }

  update();
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) update();
  });
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) update();
  });
})();

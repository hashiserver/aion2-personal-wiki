/* Only loaded on the pet purchase page. */
(() => {
  "use strict";

  const root = document.getElementById("pet-tracker");
  if (!root) return;

  const storageKey = "aion2-pet-completed-v1";
  const pendingBody = root.querySelector("#pet-pending-body");
  const completedBody = root.querySelector("#pet-completed-body");
  const pendingTable = pendingBody.closest(".pet-table-wrap");
  const completedTable = completedBody.closest(".pet-table-wrap");
  const search = root.querySelector("#pet-search");
  const group = root.querySelector("#pet-group");
  const quick = root.querySelector("#pet-quick");
  const groupButtons = Array.from(quick.querySelectorAll("button"));
  const genus = root.querySelector("#pet-genus");
  const pendingCount = root.querySelector("#pet-pending-count");
  const doneCount = root.querySelector("#pet-done-count");
  const doneSummary = root.querySelector("#pet-done-summary");
  const completedSummary = root.querySelector("#pet-completed-summary");
  const completedPanel = root.querySelector("#pet-completed-panel");
  const completedLink = root.querySelector("#pet-completed-link");
  const empty = root.querySelector("#pet-empty");
  const doneEmpty = root.querySelector("#pet-done-empty");
  const results = root.querySelector("#pet-results");
  const status = root.querySelector("#pet-action-status");
  const reset = root.querySelector("#pet-reset");
  let storageAvailable = true;

  function normalize(value) {
    return value.normalize("NFKC").toLowerCase()
      .replace(/[ァ-ヶ]/g, (char) => String.fromCharCode(char.charCodeAt(0) - 0x60))
      .replace(/\s+/g, "");
  }

  const pets = Array.from(root.querySelectorAll(".pet-row"), (row) => ({
    row,
    input: row.querySelector(".pet-done-input"),
    key: row.dataset.key,
    name: row.dataset.name,
    groups: row.dataset.groups.split(" "),
    genus: row.dataset.genus,
    searchText: [row.dataset.name, row.dataset.reading, row.dataset.key].map(normalize),
  }));

  function readCompleted() {
    try {
      const value = JSON.parse(localStorage.getItem(storageKey) || "[]");
      return new Set(Array.isArray(value) ? value.filter((key) => typeof key === "string") : []);
    } catch {
      storageAvailable = false;
      status.textContent = "保存先にアクセスできません。このタブを閉じるとチェックが失われる場合があります。";
      return new Set();
    }
  }

  const completed = readCompleted();

  function save() {
    if (!storageAvailable) return;
    try {
      localStorage.setItem(storageKey, JSON.stringify(Array.from(completed)));
    } catch {
      storageAvailable = false;
      status.textContent = "ブラウザへの保存に失敗しました。チェックはこの画面内だけに保持されています。";
    }
  }

  function updateTotals() {
    const finished = completedBody.rows.length;
    pendingCount.textContent = String(pendingBody.rows.length);
    doneCount.textContent = String(finished);
    doneSummary.textContent = String(finished);
    completedLink.hidden = finished === 0;
    reset.disabled = completed.size === 0;
  }

  function applyFilters() {
    const phrase = normalize(search.value);
    const selectedGroup = group.value;
    const selectedGenus = genus.value;
    for (const button of groupButtons) {
      button.setAttribute("aria-pressed", String(button.dataset.petGroup === selectedGroup));
    }
    const filtering = phrase || selectedGroup !== "all" || selectedGenus !== "all";
    let visiblePending = 0;
    let visibleDone = 0;
    for (const pet of pets) {
      const visible = (!phrase || pet.searchText.some((text) => text.includes(phrase))) &&
        (selectedGroup === "all" || pet.groups.includes(selectedGroup)) &&
        (selectedGenus === "all" || selectedGenus === pet.genus);
      if (pet.row.hidden === visible) pet.row.hidden = !visible;
      if (visible) {
        if (pet.input.checked) visibleDone++;
        else visiblePending++;
      }
    }

    pendingTable.hidden = visiblePending === 0;
    completedTable.hidden = visibleDone === 0;
    empty.hidden = visiblePending !== 0;
    doneEmpty.hidden = visibleDone !== 0;
    const doneMessage = completedBody.rows.length
      ? "条件に一致する完了済みのペットはありません。"
      : "まだ完了済みのペットはありません。";
    if (doneEmpty.textContent !== doneMessage) doneEmpty.textContent = doneMessage;
    const message = filtering ? `表示中 未完了 ${visiblePending}件・完了 ${visibleDone}件` : "";
    if (results.textContent !== message) results.textContent = message;
  }

  for (const pet of pets) {
    pet.input.checked = completed.has(pet.key);
    if (pet.input.checked) completedBody.append(pet.row);
  }
  updateTotals();
  applyFilters();

  root.addEventListener("change", (event) => {
    if (!event.target.matches(".pet-done-input")) return;
    const index = pets.findIndex((pet) => pet.input === event.target);
    const pet = pets[index];
    const checked = pet.input.checked;
    if (checked) completed.add(pet.key);
    else completed.delete(pet.key);

    const hadFocus = document.activeElement === pet.input;
    const nextFocus = pets.find((candidate, position) => position > index &&
      candidate.input.checked !== checked && !candidate.row.hidden) ??
      pets.findLast((candidate, position) => position < index &&
        candidate.input.checked !== checked && !candidate.row.hidden);
    const target = checked ? completedBody : pendingBody;
    const nextPet = pets.find((candidate, position) => position > index && candidate.row.parentElement === target);
    target.insertBefore(pet.row, nextPet?.row ?? null);
    updateTotals();
    applyFilters();
    if (hadFocus) (nextFocus?.input ?? (checked ? search : completedSummary)).focus();
    save();
    if (storageAvailable) {
      status.textContent = pet.name + (checked ? "を完了にしました。" : "を未完了に戻しました。");
    }
  });

  search.addEventListener("input", applyFilters);
  group.addEventListener("change", applyFilters);
  genus.addEventListener("change", applyFilters);
  quick.hidden = false;
  quick.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-pet-group]");
    if (!button) return;
    group.value = button.dataset.petGroup;
    applyFilters();
  });

  completedLink.addEventListener("click", () => {
    completedPanel.open = true;
  });

  reset.addEventListener("click", () => {
    if (!completed.size || !window.confirm("このブラウザで保存したペットの完了チェックをすべて解除しますか？")) return;

    completed.clear();
    const rows = document.createDocumentFragment();
    for (const pet of pets) {
      pet.input.checked = false;
      rows.append(pet.row);
    }
    pendingBody.append(rows);
    search.focus();
    updateTotals();
    applyFilters();
    save();
    if (storageAvailable) status.textContent = "すべて未完了に戻しました。";
  });
})();

/* Only loaded by /pets/. No backend calls and no account tracking. */
(() => {
  "use strict";

  const root = document.getElementById("pet-tracker");
  if (!root) return;

  const storageKey = "aion2-pet-completed-v1";
  const pendingBody = root.querySelector("#pet-pending-body");
  const completedBody = root.querySelector("#pet-completed-body");
  const search = root.querySelector("#pet-search");
  const group = root.querySelector("#pet-group");
  const genus = root.querySelector("#pet-genus");
  const pendingCount = root.querySelector("#pet-pending-count");
  const doneCount = root.querySelector("#pet-done-count");
  const doneSummary = root.querySelector("#pet-done-summary");
  const empty = root.querySelector("#pet-empty");
  const doneEmpty = root.querySelector("#pet-done-empty");
  const status = root.querySelector("#pet-action-status");
  const reset = root.querySelector("#pet-reset");
  const rows = Array.from(root.querySelectorAll("tr.pet-row"));
  let storageAvailable = true;

  function readCompleted() {
    try {
      const value = JSON.parse(localStorage.getItem(storageKey) || "[]");
      if (!Array.isArray(value)) return new Set();
      return new Set(value.filter((key) => typeof key === "string"));
    } catch (_error) {
      storageAvailable = false;
      return new Set();
    }
  }

  const completed = readCompleted();
  if (!storageAvailable) {
    status.textContent = "保存先にアクセスできません。このタブを閉じるとチェックが失われる場合があります。";
  }

  function checkbox(row) {
    return row.querySelector("input.pet-done-input");
  }

  function updateLabel(row) {
    checkbox(row).setAttribute(
      "aria-label",
      row.dataset.key + (checkbox(row).checked ? "の完了を解除する" : "を完了済みにする")
    );
  }

  function matchesFilters(row) {
    const phrase = search.value.trim().toLocaleLowerCase();
    const matchesName = !phrase || row.dataset.key.toLocaleLowerCase().includes(phrase);
    const matchesGroup = group.value === "all" ||
      row.dataset.groups.split(" ").includes(group.value);
    const matchesGenus = genus.value === "all" || row.dataset.genus === genus.value;
    return matchesName && matchesGroup && matchesGenus;
  }

  function repaint() {
    let pending = 0;
    let finished = 0;
    let visiblePending = 0;
    let visibleDone = 0;

    rows.forEach((row) => {
      const input = checkbox(row);
      const isDone = input.checked;
      row.classList.toggle("is-done", isDone);
      const target = isDone ? completedBody : pendingBody;
      target.appendChild(row);
      row.hidden = !matchesFilters(row);
      if (isDone) {
        finished++;
        if (!row.hidden) visibleDone++;
      } else {
        pending++;
        if (!row.hidden) visiblePending++;
      }
      updateLabel(row);
    });

    // Re-checking a row restores its original gojuon order rather than
    // leaving it at the end of the list.
    [pendingBody, completedBody].forEach((body) => {
      Array.from(body.children)
        .sort((a, b) => Number(a.dataset.order) - Number(b.dataset.order))
        .forEach((row) => body.appendChild(row));
    });

    pendingCount.textContent = String(pending);
    doneCount.textContent = String(finished);
    doneSummary.textContent = String(finished);
    empty.hidden = visiblePending !== 0;
    doneEmpty.hidden = visibleDone !== 0;
    reset.disabled = finished === 0;
  }

  function save() {
    if (!storageAvailable) return;
    try {
      localStorage.setItem(storageKey, JSON.stringify(Array.from(completed)));
    } catch (_error) {
      storageAvailable = false;
      status.textContent = "ブラウザへの保存に失敗しました。チェックはこの画面内だけに保持されています。";
    }
  }

  rows.forEach((row) => {
    checkbox(row).checked = completed.has(row.dataset.key);
  });

  root.addEventListener("change", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement) || !target.classList.contains("pet-done-input")) {
      return;
    }
    const row = target.closest("tr.pet-row");
    if (!row) return;
    if (target.checked) {
      completed.add(row.dataset.key);
    } else {
      completed.delete(row.dataset.key);
    }
    save();
    repaint();
    if (storageAvailable) {
      status.textContent = row.dataset.key + (target.checked
        ? "を完了にしました。下の「完了済み」から戻せます。"
        : "を未完了に戻しました。");
    }
  });

  [search, group, genus].forEach((control) => {
    control.addEventListener("input", repaint);
    control.addEventListener("change", repaint);
  });

  reset.addEventListener("click", () => {
    if (completed.size === 0) return;
    if (!window.confirm("このブラウザで保存したペットの完了チェックをすべて解除しますか？")) {
      return;
    }
    completed.clear();
    rows.forEach((row) => { checkbox(row).checked = false; });
    save();
    repaint();
    if (storageAvailable) status.textContent = "全て未完了に戻しました。";
  });

  repaint();
})();
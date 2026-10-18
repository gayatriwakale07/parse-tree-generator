// "My history" card: lists saved parse trees, reopens or deletes them.
// Uses apiFetch from auth.js and the render helpers from script.js.
const History = (() => {
  function el(tag, cls, text) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = text; // textContent: safe against HTML injection
    return node;
  }

  async function open(id) {
    const item = await apiFetch("/history/" + id);
    document.getElementById("grammar").value = item.grammar;
    document.getElementById("input-string").value = item.input_string;
    document.getElementById("start-symbol").value = item.start_symbol;
    renderGrammar(item.grammar);
    if (item.parse_tree) {
      renderParseResult(item.parse_tree, item.steps);
      setStatus("Loaded from your history", "info");
    } else {
      clearResult();
      setStatus("This attempt failed when it was saved. Generate again to see the reason.", "error");
    }
  }

  async function remove(id) {
    if (!confirm("Delete this record?")) return;
    await apiFetch("/history/" + id, { method: "DELETE" });
    await refresh();
  }

  async function refresh() {
    const list = document.getElementById("history-list");
    if (!list) return;
    const { history } = await apiFetch("/history");
    list.replaceChildren();

    if (!history.length) {
      list.append(el("li", "history-empty", "Nothing saved yet. Generate a parse tree and it will appear here."));
      return;
    }
    for (const h of history) {
      const li = el("li", "history-item");

      const openBtn = el("button", "history-open");
      openBtn.type = "button";
      openBtn.append(
        el("span", "history-input", h.input_string || "(empty string)"),
        el("span", "history-meta", (h.success ? "" : "Failed · ") + h.created_at.slice(0, 16))
      );
      openBtn.addEventListener("click", () => open(h.id).catch((e) => setStatus(e.message, "error")));

      const del = el("button", "history-del", "Delete");
      del.type = "button";
      del.addEventListener("click", () => remove(h.id).catch((e) => setStatus(e.message, "error")));

      li.append(openBtn, del);
      list.append(li);
    }
  }

  return { refresh, open };
})();
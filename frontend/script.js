// Main page logic: generate / reset, error suggestions, and drawing the parse tree as SVG.
const $ = (id) => document.getElementById(id);
const SVG_NS = "http://www.w3.org/2000/svg";

function setStatus(text, type) {
  const box = $("status");
  box.textContent = text || "";
  box.className = "status" + (text ? " " + type : "");
}

function renderGrammar(text) {
  $("grammar-echo").textContent = text || "";
}

function renderSteps(steps) {
  const items = steps.map((s) => {
    const li = document.createElement("li");
    li.textContent = s;
    return li;
  });
  $("steps").replaceChildren(...items);
}

// ---------- suggestions (shown when the grammar or the input is wrong) ----------
function hideSuggestions() {
  const box = $("suggestions");
  box.hidden = true;
  box.replaceChildren();
}

function suggestionBlock(label, code, buttonText, onApply) {
  const wrap = document.createElement("div");
  const title = document.createElement("div");
  title.className = "suggest-label";
  title.textContent = label;
  const pre = document.createElement("pre");
  pre.className = "suggest-code";
  pre.textContent = code || "(empty string)";
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "btn-apply";
  btn.textContent = buttonText;
  btn.addEventListener("click", onApply);
  wrap.append(title, pre, btn);
  return wrap;
}

function showSuggestions(data) {
  const list = (data && data.suggestions) || [];
  const fixedGrammar = data && data.fixed_grammar;
  const fixedInput = data && data.fixed_input;
  if (!list.length && !fixedGrammar && fixedInput == null) { hideSuggestions(); return; }

  const nodes = [];
  const heading = document.createElement("h3");
  heading.textContent = "Suggestions";
  nodes.push(heading);

  if (list.length) {
    const ul = document.createElement("ul");
    for (const text of list) {
      const li = document.createElement("li");
      li.textContent = text;
      ul.append(li);
    }
    nodes.push(ul);
  }
  if (fixedGrammar) {
    nodes.push(suggestionBlock("Suggested grammar", fixedGrammar, "Use suggested grammar", () => {
      $("grammar").value = fixedGrammar;
      hideSuggestions();
      setStatus("Suggested grammar applied. Click “Generate parse tree” to try it.", "info");
    }));
  }
  if (fixedInput != null) {
    nodes.push(suggestionBlock("Suggested input", fixedInput, "Use suggested input", () => {
      $("input-string").value = fixedInput;
      hideSuggestions();
      setStatus("Suggested input applied. Click “Generate parse tree” to try it.", "info");
    }));
  }
  const box = $("suggestions");
  box.replaceChildren(...nodes);
  box.hidden = false;
}

// ---------- results ----------
function clearResult() {
  const empty = document.createElement("p");
  empty.className = "tree-empty";
  empty.textContent = "Your parse tree will appear here.";
  $("tree").replaceChildren(empty);
  $("steps").replaceChildren();
  hideSuggestions();
}

function svgEl(name, attrs) {
  const el = document.createElementNS(SVG_NS, name);
  for (const [k, v] of Object.entries(attrs || {})) el.setAttribute(k, v);
  return el;
}

function renderTree(tree) {
  const NODE_H = 30, V_GAP = 64, H_GAP = 14, PAD = 20, CHAR_W = 9.6;
  const nodes = [];
  let leafX = PAD, maxDepth = 0;

  // leaves get consecutive slots; each parent is centred over its children
  (function place(n, depth) {
    n.w = Math.max(34, n.symbol.length * CHAR_W + 22);
    n.y = PAD + depth * V_GAP + NODE_H / 2;
    maxDepth = Math.max(maxDepth, depth);
    if (!n.children.length) {
      n.x = leafX + n.w / 2;
      leafX += n.w + H_GAP;
    } else {
      n.children.forEach((c) => place(c, depth + 1));
      n.x = (n.children[0].x + n.children[n.children.length - 1].x) / 2;
    }
    nodes.push(n);
  })(tree, 0);

  const width = Math.ceil(leafX - H_GAP + PAD);
  const height = PAD * 2 + maxDepth * V_GAP + NODE_H;
  const svg = svgEl("svg", {
    class: "tree-svg", width, height, viewBox: `0 0 ${width} ${height}`,
    role: "img", "aria-label": "Parse tree",
  });

  for (const n of nodes) {
    for (const c of n.children) {
      svg.append(svgEl("line", {
        class: "edge", x1: n.x, y1: n.y + NODE_H / 2, x2: c.x, y2: c.y - NODE_H / 2,
      }));
    }
  }
  const cls = { nonterminal: "node-nt", terminal: "node-t", epsilon: "node-eps" };
  for (const n of nodes) {
    const g = svgEl("g", { class: cls[n.type] });
    g.append(svgEl("rect", { x: n.x - n.w / 2, y: n.y - NODE_H / 2, width: n.w, height: NODE_H, rx: 8 }));
    const t = svgEl("text", { x: n.x, y: n.y });
    t.textContent = n.symbol;
    g.append(t);
    svg.append(g);
  }
  $("tree").replaceChildren(svg);
}

// also used by history.js when a saved record is opened
function renderParseResult(tree, steps) {
  renderTree(tree);
  renderSteps(steps || []);
  hideSuggestions();
}

// ---------- actions ----------
async function generate() {
  const grammar = $("grammar").value;

  if (!grammar.trim()) {
    clearResult();
    renderGrammar("");
    setStatus("Please enter a grammar first.", "error");
    showSuggestions({
      suggestions: [
        "Write one rule per line, for example:  E -> T E'",
        "Separate the symbols with spaces and use | between alternatives.",
        "Use ε (or the word eps) for the empty string.",
      ],
    });
    $("grammar").focus();
    return;
  }

  const btn = $("generate-btn");
  btn.disabled = true;
  setStatus("Generating…", "info");
  try {
    const data = await apiFetch("/parse", {
      method: "POST",
      body: JSON.stringify({
        grammar,
        input: $("input-string").value,
        start: $("start-symbol").value,
      }),
    });
    renderGrammar(grammar);
    renderParseResult(data.tree, data.steps);
    setStatus("Parse tree generated successfully", "ok");
  } catch (err) {
    if (err.status === 401) { window.location.href = "login.html"; return; }
    clearResult();
    renderGrammar(grammar);
    setStatus(err.message, "error");
    showSuggestions(err.data);
  } finally {
    btn.disabled = false;
    History.refresh().catch(() => {});
  }
}

function reset() {
  $("grammar").value = "";
  $("input-string").value = "";
  $("start-symbol").value = "";
  renderGrammar("");
  clearResult();
  setStatus("", "");
  $("grammar").focus();
  apiFetch("/event", { method: "POST", body: JSON.stringify({ action: "reset" }) }).catch(() => {});
}

// ---- start: the form is empty, nothing is pre-filled ----
renderGrammar("");
clearResult();
$("generate-btn").addEventListener("click", generate);
$("reset-btn").addEventListener("click", reset);

Auth.requireLogin()
  .then(() => History.refresh())
  .catch(() => { /* redirected to login.html */ });
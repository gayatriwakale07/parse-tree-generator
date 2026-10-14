// Address of the Flask backend. Change it here if the backend runs elsewhere.
const API_BASE = "http://localhost:5000";

const EXAMPLES = [
  { name: "a^n b^n", grammar: "S -> aSb | ab", string: "aabb" },
  { name: "Arithmetic expressions", grammar: "E -> E + T | T\nT -> T * F | F\nF -> id", string: "id + id * id" },
  { name: "Ambiguous expression grammar", grammar: "E -> E + E | E * E | id", string: "id + id * id" },
  { name: "Palindromes over a, b", grammar: "S -> aSa | bSb | a | b | eps", string: "abba" },
  { name: "Balanced parentheses", grammar: "S -> ( S ) S | eps", string: "(())()" },
  { name: "String not in the language", grammar: "S -> aSb | ab", string: "aab" },
];

const $ = (id) => document.getElementById(id);

// ---------- setup ----------
function setupExamples() {
  const select = $("examples");
  select.add(new Option("Choose an example...", ""));
  EXAMPLES.forEach((ex, i) => select.add(new Option(ex.name, String(i))));
  select.addEventListener("change", () => {
    if (select.value === "") return;
    const ex = EXAMPLES[Number(select.value)];
    $("grammar").value = ex.grammar;
    $("string").value = ex.string;
    generate();
  });
}

// ---------- calling the backend ----------
async function generate() {
  const button = $("generate");
  button.disabled = true;
  button.textContent = "Working...";
  try {
    const response = await fetch(`${API_BASE}/api/parse`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ grammar: $("grammar").value, string: $("string").value }),
    });
    const data = await response.json();
    render(data);
  } catch (err) {
    showStatus([["bad", `Cannot reach the backend at ${API_BASE}. Is it running? (python backend/app.py)`]]);
  } finally {
    button.disabled = false;
    button.textContent = "Generate";
  }
}

// ---------- showing the result ----------
function showStatus(messages) {
  $("result").classList.remove("hidden");
  const box = $("status");
  box.replaceChildren();
  for (const [kind, text] of messages) {
    const div = document.createElement("div");
    div.className = `msg ${kind}`;
    div.textContent = text;      // textContent keeps user input safe
    box.appendChild(div);
  }
  $("details").classList.add("hidden");
}

function render(data) {
  if (data.success === false) {
    showStatus([["bad", data.error || "Something went wrong"]]);
    return;
  }
  if (!data.accepted) {
    showStatus([["bad", `Rejected: ${data.message}`]]);
    showCnf(data);
    return;
  }

  showStatus([
    ["ok", "Accepted: the string belongs to the language."],
    [data.ambiguous ? "warn" : "ok", data.ambiguity_message],
  ]);
  $("leftmost").textContent = data.leftmost.join("  ⇒  ");
  $("rightmost").textContent = data.rightmost.join("  ⇒  ");

  const box = $("trees");
  box.replaceChildren();
  data.trees.forEach((tree, i) => {
    const figure = document.createElement("figure");
    const caption = document.createElement("figcaption");
    caption.textContent = data.trees.length > 1
      ? `Parse tree ${i + 1} of ${data.tree_count}${data.tree_count_capped ? "+" : ""}`
      : "Parse tree";
    const holder = document.createElement("div");
    holder.className = "tree-box";
    figure.append(caption, holder);
    box.appendChild(figure);
    drawTree(holder, tree);
  });
  showCnf(data);
}

function showCnf(data) {
  $("cnf").textContent = data.cnf.join("\n");
  $("treePart").classList.toggle("hidden", !data.accepted);   // nothing to draw when rejected
  $("details").classList.remove("hidden");
}

// ---------- drawing a tree with D3 ----------
function drawTree(container, data) {
  if (typeof d3 === "undefined") {
    container.textContent = "D3.js could not be loaded. Check your internet connection.";
    return;
  }
  const root = d3.hierarchy(data, (d) => d.children);
  const maxLabel = d3.max(root.descendants(), (d) => d.data.symbol.length);
  const dx = Math.max(56, maxLabel * 10 + 34);
  const dy = 70;
  d3.tree().nodeSize([dx, dy])(root);

  let x0 = Infinity, x1 = -Infinity;
  root.each((d) => { x0 = Math.min(x0, d.x); x1 = Math.max(x1, d.x); });
  const width = x1 - x0 + dx * 2;
  const height = root.height * dy + 70;

  const svg = d3.select(container).append("svg")
    .attr("width", width)
    .attr("height", height)
    .attr("viewBox", [x0 - dx, -35, width, height]);

  svg.append("g").selectAll("path").data(root.links()).join("path")
    .attr("class", "link")
    .attr("d", d3.linkVertical().x((d) => d.x).y((d) => d.y));

  const node = svg.append("g").selectAll("g").data(root.descendants()).join("g")
    .attr("class", (d) => `node ${d.data.children ? "var" : "term"}`)
    .attr("transform", (d) => `translate(${d.x},${d.y})`);

  node.append("rect")
    .attr("rx", 8)
    .attr("height", 30).attr("y", -15)
    .attr("width", (d) => Math.max(34, d.data.symbol.length * 10 + 18))
    .attr("x", (d) => -Math.max(34, d.data.symbol.length * 10 + 18) / 2);
  node.append("text").text((d) => d.data.symbol);
}

// ---------- events ----------
$("generate").addEventListener("click", generate);
document.addEventListener("keydown", (e) => {
  if (e.ctrlKey && e.key === "Enter") generate();
});
setupExamples();
generate();
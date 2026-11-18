# parse-tree-generato
# Parse Tree Generator

A web application for **Theory of Computation** that takes a **Context-Free Grammar (CFG)** and an input string, checks whether the string belongs to the language, and generates its **derivations** and **parse tree**. It also detects whether a string has more than one parse tree (**ambiguity**).

## 1. Project Status

> Update this section as the team completes each item.

### Completed

- [ ] GitHub repository and `main` branch setup
- [ ] Project folder structure committed
- [ ] `README.md` and `.gitignore` committed
- [ ] `requirements.txt` committed

### Current development starting point

The first development phase is **Grammar Parsing and Validation**, followed by CNF conversion and the CYK algorithm.

---

# 2. About the Project

In Theory of Computation, students derive strings from a CFG and draw parse trees by hand. This is slow and easy to get wrong, especially for long strings or tricky grammars.

This project automates it. You enter a grammar such as:

```text
S -> aSb | ab
```

and a string such as `aabb`. The tool tells you whether the string is in the language and, if it is, shows the derivation steps and draws the parse tree.

## Features

- Accept any Context-Free Grammar and an input string
- Validate the grammar format
- Convert the grammar to Chomsky Normal Form (CNF)
- Check membership using the CYK algorithm
- Show leftmost and rightmost derivations step by step
- Generate and draw the parse tree
- Detect ambiguity (more than one parse tree for a string)
- Show clear error messages for invalid input

## Key terms

| Term | Simple meaning |
|---|---|
| CFG | A set of rules that generate strings, written G = (V, T, P, S) |
| Variables (non-terminals) | Symbols that can be replaced, like `S`, `E`, `T` |
| Terminals | Final symbols that stay, like `a`, `b`, `+`, `id` |
| Start symbol | Where every derivation begins (usually `S`) |
| Production | One rule, like `S -> aSb` |
| Derivation | Replacing variables step by step until only terminals remain |
| Leftmost / rightmost derivation | Always replace the leftmost / rightmost variable first |
| Parse tree | The derivation drawn as a tree |
| Ambiguous grammar | A grammar where one string has more than one parse tree |
| CNF | Chomsky Normal Form: every rule is `A -> BC` or `A -> a` |

---

# 3. System Architecture

```text
parse-tree-generator/
│
├── frontend/              # HTML + CSS + JavaScript (D3.js) user interface
├── backend/               # Python + Flask REST API and all TOC algorithms
├── docs/                  # API notes, diagrams and report material
├── requirements.txt       # Python dependencies
└── .gitignore
```

### Responsibility of each part

| Folder | Responsibility |
|---|---|
| `frontend/` | Input boxes, Generate button, result display, parse tree drawing, API calls |
| `backend/` | Grammar validation, CNF conversion, CYK, derivations, tree building, ambiguity check, REST API |
| `docs/` | API documentation, architecture diagrams, report and presentation material |

### Main data flow

```text
User
  ↓
Frontend (HTML/CSS/JS + D3.js)
  ↓ HTTP/JSON
Flask Backend
  ├── Validate grammar
  ├── Convert to CNF
  ├── CYK membership check
  ├── Build derivations + parse tree
  └── Check ambiguity
        ↓
     JSON result
        ↓
     Frontend draws the tree
```

**Important:** All grammar logic lives in the backend. The frontend only collects input and displays results.

### Design note: which tree to show

CYK works on the CNF version of the grammar, so a tree built directly from the CYK table follows the CNF rules, not the grammar the user typed. The team should decide early:

- Build the displayed tree with a separate parser that works on the **original** grammar (for example a memoized top-down parser or Earley), and use CYK for the membership check, or
- Build the tree from CYK and map it back to the original grammar.

---

# 4. Prerequisites for Every Team Member

Install these on your computer before setting up the project:

```text
Git
Python 3.9 or newer
pip
VS Code
A modern web browser
```

Verify the installations:

```powershell
git --version
python --version
pip --version
```

Optional: Graphviz (only if the team chooses server-side tree images) and Node.js (only if the team adds a frontend build tool later).

---

# 5. Clone the Repository

Open PowerShell and run:

```powershell
git clone https://github.com/gayatriwakale07/parse-tree-generator.git
```

Move into the project:

```powershell
cd parse-tree-generator
```

Open the complete project in VS Code:

```powershell
code .
```

Do not create a second project structure. Work inside the existing folders.

---

# 6. Backend Setup

From the project root:

```powershell
python -m venv .venv
```

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

(Mac/Linux: `source .venv/bin/activate`)

Install the dependencies:

```powershell
pip install -r requirements.txt
```

The baseline `requirements.txt`:

```text
flask
flask-cors
pytest
```
Running The application
stremlit run app.py
Start the backend:

```powershell
python backend/app.py
```

Expected local backend:

```text
http://localhost:5000
```

Health endpoint (once implemented):

```text
http://localhost:5000/api/health
```

Expected response:

```json
{
  "success": true,
  "message": "Parse Tree Generator backend is running"
}
```

Do not commit:

```text
.venv/
__pycache__/
```

---

# 7. Environment Setup

The basic project needs very little configuration. If the team adds a `.env` file, keep a template in the repository:

```text
backend/.env.example
```

Create your local file from it:

```powershell
cd backend
Copy-Item .env.example .env
```

Possible template contents:

```env
PORT=5000
FLASK_DEBUG=1
ALLOWED_ORIGIN=http://localhost:5500
```

**Never commit the real `.env` file.**

---

# 8. Frontend Setup

The frontend is plain HTML, CSS and JavaScript, so no install step is needed.

Open the project in VS Code and use one of these:

- Install the **Live Server** extension, right-click `frontend/index.html`, and choose **Open with Live Server** (usually `http://localhost:5500`), or
- From the `frontend` folder run:
  ```powershell
  python -m http.server 5500
  ```

Open:

```text
http://localhost:5500
```

**CORS tip:** Live Server often opens `http://127.0.0.1:5500` instead of `http://localhost:5500`. These count as different origins, so allow the exact address you use in the backend CORS setting (or allow both).

The frontend calls the backend at `http://localhost:5000`. Keep the backend URL in one place at the top of `frontend/script.js` so it is easy to change.

Tree drawing uses **D3.js** (or Viz.js), loaded from a CDN script tag in `index.html`.

---

# 9. Data Management

- **No database is needed** for the basic project. The grammar, tokens and tree live in memory while a request runs.
- **Format everywhere:** JSON for sending and receiving data.
- **Optional later feature:** SQLite to save past grammars, test strings and results (a history page). If added, any schema change must be documented in `docs/`.

---

# 10. Running the Complete System

Use separate terminals.

### Terminal 1: Backend

```powershell
.\.venv\Scripts\Activate.ps1
python backend/app.py
```

### Terminal 2: Frontend

```powershell
cd frontend
python -m http.server 5500
```

Expected local arrangement:

```text
Frontend  → http://localhost:5500
Backend   → http://localhost:5000
```

---

# 11. How the Algorithms Work

### Workflow

```text
Input grammar + string
        ↓
Validate grammar
        ↓
Convert to CNF
        ↓
CYK membership check
        ↓
accepted? ── no ──→ "String not in the language"
        ↓ yes
Build derivations + parse tree
        ↓
Check ambiguity
        ↓
Return JSON → frontend draws the tree
```

### Grammar validation

- Every rule has the form `Variable -> alternatives separated by |`
- The left side must be a single variable
- A start symbol exists (default: the left side of the first rule)
- Empty rules are written with `eps` (or `ε`)
- Report the line number for any format error

### CNF conversion (in this order)

1. Add a new start symbol if the old one appears on a right side
2. Remove ε-productions
3. Remove unit productions (`A -> B`)
4. Remove useless symbols
5. Replace terminals inside longer rules with new variables
6. Break rules longer than two variables into pairs

### CYK in plain words

CYK builds a table. It first finds which variables can produce each single letter, then each pair of letters, then longer groups, always combining smaller answers into bigger ones. If the start symbol can produce the whole string, the string is accepted. It is dynamic programming: solve small pieces first, then combine.

### Derivations

- **Leftmost:** always replace the leftmost variable first
- **Rightmost:** always replace the rightmost variable first

Both are returned as a list of sentential forms.

### Ambiguity

The tool counts or lists the distinct parse trees for the given string (with a safe limit on how many it generates). If there are two or more, the grammar is reported as ambiguous **for that string**.

Note for the report: deciding whether a grammar is ambiguous for *all* strings is undecidable in general, so the tool checks per string, not for the whole language.

---

# 12. API

**POST** `/api/parse`

Request:

```json
{
  "grammar": "S -> aSb | ab",
  "string": "aabb"
}
```

Response:

```json
{
  "accepted": true,
  "ambiguous": false,
  "leftmost": ["S", "aSb", "aabb"],
  "rightmost": ["S", "aSb", "aabb"],
  "tree": {
    "symbol": "S",
    "children": [
      {"symbol": "a"},
      {"symbol": "S", "children": [{"symbol": "a"}, {"symbol": "b"}]},
      {"symbol": "b"}
    ]
  }
}
```

If the string is not in the language:

```json
{
  "accepted": false,
  "message": "String not in the language"
}
```

If the grammar or input is invalid:

```json
{
  "success": false,
  "error": "Line 2: left side must be a single variable"
}
```

Keep the final request and response formats documented in `docs/api/`.

---

# 13. Examples

### Example 1: simple grammar

Grammar: `S -> aSb | ab`  
String: `aabb`

Derivation: `S => aSb => aabb`

```text
        S
     /  |  \
    a   S   b
       / \
      a   b
```

### Example 2: expression grammar

```text
E -> E + T | T
T -> T * F | F
F -> id
```

String: `id + id * id`

```text
            E
        /   |   \
       E    +    T
       |        /|\
       T       T * F
       |       |   |
       F       F   id
       |       |
       id      id
```

Multiplication sits deeper in the tree, so it is evaluated before addition.

### Example 3: ambiguous grammar

Grammar: `E -> E + E | E * E | id`  
String: `id + id * id`

This string can be parsed in two ways: one where `+` is done first and one where `*` is done first. The tool shows both trees and reports ambiguity.

---

# 14. Development Order

Do not develop modules randomly. Follow this sequence.

```text
PHASE 1
Grammar input + validation
        ↓
PHASE 2
CNF conversion
        ↓
PHASE 3
CYK membership check
        ↓
PHASE 4
Derivations + parse tree (JSON)
        ↓
PHASE 5
Flask API
        ↓
PHASE 6
Frontend page + tree drawing
        ↓
PHASE 7
Ambiguity detection
        ↓
PHASE 8
Testing + documentation + final report
```

## Immediate next sprint

```text
1. Create the folder structure and push to GitHub
2. Write grammar.py (read and validate rules)
3. Test grammar parsing with 5 sample grammars
4. Write cnf.py step by step
5. Write cyk.py
6. Test membership on accepted and rejected strings
7. Review and merge each piece
```

---

# 15. Git Workflow for Team Members

Do not develop directly on `main`.

Before starting work:

```powershell
git checkout main
git pull origin main
```

Create a feature branch:

```powershell
git checkout -b feature/cyk-algorithm
```

Branch name examples:

```text
feature/grammar-validation
feature/cnf-conversion
feature/cyk-algorithm
feature/tree-builder
feature/ambiguity
feature/flask-api
feature/frontend-ui
feature/tree-drawing
docs/report
```

Keep one logical feature per branch.

Commit meaningful changes:

```powershell
git add .
git commit -m "Add unit production removal to CNF"
```

Push the branch:

```powershell
git push -u origin feature/cnf-conversion
```

Then open a **Pull Request** on GitHub and ask a teammate to review it.

Recommended flow:

```text
main
  ↓
feature/<module>
  ↓
Pull Request
  ↓
review + testing
  ↓
merge into main
```

After a merge, everyone updates:

```powershell
git checkout main
git pull origin main
```

Keep `main` in a runnable state.

### Fixing a merge conflict

1. Git marks the file with `<<<<<<<`, `=======` and `>>>>>>>`.
2. In VS Code, choose **Accept Current**, **Accept Incoming** or **Accept Both**, or edit by hand.
3. Delete the marker lines, then run:
   ```powershell
   git add .
   git commit -m "Resolve merge conflict"
   git push
   ```

To reduce conflicts, have each person work on different files.

---

# 16. Dependency Rules

Use `requirements.txt` as the source of truth for Python packages.

Install packages inside the virtual environment, then update the file:

```powershell
pip freeze > requirements.txt
```

### Team rule

Only add a dependency when a feature actually needs it.

Do not:

```text
commit .venv
commit .env
commit passwords
commit API keys
install arbitrary versions globally
```

---

# 17. What Each Team Member Can Work On

| Team Area | Main Responsibility | Files |
|---|---|---|
| Algorithms (CNF + CYK) | Grammar reading, CNF conversion, membership check | `grammar.py`, `cnf.py`, `cyk.py` |
| Tree + Ambiguity + API | Derivations, parse tree, ambiguity, Flask routes | `tree.py`, `ambiguity.py`, `app.py` |
| Frontend | Page, forms, API integration, tree drawing, error states | `index.html`, `style.css`, `script.js` |
| QA/Documentation | Test cases, bug reports, diagrams, report, presentation | `backend/tests/`, `docs/`, `README.md` |

Important modules should receive review from another teammate before merging.

### Team

| Name | GitHub | Role |
|---|---|---|
| Your Name | [@gayatriwakale07](https://github.com/gayatriwakale07) | Algorithms (CNF, CYK) |
| Teammate 2 | [@username2](https://github.com/username2) | Tree builder, ambiguity, API |
| Teammate 3 | [@username3](https://github.com/username3) | Frontend and tree drawing |

---

# 18. Definition of Done

A feature is complete only when:

```text
Algorithm gives correct results
        ↓
Edge cases handled (empty string, ε-rules, unit rules)
        ↓
Validation and error messages work
        ↓
API returns the agreed JSON
        ↓
Frontend is integrated
        ↓
Loading/error/empty states handled
        ↓
Test cases pass
        ↓
Documentation updated
        ↓
Code reviewed
        ↓
Feature merged
```

A tree appearing in the browser or an endpoint returning HTTP 200 alone does not mean the feature is complete.

---

# 19. Security and Safety Rules

Never commit:

```text
.env
passwords
secret keys
API keys
.venv
__pycache__
```

Because users type grammars and strings that the backend processes:

- Limit the input size (for example, maximum grammar lines and string length)
- Limit the number of trees generated during ambiguity checking
- Add a time limit so a hard grammar cannot hang the server
- Never use `eval` or `exec` on user input
- Return clear errors instead of raw Python tracebacks
- Restrict CORS to the frontend origin

---

# 20. Testing Plan

Baseline tool: **pytest** for the backend.

```powershell
pytest
```

Keep tests in `backend/tests/`.

### Starter test cases

| Grammar | String | Expected |
|---|---|---|
| `S -> aSb \| ab` | `aabb` | Accepted |
| `S -> aSb \| ab` | `aab` | Rejected |
| `S -> aSb \| ab` | `ab` | Accepted |
| `S -> aSb \| eps` | empty string | Accepted |
| `E -> E+T \| T`, `T -> T*F \| F`, `F -> id` | `id+id*id` | Accepted, not ambiguous |
| `E -> E+E \| E*E \| id` | `id+id*id` | Accepted, ambiguous |
| Rule with two symbols on the left side | any | Validation error |
| Empty grammar | any | Validation error |

The final end-to-end scenario should cover:

```text
Enter grammar and string
        ↓
Click Generate
        ↓
Backend validates and converts to CNF
        ↓
CYK accepts or rejects
        ↓
Derivations + parse tree returned
        ↓
Frontend draws the tree
        ↓
Ambiguity message shown when relevant
```

---

# 21. Current Repository Map

```text
parse-tree-generator/
│
├── backend/
│   ├── app.py             # Flask server and API routes
│   ├── grammar.py         # Read and validate the CFG
│   ├── cnf.py             # Convert grammar to Chomsky Normal Form
│   ├── cyk.py             # CYK algorithm
│   ├── tree.py            # Derivations and parse tree builder
│   ├── ambiguity.py       # Ambiguity detection
│   └── tests/
│
├── frontend/
│   ├── index.html         # Main page
│   ├── style.css          # Styling
│   └── script.js          # API calls and D3.js tree drawing
│
├── docs/
│   ├── api/               # API request/response notes
│   ├── diagrams/          # Architecture and workflow diagrams
│   └── report/            # Project report and presentation
│
├── requirements.txt
├── .gitignore
└── README.md
```

This is the baseline structure. New files should fit these responsibilities rather than creating a new top-level layer without team agreement.

Git does not save empty folders, so keep at least one file (for example `.gitkeep`) in each folder.

---

# 22. New Teammate Quick Start

For a teammate who just cloned the repository:

```powershell
git clone https://github.com/gayatriwakale07/parse-tree-generator.git

cd parse-tree-generator

code .

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Then:

```text
1. Start the backend: python backend/app.py
2. Verify /api/health (once implemented)
3. Start the frontend: cd frontend, then python -m http.server 5500
4. Open http://localhost:5500
5. Create your feature branch from the updated main
```

---

# 23. Before Starting Feature Development

Every teammate should confirm:

```text
[ ] GitHub invitation accepted
[ ] Repository cloned
[ ] VS Code opened at project root
[ ] Git installed and name/email configured
[ ] Python installed
[ ] Virtual environment created and activated
[ ] pip install -r requirements.txt completed
[ ] Backend starts successfully
[ ] Frontend opens in the browser
[ ] Feature branch created from updated main
```

---

# 24. Applications

- **Education:** learning and checking Theory of Computation and compiler design answers
- **Compilers:** every compiler parses code using grammars like these
- **Programming language design:** testing a new language's rules
- **NLP:** analyzing sentence structure
- **Validation:** checking formats such as JSON, XML and SQL

## Advantages

- Saves time compared to drawing parse trees by hand
- Avoids human mistakes
- Makes abstract grammar ideas visual and easy to understand
- Detects ambiguity automatically
- Works for any grammar you give it

---

## Project Principle

Build the system **from correct algorithms toward a polished interface**.

```text
Grammar reading
  ↓
CNF conversion
  ↓
CYK membership
  ↓
Derivations + tree
  ↓
API
  ↓
Frontend drawing
  ↓
Ambiguity + extras
```

Get each algorithm correct and tested before building the screen on top of it.

---

## License

This project is for educational purposes. Add a license (for example MIT) if you plan to share it publicly.

Parse tree generator for Theory of Computation using CFG

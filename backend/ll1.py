"""LL(1) predictive parser: grammar text + input string -> parse tree + steps.

When the grammar or the input is wrong, the exceptions carry helpful extras:
    .suggestions    list of plain-English hints
    .fixed_grammar  a corrected grammar the user can apply (when one can be worked out)
    .fixed_input    a corrected input string (when one can be worked out)
"""
import difflib

EPS = "ε"
EPS_ALIASES = {"ε", "eps", "epsilon", "λ"}
END = "$"
MAX_TOKENS = 100
MAX_STEPS = 5000


class ParserProblem(Exception):
    def __init__(self, message, suggestions=None, fixed_grammar=None, fixed_input=None,
                 pos=None, expected=None):
        super().__init__(message)
        self.suggestions = list(suggestions or [])
        self.fixed_grammar = fixed_grammar
        self.fixed_input = fixed_input
        self.pos = pos
        self.expected = list(expected or [])


class GrammarError(ParserProblem):
    """The grammar text is invalid or is not LL(1)."""


class ParseError(ParserProblem):
    """The input string is not accepted by the grammar."""


# ---------------------------------------------------------------------
# Reading the grammar
# ---------------------------------------------------------------------

def _auto_fix(text):
    """Best-effort repair of common typing mistakes in rule syntax."""
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            out.append(raw)
            continue
        line = line.replace("-->", "->").replace("—>", "->").replace("=>", "->")
        if "->" not in line and "→" not in line:
            for alt in ("::=", ":=", "="):
                if alt in line:
                    line = line.replace(alt, "->", 1)
                    break
        sep = "->" if "->" in line else ("→" if "→" in line else None)
        if sep:
            lhs, rhs = line.split(sep, 1)
            alts = [a.strip() or EPS for a in rhs.split("|")]
            line = f"{lhs.strip()} -> {' | '.join(alts)}"
        out.append(line)
    return "\n".join(out)


def _syntax_problem(text, message, suggestions, fixing):
    fixed = None
    if not fixing:
        candidate = _auto_fix(text)
        if candidate.strip() != text.strip():
            try:
                parse_grammar(candidate, _fixing=True)
                fixed = candidate
            except GrammarError:
                fixed = None
    return GrammarError(message, suggestions, fixed_grammar=fixed)


def parse_grammar(text, _fixing=False):
    rules, order = {}, []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        sep = "->" if "->" in line else ("→" if "→" in line else None)
        if sep is None:
            raise _syntax_problem(text, f"Line {lineno}: the arrow '->' is missing in “{line}”.", [
                "Write each rule as  A -> x y | z : the left side, an arrow, then the alternatives.",
                "Put one rule on each line, for example:  E -> T E'",
            ], _fixing)
        lhs, rhs = (part.strip() for part in line.split(sep, 1))
        if not lhs or " " in lhs:
            found = f"found “{lhs}”" if lhs else "nothing was found"
            raise _syntax_problem(text, f"Line {lineno}: the left side of '->' must be exactly one symbol ({found}).", [
                "Put a single non-terminal before the arrow, for example  E -> T E'.",
                "Symbols are separated by spaces, so  E'  is one symbol but  E '  is two.",
            ], _fixing)
        if lhs not in rules:
            rules[lhs] = []
            order.append(lhs)
        for alt in rhs.split("|"):
            symbols = alt.split()
            if not symbols:
                raise _syntax_problem(text, f"Line {lineno}: one alternative after '->' or '|' is empty.", [
                    "Write ε (or the word eps) for the empty string, for example  A -> x | ε.",
                    "If the '|' at the start or end of the rule is a typo, delete it.",
                ], _fixing)
            if len(symbols) == 1 and symbols[0] in EPS_ALIASES:
                symbols = []
            rules[lhs].append(symbols)
    if not rules:
        raise GrammarError("Enter at least one grammar rule.", [
            "Write one rule per line, for example:  S -> a S b | ε",
            "Separate the symbols with spaces and use | between alternatives.",
        ])
    return rules, order


# ---------------------------------------------------------------------
# FIRST / FOLLOW / table
# ---------------------------------------------------------------------

def _first_seq(seq, rules, first, nullable):
    out = set()
    for sym in seq:
        if sym in rules:
            out |= first[sym]
            if sym not in nullable:
                return out, False
        else:
            out.add(sym)
            return out, False
    return out, True


def _first_follow(rules, start):
    first = {nt: set() for nt in rules}
    nullable = set()
    changed = True
    while changed:
        changed = False
        for nt, prods in rules.items():
            for prod in prods:
                f, null = _first_seq(prod, rules, first, nullable)
                if not f <= first[nt]:
                    first[nt] |= f
                    changed = True
                if null and nt not in nullable:
                    nullable.add(nt)
                    changed = True

    follow = {nt: set() for nt in rules}
    follow[start].add(END)
    changed = True
    while changed:
        changed = False
        for nt, prods in rules.items():
            for prod in prods:
                for i, sym in enumerate(prod):
                    if sym not in rules:
                        continue
                    f, null = _first_seq(prod[i + 1:], rules, first, nullable)
                    add = set(f)
                    if null:
                        add |= follow[nt]
                    if not add <= follow[sym]:
                        follow[sym] |= add
                        changed = True
    return first, follow, nullable


def _compute_table(rules, start):
    """Returns (table, conflict). conflict is (nonterminal, lookahead) or None."""
    first, follow, nullable = _first_follow(rules, start)
    table = {}
    for nt, prods in rules.items():
        for idx, prod in enumerate(prods):
            f, null = _first_seq(prod, rules, first, nullable)
            for t in set(f) | (follow[nt] if null else set()):
                if (nt, t) in table and table[(nt, t)] != idx:
                    return table, (nt, t)
                table[(nt, t)] = idx
    return table, None


def _is_ll1(rules, start):
    return _compute_table(rules, start)[1] is None


# ---------------------------------------------------------------------
# Grammar repairs (left recursion, left factoring)
# ---------------------------------------------------------------------

def _format_grammar(rules):
    width = max(len(nt) for nt in rules)
    lines = []
    for nt, prods in rules.items():
        rhs = " | ".join(" ".join(p) if p else EPS for p in prods)
        lines.append(f"{nt.ljust(width)} -> {rhs}")
    return "\n".join(lines)


def _fresh(name, taken):
    cand = name + "'"
    while cand in taken:
        cand += "'"
    taken.add(cand)
    return cand


def _left_recursive_names(rules):
    return [nt for nt, ps in rules.items() if any(len(p) > 1 and p[0] == nt for p in ps)]


def _eliminate_left_recursion(rules):
    """A -> A a | b   becomes   A -> b A'  and  A' -> a A' | ε."""
    taken = set(rules)
    new = {}
    for nt, prods in rules.items():
        rec = [p[1:] for p in prods if len(p) > 1 and p[0] == nt]
        base = [p for p in prods if not (p and p[0] == nt)]
        if not rec:
            new[nt] = base or prods
            continue
        if not base:
            return None  # every alternative is recursive: cannot be fixed automatically
        nt2 = _fresh(nt, taken)
        new[nt] = [b + [nt2] for b in base]
        new[nt2] = [r + [nt2] for r in rec] + [[]]
    return new


def _left_factor(rules, nt):
    """A -> x a | x b   becomes   A -> x A'  and  A' -> a | b."""
    prods = []
    for p in rules[nt]:
        if p not in prods:
            prods.append(p)
    groups = {}
    for p in prods:
        if p:
            groups.setdefault(p[0], []).append(p)
    group = next((g for g in groups.values() if len(g) > 1), None)
    if group is None:
        return None
    prefix = []
    for symbols in zip(*group):
        if all(s == symbols[0] for s in symbols):
            prefix.append(symbols[0])
        else:
            break
    nt2 = _fresh(nt, set(rules))
    new_prods, placed = [], False
    for p in prods:
        if p in group:
            if not placed:
                new_prods.append(prefix + [nt2])
                placed = True
        else:
            new_prods.append(p)
    new = {}
    for name, ps in rules.items():
        if name == nt:
            new[name] = new_prods
            new[nt2] = [p[len(prefix):] for p in group]
        else:
            new[name] = ps
    return new, prefix, nt2


def _conflict_error(rules, start, nt, lookahead):
    shown = "the end of the input" if lookahead == END else f"'{lookahead}'"
    message = f"This grammar is not LL(1): {nt} has two possible choices when the next symbol is {shown}."
    suggestions, candidate = [], None

    recursive = _left_recursive_names(rules)
    if recursive:
        names = ", ".join(recursive)
        suggestions.append(
            f"Left recursion found in {names} (a rule like  A -> A x ). A top-down parser can't handle it. "
            "Rewrite  A -> A α | β  as  A -> β A'  and  A' -> α A' | ε."
        )
        candidate = _eliminate_left_recursion(rules)
        if candidate is None:
            suggestions.append("Every alternative of a left-recursive rule starts with itself. Add at least one alternative that doesn't.")
    else:
        factored = _left_factor(rules, nt)
        if factored:
            candidate, prefix, nt2 = factored
            suggestions.append(
                f"Several alternatives of {nt} begin with the same symbols ({' '.join(prefix)}). "
                f"Factor that start out:  {nt} -> {' '.join(prefix)} {nt2}  and let {nt2} hold the different endings."
            )
        else:
            suggestions.append(
                f"Make the alternatives of {nt} start with different terminals, "
                f"so the parser can choose using only the next symbol ({shown})."
            )
            suggestions.append("Also check the rules that follow {0}: an ε-alternative overlaps with what can come after it.".format(nt))

    fixed = None
    if candidate:
        fixed = _format_grammar(candidate)
        if not _is_ll1(candidate, start):
            suggestions.append("This rewrite may need one more round: apply it, then generate again to see if more suggestions appear.")
    return GrammarError(message, suggestions, fixed_grammar=fixed)


def build_table(rules, start):
    table, conflict = _compute_table(rules, start)
    if conflict:
        raise _conflict_error(rules, start, *conflict)
    return table


# ---------------------------------------------------------------------
# Parsing the input
# ---------------------------------------------------------------------

def _node(symbol, rules):
    return {"symbol": symbol, "type": "nonterminal" if symbol in rules else "terminal", "children": []}


def _terminals(rules):
    return {s for ps in rules.values() for p in ps for s in p if s not in rules}


def _show(sym):
    return "end of input" if sym == END else sym


def _run(rules, table, start, toks):
    tokens = toks + [END]
    root = _node(start, rules)
    stack, steps, pos = [root], [], 0

    while stack:
        if len(steps) > MAX_STEPS:
            raise ParseError("Parsing took too many steps. Check the grammar for loops.")
        node = stack.pop()
        look = tokens[pos]
        shown = "the end of the input" if look == END else f"'{look}'"

        if node["type"] == "nonterminal":
            idx = table.get((node["symbol"], look))
            if idx is None:
                expected = sorted(t for (nt, t) in table if nt == node["symbol"])
                opening = (f"The input ended unexpectedly while expanding {node['symbol']}."
                           if look == END else f"Unexpected {shown} while expanding {node['symbol']}.")
                raise ParseError(
                    f"{opening} Expected one of: {', '.join(_show(t) for t in expected) or 'nothing'}.",
                    pos=pos, expected=expected,
                )
            prod = rules[node["symbol"]][idx]
            steps.append(f"{node['symbol']} → {' '.join(prod) if prod else EPS}")
            if not prod:
                node["children"] = [{"symbol": EPS, "type": "epsilon", "children": []}]
            else:
                node["children"] = [_node(s, rules) for s in prod]
                stack.extend(reversed(node["children"]))
        else:
            if node["symbol"] != look:
                raise ParseError(f"Expected '{node['symbol']}' but found {shown}.",
                                 pos=pos, expected=[node["symbol"]])
            pos += 1

    if tokens[pos] != END:
        raise ParseError(f"Unexpected '{tokens[pos]}' after the end of a valid string.", pos=pos, expected=[])

    return root, steps


def _accepts(rules, table, start, toks):
    try:
        _run(rules, table, start, toks)
        return True
    except ParseError:
        return False


def _try_split(token, terminals):
    """Split 'id+id' into ['id', '+', 'id'] using the grammar's terminals."""
    by_len = sorted(terminals, key=len, reverse=True)
    memo = {}

    def go(i):
        if i == len(token):
            return []
        if i in memo:
            return memo[i]
        result = None
        for t in by_len:
            if token.startswith(t, i):
                rest = go(i + len(t))
                if rest is not None:
                    result = [t] + rest
                    break
        memo[i] = result
        return result

    return go(0)


def _lookalike_hint(terminals):
    names = [s for s in sorted(terminals) if s[:1].isupper()]
    if not names:
        return []
    listed = ", ".join(f"'{n}'" for n in names)
    if len(names) == 1:
        return [f"{listed} starts with a capital letter but has no rule, so it is treated as a terminal. "
                f"If it should be a non-terminal, add a rule such as  {names[0]} -> ..."]
    return [f"{listed} start with a capital letter but have no rule, so they are treated as terminals. "
            f"If they should be non-terminals, add a rule such as  {names[0]} -> ..."]


def _unknown_symbols_error(terminals, toks):
    unknown = []
    fixed, suggestions, fully_fixed = [], [], True
    for t in toks:
        if t in terminals:
            fixed.append(t)
            continue
        if t not in unknown:
            unknown.append(t)
        parts = _try_split(t, terminals)
        if parts:
            fixed.extend(parts)
            suggestions.append(f"'{t}' looks like several symbols written together. Separate them with spaces:  {' '.join(parts)}")
            continue
        close = difflib.get_close_matches(t, sorted(terminals), n=1, cutoff=0.6)
        if close:
            fixed.append(close[0])
            suggestions.append(f"'{t}' is not used in the grammar. Did you mean '{close[0]}'?")
        else:
            fixed.append(t)
            fully_fixed = False
            suggestions.append(f"'{t}' is not a terminal of this grammar.")
    if terminals:
        suggestions.append("The terminals your grammar uses are: " + ", ".join(sorted(terminals)) + ".")
    suggestions += _lookalike_hint(terminals)
    names = ", ".join(f"'{u}'" for u in unknown)
    return ParseError(
        f"The input contains symbols that the grammar does not use: {names}.",
        suggestions, fixed_input=" ".join(fixed) if fully_fixed else None,
    )


def _find_repairs(rules, table, start, toks, err):
    pos = err.pos
    expected = [t for t in err.expected if t != END][:25]
    cands = []
    if pos < len(toks):
        cands.append((f"Remove '{toks[pos]}' (symbol {pos + 1})", toks[:pos] + toks[pos + 1:]))
    for t in expected:
        where = f"before '{toks[pos]}'" if pos < len(toks) else "at the end"
        cands.append((f"Insert '{t}' {where}", toks[:pos] + [t] + toks[pos:]))
        if pos < len(toks):
            cands.append((f"Replace '{toks[pos]}' with '{t}'", toks[:pos] + [t] + toks[pos + 1:]))
    found = []
    for desc, cand in cands:
        if len(cand) <= MAX_TOKENS and _accepts(rules, table, start, cand):
            found.append((desc, " ".join(cand)))
            if len(found) == 3:
                break
    return found


def _enrich_parse_error(err, rules, table, start, toks):
    suggestions, fixed_input, fixes = [], None, []
    if err.pos is not None:
        expected = [t for t in err.expected]
        if err.expected:
            names = ", ".join(_show(t) for t in expected)
            if err.pos >= len(toks):
                suggestions.append(f"The input ends too early. The grammar still needs one of: {names}.")
            else:
                suggestions.append(f"At symbol {err.pos + 1} ('{toks[err.pos]}') the grammar needs one of: {names}.")
        elif err.pos < len(toks):
            suggestions.append(f"Symbol {err.pos + 1} ('{toks[err.pos]}') is extra: the string was already complete before it.")
        fixes = _find_repairs(rules, table, start, toks, err)
        for desc, text in fixes:
            suggestions.append(f"{desc}:  {text or '(empty string)'}")
        if fixes:
            fixed_input = fixes[0][1]
    if not fixes:
        suggestions.append(f"Check that the string can be built from the start symbol '{start}', and that symbols are separated by spaces.")
    suggestions += _lookalike_hint(_terminals(rules))
    err.suggestions = suggestions
    err.fixed_input = fixed_input
    return err


def parse_input(grammar_text, input_string, start=""):
    rules, order = parse_grammar(grammar_text)
    start = (start or "").strip() or order[0]

    if start not in rules:
        same_letters = next((n for n in order if n.lower() == start.lower()), None)
        close = same_letters or next(iter(difflib.get_close_matches(start, order, n=1, cutoff=0.5)), None)
        hints = []
        if close:
            hints.append(f"Did you mean '{close}'?")
        hints.append(f"Use one of the non-terminals that have a rule: {', '.join(order)}.")
        hints.append(f"Or leave the start symbol empty to use the first rule ('{order[0]}').")
        raise GrammarError(f"Start symbol '{start}' has no rule in the grammar.", hints)

    toks = input_string.split()
    if len(toks) > MAX_TOKENS:
        raise ParseError(f"The input is too long ({len(toks)} symbols).",
                         [f"Use a string with at most {MAX_TOKENS} symbols."])

    table = build_table(rules, start)

    terminals = _terminals(rules)
    if any(t not in terminals for t in toks):
        raise _unknown_symbols_error(terminals, toks)

    try:
        root, steps = _run(rules, table, start, toks)
    except ParseError as err:
        raise _enrich_parse_error(err, rules, table, start, toks)

    return {"tree": root, "steps": steps, "start": start}
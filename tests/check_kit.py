"""Checks that the AI SDR Niche Kit is complete, correct and clean.

Standard library only. Run from anywhere:

    python3 tests/check_kit.py

Exit code 0 means every check passed. Exit code 1 lists each problem found.
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

EXPECTED_NICHES = 50
EXPECTED_CRITERIA = 7
EXPECTED_EXAMPLES = 3
TOOL = str(ROOT / "tools" / "rank.py")

REQUIRED_TEXT_FIELDS = (
    "slug", "name", "category", "buyer", "calls_with", "why_pay", "offer",
    "opening_message", "score_note",
)
REQUIRED_FILES = (
    "README.md", "QUICK-START-PROMPT.md", "PICK-YOUR-NICHE-WORKSHEET.md", "RUBRIC.md",
    "LEADERBOARD.md", "SOURCES.md", "HONEST-LIMITS.md", "CHANGELOG.md", "LICENSE",
    "CLAUDE.md", "AGENTS.md", ".gitignore", ".github/workflows/check.yml",
    ".claude/skills/niche-picker/SKILL.md", ".claude/commands/pick-niche.md",
    "docs/WHY-BOOKED-CALLS.md", "docs/BOOKED-CALL-OFFER-GUIDE.md",
    "docs/SENDING-RULES.md", "docs/TEN-CONVERSATION-TEST.md",
    "examples/README.md", "examples/sample-lead-sheet.csv",
    "tools/niche_lib.py", "tools/rank.py", "tools/build_docs.py",
    "data/niches.json", "data/rubric.json",
)
VALID_GEO = ("global", "us_first", "us_only")
VALID_REGULATED = (None, "health", "finance", "legal")

# Written as code points so this file stays clean.
BANNED_DASHES = {
    0x2010: "a unicode hyphen", 0x2011: "a non breaking hyphen", 0x2012: "a figure dash",
    0x2013: "an en dash", 0x2014: "an em dash", 0x2015: "a horizontal bar",
    0x2212: "a minus sign", 0xFE58: "a small em dash", 0xFE63: "a small hyphen",
    0xFF0D: "a full width hyphen",
}

# Built from parts so this file does not match itself.
SECRET_PATTERNS = [
    ("OpenAI style key", re.compile("s" + r"k-[A-Za-z0-9_\-]{20,}")),
    ("GitHub token", re.compile("gh" + r"[pousr]_[A-Za-z0-9]{30,}")),
    ("AWS access key", re.compile("AK" + r"IA[0-9A-Z]{16}")),
    ("Slack token", re.compile("xo" + r"x[abpr]-[A-Za-z0-9\-]{10,}")),
    ("Private key block", re.compile("-----BEGIN " + r"[A-Z ]*PRIVATE KEY-----")),
    ("Assigned key", re.compile(r"(?i)(api[_ ]?key|secret|token|password)\s*[:=]\s*['\"][A-Za-z0-9_\-]{12,}['\"]")),
]
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
ALLOWED_EMAIL_DOMAINS = ("example.com", "example.org", "example.net")
FORBIDDEN_NAMES = ["sen" + "dora", "ig." + "sen", "ma" + "llard"]

# Numbers that would look like market data must never appear in the niche records.
INVENTED_NUMBER_PATTERNS = [
    ("a percentage", re.compile(r"\d+(\.\d+)?\s*(%|percent)", re.I)),
    ("a money amount", re.compile(r"[$£€₹]\s?\d")),
    ("a money amount in words", re.compile(r"\b\d[\d,]*\s*(dollars|usd|k per|million|billion)\b", re.I)),
    ("a rate claim", re.compile(r"\b(reply|response|open|close|conversion|show) rate\b", re.I)),
    ("a market size claim", re.compile(r"\bmarket size\b|\bstudies show\b|\bon average\b|\baverage deal\b", re.I)),
]

# Vendor names may appear only in the files that use the dated facts.
VENDOR_NAMES = re.compile(r"\b(Salesforce|HubSpot|Agentforce)\b|\bClay\b")
VENDOR_FILES = {
    "README.md", "SOURCES.md", "HONEST-LIMITS.md", "docs/WHY-BOOKED-CALLS.md",
    "tests/check_kit.py", "CHANGELOG.md",
}
TEXT_SUFFIXES = {".md", ".py", ".yml", ".yaml", ".txt", ".json", ".csv", ""}
SKIP_DIRS = {".git", "__pycache__", "results"}


def text_files() -> list[pathlib.Path]:
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.name.startswith("my-"):
            continue  # the viewer's own files, git ignored
        if path.suffix.lower() in TEXT_SUFFIXES and path.name != ".DS_Store":
            files.append(path)
    return files


def run_tool(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, TOOL, *args], capture_output=True, text=True, cwd=str(ROOT), timeout=60
    )


def load_data(errors: list[str]) -> tuple[list[dict], dict]:
    try:
        niches = json.loads((ROOT / "data/niches.json").read_text(encoding="utf-8"))
        rubric = json.loads((ROOT / "data/rubric.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"data files could not be read: {exc}")
        return [], {}
    return niches, rubric


def check_files(errors: list[str]) -> None:
    for name in REQUIRED_FILES:
        if not (ROOT / name).exists():
            errors.append(f"missing {name}")


def check_rubric(rubric: dict, errors: list[str]) -> None:
    criteria = rubric.get("criteria", [])
    if len(criteria) != EXPECTED_CRITERIA:
        errors.append(f"rubric: expected {EXPECTED_CRITERIA} criteria, found {len(criteria)}")
    if sum(c["weight"] for c in criteria) != 20:
        errors.append("rubric: weights must sum to 20 so the maximum total is 100")
    for crit in criteria:
        for field in ("key", "name", "question"):
            if not crit.get(field):
                errors.append(f"rubric: a criterion is missing {field}")
        if sorted(crit.get("anchors", {})) != ["1", "3", "5"]:
            errors.append(f"rubric: {crit.get('key')} needs anchors 1, 3 and 5")


def check_niche_shape(niche: dict, rubric: dict, errors: list[str]) -> None:
    label = niche.get("slug", f"id {niche.get('id')}")
    for field in REQUIRED_TEXT_FIELDS:
        value = niche.get(field)
        if not isinstance(value, str) or len(value.strip()) < 3:
            errors.append(f"{label}: field {field} is empty")
    for field in ("where_to_find", "avoid"):
        items = niche.get(field)
        if not isinstance(items, list) or len(items) < 3 or not all(isinstance(i, str) and i.strip() for i in items):
            errors.append(f"{label}: {field} needs at least 3 items")
    if niche.get("geo") not in VALID_GEO:
        errors.append(f"{label}: geo must be one of {VALID_GEO}")
    if niche.get("regulated") not in VALID_REGULATED:
        errors.append(f"{label}: regulated must be one of {VALID_REGULATED}")
    tags = niche.get("experience_tags") or []
    if not tags:
        errors.append(f"{label}: needs at least one experience tag")
    for tag in tags:
        if tag not in rubric.get("experience_tags", {}):
            errors.append(f"{label}: unknown experience tag {tag}")
    message = niche.get("opening_message", "")
    if "[First name]" not in message or "?" not in message:
        errors.append(f"{label}: opening message needs [First name] and must end on a question")
    if not 25 <= len(message.split()) <= 75:
        errors.append(f"{label}: opening message should be 25 to 75 words, found {len(message.split())}")


def check_scores(niche: dict, rubric: dict, errors: list[str]) -> None:
    label = niche.get("slug", "?")
    scores = niche.get("scores", {})
    keys = [c["key"] for c in rubric.get("criteria", [])]
    if sorted(scores) != sorted(keys):
        errors.append(f"{label}: scores must cover exactly the {len(keys)} criteria")
        return
    for key, value in scores.items():
        if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 5:
            errors.append(f"{label}: score {key} must be a whole number from 1 to 5")
            return
    expected = sum(scores[c["key"]] * c["weight"] for c in rubric["criteria"])
    if niche.get("total") != expected:
        errors.append(f"{label}: total is {niche.get('total')} but the scores add up to {expected}")


def check_niches(niches: list[dict], rubric: dict, errors: list[str]) -> None:
    if len(niches) != EXPECTED_NICHES:
        errors.append(f"data/niches.json: expected exactly {EXPECTED_NICHES} niches, found {len(niches)}")
    if [n.get("id") for n in niches] != list(range(1, len(niches) + 1)):
        errors.append("data/niches.json: ids must run 1, 2, 3 and so on with no gaps")
    for field in ("slug", "name", "buyer", "why_pay", "offer", "opening_message", "score_note"):
        values = [n.get(field) for n in niches]
        if len(set(values)) != len(values):
            errors.append(f"data/niches.json: two niches share the same {field}")
    firsts = [re.split(r"(?<=[.?!])\s", n.get("opening_message", ""))[0] for n in niches]
    if len(set(firsts)) != len(firsts):
        errors.append("data/niches.json: two opening messages start with the same sentence")
    for niche in niches:
        check_niche_shape(niche, rubric, errors)
        check_scores(niche, rubric, errors)
        if niche.get("regulated"):
            note = niche.get("compliance_note", "")
            if len(note) < 60:
                errors.append(f"{niche.get('slug')}: regulated niche needs a real compliance note")
        blob = json.dumps(niche, ensure_ascii=False)
        for name, pattern in INVENTED_NUMBER_PATTERNS:
            found = pattern.search(blob)
            if found:
                errors.append(f"{niche.get('slug')}: contains {name} ({found.group(0)})")


def check_regulated_mix(niches: list[dict], errors: list[str]) -> None:
    for area in ("health", "finance", "legal"):
        if not any(n.get("regulated") == area for n in niches):
            errors.append(f"no niche is marked regulated as {area}")


def check_generated_docs(errors: list[str]) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/build_docs.py"), "--check"],
        capture_output=True, text=True, cwd=str(ROOT), timeout=60,
    )
    if result.returncode != 0:
        errors.append(f"generated docs are out of date: {result.stdout.strip()} {result.stderr.strip()}")


def check_cards(niches: list[dict], errors: list[str]) -> None:
    cards = sorted((ROOT / "niches").glob("*.md")) if (ROOT / "niches").is_dir() else []
    if len(cards) != EXPECTED_NICHES:
        errors.append(f"niches/: expected {EXPECTED_NICHES} cards, found {len(cards)}")
    for niche in niches:
        card = ROOT / "niches" / f"{niche['id']:02d}-{niche['slug']}.md"
        if not card.exists():
            errors.append(f"niches/: missing card for {niche['slug']}")
            continue
        text = card.read_text(encoding="utf-8")
        if niche.get("regulated") and "## Compliance note" not in text:
            errors.append(f"{card.name}: regulated niche card has no compliance note")
        if niche["opening_message"] not in text:
            errors.append(f"{card.name}: opening message missing")


def check_leaderboard(niches: list[dict], errors: list[str]) -> None:
    path = ROOT / "LEADERBOARD.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    rows = re.findall(r"^\| (\d+) \| \[(.+?)\]\(.+?\) \| (\d+) \|", text, flags=re.M)
    if len(rows) != EXPECTED_NICHES:
        errors.append(f"LEADERBOARD.md: expected {EXPECTED_NICHES} rows, found {len(rows)}")
        return
    totals = [int(r[2]) for r in rows]
    if totals != sorted(totals, reverse=True):
        errors.append("LEADERBOARD.md: rows are not sorted by total")
    by_name = {n["name"]: n["total"] for n in niches}
    for _, name, total in rows:
        if by_name.get(name) != int(total):
            errors.append(f"LEADERBOARD.md: {name} shows {total}, data says {by_name.get(name)}")
    if "judgment" not in text.lower():
        errors.append("LEADERBOARD.md: must say the scores are judgment scores")


def check_tool(niches: list[dict], errors: list[str]) -> None:
    import niche_lib  # local import so a missing tool is reported as a check failure

    default = run_tool("--all", "--json")
    if default.returncode != 0:
        errors.append(f"tools/rank.py --all --json failed: {default.stderr.strip()}")
        return
    rows = json.loads(default.stdout)["ranking"]
    if len(rows) != EXPECTED_NICHES:
        errors.append(f"rank.py: expected {EXPECTED_NICHES} rows, got {len(rows)}")
    by_slug = {n["slug"]: n["total"] for n in niches}
    for row in rows:
        if row["fit"] != by_slug.get(row["slug"]):
            errors.append(f"rank.py: default fit for {row['slug']} is {row['fit']}, total is {by_slug.get(row['slug'])}")
    expected_order = sorted(niches, key=lambda n: (-n["total"], n["name"]))
    if [r["slug"] for r in rows] != [n["slug"] for n in expected_order]:
        errors.append("rank.py: default order does not match the data")

    # Changing weights must change the arithmetic in a checkable way.
    only_value = json.loads(run_tool("--all", "--json", "--weights", _zero_all_but("call_value")).stdout)["ranking"]
    for row in only_value:
        niche = next(n for n in niches if n["slug"] == row["slug"])
        if abs(row["fit"] - niche["scores"]["call_value"] * 20) > 0.01:
            errors.append(f"rank.py: weights not applied correctly for {row['slug']}")
            break

    # The experience bonus and the country rule.
    tagged = json.loads(run_tool("--all", "--json", "--know", "manufacturing,engineering").stdout)["ranking"]
    cnc = next(r for r in tagged if r["slug"] == "cnc-machine-shops")
    if cnc["fit"] != 83 + 15:
        errors.append(f"rank.py: two matching tags should add 15, got {cnc['fit']}")
    single = json.loads(run_tool("--all", "--json", "--know", "dental").stdout)["ranking"]
    lab = next(r for r in single if r["slug"] == "dental-laboratories")
    if lab["fit"] != 73 + 10:
        errors.append(f"rank.py: one matching tag should add 10, got {lab['fit']}")
    abroad = json.loads(run_tool("--all", "--json", "--country", "IN").stdout)
    slugs = {r["slug"] for r in abroad["ranking"]}
    us_only = {n["slug"] for n in niches if n["geo"] == "us_only"}
    if slugs & us_only:
        errors.append("rank.py: US only niches should be left out for other countries")
    if {x["slug"] for x in abroad["left_out"]} != us_only:
        errors.append("rank.py: left out list should name the US only niches")
    us_first = next(n for n in niches if n["geo"] == "us_first")
    row = next(r for r in abroad["ranking"] if r["slug"] == us_first["slug"])
    if row["fit"] != us_first["total"] - 10:
        errors.append("rank.py: US first niches should lose 10 points outside the US")

    no_reg = json.loads(run_tool("--all", "--json", "--no-regulated").stdout)["ranking"]
    if any(n["regulated"] for n in niches if n["slug"] in {r["slug"] for r in no_reg}):
        errors.append("rank.py: --no-regulated still shows regulated niches")

    # Overrides are applied through the library and reported.
    profile = {"overrides": {"cnc-machine-shops": {"scores": {"open_field": 1}, "reason": "test"}}}
    changed = niche_lib.rank(niches, niche_lib.load_rubric(), niche_lib.Profile.from_dict(profile, niche_lib.load_rubric()))
    cnc_row = next(r for r in changed["ranking"] if r["slug"] == "cnc-machine-shops")
    if cnc_row["fit"] != 83 - 6 or not cnc_row["overrides"]:
        errors.append("niche_lib: score override was not applied or not reported")

    skip = json.loads(run_tool("--all", "--json", "--skip-area", "health,legal").stdout)["ranking"]
    kept = {n["regulated"] for n in niches if n["slug"] in {r["slug"] for r in skip}}
    if "health" in kept or "legal" in kept or "finance" not in kept:
        errors.append("rank.py: --skip-area did not leave out only the named areas")

    # A report must show the person's changed scores, not the original ones.
    with tempfile.TemporaryDirectory() as folder:
        profile_path = pathlib.Path(folder) / "my-profile.json"
        report_path = pathlib.Path(folder) / "my-report.md"
        profile_path.write_text(json.dumps({"overrides": {"cnc-machine-shops": {"scores": {"findability": 5}, "reason": "test"}}}), encoding="utf-8")
        made = run_tool("--profile", str(profile_path), "--report", str(report_path))
        if made.returncode != 0 or not report_path.exists():
            errors.append("rank.py --report did not write a report")
        else:
            report = report_path.read_text(encoding="utf-8")
            if "| How findable the buyers are | 3 | 5 | 15 |" not in report or "**86**" not in report:
                errors.append("rank.py --report ignores the person's score changes")

    # Bad input must give a plain message, not a traceback.
    for args in (["--weights", "nonsense=3"], ["--weights", _zero_all()], ["--profile", "no-such-file.json"], ["--know", "astronaut"], ["--show", "no-such-niche"], ["--skip-area", "space"], ["--top", "0"]):
        bad = run_tool(*args)
        if bad.returncode == 0 or "Traceback" in bad.stderr:
            errors.append(f"rank.py {' '.join(args)}: should fail politely")

    shown = run_tool("--show", "cnc-machine-shops")
    if shown.returncode != 0 or "CNC machine shops" not in shown.stdout:
        errors.append("rank.py --show did not print the niche card")
    printed = run_tool("--top", "3")
    if printed.returncode != 0 or "judgment" not in printed.stdout.lower():
        errors.append("rank.py must print that the scores are judgment scores")


def _zero_all_but(keep: str) -> str:
    rubric = json.loads((ROOT / "data/rubric.json").read_text(encoding="utf-8"))
    return ",".join(f"{c['key']}={1 if c['key'] == keep else 0}" for c in rubric["criteria"])


def _zero_all() -> str:
    rubric = json.loads((ROOT / "data/rubric.json").read_text(encoding="utf-8"))
    return ",".join(f"{c['key']}=0" for c in rubric["criteria"])


def check_examples(errors: list[str]) -> None:
    folders = sorted(p for p in (ROOT / "examples").glob("example-*") if p.is_dir())
    if len(folders) != EXPECTED_EXAMPLES:
        errors.append(f"examples: expected {EXPECTED_EXAMPLES} worked examples, found {len(folders)}")
    for folder in folders:
        for name in ("profile.json", "RANKING.txt", "WORKSHEET-FILLED.md"):
            if not (folder / name).exists():
                errors.append(f"{folder.name}: missing {name}")
                break
        else:
            profile = json.loads((folder / "profile.json").read_text(encoding="utf-8"))
            if "SYNTHETIC" not in profile.get("label", ""):
                errors.append(f"{folder.name}: profile.json is not labelled SYNTHETIC")
            if "SYNTHETIC" not in (folder / "WORKSHEET-FILLED.md").read_text(encoding="utf-8"):
                errors.append(f"{folder.name}: worksheet is not labelled SYNTHETIC")
            result = run_tool("--profile", str((folder / "profile.json").relative_to(ROOT)), "--top", "10")
            if result.returncode != 0:
                errors.append(f"{folder.name}: profile did not run: {result.stderr.strip()}")
            elif result.stdout.strip() != (folder / "RANKING.txt").read_text(encoding="utf-8").strip():
                errors.append(f"{folder.name}: RANKING.txt does not match the tool output")
    sheet = ROOT / "examples/sample-lead-sheet.csv"
    if sheet.exists() and "SYNTHETIC" not in sheet.read_text(encoding="utf-8"):
        errors.append("examples/sample-lead-sheet.csv: not labelled SYNTHETIC")


def check_skill(errors: list[str]) -> None:
    skill = ROOT / ".claude/skills/niche-picker/SKILL.md"
    if skill.exists():
        text = skill.read_text(encoding="utf-8")
        if not re.match(r"---\nname: niche-picker\ndescription: .+\n---\n", text):
            errors.append("SKILL.md: needs name and description frontmatter")
        if "tools/rank.py" not in text:
            errors.append("SKILL.md: must use tools/rank.py")
    command = ROOT / ".claude/commands/pick-niche.md"
    if command.exists() and not command.read_text(encoding="utf-8").startswith("---\ndescription:"):
        errors.append("pick-niche.md: needs description frontmatter")
    prompt = ROOT / "QUICK-START-PROMPT.md"
    if prompt.exists():
        text = prompt.read_text(encoding="utf-8")
        if "```text" not in text or "tools/rank.py" not in text:
            errors.append("QUICK-START-PROMPT.md: needs a paste in block that runs the tool")
    readme = ROOT / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        if "50" not in text or "judgment" not in text.lower():
            errors.append("README.md: must state 50 niches and that scores are judgment scores")


def check_links(errors: list[str]) -> None:
    for path in text_files():
        if path.suffix != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)\s]+)\)", text):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            if not (path.parent / target.split("#")[0]).resolve().exists():
                errors.append(f"{path.relative_to(ROOT)}: broken link to '{target}'")


def check_clean_text(errors: list[str]) -> None:
    for path in text_files():
        rel = path.relative_to(ROOT)
        rel_text = rel.as_posix()
        text = path.read_text(encoding="utf-8")
        if rel_text != "tests/check_kit.py" and VENDOR_NAMES.search(text) and rel_text not in VENDOR_FILES:
            errors.append(f"{rel}: vendor names are only allowed in the files that use the dated facts")
        for lineno, line in enumerate(text.splitlines(), 1):
            for code, name in BANNED_DASHES.items():
                if chr(code) in line:
                    errors.append(f"{rel}:{lineno}: contains {name}")
            stripped = line.lstrip("- ").strip()
            if path.suffix == ".md" and " - " in stripped and "|" not in stripped:
                errors.append(f"{rel}:{lineno}: a spaced hyphen is used as a dash")
            for name, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    errors.append(f"{rel}:{lineno}: looks like a {name}")
            for email in EMAIL_PATTERN.findall(line):
                if not email.lower().endswith(ALLOWED_EMAIL_DOMAINS):
                    errors.append(f"{rel}:{lineno}: contains an email address ({email})")
            if rel_text != "tests/check_kit.py":
                for name in FORBIDDEN_NAMES:
                    if name in line.lower():
                        errors.append(f"{rel}:{lineno}: contains a name that must stay out of this kit")


def check_vendor_facts(errors: list[str]) -> None:
    """Only the sourced facts may appear: no price for Hunter, and the HubSpot price only as sourced."""
    for path in text_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel == "tests/check_kit.py":
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if "Hunter" in line and re.search(r"[$£€₹]\s?\d", line):
                errors.append(f"{rel}: a price appears next to Hunter")
            if "HubSpot" in line and re.search(r"\$\s?\d", line) and "$1" not in line:
                errors.append(f"{rel}: a HubSpot price other than the sourced one")


def check_github_links(errors: list[str]) -> None:
    pattern = re.compile(r"github\.com/onittindwani-ai/[A-Za-z0-9_.-]+(/[^\s)\"']+)")
    for path in text_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel == "tests/check_kit.py":
            continue
        found = pattern.search(path.read_text(encoding="utf-8"))
        if found:
            errors.append(f"{rel}: GitHub link must stop at the repo name ({found.group(0)})")


def check_readme_counts(niches: list[dict], errors: list[str]) -> None:
    """Numbers written by hand in the README and CHANGELOG must match the data."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\| (\d+) \| ([^|\[]+?) \| (\d+) \|$", readme, flags=re.M)
    top = sorted(niches, key=lambda n: (-n["total"], n["name"]))[:10]
    if [(n["name"], n["total"]) for n in top] != [(r[1], int(r[2])) for r in rows]:
        errors.append("README.md: the top 10 table does not match the data")
    regulated = sum(1 for n in niches if n.get("regulated"))
    if f"| {regulated} |" not in readme:
        errors.append(f"README.md: regulated count should be {regulated}")
    for name in ("HONEST-LIMITS.md", "CHANGELOG.md"):
        if f"{regulated} " not in (ROOT / name).read_text(encoding="utf-8"):
            errors.append(f"{name}: regulated count should be {regulated}")


CHECKS = (
    check_github_links, check_links, check_clean_text, check_vendor_facts, check_generated_docs,
    check_examples, check_skill,
)


def main() -> int:
    errors: list[str] = []
    check_files(errors)
    niches, rubric = load_data(errors)
    if niches and rubric:
        check_rubric(rubric, errors)
        check_niches(niches, rubric, errors)
        check_regulated_mix(niches, errors)
        check_cards(niches, errors)
        check_leaderboard(niches, errors)
        check_readme_counts(niches, errors)
        try:
            check_tool(niches, errors)
        except (ImportError, OSError, ValueError, KeyError, StopIteration) as exc:
            errors.append(f"tool check could not run: {type(exc).__name__}: {exc}")
    for check in CHECKS:
        try:
            check(errors)
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            errors.append(f"{check.__name__} could not run: {type(exc).__name__}: {exc}")

    regulated = sum(1 for n in niches if n.get("regulated"))
    print(f"Niches: {len(niches)} ({regulated} regulated)")
    print(f"Criteria: {len(rubric.get('criteria', []))}")
    if niches:
        print(f"Totals range: {min(n['total'] for n in niches)} to {max(n['total'] for n in niches)}")
    print(f"Niche cards: {len(list((ROOT / 'niches').glob('*.md'))) if (ROOT / 'niches').is_dir() else 0}")
    print(f"Worked examples: {len(list((ROOT / 'examples').glob('example-*')))}")
    print(f"Text files scanned: {len(text_files())}")
    if errors:
        print(f"\nFAILED with {len(errors)} problem(s):")
        for err in errors:
            print(f"  {err}")
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

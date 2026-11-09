#!/usr/bin/env python3
"""Rank the 50 niches for one person. Standard library only.

Usage:
    python3 tools/rank.py                                  top 10 with the published weights
    python3 tools/rank.py --all                            all 50
    python3 tools/rank.py --know trades,facilities --country US
    python3 tools/rank.py --weights call_value=6,open_field=4
    python3 tools/rank.py --no-regulated
    python3 tools/rank.py --skip-area health,legal
    python3 tools/rank.py --profile my-profile.json --report my-niche-report.md
    python3 tools/rank.py --show cnc-machine-shops
    python3 tools/rank.py --list-tags
    python3 tools/rank.py --list-criteria

It only reads the data and prints a ranking. --report writes one local Markdown file. It sends nothing.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any, Dict, List, Mapping

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import niche_lib as lib  # noqa: E402


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank the 50 AI SDR niches for you. Scores are judgment scores, not market data.")
    parser.add_argument("--profile", help="a JSON profile file, for example examples/example-1-field-tech-ohio/profile.json")
    parser.add_argument("--know", help="comma separated experience tags, see --list-tags")
    parser.add_argument("--country", help="the country your customers are in, for example US, UK or IN")
    parser.add_argument("--weights", help="changes to the weights, for example call_value=6,open_field=4")
    parser.add_argument("--no-regulated", action="store_true", help="leave out health, finance and legal niches")
    parser.add_argument("--skip-area", help="leave out only these regulated areas, for example health,legal")
    parser.add_argument("--top", type=int, default=10, help="how many rows to print (default 10)")
    parser.add_argument("--all", action="store_true", help="print every niche")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a table")
    parser.add_argument("--report", help="also write a Markdown report of your top 3 to this file")
    parser.add_argument("--show", help="print the full card of one niche by its slug")
    parser.add_argument("--list-tags", action="store_true", help="print the experience tags")
    parser.add_argument("--list-criteria", action="store_true", help="print the criteria and default weights")
    return parser.parse_args(argv)


def parse_weights(text: str) -> Dict[str, float]:
    weights: Dict[str, float] = {}
    for part in filter(None, (piece.strip() for piece in text.split(","))):
        if "=" not in part:
            raise lib.KitError(f"Could not read '{part}'. Write weights like call_value=6,open_field=4.")
        key, value = part.split("=", 1)
        try:
            weights[key.strip()] = float(value)
        except ValueError:
            raise lib.KitError(f"The weight in '{part}' is not a number.") from None
    return weights


def build_profile(args: argparse.Namespace, rubric: Mapping[str, Any]) -> lib.Profile:
    data = dict(lib.load_profile(args.profile, rubric)) if args.profile else {}
    if args.know:
        data["experience_tags"] = [tag.strip() for tag in args.know.split(",") if tag.strip()]
    if args.country:
        data["country"] = args.country
    if args.weights:
        data["weights"] = {**data.get("weights", {}), **parse_weights(args.weights)}
    if args.no_regulated:
        data["exclude_regulated"] = True
    if args.skip_area:
        data["exclude_regulated_areas"] = [area.strip() for area in args.skip_area.split(",") if area.strip()]
    return lib.Profile.from_dict(data, rubric)


def show_number(value: float) -> str:
    return str(lib.clean_number(value))


def format_table(result: Mapping[str, Any], profile: lib.Profile, limit: int) -> str:
    lines = ["AI SDR Niche Kit ranking", result["note"]]
    if profile.label:
        lines.append(f"Profile: {profile.label}")
    lines.append("Experience tags: " + (", ".join(profile.experience_tags) or "none given"))
    lines.append("Customers in: " + (profile.country or "not given (no location change)"))
    lines.append("Weights: " + ", ".join(f"{key}={show_number(value)}" for key, value in result["weights"].items()))
    lines.extend(["", f"{'Rank':<5}{'Fit':<7}{'Base':<7}{'Exp':<5}{'Geo':<5}{'Reg':<9}Niche"])
    for row in result["ranking"][:limit]:
        regulated = row["regulated"] or "no"
        lines.append(
            f"{row['rank']:<5}{show_number(row['fit']):<7}{show_number(row['base']):<7}"
            f"{row['experience_bonus']:<5}{row['location_adjustment']:<5}{regulated:<9}{row['name']}  [{row['slug']}]"
        )
        for change in row["overrides"]:
            lines.append(f"     You changed {change['criterion']} from {change['was']} to {change['now']}: {change['reason']}")
    lines.append("")
    lines.append(f"Showing {min(limit, len(result['ranking']))} of {len(result['ranking'])} ranked niches.")
    if result["left_out"]:
        lines.append(f"Left out: {len(result['left_out'])}.")
        lines.extend(f"  {item['name']}: {item['reason']}" for item in result["left_out"])
    lines.append("Fit = Base (your weights, out of 100) + Exp (your experience) + Geo (your country). Fit can go above 100.")
    return "\n".join(lines)


def build_report(result: Mapping[str, Any], niches: list, rubric: Mapping[str, Any], profile: lib.Profile) -> str:
    lines = ["# My top 3 AI SDR niches", "", result["note"], ""]
    if profile.label:
        lines += [f"Profile: {profile.label}", ""]
    lines += ["Experience tags: " + (", ".join(profile.experience_tags) or "none given"),
              "", "Customers in: " + (profile.country or "not given"), ""]
    for row in result["ranking"][:3]:
        niche = lib.find_niche(niches, row["slug"])
        lines += [f"# {row['rank']}. {row['name']}", "",
                  f"Fit {show_number(row['fit'])} = base {show_number(row['base'])}, experience {row['experience_bonus']}, country {row['location_adjustment']}", ""]
        lines += [f"You changed {c['criterion']} from {c['was']} to {c['now']}: {c['reason']}" for c in row["overrides"]]
        if row["overrides"]:
            lines.append("")
        if row["overrides"]:
            lines += ["Your score changes are included below. The Total in the table uses the published weights, so it can differ from your Fit.", ""]
        lines += [lib.niche_body(lib.with_scores(niche, row["scores"], rubric), rubric), ""]
    lines += ["# Next step", "", "Before you buy anything, run docs/TEN-CONVERSATION-TEST.md on your first pick and fill in PICK-YOUR-NICHE-WORKSHEET.md.", ""]
    return "\n".join(lines)


def print_tags(rubric: Mapping[str, Any]) -> None:
    for tag, meaning in rubric["experience_tags"].items():
        print(f"{tag:<16}{meaning}")


def print_criteria(rubric: Mapping[str, Any]) -> None:
    for crit in rubric["criteria"]:
        print(f"{crit['key']:<20}weight {crit['weight']:<3}{crit['name']}")


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    if args.top < 1:
        raise lib.KitError("--top must be 1 or higher.")
    rubric = lib.load_rubric()
    niches = lib.load_niches()
    if args.list_tags:
        print_tags(rubric)
        return 0
    if args.list_criteria:
        print_criteria(rubric)
        return 0
    if args.show:
        niche = lib.find_niche(niches, args.show)
        print(f"# {niche['name']}\n\n{lib.NOTE}\n\n{lib.niche_body(niche, rubric)}")
        return 0
    profile = build_profile(args, rubric)
    result = lib.rank(niches, rubric, profile)
    limit = len(result["ranking"]) if args.all else args.top
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_table(result, profile, limit))
    if args.report:
        pathlib.Path(args.report).write_text(build_report(result, niches, rubric, profile), encoding="utf-8")
        if not args.json:
            print(f"Wrote your top 3 to {args.report}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except lib.KitError as exc:
        print(f"Problem: {exc}", file=sys.stderr)
        sys.exit(2)

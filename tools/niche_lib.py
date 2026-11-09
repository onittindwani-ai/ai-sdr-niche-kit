"""Core library for the AI SDR Niche Kit. Standard library only, Python 3.9 or newer.

It loads the 50 niches and the rubric, applies a person's weights, experience and country, and returns a
ranking. Nothing here sends anything, calls a network or changes a file. Every score is a judgment score
against RUBRIC.md, not market data.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

ROOT = pathlib.Path(__file__).resolve().parent.parent
NICHES_PATH = ROOT / "data" / "niches.json"
RUBRIC_PATH = ROOT / "data" / "rubric.json"
NOTE = "Scores are judgment scores against RUBRIC.md, not market data."
REGULATED_AREAS = ("health", "finance", "legal")
US_NAMES = {"US", "USA", "U.S.", "U.S.A.", "UNITED STATES", "UNITED STATES OF AMERICA", "AMERICA"}


class KitError(Exception):
    """A problem a person can fix. The message says what to do."""


def _read_json(path: pathlib.Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise KitError(f"Could not find {path}. Check the path and try again.") from None
    except json.JSONDecodeError as exc:
        raise KitError(f"{path} is not valid JSON (line {exc.lineno}): {exc.msg}.") from None


def load_rubric(path: pathlib.Path = RUBRIC_PATH) -> Dict[str, Any]:
    return _read_json(path)


def load_niches(path: pathlib.Path = NICHES_PATH) -> list:
    return _read_json(path)


def default_weights(rubric: Mapping[str, Any]) -> Dict[str, float]:
    return {c["key"]: c["weight"] for c in rubric["criteria"]}


def criterion_keys(rubric: Mapping[str, Any]) -> list:
    return [c["key"] for c in rubric["criteria"]]


def is_us(country: Optional[str]) -> bool:
    return country is not None and country.strip().upper() in US_NAMES


def clean_number(value: float) -> float:
    """Round to 1 decimal and drop a trailing .0 so whole scores stay whole."""
    rounded = round(float(value), 1)
    return int(rounded) if rounded == int(rounded) else rounded


def merged_weights(rubric: Mapping[str, Any], changes: Optional[Mapping[str, Any]]) -> Dict[str, float]:
    """Return a new weights dict with the changes applied over the defaults."""
    weights = default_weights(rubric)
    for key, value in (changes or {}).items():
        if key not in weights:
            names = ", ".join(weights)
            raise KitError(f"Unknown criterion '{key}'. Use one of: {names}.")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            raise KitError(f"The weight for {key} must be a number that is 0 or higher.")
        weights = {**weights, key: value}
    if sum(weights.values()) <= 0:
        raise KitError("At least one weight must be above 0.")
    return weights


def _clean_tags(rubric: Mapping[str, Any], tags: Sequence[str]) -> Tuple[str, ...]:
    known = rubric["experience_tags"]
    for tag in tags:
        if tag not in known:
            raise KitError(f"Unknown experience tag '{tag}'. See the list with: python3 tools/rank.py --list-tags")
    return tuple(tags)


def _clean_overrides(rubric: Mapping[str, Any], overrides: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    keys = criterion_keys(rubric)
    cleaned = {}
    for slug, change in overrides.items():
        if not isinstance(change, Mapping) or not isinstance(change.get("scores"), Mapping):
            raise KitError(f"The override for {slug} needs a 'scores' object.")
        for key, value in change["scores"].items():
            if key not in keys:
                raise KitError(f"The override for {slug} names an unknown criterion '{key}'.")
            if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 5:
                raise KitError(f"The override for {slug} must give {key} a whole number from 1 to 5.")
        if not str(change.get("reason", "")).strip():
            raise KitError(f"The override for {slug} needs a reason, so you can check it later.")
        cleaned[slug] = {"scores": dict(change["scores"]), "reason": str(change["reason"]).strip()}
    return cleaned


@dataclass(frozen=True)
class Profile:
    """A person's choices. Frozen, so a ranking can never change it."""

    weights: Mapping[str, float]
    experience_tags: Tuple[str, ...] = ()
    country: Optional[str] = None
    exclude_regulated: bool = False
    exclude_regulated_areas: Tuple[str, ...] = ()
    exclude_slugs: Tuple[str, ...] = ()
    overrides: Mapping[str, Dict[str, Any]] = field(default_factory=dict)
    label: str = ""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any], rubric: Mapping[str, Any]) -> "Profile":
        allowed = {"weights", "experience_tags", "country", "exclude_regulated", "exclude_regulated_areas", "exclude_slugs", "overrides", "label"}
        unknown = sorted(set(data) - allowed)
        if unknown:
            raise KitError(f"Unknown profile field: {', '.join(unknown)}. Allowed: {', '.join(sorted(allowed))}.")
        country = data.get("country") or None
        areas = tuple(data.get("exclude_regulated_areas") or ())
        for area in areas:
            if area not in REGULATED_AREAS:
                raise KitError(f"Unknown regulated area '{area}'. Use one of: {', '.join(REGULATED_AREAS)}.")
        return cls(
            weights=merged_weights(rubric, data.get("weights")),
            experience_tags=_clean_tags(rubric, data.get("experience_tags") or ()),
            country=str(country).strip() if country else None,
            exclude_regulated=bool(data.get("exclude_regulated", False)),
            exclude_regulated_areas=areas,
            exclude_slugs=tuple(data.get("exclude_slugs") or ()),
            overrides=_clean_overrides(rubric, data.get("overrides") or {}),
            label=str(data.get("label", "")),
        )


def load_profile(path: str, rubric: Mapping[str, Any]) -> Dict[str, Any]:
    data = _read_json(pathlib.Path(path))
    if not isinstance(data, dict):
        raise KitError(f"{path} must hold one JSON object.")
    Profile.from_dict(data, rubric)
    return data


def weighted_score(scores: Mapping[str, int], weights: Mapping[str, float]) -> float:
    """Score out of 100. With the published weights this equals the stored total."""
    top = 5 * sum(weights.values())
    return clean_number(sum(scores[key] * weight for key, weight in weights.items()) / top * 100)


def experience_bonus(niche: Mapping[str, Any], profile: Profile, rubric: Mapping[str, Any]) -> Tuple[int, Tuple[str, ...]]:
    matched = tuple(tag for tag in niche["experience_tags"] if tag in profile.experience_tags)
    rules = rubric["fit_rules"]
    if len(matched) >= 2:
        return rules["experience_bonus_two_or_more_tags"], matched
    if len(matched) == 1:
        return rules["experience_bonus_one_tag"], matched
    return 0, matched


def location_adjustment(niche: Mapping[str, Any], profile: Profile, rubric: Mapping[str, Any]) -> Optional[int]:
    """0 for no change, a negative number for a penalty, or None when the niche does not apply."""
    if profile.country is None or is_us(profile.country):
        return 0
    return rubric["fit_rules"]["geo"][niche["geo"]]["outside_us_adjustment"]


def _exclusion_reason(niche: Mapping[str, Any], profile: Profile, rubric: Mapping[str, Any]) -> Optional[str]:
    if niche["slug"] in profile.exclude_slugs:
        return "You asked to leave this one out."
    if niche["regulated"] and (profile.exclude_regulated or niche["regulated"] in profile.exclude_regulated_areas):
        return f"Regulated ({niche['regulated']}) and you chose to leave those out."
    if location_adjustment(niche, profile, rubric) is None:
        return "Depends on US law or US programs, and your customers are outside the US."
    return None


def _row(niche: Mapping[str, Any], profile: Profile, rubric: Mapping[str, Any]) -> Dict[str, Any]:
    change = profile.overrides.get(niche["slug"])
    scores = {**niche["scores"], **(change["scores"] if change else {})}
    base = weighted_score(scores, profile.weights)
    bonus, matched = experience_bonus(niche, profile, rubric)
    adjustment = location_adjustment(niche, profile, rubric) or 0
    return {
        "slug": niche["slug"],
        "name": niche["name"],
        "category": niche["category"],
        "card": f"niches/{niche['id']:02d}-{niche['slug']}.md",
        "regulated": niche["regulated"],
        "geo": niche["geo"],
        "base": base,
        "experience_bonus": bonus,
        "location_adjustment": adjustment,
        "fit": clean_number(base + bonus + adjustment),
        "matched_tags": list(matched),
        "scores": scores,
        "overrides": [
            {"criterion": key, "was": niche["scores"][key], "now": value, "reason": change["reason"]}
            for key, value in (change["scores"].items() if change else ())
        ],
    }


def rank(niches: Sequence[Mapping[str, Any]], rubric: Mapping[str, Any], profile: Profile) -> Dict[str, Any]:
    """Return the ranking as new data. The inputs are never changed."""
    known = {n["slug"] for n in niches}
    for slug in list(profile.overrides) + list(profile.exclude_slugs):
        if slug not in known:
            raise KitError(f"Unknown niche '{slug}'. See the slugs in LEADERBOARD.md.")
    left_out = []
    rows = []
    for niche in niches:
        reason = _exclusion_reason(niche, profile, rubric)
        if reason:
            left_out.append({"slug": niche["slug"], "name": niche["name"], "reason": reason})
        else:
            rows.append(_row(niche, profile, rubric))
    ordered = sorted(rows, key=lambda r: (-r["fit"], -r["base"], r["name"]))
    ranking = [{"rank": index, **row} for index, row in enumerate(ordered, 1)]
    return {"note": NOTE, "weights": dict(profile.weights), "ranking": ranking, "left_out": left_out}


def find_niche(niches: Sequence[Mapping[str, Any]], slug: str) -> Mapping[str, Any]:
    for niche in niches:
        if niche["slug"] == slug:
            return niche
    raise KitError(f"Unknown niche '{slug}'. See the slugs in LEADERBOARD.md.")


def with_scores(niche: Mapping[str, Any], scores: Mapping[str, int], rubric: Mapping[str, Any]) -> Dict[str, Any]:
    """A new niche record using these scores, with the total recalculated at the published weights."""
    total = sum(scores[c["key"]] * c["weight"] for c in rubric["criteria"])
    return {**niche, "scores": dict(scores), "total": total}


def niche_body(niche: Mapping[str, Any], rubric: Mapping[str, Any]) -> str:
    """The shared Markdown body of a niche, used by the cards and the report."""
    lines = [
        "## Who the buyer is", "", niche["buyer"], "",
        "## Who the booked calls are with", "", niche["calls_with"], "",
        "## Why they would pay for booked calls", "", niche["why_pay"], "",
        "## A ready offer", "", niche["offer"], "",
        "## Opening message", "",
        "Replace every part in square brackets with something true you found yourself. Never send it with a detail you made up.", "",
        f"> {niche['opening_message']}", "",
        "## Where to find the leads", "", *[f"- {item}" for item in niche["where_to_find"]], "",
        "## What to avoid", "", *[f"- {item}" for item in niche["avoid"]], "",
    ]
    if niche.get("compliance_note"):
        lines += ["## Compliance note", "", niche["compliance_note"], ""]
    lines += ["## Scores", "", "| Criterion | Weight | Score | Points |", "| --- | --- | --- | --- |"]
    for crit in rubric["criteria"]:
        score = niche["scores"][crit["key"]]
        lines.append(f"| {crit['name']} | {crit['weight']} | {score} | {score * crit['weight']} |")
    lines += [f"| **Total** | | | **{niche['total']}** |", "", f"Why these scores: {niche['score_note']}", ""]
    return "\n".join(lines)

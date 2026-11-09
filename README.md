# AI SDR Niche Kit

**50 niches for an AI SDR business, each scored on a published rubric, with a ready offer, an opening message, and a tool that re ranks all 50 for your own experience and country.**

An AI SDR (an AI sales development rep) is software that finds leads and starts sales conversations. This kit is for people building a business around one. The big software companies now sell this as a product, so the idea here is different: stop selling a tool, and sell booked calls in 1 niche you know really well, to owners who have no sales team. See [why booked calls](docs/WHY-BOOKED-CALLS.md).

All scores in this kit are **judgment scores** against [the rubric](RUBRIC.md). They are not market data. Nothing here promises results.

## Quick start: paste one prompt

Open Claude Code in this folder and paste the prompt in [QUICK-START-PROMPT.md](QUICK-START-PROMPT.md). It asks about your background, re scores the 50 for you, and picks your top 3.

Or, once the folder is open in Claude Code, type:

```text
/pick-niche
```

No Claude Code? It works by hand too. You only need Python 3.9 or newer, with nothing to install:

```bash
python3 tools/rank.py --know trades,facilities --country US --top 10
```

Then fill in the [worksheet](PICK-YOUR-NICHE-WORKSHEET.md).

## What is inside

| Part | Count | Where |
| --- | --- | --- |
| Niches, each one a structured record | 50 | [data/niches.json](data/niches.json) |
| Readable niche cards: buyer, why they would pay, offer, opening message, where to find leads, what to avoid, scores | 50 | [niches](niches) |
| Scoring criteria with written meanings | 7 | [RUBRIC.md](RUBRIC.md) |
| Ranked leaderboard, generated from the data | 1 | [LEADERBOARD.md](LEADERBOARD.md) |
| Pick your niche worksheet | 1 | [PICK-YOUR-NICHE-WORKSHEET.md](PICK-YOUR-NICHE-WORKSHEET.md) |
| Paste in Claude Code quick start prompt | 1 | [QUICK-START-PROMPT.md](QUICK-START-PROMPT.md) |
| Claude Code skill and command | 1 of each | [.claude/skills/niche-picker](.claude/skills/niche-picker/SKILL.md), [.claude/commands](.claude/commands/pick-niche.md) |
| Ranking tool, standard library Python | 1 | [tools/rank.py](tools/rank.py) |
| Worked examples, invented people, labelled synthetic | 3 | [examples](examples/README.md) |
| Guides: why booked calls, offer, sending rules, 10 conversation test | 4 | [docs](docs) |
| Regulated niches with a compliance note (health, finance, legal) | 16 | marked in the [leaderboard](LEADERBOARD.md) |
| Sources and honest limits | 2 | [SOURCES.md](SOURCES.md), [HONEST-LIMITS.md](HONEST-LIMITS.md) |

## The top 10 with the default weights

Your own top 10 will differ, which is the point. The full table is in [LEADERBOARD.md](LEADERBOARD.md).

| Rank | Niche | Total out of 100 |
| --- | --- | --- |
| 1 | CNC machine shops selling to engineers | 83 |
| 2 | Commercial kitchen exhaust hood cleaning companies | 82 |
| 3 | Commercial flat roof repair contractors | 81 |
| 4 | Custom metal fabrication shops | 81 |
| 5 | Small third party logistics warehouses for ecommerce brands | 81 |
| 6 | Land surveying firms | 80 |
| 7 | Small plastic injection molders | 80 |
| 8 | CMMC compliance consultants for defense subcontractors | 79 |
| 9 | Commercial electrical contractors doing tenant fit outs | 79 |
| 10 | Fire extinguisher and sprinkler inspection companies | 79 |

## How to use the tool

```bash
python3 tools/rank.py                                  # top 10, default weights
python3 tools/rank.py --all                            # all 50
python3 tools/rank.py --list-tags                      # the experience tags
python3 tools/rank.py --know logistics --country IN    # your experience and your customers' country
python3 tools/rank.py --weights call_value=6,open_field=4
python3 tools/rank.py --no-regulated                   # leave out health, finance, legal
python3 tools/rank.py --show cnc-machine-shops         # one full card
python3 tools/rank.py --profile my-profile.json --report my-niche-report.md
```

Files that start with `my-` are ignored by git, so your own notes stay on your computer.

## Honest limits

- **Judgment scores, not data.** One person scored the 50 using the written rubric. You should change any score you disagree with.
- **No numbers invented.** The kit has no market sizes, deal values, response rates or earnings, because we do not have real ones to give you.
- **Not legal advice.** Regulated niches carry a compliance note. A note is a warning to go and check, not permission. Read the [sending rules](docs/SENDING-RULES.md) before you email anyone.
- **The tool only ranks.** Nothing in this kit sends, posts or messages anyone.
- **Independent.** This kit is not made or endorsed by Salesforce, HubSpot, Clay, LinkedIn or any company named in it.

More in [HONEST-LIMITS.md](HONEST-LIMITS.md). Product facts were checked on 2026-11-09 and are listed in [SOURCES.md](SOURCES.md).

## Check the kit yourself

```bash
python3 tests/check_kit.py
```

It confirms there are exactly 50 niches, that every total matches its scores, that the tool behaves, and that the files are clean. It runs on every push through GitHub Actions.

You can also download the zip from the latest release.

## Licence

MIT. See [LICENSE](LICENSE). Use it, change it and share it.

Made by Onit Tindwani.

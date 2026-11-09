# Worked examples

**Everything in this folder is synthetic.** The people, companies, addresses and answers are invented to show how the kit is used. None of them are real, and none of this is evidence that a niche works.

| Example | Who (invented) | What it shows |
| --- | --- | --- |
| [Example 1](example-1-field-tech-ohio/WORKSHEET-FILLED.md) | A former commercial HVAC technician in Ohio | Experience and a personal score change decide the top pick |
| [Example 2](example-2-practice-manager-manchester/WORKSHEET-FILLED.md) | A former dental practice manager in Manchester | A regulated niche, outside the US, with extra care needed |
| [Example 3](example-3-ops-lead-bengaluru/WORKSHEET-FILLED.md) | A logistics operations lead in Bengaluru | Selling by email only from another country, with different weights |

Each folder has:

- `profile.json`: the input to the tool.
- `RANKING.txt`: the exact output of the tool for that profile. `tests/check_kit.py` confirms it still matches.
- `WORKSHEET-FILLED.md`: the [worksheet](../PICK-YOUR-NICHE-WORKSHEET.md), filled in as that person might.

Try one yourself:

```bash
python3 tools/rank.py --profile examples/example-1-field-tech-ohio/profile.json --top 10
```

[sample-lead-sheet.csv](sample-lead-sheet.csv) shows columns you might use for a lead list, filled with invented rows on example.com addresses.

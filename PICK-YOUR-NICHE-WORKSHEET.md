# Pick your niche worksheet

Work through this by hand, or let Claude Code fill it in with the [quick start prompt](QUICK-START-PROMPT.md). It should take about 30 minutes. Copy it to `my-worksheet.md` so your answers stay out of git.

See [example answers](examples/README.md) from 3 invented people.

## Step 1. What do you actually know?

The goal is 1 niche you know really well. List real experience only.

| Job or industry | How long | What you know that an outsider would not |
| --- | --- | --- |
| | | |
| | | |
| | | |

Experience tags that truly apply to you (from `python3 tools/rank.py --list-tags`):

## Step 2. Who do you already know?

Write the names of business owners you could talk to this week, even through a friend.

| Name | Their business | How you know them |
| --- | --- | --- |
| | | |
| | | |
| | | |

## Step 3. Where are you, and where are your customers?

- I work from:
- My customers would be in:
- Is my time zone workable for their office hours? (yes or no)
- Do I understand the email rules in that country? (read [the sending rules](docs/SENDING-RULES.md))

## Step 4. What are you willing to deal with?

- Will I work in regulated niches (health, finance, legal)? (yes or no)
- If yes, who will review my messages and my deal?
- Am I willing to reach out to owners who are out in the field and slow on email? (yes or no)

## Step 5. Set your weights

The defaults are in [the rubric](RUBRIC.md). Change them only if you have a reason.

| Criterion | Default | My weight | Why |
| --- | --- | --- | --- |
| Owner has no sales team | 4 | | |
| Value of one booked call | 4 | | |
| How findable the buyers are | 3 | | |
| How reachable by email | 3 | | |
| Seasonality (steady all year scores high) | 2 | | |
| Compliance risk (low risk scores high) | 2 | | |
| How crowded (a quiet market scores high) | 2 | | |

## Step 6. Run the ranking and write your top 3

```bash
python3 tools/rank.py --know YOUR,TAGS --country CUSTOMER_COUNTRY --weights YOUR=WEIGHTS --top 10
```

| Rank | Niche | Fit score | Why it suits me | Biggest risk |
| --- | --- | --- | --- | --- |
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

## Step 7. Argue with the scores

Read the card for each of your top 3. Which score do you disagree with, based on something you know?

| Niche | Criterion | Score in the kit | My score | My reason |
| --- | --- | --- | --- | --- |
| | | | | |
| | | | | |

## Step 8. The gut check

Answer yes or no for your first pick.

- I could spend a year talking to these owners and not get bored.
- I can name a specific problem they have without looking it up.
- I can build a list of 50 of them from public sources in an afternoon.
- I can build a list of the people they want to reach.
- I know what counts as a good booked call for them.
- I could explain the offer on the niche card in my own words.

If you answered no to 2 or more, go to your second pick and answer again.

## Step 9. My decision

- The niche I will test first:
- The 10 owners I will talk to first: use the [10 conversation test](docs/TEN-CONVERSATION-TEST.md).
- The date I will decide whether to continue:
- What result would make me stop:

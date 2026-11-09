# The 10 conversation test

The scores in this kit are one person's judgment. Your first real data comes from talking to owners. Do this before you buy tools, domains or data.

## What to do

1. Pick your first niche from the [worksheet](../PICK-YOUR-NICHE-WORKSHEET.md).
2. List 10 owners in that niche. Start with people you know, then people you can be introduced to.
3. Ask each for 15 minutes. Say that you are researching and not selling anything yet, and mean it.
4. Ask the questions below and write down their exact words.

## The questions

1. How do new customers find you today?
2. Who does the selling here? How many hours a week does it really get?
3. When did you last try to get more customers on purpose? What did you try, and what happened?
4. What is one good new customer worth to you, over the time they usually stay?
5. Who exactly would you want to be talking to, if I could put them on your calendar?
6. What would make a call a waste of your time?
7. How many more calls could you actually take in a month?
8. Have you paid anyone for leads or calls before? How did that go?
9. Who else gets asked to help with this? Do people pitch you often?
10. If someone reliably put the right people on your calendar, what would you expect that to cost?

## How to read the answers

Count these across your 10 conversations. These are thresholds for you to decide on, not industry numbers.

| Signal | Good sign | Warning sign |
| --- | --- | --- |
| Who sells | The owner, in spare moments | There is a salesperson already |
| Value of a customer | Clearly more than you plan to charge | The owner cannot say, or it is small |
| Capacity | They can take more work | They are fully booked |
| Target customer | They can describe them precisely | They say "anyone" |
| Past experience | They tried something and can say why it failed | They were burned and will not try again |
| Budget | They name a figure you could live with | They expect it to be free |

Before you begin, write down what result would make you continue, and what would make you stop. Decide this first, so you cannot move the goalposts afterwards.

## After the 10

- Update your scores with what you learned, in `my-profile.json` under `overrides`.
- Re run `python3 tools/rank.py --profile my-profile.json --top 10`.
- If the niche holds up, offer a short pilot to the owner who sounded most ready. See the [offer guide](BOOKED-CALL-OFFER-GUIDE.md).
- If it does not, go to your second pick. A niche you dropped after 10 conversations has cost you very little.

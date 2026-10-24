# Voice and copy

AeroPulse talks to a traveller with a booking tab open, a reporter on deadline, and a
researcher reading the method. Write for the first; don't lose the other two.

## Rules

- **Plain words.** "Higher than usual", "2 weeks out", "cheapest fare". Not "elevated",
  "T+14", "fare class".
- **Sentence case** everywhere, including buttons and headings.
- **Describe the past.** "Fares were usually lowest 3 to 5 weeks before departure." Never
  "will", "expected to", "book now", "prices are about to".
- **Numbers carry their basis.** Next to any figure: how many prices, which day, and a link
  to how it is measured.
- **Buttons say what happens.** "Download CSV", "Copy citation". The result uses the same
  verb: "Copied".
- **Empty and error states give direction.** Say what is missing and what to do. Don't
  apologise.
- **Demo data is always named.** "Demo data. These fares are synthetic, not real prices."

## Words

| Use | Avoid |
|---|---|
| fare, price | ticket cost, tariff |
| usual | normal, average (unless you mean the mean) |
| higher / lower than usual | expensive / cheap (judgement), spike (unless it is one) |
| within a week, 1–2 weeks out | T+7, short window |
| route | sector, city pair (in UI) |
| 95% range | confidence interval (UI); CI is fine in docs |

Generated sentences live in `web/src/lib/copy.ts` and `web/src/lib/insight.ts` for the
website, and `src/aeropulse/render/text.py` for chart images and feeds. Change them there, not
in page components.

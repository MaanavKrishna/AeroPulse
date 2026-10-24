# Design

The site borrows its visual language from **aeronautical en-route charts**: cool chart paper,
ink, a fine latitude/longitude grid, thin airway lines, airport symbols labelled with their
codes. It should read like a well-made reference document, not a marketing page.

## Principles

1. **Answer first, in words.** The home page leads with "Yes, higher than usual." The numbers
   sit in a ruled strip under the sentence, not in a giant figure with a coloured pill.
2. **One memorable thing.** The route chart is the signature. Everything around it stays
   quiet: hairlines, type, white space.
3. **Structure is information.** A heavy rule opens a section. A light rule separates rows.
   Borders only where things differ. No decorative numbering, eyebrows or dividers.
4. **Colour encodes fares, nothing else.** Blue is cheaper than usual, vermilion is dearer,
   grey is usual. Ink is for interaction (buttons, current tab). Colour is always paired
   with a word or a mark (▲ ▼ ●).
5. **Motion answers the reader.** One arrival per page: the selected airway draws in, the
   chart sweeps to today. After that, motion only responds to a hover, a click or a route
   change. The one plane on the chart is the only continuous motion, and it stops under
   reduced motion.

## Things we do not do

These are the commonest signs of a generated page. They are out unless a real need argues
for them:

- dark hero with stars, glows, radial gradient washes or neon lines;
- frosted glass, drop shadows and blur;
- identical rounded cards in a grid;
- a big number with a small label and a delta pill as the hero;
- small all-caps labels above headings;
- count-up numbers, pulsing rings, scroll-triggered fade-ins on every section;
- arrows appended to link text; middle dots joining metadata.

## Tokens

All colour, type and spacing tokens live in `src/aeropulse/web/static/css/tokens.css`, with
a light "chart paper" palette and a dark "night chart" palette. Charts read the same tokens,
so they follow the theme automatically.

| Token | Use |
|---|---|
| `--paper`, `--surface` | Page and panel backgrounds |
| `--ink`, `--ink-muted`, `--ink-faint` | Text, rules, chart labels |
| `--grid`, `--airway` | Graticule, usual-fare airways |
| `--r-cool-2` … `--r-warm-2` | The fare scale, cheaper to dearer |
| `--cool-ink`, `--warm-ink` | Text-safe versions of the scale ends (4.5:1 on paper) |

## Type

Anek Latin (by Ek Type, an Indian foundry) for everything on screen; its width axis sets the
airport codes wide. Source Serif 4 for long reading (method, about). Numbers use tabular
figures. Rupees use Indian digit grouping (₹1,24,500).

## Checking a change

Screenshot the home page, a route page and a festival page at 390px and 1440px, in light and
dark, before opening a pull request. Pages must work with JavaScript off and with reduced
motion on.

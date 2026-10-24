# Design

The site borrows its visual language from **airport wayfinding**: dark sign panels, signal
yellow, simple pictograms and big, legible type. Travellers already know how to read an
airport sign at a glance; AeroPulse should feel just as easy to find your way around.

## Principles

1. **Answer first, in words.** Every route view leads with a sentence ("Yes, higher than
   usual."), then the numbers, then the chart.
2. **Signs for structure, colour for fares.** Dark sign panels open pages and hold the main
   answer. Yellow means "you can act here": the selected tab, the primary button, section
   tiles. Blue (cheaper than usual) and orange (dearer than usual) are kept for fares alone,
   and always come with a word or a mark (▲ ▼ ●).
3. **One pictogram per idea.** Each section gets a pictogram from `Pictogram.tsx`, used the
   same way everywhere: calendar for booking windows, clock for timing, shield for ethics,
   data for downloads. Add a pictogram before reusing one for a different meaning.
4. **Cards hold one thing.** A card is one route, one file, one question. Lists of like
   things share a card; different things get their own.
5. **Motion answers the reader.** Each page has one arrival (the chart wipes in, the selected
   airway draws, the plane takes off). After that, motion responds to a click, hover or
   route change: tab backgrounds slide (`layoutId`), answers cross-fade, FAQ answers open in
   place. Everything respects reduced motion (`MotionConfig reducedMotion="user"`).

## Things we do not do

- frosted glass, glows, neon gradients, starfields;
- a big number with a small label and a delta pill as the hero;
- small all-caps labels above headings;
- scroll-triggered fade-ins on every section, count-ups on unrelated numbers;
- decorative numbering (numbers only for real sequences, like the six method steps);
- arrows appended to link text; middle dots joining metadata.

## Tokens

All colour, type and spacing tokens live in `web/src/styles/tokens.css`, with light and dark
palettes. The `.sign` class re-maps text and surface tokens for content on a dark panel, so
components work on both without extra props. Charts read the same tokens.

| Token | Use |
|---|---|
| `--paper`, `--paper-deep`, `--surface` | Page background, insets, cards |
| `--sign`, `--sign-2`, `--sign-ink` | Sign panels and their text |
| `--yellow`, `--yellow-ink` | Selection, primary actions, section tiles |
| `--ink`, `--ink-muted`, `--ink-faint` | Text and chart labels |
| `--r-cool-2` … `--r-warm-2` | The fare scale, cheaper (blue) to dearer (orange) |
| `--cool-ink`, `--warm-ink` | Text-safe versions of the scale ends (4.5:1) |
| `--cat-1` … `--cat-4` | Series colours on the compare chart |
| `--radius`, `--shadow` | Cards |

## Type

Anek Latin (by Ek Type, an Indian foundry) for everything on screen; its width axis sets
airport codes wide, like departure boards. Source Serif 4 for long reading. Numbers use
tabular figures. Rupees use Indian digit grouping (₹1,24,500).

## Checking a change

Screenshot the home page, a route page and one inner page at 390px and 1440px, in light and
dark, before opening a pull request. Turn on reduced motion and check nothing important
depends on animation. `npm run lint` must pass; it includes accessibility rules.

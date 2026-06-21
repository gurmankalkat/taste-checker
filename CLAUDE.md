# CLAUDE.md — Quiet-Floor: an undertone-coherence floor probe

## What this project is

A small, honest probe testing whether a current vision model can detect a
specific color-coherence FLOOR violation in neutral ("quiet luxury") outfits,
judged against human-authored ground truth. Built as a portfolio artifact for a
role at Taste Labs, a company building taste/judgment infrastructure for AI.

The artifact's job is to surface and measure the GAP between model judgment and
human judgment, and report it honestly, including where the model is blind.

## The single most important constraint (do not violate)

**Human judgment is the ground truth. The model is the thing being checked
against it, never the reverse.** Any design that lets the model define what
"correct" taste is defeats the entire purpose. We measure the model against the
human, find where it falls short, and say so plainly.

## Floor vs ceiling (the conceptual spine)

We test the FLOOR (combinations almost any trained eye agrees are broken), not
the CEILING (which of two good looks is better). Floor violations have high
human agreement, which is what makes them defensible with a single labeler.

## Scope — locked, do not expand

- Domain: neutral / quiet-luxury palettes only.
- **Exactly ONE violation category: `undertone_clash`** — warm-family and
  cool-family neutrals presented as if they should match. This is the only
  violation we label, test, and score. It was chosen because it is the floor
  violation that is BOTH high-agreement AND numerically defensible via the
  CIELAB b* (blue-yellow) axis. Items are therefore either `clean` or
  `undertone_clash`. The task is binary.
- ~25–30 items total. This is a probe, not a benchmark, and the writeup says so.

### LABELING RULE (hard rule)

Only label an item `undertone_clash` if you can NAME the warm piece and the cool
piece. If the eye says "off" but the temperature direction can't be stated, the
item is excluded, not labeled. Naming the warm and cool piece is the defense
line. Any clash that can't be decomposed that way has drifted into the
muddy_midtone territory that was deliberately cut.

### Deliberately EXCLUDED (named in the writeup as reasoned scope decisions,
### NOT built — each exclusion is itself evidence of judgment):

- `muddy_midtone` (two near-but-off neutrals in the same value band).
  EXCLUDED because distinguishing a failed match from intentional subtle tonal
  dressing has genuinely low inter-rater agreement, so a single labeler cannot
  call it defensibly. This is the line where the floor ends and the ceiling
  begins, and naming it is a finding.
- `value_no_anchor` (everything floating at one mid lightness). EXCLUDED as too
  close to the ceiling: deliberate soft monochrome and "flat/unanchored" overlap.
- Patterns. EXCLUDED as near-ceiling and not reducible to dominant-color math.

## Resist these failure modes

- Do NOT build a web app or any UI. The substance is the data, the measurement,
  and the writeup. A slick interface is the demo-polish trap.
- Do NOT add categories back in. The strength of this artifact is that EVERY
  labeled violation is defensible by both eye and number. A second, softer
  category would reintroduce the "trust my taste" attack surface.
- Do NOT let the model probe prompt vary per image. One fixed prompt for all
  items, or the test is meaningless.
- Do NOT let scoring become subjective free-text grading. The model must return
  a STRUCTURED verdict so scoring is mechanical and the author's thumb is off
  the scale.

## Files

- `items.py` — Ground-truth item list. Each item: id, image path, label
  (`clean` or `undertone_clash`), a ONE-sentence human reasoning that names the
  temperature conflict, and source (`real` or `controlled`). Replace seed items
  with ~25–30 real labeled items. This file is the center of gravity.
- `colorlib.py` — Dominant-color extraction + LAB-based warm/cool classification
  + warm/cool family-mix detection. Prints raw b* so calls are inspectable. For
  an `undertone_clash` item, the warm and cool dominant colors should land on
  opposite sides of b*=0; that is how you back the label with numbers. Colors
  within a small neutral band of b*=0 are reported as "ambiguous" rather than
  forced, and close calls are surfaced honestly.
- `probe.py` — TO BUILD. Blind structured-output vision probe (see spec).
- `score.py` — **AUTHOR THIS YOURSELF.** The intellectual core. You must be
  able to defend every line in an interview (see spec).
- `chart.py` — TO BUILD. One clear chart of the results (see spec).
- `WRITEUP.md` — TO BUILD. The point of view (see required sections).

## probe.py spec

- Read items from `items.py`.
- For each item, send the image + ONE fixed prompt to the Anthropic Messages
  API (vision-capable model). Read the API key from env var `ANTHROPIC_API_KEY`.
- The prompt asks the model to judge whether the neutral palette coheres and
  return STRUCTURED JSON:
  `{ "verdict": "clean" | "flawed", "is_undertone_clash": true | false,
     "reasoning": "<one sentence>" }`
- The model MUST NOT see the human labels or reasoning. It judges blind.
- Save raw model outputs to `output/model_verdicts.json` so runs are auditable.
- Be robust: if the model returns non-JSON, capture the raw text and mark the
  item unparsed rather than crashing.

## score.py spec — YOU AUTHOR THIS

The task is binary, so compute two SEPARATE axes (keep them separate, that is
the point):

1. **Detection agreement.** On the clean-vs-flawed call, how often does the
   model agree with the human label? Report overall, and break out the false
   positive rate (model calls a clean item flawed) separately from the miss rate
   (model calls an undertone_clash item clean). The miss rate is the headline:
   it is the slop the model lets through.
2. **Localization.** Among items the human labeled `undertone_clash` AND the
   model called flawed, how often did the model specifically attribute it to an
   undertone/temperature conflict (its `is_undertone_clash` field) versus
   flagging "something off" without locating it? A model can pass axis 1 on
   vibes while failing axis 2; that gap is the finding.

Optionally correlate model misses with the `colorlib` b* gap for each item: the
prediction is that the model catches large-temperature-gap clashes and misses
small-gap ones, and that boundary is your point of view.

Design questions to answer in code comments (interviewers will ask):
- How do you handle a model false positive on a clean item, and why does it
  belong in a different bucket than a miss?
- How do you avoid your own bias when judging whether the model "located" the
  violation? (Rely on the structured `is_undertone_clash` field, not on
  interpreting the model's prose.)

## chart.py spec

One clear chart, saved to `output/agreement.png`. Show detection agreement with
miss rate and false-positive rate distinguished, and the localization rate.
Plain and readable, no decoration for its own sake. Define the small data
structure it expects from score.py and document it.

## WRITEUP.md required sections

- What I measured, and why a single, binary, numerically-backed floor violation
  over a broad taste score.
- The agreement numbers + the chart, read honestly. Lead with the miss rate.
- Where the model is blind: the b*-gap boundary where it stops catching clashes.
- **Where this breaks / what's next.** Cover: the three reasoned exclusions
  above (muddy_midtone, value_no_anchor, patterns) and WHY each was cut, the
  single-labeler limitation, and what a real validation would add (a curated
  rater panel + inter-rater reliability). This section is what separates a
  candidate from a fan. It proves you can see your own method's floor and tell
  it from the ceiling.

## Style rules for any prose/copy

No em dashes, no semicolons, no colons in message/copy prose. Avoid "feasible,"
"augmented," "revamped." Prefer strong action verbs. No mission-statement or
founder-worship language anywhere a Taste Labs reader might see it.

## Setup

```
pip install pillow scikit-learn scikit-image numpy matplotlib anthropic
export ANTHROPIC_API_KEY=...   # your key, never commit it
```

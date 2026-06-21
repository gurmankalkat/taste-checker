# Quiet-Floor

A probe: can a current vision model detect undertone-clash floor violations in
neutral outfits, judged against human ground truth? Built to surface the gap
between model and human judgment, not to paper over it.

## Run order
1. Put labeled images in images/ and fill items.py with ~25-30 real items.
2. python probe.py   - blind model probe -> output/model_verdicts.json
3. python score.py   - detection agreement + localization (you author this)
4. python chart.py   - output/agreement.png
5. Write WRITEUP.md  - the point of view.

## Setup
    pip install pillow scikit-learn scikit-image numpy matplotlib anthropic
    export ANTHROPIC_API_KEY=...

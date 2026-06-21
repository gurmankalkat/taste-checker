"""
Fill-in helper: run colorlib over every item's image and print the measured
color profile plus a suggested b_note. This is how you fill b_note HONESTLY,
from measurement, never from memory or copied from another item.

Usage:
    python profile_items.py

For each item it prints:
  - every dominant color's hex, warm/cool call, and b* value
  - whether the warm and cool families are mixed (the numeric clash signature)
  - a suggested b_note string you can paste into items.py

If an item is labeled undertone_clash but the math says NOT mixed, you get a
loud warning. That is the tool checking your eye (and catching filter tricks or
mislabels). Investigate before keeping the label.
"""

import os
import colorlib as cl
from items import ITEMS


def suggest_note(profile, split, label):
    sig = [p for p in profile if p["weight"] >= 0.10]
    warm = [p for p in sig if p["warm_cool"] == "warm"]
    cool = [p for p in sig if p["warm_cool"] == "cool"]
    amb = [p for p in sig if p["warm_cool"] == "ambiguous"]

    if split["mixed"]:
        w = max(warm, key=lambda p: p["weight"])
        c = max(cool, key=lambda p: p["weight"])
        return f"clash confirmed by math: warm {w['b_star']} vs cool {c['b_star']}"
    if label == "undertone_clash":
        # eye says clash, math did not confirm: note where the cool side landed
        near = amb or cool
        if near:
            n = min(near, key=lambda p: abs(p["b_star"]))
            return (f"SUBTLE gap, a side (b*={n['b_star']}) inside ambiguous band; "
                    f"eye sees clash, math stays quiet")
        return "math did not detect a warm-cool split; CHECK this label"
    # clean item
    fams = "/".join(split["families"])
    return f"all one family ({fams}); resolves"


def main():
    for it in ITEMS:
        path = it["image"]
        print("=" * 70)
        print(f"{it['id']}   [{it['label']}]   source={it.get('source','?')}")
        if not os.path.exists(path):
            print(f"  !! image not found: {path}  (add it to images/ first)")
            continue
        profile = cl.profile_item(path, k=4)
        split = cl.temperature_split(profile)
        for p in profile:
            if p["weight"] >= 0.05:
                print(f"   {p['hex']}  {p['warm_cool']:9} b*={p['b_star']:6}  w={p['weight']}")
        print(f"   families={split['families']}  mixed={split['mixed']}")
        if it["label"] == "undertone_clash" and not split["mixed"]:
            print("   *** WARNING: labeled undertone_clash but math says NOT mixed."
                  " Eye-only call, or mislabel/filter. Investigate. ***")
        print(f'   suggested b_note: "{suggest_note(profile, split, it["label"])}"')


if __name__ == "__main__":
    main()

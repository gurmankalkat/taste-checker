"""
Color extraction and warm-cool classification.

Honest design note: warm-vs-cool is itself a judgment. Rather than hide that
behind a hardcoded hue cutoff, we convert each dominant color to CIELAB and
read the b* axis (negative = blue/cool, positive = yellow/warm). We print the
raw b* value and flag close calls, so the classification is inspectable, not
asserted. This is the move that lets you back an undertone-clash label with
numbers instead of "trust my eye."
"""

import numpy as np
from PIL import Image
from sklearn.cluster import KMeans
from skimage import color as skcolor

# b* values inside this band are too close to call warm vs cool.
# Surface these in the writeup rather than pretending the rule is crisp.
NEUTRAL_B_BAND = 4.0


def dominant_colors(image_path, k=4, resize=200):
    """Return k dominant RGB colors (0-255) sorted by cluster size, with weights."""
    img = Image.open(image_path).convert("RGB")
    img.thumbnail((resize, resize))
    pixels = np.asarray(img).reshape(-1, 3)
    km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(pixels)
    counts = np.bincount(km.labels_, minlength=k)
    order = np.argsort(counts)[::-1]
    centers = km.cluster_centers_[order].astype(int)
    weights = (counts[order] / counts.sum())
    return centers, weights


def warm_cool(rgb):
    """
    Classify a single RGB color on the warm-cool axis via CIELAB b*.
    Returns (verdict, b_value). verdict in {"warm","cool","ambiguous"}.
    """
    rgb01 = np.array(rgb, dtype=float).reshape(1, 1, 3) / 255.0
    lab = skcolor.rgb2lab(rgb01)[0, 0]
    b = float(lab[2])  # blue(-) <-> yellow(+)
    if abs(b) < NEUTRAL_B_BAND:
        return "ambiguous", b
    return ("warm" if b > 0 else "cool"), b


def hex_of(rgb):
    return "#{:02x}{:02x}{:02x}".format(*[int(c) for c in rgb])


def profile_item(image_path, k=4):
    """Full color profile for one item: dominant hexes + warm/cool calls."""
    centers, weights = dominant_colors(image_path, k=k)
    out = []
    for c, w in zip(centers, weights):
        verdict, b = warm_cool(c)
        out.append({
            "hex": hex_of(c),
            "rgb": [int(x) for x in c],
            "weight": round(float(w), 3),
            "warm_cool": verdict,
            "b_star": round(b, 1),
        })
    return out


def temperature_split(profile, min_weight=0.10):
    """
    Does this item mix warm and cool families among its meaningful colors?
    Returns dict with families present and a boolean 'mixed' flag.
    This is the numeric backbone of an undertone_clash claim.
    """
    sig = [p for p in profile if p["weight"] >= min_weight]
    fams = {p["warm_cool"] for p in sig}
    return {
        "families": sorted(fams),
        "has_warm": "warm" in fams,
        "has_cool": "cool" in fams,
        "mixed": ("warm" in fams) and ("cool" in fams),
    }

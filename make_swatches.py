"""
Generate controlled swatch items for the undertone-coherence probe.

These are FLAT COLOR BLOCKS, not garments. They exist to anchor the set with
exact, defensible color values: each undertone_clash pairs a warm-family neutral
(b* > 0) with a cool-family neutral (b* < 0) at a known temperature gap, and each
clean item keeps all blocks in one family. We print every block's b* so the
label is backed by numbers, not assertion.

LIMITATION (state this in the writeup): swatches remove texture, lighting and
styling, so they are the EASY case for a model. They calibrate the probe; real
garment photos must carry the rest of the set or you are only testing color
theory, not slop detection.
"""

import os
import numpy as np
from PIL import Image
from skimage import color as skcolor


def lab_to_rgb255(L, a, b):
    lab = np.array([[[L, a, b]]], dtype=float)
    rgb = skcolor.lab2rgb(lab)[0, 0]
    return tuple(int(round(np.clip(c, 0, 1) * 255)) for c in rgb)


def b_star(rgb):
    rgb01 = np.array(rgb, dtype=float).reshape(1, 1, 3) / 255.0
    return float(skcolor.rgb2lab(rgb01)[0, 0][2])


def make_swatch(path, colors, size=(600, 400)):
    """Render N vertical blocks of the given RGB colors into one image."""
    w, h = size
    img = np.zeros((h, w, 3), dtype=np.uint8)
    n = len(colors)
    for i, c in enumerate(colors):
        x0 = int(i * w / n)
        x1 = int((i + 1) * w / n)
        img[:, x0:x1] = c
    Image.fromarray(img).save(path)


# Each neutral defined in LAB so its temperature is exact and intentional.
# L = lightness, a = green/red (kept low for neutrals), b = blue(-)/yellow(+).
NEUTRALS = {
    # warm family (b* clearly positive)
    "cream":    (88, 2, 16),
    "camel":    (68, 8, 34),
    "tobacco":  (40, 10, 26),
    "warm_beige":(80, 4, 20),
    # cool family (b* clearly negative)
    "dove_grey":(66, 0, -4),
    "cool_taupe":(70, 1, -3),
    "oyster":   (86, -1, -2),
    "charcoal": (32, 0, -2),
    "blue_grey":(60, -2, -8),
}


def build(out_dir="images"):
    os.makedirs(out_dir, exist_ok=True)
    rgb = {k: lab_to_rgb255(*v) for k, v in NEUTRALS.items()}

    # (id, label, [color keys], reasoning)
    SPEC = [
        ("sw_clean_warm", "clean", ["cream", "camel", "tobacco"],
         "Cream, camel and tobacco are all warm-family neutrals stepped light to dark, so the palette resolves as one choice."),
        ("sw_clean_cool", "clean", ["oyster", "dove_grey", "charcoal"],
         "Oyster, dove grey and charcoal are all cool-based with a clear value range, so the tonal stack resolves."),
        ("sw_clash_camel_bluegrey", "undertone_clash", ["camel", "blue_grey"],
         "A warm camel sits against a cool blue-grey as if matched, so the two neutrals fight on the warm-cool axis."),
        ("sw_clash_warmbeige_cooltaupe", "undertone_clash", ["warm_beige", "cool_taupe"],
         "A yellow-based warm beige is paired with a grey-based cool taupe at similar lightness, a near-match that diverges on undertone."),
        ("sw_clash_cream_oyster", "undertone_clash", ["cream", "oyster"],
         "Two off-whites that look matched but split on temperature, warm cream against cool oyster, so the pairing reads slightly wrong."),
    ]

    rows = []
    for item_id, label, keys, reasoning in SPEC:
        cols = [rgb[k] for k in keys]
        path = os.path.join(out_dir, f"{item_id}.jpg")
        make_swatch(path, cols)
        bvals = {k: round(b_star(rgb[k]), 1) for k in keys}
        rows.append((item_id, label, keys, bvals, reasoning, path))
    return rows


if __name__ == "__main__":
    for item_id, label, keys, bvals, reasoning, path in build():
        fams = " ".join(f"{k}(b*={bvals[k]})" for k in keys)
        print(f"{item_id:32} {label:16} {fams}")

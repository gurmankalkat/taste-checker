"""
Blind, structured-output vision probe for the undertone-coherence floor test.

Usage:
    export ANTHROPIC_API_KEY=your_key_here
    python probe.py

Sends each item's image to the Anthropic vision API with one fixed prompt.
The model never sees human labels or reasoning — it judges blind.
Raw outputs are saved to output/model_verdicts.json for auditability.
"""

import base64
import json
import os
import pathlib
import sys

import anthropic

from items import ITEMS

MODEL = "claude-opus-4-8"

# One fixed prompt for every item. Never changes between items.
# Defines the vocabulary (undertone_clash) so the model can name it,
# but passes no per-item hints, labels, or human reasoning.
PROBE_PROMPT = """\
You are evaluating a neutral / quiet-luxury outfit for color coherence.

Look at the outfit in the image. Judge whether the neutral colors cohere \
or whether there is a floor-level violation.

A floor violation means the combination is broken in a way that most trained \
eyes agree on — not a matter of personal preference. The specific violation \
to watch for is an undertone clash: a warm-family neutral (ivory, cream, camel, \
warm beige, warm tan, warm grey with yellow/orange undertones) paired as a match \
with a cool-family neutral (cool white, ash grey, blue-grey, cool taupe with \
blue/purple undertones). These undertones fight each other.

Respond with ONLY valid JSON and nothing else:
{"verdict": "clean" | "flawed", "is_undertone_clash": true | false, "reasoning": "<one sentence>"}

Rules:
- verdict "clean" means the palette coheres, no floor violation present
- verdict "flawed" means a floor violation is present
- is_undertone_clash must be true if and only if the flaw is specifically a warm/cool undertone conflict
- reasoning is exactly one sentence describing what you observe
- Do not include any text outside the JSON object"""


def load_image_b64(path: str) -> tuple[str, str]:
    ext = pathlib.Path(path).suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_types.get(ext, "image/jpeg")
    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, media_type


def probe_item(client: anthropic.Anthropic, item: dict) -> dict:
    item_id = item["id"]
    image_path = item["image"]

    # human_label is stored in the result for score.py — it is never sent to the model
    base = {
        "id": item_id,
        "image": image_path,
        "human_label": item["label"],
    }

    if not pathlib.Path(image_path).exists():
        print(f"  SKIP {item_id}: image not found")
        return {**base, "raw_response": None, "parsed": None, "parse_error": "image_not_found"}

    try:
        b64_data, media_type = load_image_b64(image_path)
    except Exception as exc:
        print(f"  SKIP {item_id}: read error — {exc}")
        return {**base, "raw_response": None, "parsed": None, "parse_error": f"read_error: {exc}"}

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=256,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": b64_data,
                            },
                        },
                        {"type": "text", "text": PROBE_PROMPT},
                    ],
                }
            ],
        )
    except Exception as exc:
        print(f"  SKIP {item_id}: API error — {exc}")
        return {**base, "raw_response": None, "parsed": None, "parse_error": f"api_error: {exc}"}

    raw = response.content[0].text.strip()

    # Strip markdown code fences if the model wraps its JSON in ```
    if raw.startswith("```"):
        inner = "\n".join(
            line for line in raw.splitlines() if not line.startswith("```")
        ).strip()
    else:
        inner = raw

    try:
        parsed = json.loads(inner)
        print(f"  {item_id}: verdict={parsed.get('verdict')}  is_undertone_clash={parsed.get('is_undertone_clash')}")
        return {**base, "raw_response": raw, "parsed": parsed, "parse_error": None}
    except json.JSONDecodeError:
        print(f"  {item_id}: UNPARSED — raw text captured")
        return {**base, "raw_response": raw, "parsed": None, "parse_error": "unparsed"}


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    output_dir = pathlib.Path("output")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "model_verdicts.json"

    print(f"Probing {len(ITEMS)} items with {MODEL}...")
    results = [probe_item(client, item) for item in ITEMS]

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    n_parsed = sum(1 for r in results if r["parsed"] is not None)
    n_unparsed = sum(1 for r in results if r["parse_error"] == "unparsed")
    n_skipped = len(results) - n_parsed - n_unparsed
    print(f"\nDone. {n_parsed} parsed, {n_unparsed} unparsed, {n_skipped} skipped.")
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()

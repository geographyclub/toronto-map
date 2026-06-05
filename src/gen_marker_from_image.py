import os
import sys
import base64
from dotenv import load_dotenv
from openai import OpenAI
import hashlib

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY not set.")

client = OpenAI(api_key=api_key)

# ---- CONFIG ----
TRANSPARENT = True
SIZE = "1024x1024"
QUALITY = "high"
MODEL="gpt-image-1.5"
IMAGES_FOLDER = "/home/steve/Downloads"

STYLE_PROMPT = """
Generate a stylized product render of the input image.

STRICT SUBJECT CONSTRAINT: Only the original item may appear. Do not add any other objects, icons, props, text, labels, or environmental elements.

Style: A mid-century modern editorial illustration with geometric vector shapes, flat colors, Scandinavian design influence, clean edges, minimal shading, screen-print poster aesthetic.

Composition: Isolated centered product, no infographic layout, no supporting visuals, no scene.

Background: fully transparent.
"""

os.makedirs(IMAGES_FOLDER, exist_ok=True)

if len(sys.argv) < 2:
    raise RuntimeError("Usage: python generate_image_from_image.py img1.png img2.png ...")

reference_path = sys.argv[1]
if not os.path.exists(reference_path):
    raise RuntimeError(f"File not found: {reference_path}")

with open(reference_path, "rb") as f:
    file_hash = hashlib.sha256(f.read()).hexdigest()[:16]
output_path = os.path.join(IMAGES_FOLDER, f"{file_hash}.png")

try:
    with open(reference_path, "rb") as img_file:
        image_files = []
        for path in sys.argv[1:]:
            if not os.path.exists(path):
                raise RuntimeError(f"File not found: {path}")
            image_files.append(open(path, "rb"))

        params = {
            "model": MODEL,
            "image": image_files,
            "prompt": STYLE_PROMPT.strip(),
            # "size": SIZE,
            "quality": QUALITY
        }
        if TRANSPARENT:
            params["background"] = "transparent"

        result = client.images.edit(**params)

    image_base64 = result.data[0].b64_json
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(image_base64))

    print("Saved:", output_path)

except Exception as e:
    print("Failed →", e)
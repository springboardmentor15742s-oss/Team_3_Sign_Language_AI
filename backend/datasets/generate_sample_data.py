"""
Generates a tiny SYNTHETIC sample dataset so the Dataset Explorer works
immediately offline, without requiring a real Kaggle download.

Layout mirrors the real ASL Alphabet / Sign-MNIST datasets:
    sample_data/<letter>/<image files>.png

NOTE: Simple generated placeholder images — NOT real sign-language photos.
They demonstrate the folder-structure / label-distribution / preprocessing
workflow for Milestone 1. Replace `sample_data/` with a real dataset (via
dataset_downloader.py) for actual model training in later milestones.
"""
import os
import random

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR = os.path.join(HERE, "sample_data")

LETTERS = ["A", "B", "C", "D", "E"]
IMAGES_PER_CLASS = 6
IMG_SIZE = (200, 200)


def _random_color():
    return tuple(random.randint(60, 220) for _ in range(3))


def generate():
    os.makedirs(SAMPLE_DIR, exist_ok=True)
    for letter in LETTERS:
        class_dir = os.path.join(SAMPLE_DIR, letter)
        os.makedirs(class_dir, exist_ok=True)
        for i in range(IMAGES_PER_CLASS):
            img = Image.new("RGB", IMG_SIZE, color=_random_color())
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", 90)
            except Exception:  # noqa: BLE001
                font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), letter, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text(
                ((IMG_SIZE[0] - w) / 2, (IMG_SIZE[1] - h) / 2 - bbox[1]),
                letter, fill=(255, 255, 255), font=font,
            )
            img.save(os.path.join(class_dir, f"{letter.lower()}_{i}.png"))

    print(f"Synthetic sample dataset generated at: {SAMPLE_DIR}")
    print(f"Classes: {LETTERS} | Images per class: {IMAGES_PER_CLASS}")


if __name__ == "__main__":
    generate()

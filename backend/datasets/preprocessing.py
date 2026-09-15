"""
Preprocessing — Milestone 1 (Task: Begin preprocessing).
Resizes/normalizes images from dataset_dir/<class_label>/<images> into
output_dir/<class_label>/<images>, ready for Milestone-2 model training.
"""
import os

import numpy as np
from PIL import Image

VALID_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")
DEFAULT_TARGET_SIZE = (128, 128)


def preprocess_image(image_path: str, target_size=DEFAULT_TARGET_SIZE) -> np.ndarray:
    with Image.open(image_path) as im:
        im = im.convert("RGB").resize(target_size)
        arr = np.asarray(im, dtype=np.float32) / 255.0
    return arr


def preprocess_dataset(dataset_dir: str, output_dir: str, target_size=DEFAULT_TARGET_SIZE):
    os.makedirs(output_dir, exist_ok=True)
    processed, errors = 0, 0

    if not os.path.isdir(dataset_dir):
        return {"processed": 0, "errors": 0, "output_dir": output_dir,
                "message": f"Dataset directory not found: {dataset_dir}"}

    for entry in sorted(os.listdir(dataset_dir)):
        class_path = os.path.join(dataset_dir, entry)
        if not os.path.isdir(class_path):
            continue
        out_class_dir = os.path.join(output_dir, entry)
        os.makedirs(out_class_dir, exist_ok=True)

        for img_name in os.listdir(class_path):
            if not img_name.lower().endswith(VALID_IMAGE_EXTENSIONS):
                continue
            img_path = os.path.join(class_path, img_name)
            try:
                arr = preprocess_image(img_path, target_size=target_size)
                out_name = os.path.splitext(img_name)[0] + ".png"
                out_path = os.path.join(out_class_dir, out_name)
                Image.fromarray((arr * 255).astype("uint8")).save(out_path)
                processed += 1
            except Exception:  # noqa: BLE001
                errors += 1

    return {"processed": processed, "errors": errors, "output_dir": output_dir}

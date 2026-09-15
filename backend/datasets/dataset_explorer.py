"""
Dataset Explorer — Milestone 1 (structure inspection, label distribution,
image format reporting). Pure Python, reusable by both the FastAPI routes
and standalone CLI use.
"""
import os
from collections import Counter

VALID_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")


def inspect_structure(dataset_dir: str) -> dict:
    if not os.path.isdir(dataset_dir):
        return {}
    summary = {}
    for entry in sorted(os.listdir(dataset_dir)):
        class_path = os.path.join(dataset_dir, entry)
        if os.path.isdir(class_path):
            images = [f for f in os.listdir(class_path) if f.lower().endswith(VALID_IMAGE_EXTENSIONS)]
            summary[entry] = len(images)
    return summary


def label_distribution(dataset_dir: str) -> Counter:
    return Counter(inspect_structure(dataset_dir))


def image_format_report(dataset_dir: str, sample_per_class: int = 3) -> list:
    from PIL import Image

    report = []
    if not os.path.isdir(dataset_dir):
        return report

    for entry in sorted(os.listdir(dataset_dir)):
        class_path = os.path.join(dataset_dir, entry)
        if not os.path.isdir(class_path):
            continue
        images = [f for f in os.listdir(class_path) if f.lower().endswith(VALID_IMAGE_EXTENSIONS)][:sample_per_class]
        for img_name in images:
            img_path = os.path.join(class_path, img_name)
            try:
                with Image.open(img_path) as im:
                    report.append(
                        {
                            "class": entry,
                            "file": img_name,
                            "width": im.width,
                            "height": im.height,
                            "mode": im.mode,
                            "format": im.format,
                        }
                    )
            except Exception as e:  # noqa: BLE001
                report.append({"class": entry, "file": img_name, "error": str(e)})
    return report


def total_images(dataset_dir: str) -> int:
    return sum(inspect_structure(dataset_dir).values())


def list_classes_with_samples(dataset_dir: str, samples_per_class: int = 4) -> dict:
    """Returns {class_label: [filenames...]} for preview purposes."""
    result = {}
    if not os.path.isdir(dataset_dir):
        return result
    for entry in sorted(os.listdir(dataset_dir)):
        class_path = os.path.join(dataset_dir, entry)
        if os.path.isdir(class_path):
            images = [f for f in os.listdir(class_path) if f.lower().endswith(VALID_IMAGE_EXTENSIONS)]
            result[entry] = images[:samples_per_class]
    return result

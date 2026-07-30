import os
from pathlib import Path

# Path to the dataset, relative to the backend folder
DATASET_ROOT = Path(__file__).resolve().parent.parent.parent / "data" / "asl_alphabet"
TRAIN_DIR = DATASET_ROOT / "asl_alphabet_train" / "asl_alphabet_train"
TEST_DIR = DATASET_ROOT / "asl_alphabet_test" / "asl_alphabet_test"


def get_class_counts(directory: Path) -> dict:
    """
    Scans a dataset directory and returns a dict of
    {class_name: image_count} for each subfolder (class).
    """
    counts = {}
    if not directory.exists():
        raise FileNotFoundError(f"Dataset directory not found: {directory}")

    for class_folder in sorted(directory.iterdir()):
        if class_folder.is_dir():
            image_count = len([
                f for f in class_folder.iterdir()
                if f.suffix.lower() in [".jpg", ".jpeg", ".png"]
            ])
            counts[class_folder.name] = image_count

    return counts


def verify_dataset():
    """
    Verifies the ASL Alphabet dataset is present and readable.
    Prints a summary of image counts per class.
    """
    print(f"Checking training data at: {TRAIN_DIR}")
    train_counts = get_class_counts(TRAIN_DIR)

    print(f"\nFound {len(train_counts)} classes in training set:")
    for class_name, count in train_counts.items():
        print(f"  {class_name}: {count} images")

    total_images = sum(train_counts.values())
    print(f"\nTotal training images: {total_images}")

    return {
        "num_classes": len(train_counts),
        "class_counts": train_counts,
        "total_images": total_images,
    }


if __name__ == "__main__":
    verify_dataset()
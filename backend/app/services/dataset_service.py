import os
from pathlib import Path
from typing import Dict, List, Optional, Any

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

def find_asl_dataset_dir() -> Optional[Path]:
    """Dynamically search for existing ASL Alphabet dataset directory."""
    candidates = []
    
    # 1. Environment variable if set
    env_dir = os.getenv("ASL_DATASET_DIR")
    if env_dir:
        candidates.append(Path(env_dir))
        
    # 2. Known local Desktop & workspace paths
    user_desktop = Path.home() / "OneDrive" / "Desktop"
    if not user_desktop.exists():
        user_desktop = Path.home() / "Desktop"

    candidates.extend([
        user_desktop / "sign lang",
        Path.cwd() / "data" / "asl_alphabet",
        Path.cwd() / "data",
        Path.cwd().parent / "sign lang",
        Path("C:/Users/rashm/OneDrive/Desktop/sign lang"),
        Path("C:/Users/rashm/OneDrive/Desktop/Sing Language/data"),
    ])

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            # Check if asl_alphabet_train exists inside candidate or directly
            if (candidate / "asl_alphabet_train").exists():
                return candidate
            if (candidate / "asl_alphabet_train" / "asl_alphabet_train").exists():
                return candidate

    return None

def get_train_and_test_dirs(base_dir: Path) -> tuple[Optional[Path], Optional[Path]]:
    """Resolve train and test directories given the base dataset directory."""
    train_dir = None
    test_dir = None

    # Check for train directory
    train_candidates = [
        base_dir / "asl_alphabet_train" / "asl_alphabet_train",
        base_dir / "asl_alphabet_train",
        base_dir / "train",
    ]
    for tc in train_candidates:
        if tc.exists() and tc.is_dir():
            train_dir = tc
            break

    # Check for test directory
    test_candidates = [
        base_dir / "asl_alphabet_test" / "asl_alphabet_test",
        base_dir / "asl_alphabet_test",
        base_dir / "test",
    ]
    for tc in test_candidates:
        if tc.exists() and tc.is_dir():
            test_dir = tc
            break

    return train_dir, test_dir

def get_dataset_summary() -> Dict[str, Any]:
    """Scan and summarize the ASL Alphabet dataset."""
    base_dir = find_asl_dataset_dir()
    if not base_dir:
        return {
            "dataset_status": "not_found",
            "message": "ASL Alphabet dataset folder was not detected on system.",
            "dataset_path": None,
            "number_of_classes": 0,
            "available_classes": [],
            "total_train_images": 0,
            "total_test_images": 0,
            "train_images_per_class": {},
            "test_images_per_class": {},
        }

    train_dir, test_dir = get_train_and_test_dirs(base_dir)

    classes: List[str] = []
    train_counts: Dict[str, int] = {}
    test_counts: Dict[str, int] = {}
    total_train = 0
    total_test = 0

    if train_dir and train_dir.exists():
        # Read subdirectories as class labels
        classes = sorted([
            entry.name for entry in train_dir.iterdir()
            if entry.is_dir() and not entry.name.startswith(".")
        ])

        for c_name in classes:
            class_folder = train_dir / c_name
            img_count = sum(
                1 for f in class_folder.iterdir()
                if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
            )
            train_counts[c_name] = img_count
            total_train += img_count

    if test_dir and test_dir.exists():
        # Check if test dir has class subdirectories or flat test files like 'A_test.jpg'
        subdirs = [e for e in test_dir.iterdir() if e.is_dir() and not e.name.startswith(".")]
        if subdirs:
            for sd in subdirs:
                c_name = sd.name
                img_count = sum(
                    1 for f in sd.iterdir()
                    if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
                )
                test_counts[c_name] = img_count
                total_test += img_count
        else:
            # Flat test files e.g. A_test.jpg, B_test.jpg
            for f in test_dir.iterdir():
                if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS:
                    total_test += 1
                    # Extract prefix e.g. A_test.jpg -> A
                    name_parts = f.stem.split("_")
                    c_name = name_parts[0] if name_parts else f.stem
                    test_counts[c_name] = test_counts.get(c_name, 0) + 1

    return {
        "dataset_status": "ready" if classes else "incomplete",
        "dataset_path": str(base_dir.resolve()),
        "number_of_classes": len(classes),
        "available_classes": classes,
        "total_train_images": total_train,
        "total_test_images": total_test,
        "train_images_per_class": train_counts,
        "test_images_per_class": test_counts,
    }

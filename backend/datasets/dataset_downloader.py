"""
Dataset Downloader — Milestone 1 (Task: Download datasets / Integrate sign
language datasets).

Downloads and organizes the datasets recommended in the project plan:
    - ASL Alphabet Dataset          (Kaggle: grassknoted/asl-alphabet)
    - Sign Language MNIST Dataset   (Kaggle: datamunge/sign-language-mnist)
    - WLASL Dataset                 (Kaggle: risangbaskoro/wlasl-processed)
    - RWTH-PHOENIX Dataset          (Academic — requires direct request)

Requires internet access + a configured Kaggle API token
(~/.kaggle/kaggle.json). Run this on your own machine — it is NOT executed
automatically by the backend, since the sandboxed demo environment has no
outbound internet access.

Usage:
    python datasets/dataset_downloader.py --dataset asl_alphabet
    python datasets/dataset_downloader.py --dataset all
"""
import argparse
import os
import sys
import zipfile

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATASETS_DIR, RECOMMENDED_DATASETS  # noqa: E402

DATASET_KEY_MAP = {
    "asl_alphabet": "ASL Alphabet Dataset",
    "sign_mnist": "Sign Language MNIST Dataset",
    "wlasl": "WLASL Dataset",
    "phoenix": "RWTH-PHOENIX Dataset",
}


def ensure_dirs():
    os.makedirs(DATASETS_DIR, exist_ok=True)


def download_via_kaggle(dataset_name: str):
    info = RECOMMENDED_DATASETS[dataset_name]
    slug = info.get("kaggle_slug")

    if not slug:
        print(f"[SKIP] '{dataset_name}' has no Kaggle slug. Follow the manual request process.")
        if info.get("info_url"):
            print(f"        Info / request URL: {info['info_url']}")
        return

    try:
        import kaggle  # noqa: F401
    except ImportError:
        print("[ERROR] The 'kaggle' package is not installed. Run: pip install kaggle")
        return
    except OSError as e:
        print(f"[ERROR] Kaggle credentials not configured: {e}")
        return

    target_dir = os.path.join(DATASETS_DIR, dataset_name)
    os.makedirs(target_dir, exist_ok=True)

    print(f"[INFO] Downloading '{dataset_name}' (Kaggle: {slug}) -> {target_dir}")
    os.system(f'kaggle datasets download -d {slug} -p "{target_dir}"')

    for fname in os.listdir(target_dir):
        if fname.endswith(".zip"):
            zip_path = os.path.join(target_dir, fname)
            print(f"[INFO] Extracting {fname} ...")
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(target_dir)
            os.remove(zip_path)

    print(f"[DONE] '{dataset_name}' ready at {target_dir}")


def main():
    parser = argparse.ArgumentParser(description="Download recommended sign-language datasets.")
    parser.add_argument("--dataset", choices=list(DATASET_KEY_MAP.keys()) + ["all"], default="all")
    args = parser.parse_args()

    ensure_dirs()
    if args.dataset == "all":
        for name in DATASET_KEY_MAP.values():
            download_via_kaggle(name)
    else:
        download_via_kaggle(DATASET_KEY_MAP[args.dataset])


if __name__ == "__main__":
    main()

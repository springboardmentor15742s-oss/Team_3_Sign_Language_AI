"""Dataset explorer & preprocessing routes."""
import os

from fastapi import APIRouter, Depends, HTTPException, Query

from config import DATASETS_DIR, PROCESSED_DIR, RECOMMENDED_DATASETS, SAMPLE_DATA_DIR
from database import db
from datasets import dataset_explorer, preprocessing
from deps import get_current_user

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


def _resolve_dataset_path(name: str) -> str:
    """Maps a dataset 'key' from the frontend to an actual folder on disk."""
    if name == "sample":
        return SAMPLE_DATA_DIR
    raw_path = os.path.join(DATASETS_DIR, name)
    if os.path.isdir(raw_path):
        return raw_path
    raise HTTPException(status_code=404, detail=f"Dataset '{name}' not found.")


@router.get("/recommended")
def recommended():
    rows = []
    for dname, info in RECOMMENDED_DATASETS.items():
        rows.append(
            {
                "name": dname,
                "purpose": info["purpose"],
                "source": info.get("kaggle_slug") or info.get("info_url") or "N/A",
            }
        )
    return rows


@router.get("/list")
def list_available():
    """Lists dataset folders available to explore right now (sample + any raw/ downloads)."""
    options = [{"key": "sample", "label": "Sample (synthetic demo) dataset"}]
    if os.path.isdir(DATASETS_DIR):
        for entry in sorted(os.listdir(DATASETS_DIR)):
            if os.path.isdir(os.path.join(DATASETS_DIR, entry)):
                options.append({"key": entry, "label": f"raw/{entry}"})
    return options


@router.get("/{name}/structure")
def structure(name: str, current_user=Depends(get_current_user)):
    path = _resolve_dataset_path(name)
    distribution = dataset_explorer.label_distribution(path)
    if not distribution:
        return {"classes": [], "total_images": 0}

    db.log_dataset_action(
        name, "explored",
        f"{len(distribution)} classes, {sum(distribution.values())} images",
        performed_by=current_user["id"],
    )
    return {
        "classes": [{"label": k, "count": v} for k, v in sorted(distribution.items())],
        "total_images": sum(distribution.values()),
    }


@router.get("/{name}/preview")
def preview(name: str, current_user=Depends(get_current_user)):
    path = _resolve_dataset_path(name)
    samples = dataset_explorer.list_classes_with_samples(path, samples_per_class=4)
    return {
        "classes": list(samples.keys()),
        "samples": {
            cls: [f"/api/datasets/{name}/image/{cls}/{fname}" for fname in files]
            for cls, files in samples.items()
        },
    }


@router.get("/{name}/image/{cls}/{filename}")
def get_image(name: str, cls: str, filename: str):
    from fastapi.responses import FileResponse

    path = _resolve_dataset_path(name)
    # basic path-traversal guard
    safe_cls = os.path.basename(cls)
    safe_filename = os.path.basename(filename)
    img_path = os.path.join(path, safe_cls, safe_filename)
    if not os.path.isfile(img_path):
        raise HTTPException(status_code=404, detail="Image not found.")
    return FileResponse(img_path)


@router.get("/{name}/format-report")
def format_report(name: str, current_user=Depends(get_current_user)):
    path = _resolve_dataset_path(name)
    return dataset_explorer.image_format_report(path, sample_per_class=2)


@router.post("/{name}/preprocess")
def preprocess(
    name: str,
    width: int = Query(128, ge=32, le=512),
    height: int = Query(128, ge=32, le=512),
    current_user=Depends(get_current_user),
):
    path = _resolve_dataset_path(name)
    output_dir = os.path.join(PROCESSED_DIR, name)
    result = preprocessing.preprocess_dataset(path, output_dir, target_size=(width, height))

    if result.get("processed", 0) > 0:
        db.log_dataset_action(
            name, "preprocessed",
            f"{result['processed']} images resized to {width}x{height}",
            performed_by=current_user["id"],
        )
    return result


@router.get("/log")
def get_log(limit: int = 20, current_user=Depends(get_current_user)):
    return db.get_dataset_log(limit=limit)

"""
Standalone training script — runs YOLOv8 training on the project-local dataset
and saves results so the Dataset & Training page can display them.
"""
import sys, json, yaml, time
from pathlib import Path

BASE_DIR  = Path(__file__).resolve().parent
DATA_DIR  = BASE_DIR / "data"
DS_DIR    = DATA_DIR / "dataset"
RUNS_DIR  = BASE_DIR / "runs"
RESULTS_F = DATA_DIR / "training_results.json"

# ── Validate dataset ──────────────────────────────────────────────────────────
yaml_path = DS_DIR / "data.yaml"
if not yaml_path.exists():
    print(f"[ERROR] data.yaml not found at {yaml_path}")
    sys.exit(1)

with open(yaml_path) as f:
    cfg = yaml.safe_load(f)

# Patch the 'path' key to the project-local dataset location
cfg["path"] = str(DS_DIR)
with open(yaml_path, "w") as f:
    yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)

print(f"[INFO] Dataset      : {DS_DIR}")
print(f"[INFO] Classes ({cfg['nc']}): {cfg['names']}")
train_count = len(list((DS_DIR / "train" / "images").glob("*")))
val_count   = len(list((DS_DIR / "valid" / "images").glob("*")))
test_count  = len(list((DS_DIR / "test"  / "images").glob("*")))
print(f"[INFO] Split        : train={train_count}  val={val_count}  test={test_count}")

# ── Training ──────────────────────────────────────────────────────────────────
EPOCHS = int(sys.argv[1]) if len(sys.argv) > 1 else 10
IMGSZ  = 640

print(f"\n[INFO] Starting YOLOv8n training — {EPOCHS} epochs, imgsz={IMGSZ}")
start = time.time()

try:
    from ultralytics import YOLO
    model = YOLO("yolov8n.pt")

    results = model.train(
        data=str(yaml_path),
        epochs=EPOCHS,
        imgsz=IMGSZ,
        project=str(RUNS_DIR),
        name="train_exp",
        exist_ok=True,
        verbose=True,
        device="cpu",
        workers=0,          # Windows safe
        cache=False,
    )

    elapsed = round(time.time() - start, 1)

    # Extract metrics
    box  = getattr(results, "box", None)
    mp50    = round(float(getattr(box, "map50",   0.0) if box else 0.0), 4)
    mp5095  = round(float(getattr(box, "map",     0.0) if box else 0.0), 4)
    prec    = round(float(getattr(box, "mp",      0.0) if box else 0.0), 4)
    rec     = round(float(getattr(box, "mr",      0.0) if box else 0.0), 4)

    # Compute class distribution from labels
    class_dist = {name: 0 for name in cfg["names"]}
    for split in ["train", "valid", "test"]:
        lbl_dir = DS_DIR / split / "labels"
        if not lbl_dir.exists():
            continue
        for lf in lbl_dir.glob("*.txt"):
            try:
                for line in lf.read_text().splitlines():
                    parts = line.strip().split()
                    if parts:
                        cid = int(parts[0])
                        if 0 <= cid < len(cfg["names"]):
                            class_dist[cfg["names"][cid]] += 1
            except Exception:
                pass

    payload = {
        "status": "success",
        "epochs": EPOCHS,
        "elapsed_seconds": elapsed,
        "weights_path": str(RUNS_DIR / "train_exp" / "weights" / "best.pt"),
        "metrics": {
            "mAP50": mp50,
            "mAP50-95": mp5095,
            "precision": prec,
            "recall": rec,
        },
        "dataset_statistics": {
            "dataset_name": DS_DIR.name,
            "dataset_path": str(DS_DIR),
            "total_images": train_count + val_count + test_count,
            "split_counts": {"train": train_count, "val": val_count, "test": test_count},
            "class_distribution": class_dist,
            "classes": cfg["names"],
            "num_classes": cfg["nc"],
        }
    }

    RESULTS_F.write_text(json.dumps(payload, indent=2))
    print(f"\n[SUCCESS] Training complete in {elapsed}s")
    print(f"  mAP50={mp50}  mAP50-95={mp5095}  Precision={prec}  Recall={rec}")
    print(f"  Weights saved: {payload['weights_path']}")
    print(f"  Results JSON : {RESULTS_F}")

except Exception as e:
    print(f"[ERROR] Training failed: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)

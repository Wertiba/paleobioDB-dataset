import json
import logging
import subprocess  # noqa
from datetime import UTC, datetime
from pathlib import Path

import yaml
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

CONFIG = yaml.safe_load((Path(__file__).parent / "config.yml").read_text())
KAGGLE = CONFIG["kaggle"]
DATASET_DIR = Path(__file__).parent.parent / CONFIG["dataset"]["path"]


def kaggle_push() -> None:
    """Create or version the Kaggle dataset."""

    metadata_path = DATASET_DIR / "dataset-metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "id": f"{KAGGLE['username']}/{KAGGLE['dataset_slug']}",
                "licenses": [{"name": KAGGLE["license"]}],
                "keywords": KAGGLE["keywords"],
            }
        )
    )

    cmd = [
        "kaggle",
        "datasets",
        "version",
        "-p",
        str(DATASET_DIR),
        "-m",
        f"Auto-update {datetime.now(tz=UTC).strftime('%Y-%m-%d')}",
    ]
    log.info("Uploading new version to Kaggle…")
    result = subprocess.run(cmd, capture_output=True, text=True)  # noqa

    if result.returncode == 0:
        log.info("Kaggle push successful ✓")
        log.info(result.stdout)
    else:
        log.error(f"Kaggle push failed:\n{result.stderr}")
        log.error(f"Kaggle push failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
        raise RuntimeError("kaggle CLI returned non-zero exit code")


if __name__ == "__main__":
    kaggle_push()

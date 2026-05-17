import logging
import os
import subprocess  # noqa
from datetime import UTC, datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

DATASET_DIR = Path(__file__).parent.parent / "dataset"


def kaggle_push(new_dataset: bool = False) -> None:
    """Create or version the Kaggle dataset."""

    if new_dataset:
        cmd = ["kaggle", "datasets", "create", "-p", str(DATASET_DIR)]
        log.info("Creating new Kaggle dataset…")
    else:
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


def main():
    # Set first_run=True only the very first time
    first_run = os.environ.get("FIRST_RUN", "false").lower() == "true"
    kaggle_push(new_dataset=first_run)


if __name__ == "__main__":
    main()

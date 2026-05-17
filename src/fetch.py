import logging
import time
from io import StringIO
from pathlib import Path

import httpx
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

BASE_URL = "https://paleobiodb.org/data1.2"
HEADERS = {"User-Agent": "paleobiodb-kaggle-pipeline/1.0"}
OUTPUT_DIR = Path(__file__).parent.parent / "dataset"
OUTPUT_DIR.mkdir(exist_ok=True)


def fetch_all(endpoint: str, params: dict, page_size: int = 5000) -> pd.DataFrame:
    all_pages = []
    offset = 0

    while True:
        page_params = {**params, "limit": page_size, "offset": offset}
        resp = httpx.get(f"{BASE_URL}/{endpoint}", params=page_params, timeout=300, headers=HEADERS)
        resp.raise_for_status()

        lines = resp.text.splitlines()
        data_lines = [l for l in lines if not l.startswith('"#') and not l.startswith("Warning")]
        clean_csv = "\n".join(data_lines)

        df_page = pd.read_csv(StringIO(clean_csv), low_memory=False, on_bad_lines="skip")

        if df_page.empty:
            break

        all_pages.append(df_page)
        log.info(f"  {endpoint} | offset={offset} → {len(df_page)} rows")

        if len(df_page) < page_size:
            break

        offset += page_size
        time.sleep(0.5)

    return pd.concat(all_pages, ignore_index=True) if all_pages else pd.DataFrame()


def simple_clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.drop_duplicates(inplace=True)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return df


def clean_occurrences(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and enrich occurrences dataframe."""
    df = simple_clean(df)

    for col in ["lng", "lat"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "lat" in df.columns and "lng" in df.columns:
        df = df[df["lat"].between(-90, 90) & df["lng"].between(-180, 180)]

    return df


def fetch_occurrences() -> pd.DataFrame:
    """All dinosaur occurrences worldwide."""
    log.info("=== Fetching occurrences ===")
    params = {
        "base_name": "Dinosauria",
        "show": "coords,paleoloc,phylo,time,strat,env,ref",
        "vocab": "pbdb",
    }
    df = fetch_all("occs/list.csv", params)
    df = clean_occurrences(df)
    log.info(f"Occurrences total: {len(df)}")
    return df


def fetch_taxa() -> pd.DataFrame:
    """Full Dinosauria taxonomy tree."""
    log.info("=== Fetching taxa ===")
    params = {
        "base_name": "Dinosauria",
        "show": "phylo,app,size,ecospace,taphonomy",
        "vocab": "pbdb",
        "rank": "species,genus,family,order,class",
    }
    df = fetch_all("taxa/list.csv", params)
    df = simple_clean(df)
    log.info(f"Taxa total: {len(df)}")
    return df


def fetch_collections() -> pd.DataFrame:
    """Collections that contain dinosaur fossils."""
    log.info("=== Fetching collections ===")
    params = {
        "base_name": "Dinosauria",
        "show": "paleoloc,time,strat,env,ref",
        "vocab": "pbdb",
    }
    df = fetch_all("colls/list.csv", params)
    df = simple_clean(df)
    log.info(f"Collections total: {len(df)}")
    return df


def fetch_diversity() -> pd.DataFrame:
    """Genus-level diversity through time (global)."""
    log.info("=== Fetching diversity over time ===")
    params = {
        "base_name": "Dinosauria",
        "count": "genera",
        "vocab": "pbdb",
    }
    try:
        resp = httpx.get(f"{BASE_URL}/occs/diversity.csv", params=params, timeout=60, headers=HEADERS)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text), low_memory=False, on_bad_lines="skip")
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        log.info(f"Diversity rows: {len(df)}")
        return df
    except Exception as e:
        log.error(f"Diversity fetch failed: {e}")
        return pd.DataFrame()


def save(df: pd.DataFrame, name: str) -> None:
    if df.empty:
        log.warning(f"Skipping {name} - empty dataframe")
        return
    path = OUTPUT_DIR / f"{name}.csv"
    df.to_csv(path, index=False)
    log.info(f"Saved {path} ({len(df)} rows, {df.shape[1]} cols, {path.stat().st_size // 1024} KB)")


def main():
    log.info("Starting PaleoBioDB fetch pipeline")

    occurrences = fetch_occurrences()
    taxa = fetch_taxa()
    collections = fetch_collections()
    diversity = fetch_diversity()

    save(occurrences, "dinosaur_occurrences")
    save(taxa, "dinosaur_taxa")
    save(collections, "dinosaur_collections")
    save(diversity, "dinosaur_diversity_over_time")

    log.info("\n=== Summary ===")
    for name, df in [
        ("occurrences", occurrences),
        ("taxa", taxa),
        ("collections", collections),
        ("diversity", diversity),
    ]:
        log.info(f"  {name}: {len(df):,} rows × {df.shape[1]} cols")

    log.info("Pipeline complete ✓")


if __name__ == "__main__":
    main()

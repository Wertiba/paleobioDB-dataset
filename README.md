# PaleoBioDB → Kaggle Pipeline 🦕

Auto-fetches global dinosaur data from [paleobiodb.org](https://paleobiodb.org) and publishes it as a Kaggle dataset every week via GitHub Actions.

## Files

| File | Description |
|---|---|
| `fetch_data.py` | Pulls data from PaleoBioDB API, cleans it, saves CSVs to `dataset/` |
| `push_to_kaggle.py` | Uploads the CSVs to Kaggle as a new dataset version |
| `.github/workflows/update_dataset.yml` | GitHub Actions: runs every Monday at 08:00 UTC |
| `requirements.txt` | Python dependencies |

## Dataset contents

- **dinosaur_occurrences.csv** — fossil finds worldwide (lat/lng, period, formation, env)
- **dinosaur_taxa.csv** — full Dinosauria taxonomy tree
- **dinosaur_collections.csv** — museum/expedition collections
- **dinosaur_diversity_over_time.csv** — genus diversity per geological interval

## Setup (one-time)

### 1. Fork / clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/paleobiodb-kaggle
cd paleobiodb-kaggle
```

### 2. Get Kaggle API credentials

1. Go to https://www.kaggle.com/settings → **API** → **Create New Token**
2. Download `kaggle.json` — it contains `{"username":"...","key":"..."}`

### 3. Add GitHub Secrets

In your repo: **Settings → Secrets and variables → Actions → New repository secret**

| Secret name | Value |
|---|---|
| `KAGGLE_USERNAME` | your Kaggle username |
| `KAGGLE_KEY` | your Kaggle API key |

### 4. First run — create the dataset on Kaggle

Trigger the workflow manually from **Actions** tab, and set the input `first_run = true`.
This calls `kaggle datasets create` instead of `version`.

After that, every Monday it will automatically push a new version.

### 5. Run locally (optional)

```bash
pip install -r requirements.txt

# Put your kaggle.json in ~/.kaggle/kaggle.json first
python fetch_data.py     # downloads ~dataset/ folder
python push_to_kaggle.py # pushes to Kaggle
```

## Tips for a great Kaggle dataset

- Add a **notebook** with EDA (map of occurrences, diversity chart) — boosts discoverability
- Fill in Kaggle dataset description with good keywords
- Engage in comments — Kaggle's algorithm rewards active datasets

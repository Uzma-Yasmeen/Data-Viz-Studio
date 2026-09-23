# Contributing

Thanks for taking a look. This started as a Batch 19/20 project at SR
University and is small enough that anyone can read the whole thing in an
afternoon — `app.py` is the entire application.

## Setting up

```bash
git clone https://github.com/Uzma-Yasmeen/Data-Viz-Studio.git
cd Data-Viz-Studio

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

streamlit run app.py
```

Streamlit hot-reloads on save locally, so leave it running while you work.

## Before opening a pull request

CI runs three things, and you can run all of them yourself:

```bash
pip install ruff
ruff check .                     # lint
python -m compileall -q app.py   # syntax

# boot smoke test — the app must answer its health endpoint
streamlit run app.py --server.headless true &
curl -fsS http://localhost:8501/_stcore/health
```

Then click through it by hand with `sample_data/sample_sales.csv`. There is no
automated UI test suite, so this matters:

- upload the sample CSV and confirm the preview and EDA sections render
- generate at least three charts of different types
- confirm they stack correctly in the combined dashboard
- download one PNG and the full PDF report, and actually open both

If your change touches file loading, test a JSON and an XLSX file too.

## Code style

Match what is already there rather than importing your own conventions:

- 4-space indentation, roughly 100-character lines
- section comments in the `# --- Section name ---` style used throughout `app.py`
- user-facing messages lead with the relevant emoji (`✅`, `❌`, `⚠️`, `ℹ️`) —
  consistent with the existing UI
- keep the app a single file unless a change genuinely needs more; the
  single-file layout is deliberate and part of why it is easy to read

## Things worth working on

The roadmap in the [README](README.md#roadmap) has the larger items. Smaller,
self-contained starting points:

- **Multi-sheet Excel.** `pd.read_excel(..., sheet_name=0)` reads only the
  first sheet. A sheet picker would be a contained change.
- **Make sampling visible.** Charts use a 1,000-row sample while the PDF
  statistics use the full dataset. Labelling sampled charts would remove a
  real source of confusion.
- **Dependency hygiene.** `reportlab` is listed but unused; `numpy` is used but
  unlisted. Both are one-line fixes, but they change `requirements.txt`, so
  raise an issue before doing it.
- **Date-aware plotting.** Date columns arrive as strings and sort
  lexicographically. Parsing them would make time-series line charts correct.
- **Per-chart removal.** You can add charts to the dashboard but not remove
  one without refreshing the page.

## Reporting a bug

Please include the chart type and column selection, the file format, a rough
idea of the dataset shape, what you expected, what happened, and the full error
text if there was one. A few rows of anonymised data that reproduce it help
enormously.

## Deployment changes

If your change touches `render.yaml`, `start.sh`, `.streamlit/config.toml` or
anything under `landing/`, read [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
first — those files are load-bearing for the live deploy and the cold-start
handling, and a plausible-looking edit can break the health check without
breaking the build.

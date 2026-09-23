# 📊 DataViz Studio

**An interactive, no-code data analytics dashboard.** Upload a CSV, JSON or
Excel file and get automated exploratory analysis, correlation heatmaps, nine
kinds of chart and a downloadable PDF report — without writing a line of code.

> Built with Streamlit · SR University 

[**Open the dashboard →**](https://data-viz-studio.onrender.com) &nbsp;•&nbsp;
[Landing page](https://uzma-yasmeen.github.io/Data-Viz-Studio/) &nbsp;•&nbsp;
[Deployment guide](docs/DEPLOYMENT.md)

---

## Contents

- [Why this exists](#why-this-exists)
- [Features](#features)
- [Quick start](#quick-start)
- [How to use it](#how-to-use-it)
- [Project structure](#project-structure)
- [Deployment](#deployment)
- [Cold starts and the wake-up page](#cold-starts-and-the-wake-up-page)
- [Tech stack](#tech-stack)
- [Known limitations](#known-limitations)
- [Roadmap](#roadmap)
- [License](#license)

---

## Why this exists

Exploring a new dataset usually means opening a notebook, importing pandas,
remembering the seaborn API and writing the same twenty lines you wrote last
time. DataViz Studio collapses that into a browser tab: point it at a file and
the exploratory work — dtypes, missing values, distributions, correlations — is
already done by the time the page renders.

It is aimed at people who have data and questions but not a Python environment:
students, analysts, and anyone who needs a chart in the next five minutes.

## Features

**Multi-format upload.** CSV, JSON (both standard and line-delimited) and XLSX.
Excel files read from the first sheet. Every loader is wrapped in error handling
so a malformed file produces a readable message instead of a traceback.

**Automated EDA.** On upload you immediately get:
- summary statistics for every numeric column (`describe().T`)
- a missing-value count per column
- the inferred dtype of each column
- a correlation heatmap, when there are at least two numeric columns

**Nine chart types.** Line, Bar, Scatter, Histogram, Boxplot, Pie, Heatmap,
Pairplot and Regression. X-axis, Y-axis, figure size and both the main and
outline colours are picked from the sidebar.

**Compatibility checks.** Before drawing, the app validates that your column
selection makes sense for the chart type — numeric axes for regression, low
cardinality for pie charts — and explains the problem rather than throwing.

**Intelligent sampling.** Datasets over 1,000 rows are randomly sampled
(`random_state=42`, so it is reproducible) for plotting only. Statistics in
the PDF report are still computed on the full dataset.

**Arrow-safe rendering.** Streamlit's dataframe widget serialises through
Apache Arrow, which rejects nullable integers and mixed-type object columns.
`arrow_safe_df()` coerces those to float and string respectively, so messy
real-world data doesn't crash the table view.

**Combined dashboard.** Generated charts persist in session state and stack
into a single grid view, so you can build up a set of visuals across many
interactions without losing earlier ones.

**Export.** Download any chart as a PNG, or the whole session as a multi-page
PDF report — cover page with file metadata, dtypes and statistics; correlation
heatmap; combined dashboard.

## Quick start

**Requirements:** Python 3.9 or newer (3.11 recommended).

```bash
# 1. Clone
git clone https://github.com/Uzma-Yasmeen/Data-Viz-Studio.git
cd Data-Viz-Studio

# 2. Create an isolated environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install
pip install -r requirements.txt

# 4. Run
streamlit run app.py
```

Streamlit opens <http://localhost:8501> automatically. Upload
[`sample_data/sample_sales.csv`](sample_data/sample_sales.csv) to try it with
no data of your own.

## How to use it

1. **Upload** a file from the sidebar (`📂 Upload Your Dataset`). A preview of
   the first five rows appears once it loads.
2. **Expand `📈 Explore Dataset`** for statistics, missing values, dtypes and
   the correlation heatmap.
3. **Configure a chart** in the sidebar: pick X, Y, the graph type, the figure
   size and your colours.
4. **Press `Generate Graph`.** The chart renders and is added to the combined
   dashboard below.
5. **Repeat** for as many charts as you want — they accumulate.
6. **Download** individual PNGs, or press `📄 Download Final Report` for the
   full PDF.

### Which chart for which columns

| Chart       | X-axis               | Y-axis        |
|-------------|----------------------|---------------|
| Line        | numeric              | numeric       |
| Bar         | categorical or numeric | numeric     |
| Scatter     | numeric              | numeric       |
| Histogram   | numeric              | — (ignored)   |
| Boxplot     | — (ignored)          | numeric       |
| Pie         | categorical, ideally under 15 distinct values | — (ignored) |
| Heatmap     | — (uses all numeric columns) | —     |
| Pairplot    | — (uses all numeric columns) | —     |
| Regression  | numeric              | numeric       |

## Project structure

```
Data-Viz-Studio/
├── app.py                      # The entire Streamlit application
├── requirements.txt            # Python dependencies
├── .python-version             # Pinned interpreter (3.11.9)
│
├── .streamlit/
│   └── config.toml             # Server settings and theme
│
├── landing/                    # Static landing page that pre-warms Render
│   ├── index.html              # Project page with live "waking up" status
│   ├── wake.js                 # Wake + readiness-polling logic
│   ├── config.js               # ← the one file you edit: your Render URL
│   └── README.md
│
├── sample_data/
│   └── sample_sales.csv        # 120-row demo dataset
│
├── docs/
│   └── DEPLOYMENT.md           # Step-by-step Render + Pages deployment
│
├── .github/workflows/
│   ├── ci.yml                  # Lint + boot smoke test
│   ├── keep-alive.yml          # Pings Render so it rarely sleeps
│   └── pages.yml               # Publishes landing/ to GitHub Pages
│
├── render.yaml                 # Render blueprint
├── start.sh                    # Binds Streamlit to $PORT
├── Procfile                    # Same, for other hosts
├── Dockerfile                  # Optional container build
├── CONTRIBUTING.md
└── LICENSE
```

## Deployment

The short version — full walkthrough in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

1. Push this repository to GitHub.
2. On [Render](https://render.com): **New → Blueprint**, select the repo. It
   reads `render.yaml` and configures everything itself.
3. Copy the resulting URL (e.g. `https://data-viz-studio.onrender.com`) into
   `landing/config.js`, and into the two `<link rel="preconnect">` tags in
   `landing/index.html`.
4. **Settings → Pages → Source: GitHub Actions** to publish the landing page.
5. **Settings → Secrets and variables → Actions → Variables**, add `APP_URL`
   with the same Render URL, to enable the keep-alive workflow.

The one thing that is not optional: Render assigns a port at runtime via
`$PORT`, and Streamlit defaults to 8501. `start.sh` bridges the two. A deploy
without it will build successfully and then fail its health check.

## Cold starts and the wake-up page

Render's free tier spins an instance down after 15 minutes without traffic.
The next visitor waits 30–60 seconds staring at a blank tab while it boots.
Two layers address that — the second is the one doing the work here:

**Layer 1 — don't fall asleep (currently off).**
`.github/workflows/keep-alive.yml` can ping `/_stcore/health` on a schedule,
which stops the instance sleeping at all. **Its schedule is commented out on
purpose**, because this project doesn't get steady traffic and an automatic
ping every 10 minutes would spend ~510 of the 750 free instance-hours per
month keeping the app awake for nobody.

Exhausting the quota costs no money — Render suspends rather than bills —
but it takes the app offline until the 1st of the next month, and the pool is
shared with any other free service on the account.

Run it by hand before a demo (**Actions → Keep Render awake → Run workflow**),
or uncomment the `schedule:` block if traffic ever justifies it.

**Layer 2 — wake it, then make it paint.** `landing/index.html` handles both
halves of the cold start. The moment someone loads that page:

- a `<link rel="preconnect">` opens the TCP/TLS connection to Render
- `wake.js` fires a `keepalive` request at `/_stcore/health`, which is what
  actually triggers the spin-up
- the page shows a live progress bar and an elapsed-seconds counter while the
  visitor reads about the project
- three probes poll in parallel — a CORS read of the health endpoint, an
  `<img>` load of a real asset, and an opaque reachability check — and the
  page only hands over once one of them genuinely confirms the app is serving
- if the visitor clicks **Open** before it's ready, the click is held and
  fires automatically the instant it is

Waking the server is only half the problem, though. Streamlit serves this:

```html
<body>
  <noscript>You need to enable JavaScript to run this app.</noscript>
  <div id="root"></div>
</body>
```

An empty div. The page is built entirely in JavaScript, so a visitor handed
over the moment the server responds *still* watches a white screen while
roughly forty script chunks download.

So there is a second phase. Once the server answers, the page loads the app
once in an offscreen iframe before handing over. Streamlit serves its assets
`Cache-Control: public, immutable, max-age=31536000`, so the real navigation
afterwards reads them from disk cache and paints almost immediately. The
iframe is torn down once loaded — it exists only for that caching side
effect.

The `<img>` probe is the important one, and on this deployment it is the only
one that actually fires. Two things make it necessary:

- Render returns a 502 HTML error page while an instance is booting, and an
  opaque `fetch` resolves on that exactly as it would on success. Relying on
  `fetch` alone would send visitors into an error page.
- The CORS probe doesn't work here. Checked against the live service,
  `/_stcore/health` answers `200` but sends no `Access-Control-Allow-Origin`
  header, so the browser blocks the read.

An `<img>` only fires `onload` for a genuine image response, so neither problem
affects it. `/favicon.png` on the live service returns `200`, `image/png`,
1019 bytes.

**Already have a portfolio site?** You don't need the landing page at all.
Copy `landing/wake.js` across and preheat Render from the link itself:

```html
<script src="wake.js"></script>
<script>
  // Boots the instance on hover, focus, touch or scroll-into-view —
  // usually several seconds before the visitor actually clicks.
  DataVizWake.warmOnIntent("a.dataviz-link", "https://data-viz-studio.onrender.com");
</script>
```

## Tech stack

| Component            | Role                                                  |
|----------------------|-------------------------------------------------------|
| **Streamlit**        | Web framework, widgets, session state                  |
| **pandas**           | File I/O for CSV/JSON/XLSX, dtype inference, statistics |
| **Matplotlib**       | Chart rendering and `PdfPages` report generation        |
| **seaborn**          | Heatmaps, pairplots and regression plots                |
| **NumPy**            | Canvas buffer handling for the combined dashboard       |
| **openpyxl**         | Excel read engine behind `pd.read_excel`                |
| **Render**           | Hosting                                                 |
| **GitHub Actions**   | CI, keep-alive pings, Pages deployment                  |

## Known limitations

- **Sampling affects charts only.** Above 1,000 rows, plots show a random
  sample. The numbers in the PDF report use the full dataset, so a chart and
  the summary table can disagree slightly. This is deliberate — it is the
  trade-off that keeps Matplotlib responsive on large files.
- **Excel reads the first sheet only.** Multi-sheet workbooks need splitting
  first.
- **Session state is per-browser-session.** Refreshing the page clears the
  accumulated dashboard.
- **50 MB upload cap** on the deployed instance, set in
  `.streamlit/config.toml` to fit Render's free 512 MB of RAM. Raise it if you
  deploy somewhere larger.
- **`reportlab` is listed in `requirements.txt` but unused** — PDF generation
  goes through Matplotlib's `PdfPages`. Removing it would shorten the build,
  but it is left in place as-is.
- **`numpy` is imported by `app.py` but not listed** in `requirements.txt`. It
  installs anyway as a pandas/Matplotlib dependency, so nothing breaks; listing
  it explicitly would make the dependency honest.

## Roadmap

- Integrate machine-learning models for prediction and clustering
- Support real-time / streaming data sources
- Personalised dashboard themes
- Per-chart export presets and configurable report layouts
- Multi-sheet Excel support
- Persist dashboards across sessions

## License

Released under the [MIT License](LICENSE).

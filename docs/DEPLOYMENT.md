# Deployment guide

Everything needed to get DataViz Studio running on Render's free tier, with a
landing page that wakes it before a visitor notices it was asleep.

Total time: about 15 minutes. Cost: nothing.

---

## Current status

The app is deployed and live at **<https://data-viz-studio.onrender.com>**.

| Step | State |
|------|-------|
| 1. Render service | ✅ done |
| 2. Landing page pointed at it | ✅ done — committed with the live URL |
| 3. GitHub Pages enabled | ✅ done — live at <https://uzma-yasmeen.github.io/Data-Viz-Studio/> |
| 4. `APP_URL` variable for keep-alive | ✅ done — but the schedule is **off** by choice (step 4) |

Everything is deployed. The steps below are kept for reference, and for
anyone redeploying this from scratch.

---

## 1. Deploy the app to Render

1. Push this repository to GitHub.
2. Sign in at [render.com](https://render.com) and connect your GitHub account.
3. **New → Blueprint**, pick `Data-Viz-Studio`, then **Apply**.

Render reads [`render.yaml`](../render.yaml) and configures the service itself:
free plan, Python runtime, `pip install -r requirements.txt` to build,
`bash start.sh` to run, health check at `/_stcore/health`.

The first build takes 4–6 minutes — Matplotlib and pandas are large wheels.
When it finishes you get a URL like `https://data-viz-studio.onrender.com`.

> **If you set the service up by hand instead of via the blueprint**, the start
> command must be `bash start.sh` (or the equivalent
> `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`).
> Render assigns the port at runtime through `$PORT`; Streamlit defaults to
> 8501 and would never receive traffic. The build succeeds and the health
> check then fails — this is the single most common way this deploy breaks.

### Region

`render.yaml` sets `region: singapore`, the closest Render region to India.
Change it if your users are elsewhere — `oregon`, `frankfurt`, `ohio` and
`virginia` are the other options.

---

## 2. Point the landing page at your service

Two places need the URL, because `<link rel="preconnect">` only accepts a
literal value and cannot read the config file.

**[`landing/config.js`](../landing/config.js):**

```js
appUrl: "https://data-viz-studio.onrender.com",   // no trailing slash
repoUrl: "https://github.com/Uzma-Yasmeen/Data-Viz-Studio",
```

**[`landing/index.html`](../landing/index.html)**, near the top of `<head>`:

```html
<link rel="preconnect" href="https://data-viz-studio.onrender.com" crossorigin>
<link rel="dns-prefetch" href="https://data-viz-studio.onrender.com">
```

---

## 3. Publish the landing page

**Settings → Pages → Build and deployment → Source: GitHub Actions.**

That's the whole setup. [`pages.yml`](../.github/workflows/pages.yml) publishes
the `landing/` folder on every push that touches it. Your page appears at
`https://uzma-yasmeen.github.io/Data-Viz-Studio/`.

This is the URL to share — not the Render one. It loads instantly and wakes
the app in the background.

---

## 4. Enable the keep-alive pings

**Settings → Secrets and variables → Actions → Variables → New repository
variable:**

| Name      | Value                                   |
|-----------|-----------------------------------------|
| `APP_URL` | `https://data-viz-studio.onrender.com`   |

A *variable*, not a secret — the URL is public anyway, and secrets are masked
in logs, which makes debugging a failed ping harder than it needs to be.

[`keep-alive.yml`](../.github/workflows/keep-alive.yml) can then ping
`/_stcore/health`. Trigger it by hand to check it works:
**Actions → Keep Render awake → Run workflow**. A healthy run logs
`attempt 1 -> HTTP 200` and finishes in about 10 seconds.

### The schedule is deliberately off

The `schedule:` block in that workflow is commented out. Pinging every 10
minutes during waking hours costs ~510 of the 750 free instance-hours per
month, which is a poor trade for a project without steady traffic — the
landing page already covers cold starts, and a visitor waits ~40s behind a
progress bar rather than a blank tab.

Running out of instance-hours is **not** a charge. Render suspends the
service until the 1st of the next month. But the pool is shared across every
free service on the account, so one idle app pinging itself can take down
another.

To turn automatic pings back on, uncomment these lines:

```yaml
# schedule:
#   - cron: "*/10 3-19 * * *"    # 03:00-19:00 UTC (08:30-00:30 IST)
```

Note that GitHub also pauses cron schedules in public repositories after 60
days with no commits, and emails you first. Any push re-enables them.

---

## 5. Verify it works

```bash
# Health endpoint responds
curl -i https://data-viz-studio.onrender.com/_stcore/health
# expect: HTTP/2 200 ... ok
```

Then test the cold path properly:

1. Leave the app untouched for 20 minutes (temporarily disable the keep-alive
   workflow, or it will never sleep).
2. Open the GitHub Pages URL in a fresh private window.
3. You should see the progress bar count up and the status flip to
   **Server ready** at roughly 30–60 seconds, after which the button works
   immediately.

To watch the machinery, open DevTools → Network before loading the page. You
should see the `/_stcore/health` request fire within milliseconds, then the
polling probes repeating every ~1.5 s until one succeeds.

---

## How the wake-up works

```
Visitor opens the Pages URL
        │
        ├─ <link rel="preconnect">  ── TCP + TLS to Render, before any JS runs
        │
        ├─ wake.js: fetch /_stcore/health (no-cors, keepalive)
        │       └─ this is the request that makes Render start the instance
        │
        ├─ progress bar paces against a ~55 s expected cold start
        │
        └─ poll every 1.5 s with three probes in parallel:
                 ① CORS read of /_stcore/health   → definitive when it works
                 ② <img> load of /favicon.png     → cannot be faked by a 502
                 ③ opaque reachability fetch      → trusted only twice in a row
                                                     and after 8 s have passed
                        │
                        └─ first confirmation → hand the visitor over
```

Probe ② carries the most weight. While an instance boots, Render answers with
a 502 HTML error page, and an opaque `fetch` resolves on that exactly as it
would on success — so relying on `fetch` alone would redirect people into an
error page. An `<img>` fires `onload` only for a genuine image response, so it
cannot be fooled.

Probe ① turns out **not** to work against this deployment. Checked against the
live service, `/_stcore/health` returns `200` but sends no
`Access-Control-Allow-Origin` header, so the browser blocks the cross-origin
read. It is kept because it costs nothing and is definitive where it does work
— but here it always reports `unknown`.

Probe ③ is the backstop for exactly that case. Because an opaque response
cannot be inspected, it is believed only after two consecutive successes and at
least 8 seconds elapsed.

Verified against `https://data-viz-studio.onrender.com`:

| Probe | Result |
|-------|--------|
| ① CORS read of `/_stcore/health` | `200`, but no CORS header — blocked in-browser |
| ③ `/favicon.png` | `200`, `image/png`, 1019 bytes — **this is the one that fires** |

If none of them confirms within 90 seconds (`maxWaitMs` in `config.js`), the
page stops blocking and lets the visitor through — by that point Render is
almost certainly up, and a working link beats a spinner that never ends.

---

## Alternative hosts

| Host | Notes |
|------|-------|
| **Streamlit Community Cloud** | Free, purpose-built, and does not sleep the same way. Point it at `app.py` and you can skip the entire wake-up layer. The most sensible option if you don't specifically need Render. |
| **Railway / Fly.io** | Use the [`Procfile`](../Procfile) or [`Dockerfile`](../Dockerfile). Same `$PORT` requirement. |
| **Hugging Face Spaces** | Native Streamlit support; needs `app.py` at the repo root, which it already is. |
| **Docker anywhere** | `docker build -t dataviz-studio . && docker run -p 8501:8501 dataviz-studio` |

---

## Troubleshooting

**Build succeeds, health check fails, deploy marked unhealthy.**
The start command isn't binding `$PORT`. Confirm it is `bash start.sh`.

**"Out of memory" during build or first request.**
The free tier has 512 MB. Lower `maxUploadSize` in `.streamlit/config.toml`,
and keep an eye on `MAX_POINTS` in `app.py`.

**Charts render locally but not on Render.**
Matplotlib needs a writable cache directory. `render.yaml` sets
`MPLCONFIGDIR=/tmp/matplotlib` for this; make sure it survived any manual edits.

**Landing page says "App URL not configured".**
`appUrl` in `landing/config.js` is empty.

**Landing page hangs at 94% forever.**
The bar deliberately stops at 94% until a probe confirms readiness. If it never
advances, open the Render URL directly — if that fails too, the problem is the
deploy, not the landing page. Check Render's logs.

**Keep-alive workflow shows a warning annotation.**
It is designed to warn rather than fail, so a transient Render hiccup doesn't
fill the repo with red X marks. Check whether the `APP_URL` variable is set,
then open the Render URL by hand.

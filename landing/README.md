# Landing page

A static page that wakes the Render service the instant a visitor lands on
it, then hands them over once the app is genuinely serving traffic.

## Files

| File         | Purpose                                                        |
|--------------|----------------------------------------------------------------|
| `index.html` | The page itself: project summary + live "waking up" status.     |
| `config.js`  | **The only file you edit.** Your Render URL lives here.         |
| `wake.js`    | Reusable wake/poll logic. No dependencies, no build step.       |

## Setup

1. Deploy the app to Render (see [`../docs/DEPLOYMENT.md`](../docs/DEPLOYMENT.md)).
2. Put the service URL in `config.js` as `appUrl`.
3. Update the two `<link rel="preconnect">` hrefs in `index.html` to the
   same host — they only accept a literal URL, so they can't read the config.
4. Publish this folder (GitHub Pages workflow is already included).

## Reusing the warm-up on another site

If you already have a portfolio and just want the project link to preheat
Render, copy `wake.js` over and add:

```html
<script src="wake.js"></script>
<script>
  var APP = "https://data-viz-studio.onrender.com";

  // Boot the instance as soon as the link is hovered, focused, touched,
  // or scrolled near — typically several seconds before the click.
  DataVizWake.warmOnIntent("a.dataviz-link", APP);
</script>
```

Or, to wake it on every page load regardless of intent:

```html
<script src="wake.js"></script>
<script>DataVizWake.ping("https://data-viz-studio.onrender.com");</script>
```

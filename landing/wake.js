/* ===================================================================
   wake.js — wakes a sleeping Render free-tier service and reports
   when it is actually serving traffic.

   Standalone and dependency-free. Two entry points:

     DataVizWake.ping(appUrl)
         Fire-and-forget. Costs nothing, returns immediately. Drop this
         on any page that links to the app (portfolio, docs, README
         site) so the instance is already booting before the click.

     DataVizWake.waitUntilAwake(appUrl, { onTick, maxWaitMs })
         Polls until the app responds, then resolves. Used by
         index.html to drive the progress screen.
   =================================================================== */
(function (global) {
  "use strict";

  var HEALTH_PATH = "/_stcore/health";   // Streamlit's built-in liveness route
  var ICON_PATH = "/favicon.png";        // served once the app is really up

  function bust(url) {
    return url + (url.indexOf("?") === -1 ? "?" : "&") + "_=" + Date.now();
  }

  /* Fire-and-forget wake request. Enough to make Render start the
     instance; we deliberately ignore the outcome. */
  function ping(appUrl) {
    if (!appUrl) return;
    try {
      fetch(bust(appUrl + HEALTH_PATH), {
        mode: "no-cors",
        cache: "no-store",
        keepalive: true,        // survives navigation away from this page
        redirect: "follow",
      }).catch(function () {});
    } catch (_) {
      // Very old browsers, or fetch blocked by an extension.
      new Image().src = bust(appUrl + HEALTH_PATH);
    }
  }

  function withTimeout(ms) {
    var ctrl = new AbortController();
    var timer = setTimeout(function () { ctrl.abort(); }, ms);
    return { signal: ctrl.signal, clear: function () { clearTimeout(timer); } };
  }

  /* Probe A — a real CORS read. Definitive when it works, but Streamlit
     only sends Access-Control-Allow-Origin on some versions/configs, so
     a failure here proves nothing. */
  function probeHealth(appUrl, timeoutMs) {
    var t = withTimeout(timeoutMs);
    return fetch(bust(appUrl + HEALTH_PATH), {
      mode: "cors", cache: "no-store", signal: t.signal,
    }).then(function (res) {
      t.clear();
      if (res.ok) return "ready";
      return res.status >= 500 ? "not-ready" : "unknown";
    }).catch(function () {
      t.clear();
      return "unknown";
    });
  }

  /* Probe B — load an actual image asset. An <img> only fires onload for
     a genuine image response, so Render's 502 "still booting" page can't
     fake it. This is the trustworthy signal when CORS is unavailable. */
  function probeIcon(appUrl, timeoutMs) {
    return new Promise(function (resolve) {
      var img = new Image();
      var done = false;
      var finish = function (result) {
        if (done) return;
        done = true;
        img.onload = img.onerror = null;
        resolve(result);
      };
      var timer = setTimeout(function () { finish("unknown"); }, timeoutMs);
      img.onload = function () { clearTimeout(timer); finish("ready"); };
      img.onerror = function () { clearTimeout(timer); finish("unknown"); };
      img.src = bust(appUrl + ICON_PATH);
    });
  }

  /* Probe C — opaque reachability. Resolving means *something* answered:
     could be the app, could be Render's holding page. Only trusted after
     it succeeds twice in a row and the instance has had time to boot. */
  function probeReachable(appUrl, timeoutMs) {
    var t = withTimeout(timeoutMs);
    return fetch(bust(appUrl + HEALTH_PATH), {
      mode: "no-cors", cache: "no-store", signal: t.signal,
    }).then(function () {
      t.clear();
      return "reachable";
    }).catch(function () {
      t.clear();
      return "unknown";
    });
  }

  function waitUntilAwake(appUrl, options) {
    options = options || {};
    var maxWaitMs = options.maxWaitMs || 90000;
    var onTick = options.onTick || function () {};
    var startedAt = Date.now();
    var reachableStreak = 0;

    ping(appUrl);

    return new Promise(function (resolve) {
      function settle(reason) {
        onTick({ elapsedMs: Date.now() - startedAt, state: reason });
        resolve(reason);
      }

      function round() {
        var elapsed = Date.now() - startedAt;
        if (elapsed >= maxWaitMs) return settle("timeout");

        var budget = Math.min(12000, maxWaitMs - elapsed);

        Promise.all([
          probeHealth(appUrl, budget),
          probeIcon(appUrl, budget),
          probeReachable(appUrl, budget),
        ]).then(function (results) {
          var health = results[0], icon = results[1], reach = results[2];

          if (health === "ready" || icon === "ready") return settle("ready");

          reachableStreak = reach === "reachable" ? reachableStreak + 1 : 0;

          // Reachable twice running, after enough time for a cold boot:
          // good enough to hand over.
          if (reachableStreak >= 2 && Date.now() - startedAt > 8000) {
            return settle("ready");
          }

          onTick({ elapsedMs: Date.now() - startedAt, state: "waking" });
          setTimeout(round, 1500);
        });
      }

      round();
    });
  }

  /* ------------------------------------------------------------------
     Second half of the problem: a woken server still paints nothing.

     Streamlit serves an empty <div id="root"></div> and builds the page
     in JavaScript, so a visitor handed over the moment the server
     responds still watches a white screen while ~40 chunks download.

     So before handing over, load the app once in an offscreen iframe.
     Its assets are served `Cache-Control: public, immutable,
     max-age=31536000`, so the real navigation afterwards reads them from
     disk cache and paints almost immediately.
     ------------------------------------------------------------------ */
  function preload(appUrl, options) {
    options = options || {};
    var timeoutMs = options.timeoutMs || 20000;
    var settleMs = options.settleMs || 1200;

    return new Promise(function (resolve) {
      var frame = document.createElement("iframe");
      frame.setAttribute("aria-hidden", "true");
      frame.setAttribute("tabindex", "-1");
      frame.title = "Preloading DataViz Studio";
      // Offscreen rather than display:none — both still load, but an
      // offscreen frame is less likely to be treated as hidden and
      // deprioritised.
      frame.style.cssText =
        "position:absolute;left:-9999px;top:0;width:1024px;height:768px;" +
        "border:0;opacity:0;pointer-events:none;";

      var done = false;
      var timer;

      function finish(result) {
        if (done) return;
        done = true;
        clearTimeout(timer);
        frame.onload = frame.onerror = null;

        // The frame holds an open websocket session on the server, and we
        // only ever wanted its caching side effect. Give late-arriving
        // lazy chunks a moment to land, then tear it down.
        setTimeout(function () {
          if (frame.parentNode) frame.parentNode.removeChild(frame);
        }, settleMs);

        setTimeout(function () { resolve(result); }, settleMs);
      }

      timer = setTimeout(function () { finish("timeout"); }, timeoutMs);
      frame.onload = function () { finish("loaded"); };
      frame.onerror = function () { finish("error"); };

      frame.src = appUrl;
      document.body.appendChild(frame);
    });
  }

  /* Wake the server, then warm the browser cache. Resolves once the app
     will actually paint on arrival, not merely respond. */
  function prepare(appUrl, options) {
    options = options || {};
    var onPhase = options.onPhase || function () {};

    onPhase("waking");
    return waitUntilAwake(appUrl, {
      maxWaitMs: options.maxWaitMs,
      onTick: options.onTick,
    }).then(function (outcome) {
      onPhase("loading");
      return preload(appUrl, { timeoutMs: options.preloadMs }).then(function () {
        onPhase("ready");
        return outcome;
      });
    });
  }

  /* Warm the instance when a link to the app is about to be used —
     pointer hover, touch start, or the link scrolling into view.
     Usage: DataVizWake.warmOnIntent('a.project-link', appUrl) */
  function warmOnIntent(selector, appUrl) {
    var nodes = document.querySelectorAll(selector);
    if (!nodes.length) return;
    var fired = false;
    var fire = function () {
      if (fired) return;
      fired = true;
      ping(appUrl);
    };

    Array.prototype.forEach.call(nodes, function (node) {
      node.addEventListener("pointerenter", fire, { once: true });
      node.addEventListener("touchstart", fire, { once: true, passive: true });
      node.addEventListener("focus", fire, { once: true });
    });

    if ("IntersectionObserver" in global) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { fire(); io.disconnect(); }
        });
      }, { rootMargin: "200px" });
      Array.prototype.forEach.call(nodes, function (n) { io.observe(n); });
    }
  }

  global.DataVizWake = {
    ping: ping,
    waitUntilAwake: waitUntilAwake,
    preload: preload,
    prepare: prepare,
    warmOnIntent: warmOnIntent,
  };
})(window);

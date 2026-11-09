// sw-register.js

if ("serviceWorker" in navigator) {
  // Only reload when an existing worker is replaced. The first install must
  // not reload the page the reader just opened.
  const hadController = Boolean(navigator.serviceWorker.controller);
  let refreshing = false;

  navigator.serviceWorker.addEventListener("controllerchange", () => {
    if (!hadController || refreshing) return;
    refreshing = true;
    window.location.reload();
  });

  // Register after the page has loaded: the first visit should not compete
  // with the pre-cache download.
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").then(reg => {
      // Ask for a new worker on each load. The browser would otherwise wait
      // up to 24 hours before checking again.
      reg.update();

      reg.addEventListener("updatefound", () => {
        const newWorker = reg.installing;
        if (!newWorker) return;

        newWorker.addEventListener("statechange", () => {
          if (
            newWorker.state === "installed" &&
            navigator.serviceWorker.controller
          ) {
            if (confirm("A new version of the fast_io docs is available. Reload now?")) {
              newWorker.postMessage("SKIP_WAITING");
            }
          }
        });
      });
    }).catch(err => {
      console.error("SW registration failed:", err);
    });
  });
}

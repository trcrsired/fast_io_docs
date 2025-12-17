// sw-register.js

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").then(reg => {
    console.log("Service Worker registered");

    // Detect new updates
    reg.addEventListener("updatefound", () => {
      const newWorker = reg.installing;
      if (newWorker) {
        newWorker.addEventListener("statechange", () => {
          if (
            newWorker.state === "installed" &&
            navigator.serviceWorker.controller
          ) {
            // A new version is available
            if (confirm("A new version of fast_io docs is available. Reload now?")) {
              newWorker.postMessage("SKIP_WAITING");
            }
          }
        });
      }
    });
  }).catch(err => {
    console.error("SW registration failed:", err);
  });

  // Reload when the new worker takes control
  navigator.serviceWorker.addEventListener("controllerchange", () => {
    window.location.reload();
  });
}

// AniGravity UI shell interactions (UI-only)
// - Mobile sidebar toggle + overlay + Escape close

(function () {
  const sidebar = document.getElementById("sidebar");
  const sidebarToggle = document.getElementById("sidebarToggle");
  const sidebarOverlay = document.getElementById("sidebarOverlay");
  const settingsOverlay = document.getElementById("settingsOverlay");
  const settingsModal = document.getElementById("settingsModal");

  function setSidebarOpen(isOpen) {
    if (!sidebar || !sidebarToggle || !sidebarOverlay) return;
    document.body.classList.toggle("sidebar-open", isOpen);
    sidebarToggle.setAttribute("aria-expanded", String(isOpen));
    sidebarOverlay.hidden = !isOpen;
  }

  function setSettingsOpen(isOpen) {
    if (!settingsOverlay || !settingsModal) return;
    settingsOverlay.hidden = !isOpen;
    settingsModal.hidden = !isOpen;
    if (isOpen) {
      // Close sidebar to avoid stacked overlays on mobile.
      setSidebarOpen(false);
      settingsModal.focus?.();
    }
  }

  if (sidebar && sidebarToggle && sidebarOverlay) {
    sidebarToggle.addEventListener("click", () => {
      setSidebarOpen(!document.body.classList.contains("sidebar-open"));
    });

    sidebarOverlay.addEventListener("click", () => setSidebarOpen(false));
  }

  // Settings open/close (frontend-only)
  document.querySelectorAll('[data-action="open-settings"]').forEach((el) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      setSettingsOpen(true);
    });
  });

  document.querySelectorAll('[data-action="close-settings"]').forEach((el) => {
    el.addEventListener("click", () => setSettingsOpen(false));
  });

  if (settingsOverlay) settingsOverlay.addEventListener("click", () => setSettingsOpen(false));

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      setSidebarOpen(false);
      setSettingsOpen(false);
    }
  });
})();


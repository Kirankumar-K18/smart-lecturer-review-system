/* ============================================================
   Smart Lecturer Review System — main.js
   ============================================================ */

(function () {
  "use strict";

  /* ── Sidebar toggle (mobile) ───────────────────────────── */
  var sidebar     = document.getElementById("sidebar");
  var openBtn     = document.getElementById("sidebarOpen");
  var closeBtn    = document.getElementById("sidebarClose");
  var mainWrapper = document.getElementById("mainWrapper");

  if (openBtn && sidebar) {
    openBtn.addEventListener("click", function () {
      sidebar.classList.add("is-open");
    });
  }

  if (closeBtn && sidebar) {
    closeBtn.addEventListener("click", function () {
      sidebar.classList.remove("is-open");
    });
  }

  // Close sidebar when clicking outside on mobile
  document.addEventListener("click", function (e) {
    if (
      sidebar &&
      sidebar.classList.contains("is-open") &&
      !sidebar.contains(e.target) &&
      e.target !== openBtn
    ) {
      sidebar.classList.remove("is-open");
    }
  });

  /* ── Auto-dismiss alert messages after 5 seconds ──────── */
  var alerts = document.querySelectorAll(".alert");
  alerts.forEach(function (alert) {
    setTimeout(function () {
      alert.style.transition = "opacity .4s";
      alert.style.opacity    = "0";
      setTimeout(function () {
        if (alert.parentNode) alert.parentNode.removeChild(alert);
      }, 400);
    }, 5000);
  });

  /* ── Collapsible panels (Add User forms) ───────────────── */
  window.togglePanel = function (id) {
    var el = document.getElementById(id);
    if (!el) return;
    if (el.style.display === "none" || el.style.display === "") {
      el.style.display = "block";
      el.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } else {
      el.style.display = "none";
    }
  };

  /* ── Set today's date as default for date inputs ──────── */
  var today = new Date().toISOString().split("T")[0];
  var dateInputs = document.querySelectorAll('input[type="date"]');
  dateInputs.forEach(function (input) {
    if (!input.value) {
      input.value = today;
    }
  });

  /* ── Review form — live overall rating preview ─────────── */
  var ratingSelects = document.querySelectorAll(
    '#id_teaching_quality, #id_communication, #id_punctuality, #id_knowledge'
  );

  function updateOverallPreview() {
    var total = 0;
    var count = 0;
    ratingSelects.forEach(function (sel) {
      var v = parseInt(sel.value, 10);
      if (!isNaN(v)) { total += v; count++; }
    });
    var preview = document.getElementById("overall-preview");
    if (preview && count > 0) {
      preview.textContent = "⭐ Overall: " + (total / count).toFixed(2);
    }
  }

  if (ratingSelects.length) {
    ratingSelects.forEach(function (sel) {
      sel.addEventListener("change", updateOverallPreview);
    });

    // Inject preview span after last rating select
    var lastSel = ratingSelects[ratingSelects.length - 1];
    if (lastSel && lastSel.parentNode) {
      var span = document.createElement("span");
      span.id = "overall-preview";
      span.style.cssText = "display:block;margin-top:8px;font-weight:600;color:#eab308;";
      lastSel.parentNode.appendChild(span);
      updateOverallPreview();
    }
  }

  /* ── Confirm reject dialog ─────────────────────────────── */
  window.confirmReject = function (form) {
    var reason = form.querySelector('input[name="rejection_reason"]');
    if (reason && !reason.value.trim()) {
      alert("Please enter a reason for rejection.");
      reason.focus();
      return false;
    }
    return confirm("Are you sure you want to reject this review?");
  };

  /* ── Theme switcher (settings page) ───────────────────── */
  var themeSelect = document.getElementById("id_theme");
  if (themeSelect) {
    themeSelect.addEventListener("change", function () {
      var body = document.body;
      // Remove existing theme classes
      ["light", "dark", "blue", "green"].forEach(function (t) {
        body.classList.remove("theme-" + t);
      });
      body.classList.add("theme-" + this.value);
    });
  }

  /* ── Table row click → highlight ──────────────────────── */
  var tableRows = document.querySelectorAll(".table tbody tr");
  tableRows.forEach(function (row) {
    row.style.cursor = "pointer";
    row.addEventListener("click", function () {
      tableRows.forEach(function (r) { r.style.background = ""; });
      this.style.background = "rgba(79,70,229,.06)";
    });
  });

})();

/* jshint esversion: 6 */
/**
 * Frontend logic for stock web app.
 *
 * Data Flow:
 *  - Python calls window.initApp(...) on load to initialize tickers and default dates.
 *  - User changes inputs -> fetchPlotData() -> ask backend for filtered data.
 *  - Backend calls window.plotStockData(x, y, errorMsg) to plot or show an error.
 *  - Stat buttons call toggleStatLine(stat). If turned on, JS asks backend for the stat.
 *  - Backend calls window.drawStatLine(stat, upper, lower, errorMsg) to overlay lines.
 */

// Only keep constants where we expect to change or reuse the value.
const ERR_START_AFTER_END = "Start date cannot be after end date.";
const LABEL_STD_UPPER = "Mean + Std Dev";
const LABEL_STD_LOWER = "Mean - Std Dev";

// Module state kept simple for readability
let tickers = [], chart = null;
let plotX = [];
let activeStats = { mean: false, median: false, std: false };

/**
 * Initialize UI and draw the initial chart.
 * Called by Python via jsc.eval_js_code("window.initApp([...], 'YYYY-MM-DD', 'YYYY-MM-DD')")
 */
window.initApp = function(tickerList, defaultStart, defaultEnd) {
  tickers = tickerList;

  // Add ticker values to dropdown
  const tickerSelect = document.getElementById("ticker-select");
  tickerSelect.innerHTML = tickers.map(t => `<option value="${t}">${t}</option>`).join('');

  // Set initial start and end dates
  const startDateInput = document.getElementById("start-date");
  const endDateInput   = document.getElementById("end-date");
  startDateInput.value = defaultStart;
  endDateInput.value   = defaultEnd;

  // Add event listeners to update chart
  tickerSelect.onchange   = fetchPlotData;
  startDateInput.onchange = fetchPlotData;
  endDateInput.onchange   = fetchPlotData;
  
  // Add event listeners to plot overlay lines
  document.getElementById("mean-btn").onclick   = () => toggleStatLine("mean");
  document.getElementById("median-btn").onclick = () => toggleStatLine("median");
  document.getElementById("std-btn").onclick    = () => toggleStatLine("std");

  // Plot initial chart from default values
  fetchPlotData();
};

/**
 * Read inputs, perform light validation, reset state, and request data from backend.
 */
function fetchPlotData() {
  const ticker         = document.getElementById("ticker-select").value;
  const startDateInput = document.getElementById("start-date");
  const endDateInput   = document.getElementById("end-date");
  const startVal       = startDateInput.value;
  const endVal         = endDateInput.value;

  const plotErrorDiv = document.getElementById("plot-error");

  // Reset UI 
  plotErrorDiv.textContent = "";
  startDateInput.classList.remove("input-error");
  endDateInput.classList.remove("input-error");

  ["mean", "median", "std"].forEach((s) => {
    document.getElementById(`${s}-btn`).classList.remove("active");
    const err = document.getElementById(`${s}-error`);
    if (err) err.textContent = "";
    activeStats[s] = false;
  });
  
  if (chart) chart.destroy();

  // Minimal client validation: start <= end
  const startDate = new Date(startVal);
  const endDate = new Date(endVal);
  
  if (startDate > endDate) {
    plotErrorDiv.textContent = ERR_START_AFTER_END;
    startDateInput.classList.add("input-error");
    endDateInput.classList.add("input-error");
    return;
  }

  // Ask backend for filtered Close data
  call_py('get_plot_data', ticker, startVal, endVal);
}

/**
 * Plot base chart or display an error under the chart.
 * Called by Python: window.plotStockData(x, y, errorMsg).
 */
window.plotStockData = function(x, y, errorMsg) {
  const plotErrorDiv = document.getElementById("plot-error");

  if (errorMsg) {
    plotErrorDiv.textContent = errorMsg;
    if (chart) { chart.destroy(); chart = null; }
    plotX = []; 
    return;
  }

  plotErrorDiv.textContent = "";
  // get points necessary to plot over-lay lines (X -> size)
  plotX = x; 

  const ctx = document.getElementById("stock-chart").getContext('2d');

  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: x,
      datasets: [{
        label: "Close Price ($)",
        data: y,
        borderColor: "blue",
        pointRadius: 1.5
      }]
    },
    options: {
      responsive: false,
      scales: {
             // presents a fluid line (no breaks due to skipped dates)
        x: { type: 'category', title: { display: true, text: 'Date' },
             // avoids clutter due to excessive ticks
             ticks: { autoSkip: true, maxTicksLimit: 12 } },
             // stock traders usually care for the relative high and lows
        y: { title: { display: true, text: 'Price ($)' }, beginAtZero: false }
      }
    }
  });
}

/**
 * Find a dataset by its label. Used to replace/remove overlays.
 */
function getStatDatasetIndex(label) {
  if (!chart) return -1;
  return chart.data.datasets.findIndex((ds) => ds.label === label);
}

/**
 * Toggle a stat overlay from the UI (buttons call this via onclick).
 * If turning ON, ask backend for the stat; if turning OFF, remove the overlay dataset(s).
 */
function toggleStatLine(stat) {
  // no chart - reset button
  
  
  // toggle button
  activeStats[stat] = !activeStats[stat];
  document.getElementById(`${stat}-btn`)
    .classList.toggle("active", activeStats[stat]);

  // reset stat-error
  const statErrorDiv = document.getElementById(`${stat}-error`);
  if (statErrorDiv) statErrorDiv.textContent = "";

  // get state 
  const ticker         = document.getElementById("ticker-select").value;
  const startDateInput = document.getElementById("start-date");
  const endDateInput   = document.getElementById("end-date");
  const startVal       = startDateInput.value;
  const endVal         = endDateInput.value;

  // get stat value for overlay if toggled on
  if (activeStats[stat]) {
    call_py('get_stat_value', ticker, startVal, endVal, stat);
  // remove overlay (splice) if toggled off
  } else {
    if (!chart) return;

    if (stat === "mean") {
      const i = getStatDatasetIndex("Mean");
      if (i > -1) chart.data.datasets.splice(i, 1);
    }
    if (stat === "median") {
      const i = getStatDatasetIndex("Median");
      if (i > -1) chart.data.datasets.splice(i, 1);
    }
    if (stat === "std") {
      const i1 = getStatDatasetIndex(LABEL_STD_UPPER);
      if (i1 > -1) chart.data.datasets.splice(i1, 1);
      const i2 = getStatDatasetIndex(LABEL_STD_LOWER);
      if (i2 > -1) chart.data.datasets.splice(i2, 1);
    }

    chart.update();
  }
}

/**
 * Draw or remove stat overlays based on backend response.
 * Only Std Dev can return a specific error ('Only one price point, two required for std dev.').
 * General logic: if overlay exists remove (splice), then add new overlay
 */
window.drawStatLine = function(stat, upper, lower, errorMsg) {
  if (errorMsg) {
    const statErrorDiv = document.getElementById(`${stat}-error`);
    if (statErrorDiv) statErrorDiv.textContent = errorMsg;
    // toggle button off 
    if (activeStats[stat]) {
      activeStats[stat] = false;
      document.getElementById(`${stat}-btn`).classList.remove("active");
    }
    return;
  }

  // doesn't exist due to frontend error 
  if (!chart) return;

  if (stat === "mean") {
    const i = getStatDatasetIndex("Mean");
    if (i > -1) chart.data.datasets.splice(i, 1);
    chart.data.datasets.push({
      label: "Mean",
      // returns array of upper with the length of X -> [upper, upper,...]
      // plotted as y axis data 
      data: plotX.map(() => upper),
      borderColor: "green",
      borderWidth: 2,
      fill: false,
      borderDash: [7, 5],
      pointRadius: 0
    });
  }

  if (stat === "median") {
    const i = getStatDatasetIndex("Median");
    if (i > -1) chart.data.datasets.splice(i, 1);
    chart.data.datasets.push({
      label: "Median",
      // returns array of upper with the length of X -> [upper, upper,...]
      // plotted as y axis data 
      data: plotX.map(() => upper),
      borderColor: "purple",
      borderWidth: 2,
      fill: false,
      borderDash: [7, 5],
      pointRadius: 0
    });
  }

  if (stat === "std") {
    const i1 = getStatDatasetIndex(LABEL_STD_UPPER);
    if (i1 > -1) chart.data.datasets.splice(i1, 1);
    const i2 = getStatDatasetIndex(LABEL_STD_LOWER);
    if (i2 > -1) chart.data.datasets.splice(i2, 1);

    chart.data.datasets.push(
      {
        label: LABEL_STD_UPPER,
        // returns array of upper with the length of X -> [upper, upper,...]
        // plotted as y axis data 
        data: plotX.map(() => upper),
        borderColor: "orange",
        borderWidth: 2,
        fill: false,
        borderDash: [6, 4],
        pointRadius: 0
      },
      {
        label: LABEL_STD_LOWER,
        // returns array of upper with the length of X -> [upper, upper,...]
        // plotted as y axis data 
        data: plotX.map(() => lower),
        borderColor: "red",
        borderWidth: 2,
        fill: false,
        borderDash: [6, 4],
        pointRadius: 0
      }
    );
  }

  chart.update();
};

const API_BASE_URL = "https://asaninvest.fastapicloud.dev";

const stockSelect = document.getElementById("stock-select");
const chartTitle = document.getElementById("chart-title");
const forecastResults = document.getElementById("forecast-results");
const themeToggle = document.getElementById("theme-toggle");
let priceChart = null;
let allStocks = [];

function applyTheme(theme) {
  document.body.setAttribute("data-theme", theme);
  themeToggle.textContent = theme === "light" ? "☀️" : "🌙";
  localStorage.setItem("theme", theme);
}

const savedTheme = localStorage.getItem("theme") || "dark";
applyTheme(savedTheme);

themeToggle.addEventListener("click", () => {
  const current = document.body.getAttribute("data-theme") || "dark";
  const next = current === "dark" ? "light" : "dark";
  applyTheme(next);
});

// Load the stock list and populate the dropdown
async function loadStocks() {
  try {
    const response = await fetch(`${API_BASE_URL}/stocks`);
    if (!response.ok) throw new Error("Failed to fetch stocks");
    const stocks = await response.json();

    stockSelect.innerHTML = "";
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Select a stock...";
    stockSelect.appendChild(placeholder);

    allStocks = stocks;
    stocks.forEach((stock) => {
      const option = document.createElement("option");
      option.value = stock.symbol;
      option.textContent = `${stock.symbol} — ${stock.name} (${stock.sector})`;
      stockSelect.appendChild(option);
    });
  } catch (err) {
    stockSelect.innerHTML = '<option value="">Failed to load stocks</option>';
    console.error(err);
  }
}

// Fetch and render price history as a line chart
async function loadHistory(symbol) {
  try {
    const response = await fetch(`${API_BASE_URL}/history/${symbol}`);
    if (!response.ok) throw new Error("Failed to fetch history");
    const history = await response.json();

    // history comes back newest-first from the API, reverse for a left-to-right chart
    const sorted = [...history].reverse();
    const labels = sorted.map((point) => point.date);
    const closes = sorted.map((point) => point.close);

    const ctx = document.getElementById("price-chart").getContext("2d");

    if (priceChart) {
      priceChart.destroy();
    }

    priceChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: `${symbol} Close Price`,
            data: closes,
            borderColor: "#4ade80",
            backgroundColor: "rgba(74, 222, 128, 0.1)",
            fill: true,
            tension: 0.2,
            pointRadius: 0,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { labels: { color: "#e8e8e8" } },
        },
        scales: {
          x: { ticks: { color: "#a0a0a0", maxTicksLimit: 8 } },
          y: { ticks: { color: "#a0a0a0" } },
        },
      },
    });
  } catch (err) {
    console.error(err);
  }
}

// Fetch and render the 4-horizon forecast
async function loadForecast(symbol) {
  forecastResults.innerHTML = "<p>Loading forecast...</p>";
  try {
    const response = await fetch(`${API_BASE_URL}/predict/${symbol}`);
    if (!response.ok) throw new Error("Failed to fetch forecast");
    const data = await response.json();

    const horizonLabels = {
      "1w": "1 Week",
      "2w": "2 Weeks",
      "3w": "3 Weeks",
      "4w": "4 Weeks",
    };

    forecastResults.innerHTML = "";
    Object.keys(horizonLabels).forEach((key) => {
        const horizonData = data.predictions[key];
        const percent = (horizonData.return * 100).toFixed(2);
        const amount = horizonData.amount.toFixed(2);
        const isPositive = horizonData.return >= 0;
        
        const card = document.createElement("div");
        card.className = "forecast-card fade-in";
        card.innerHTML = `
            <span class="horizon-label">${horizonLabels[key]}</span>
            <span class="horizon-value ${isPositive ? "positive" : "negative"}">
            ${isPositive ? "+" : ""}${percent}%
            </span>
            <span class="horizon-amount">Rs. ${amount}</span>
        `;
        forecastResults.appendChild(card);
    });
  } catch (err) {
    forecastResults.innerHTML = "<p>Could not load forecast for this stock.</p>";
    console.error(err);
  }
}

// When a stock is selected, load its history and forecast together
stockSelect.addEventListener("change", () => {
  const symbol = stockSelect.value;
  if (!symbol) return;

  const selectedStock = allStocks.find(s => s.symbol === symbol);
  const displayName = selectedStock ? `${selectedStock.name} (${selectedStock.symbol})` : symbol;
  chartTitle.textContent = `Price History of ${displayName}`;
  
  loadHistory(symbol);
  loadForecast(symbol);
});

// Kick things off
loadStocks();
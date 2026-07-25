// Swap this to your deployed backend URL once it's live
const API_BASE_URL = "http://127.0.0.1:8000";

const stockSelect = document.getElementById("stock-select");
const chartTitle = document.getElementById("chart-title");
const forecastResults = document.getElementById("forecast-results");
let priceChart = null;

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
      const value = data.predictions[key];
      const percent = (value * 100).toFixed(2);
      const isPositive = value >= 0;

      const card = document.createElement("div");
      card.className = "forecast-card";
      card.innerHTML = `
        <span class="horizon-label">${horizonLabels[key]}</span>
        <span class="horizon-value ${isPositive ? "positive" : "negative"}">
          ${isPositive ? "+" : ""}${percent}%
        </span>
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

  chartTitle.textContent = `Price History — ${symbol}`;
  loadHistory(symbol);
  loadForecast(symbol);
});

// Kick things off
loadStocks();
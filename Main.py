import yfinance as yf
from fpdf import FPDF
from datetime import datetime
from fredapi import Fred

# ---------------- SETUP ----------------
FRED_API_KEY = '2b04594b42794b8526db7ad5ad7ac29f'
fred = Fred(api_key=FRED_API_KEY)

# Indices
indices = {
    "NASDAQ": "^IXIC",
    "S&P 500": "^GSPC",
    "DOW": "^DJI",
    "FTSE 100": "^FTSE",
    "SSE Composite": "000001.SS"
}

# Economic Indicators (FRED series)
fred_series = {
    "Consumer Price Index (CPI)": "CPIAUCSL",
    "Producer Price Index (PPI)": "PPIACO",
    "Real GDP": "GDPC1",
    "Industrial Production Index": "INDPRO",
    "Median Sales Price of New Houses": "MSPNHSUS",
    "Consumer Sentiment (UMich)": "UMCSENT"
}

# Exchange Rates (FRED series)
exchange_series = {
    "EUR/USD": "DEXUSEU",
    "GBP/USD": "DEXUSUK",
    "USD/JPY": "DEXJPUS",
    "AUD/USD": "DEXUSAL",
    "USD/CAD": "DEXCAUS",
    "NZD/USD": "DEXUSNZ"
}

# ---------------- FETCH INDEX DATA ----------------
index_data = {}
for name, symbol in indices.items():
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="2d")
    if not hist.empty:
        latest = hist.iloc[-1]
        index_data[name] = {
            "Open": round(latest["Open"], 2),
            "Close": round(latest["Close"], 2)
        }
    else:
        index_data[name] = {"Open": "N/A", "Close": "N/A"}

# ---------------- FETCH FRED DATA ----------------
def get_latest_value(series_id):
    try:
        data = fred.get_series(series_id)
        value = data.dropna().iloc[-1]
        return round(value, 2)
    except Exception as e:
        return f"Error: {e}"

# Economic indicators
economic_data = {label: get_latest_value(series_id) for label, series_id in fred_series.items()}
# Exchange rates
exchange_data = {label: get_latest_value(series_id) for label, series_id in exchange_series.items()}

# ---------------- GENERATE PDF ----------------
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", 'B', 16)
pdf.cell(200, 10, txt=f"Pre-Market Report: {datetime.today().strftime('%A, %B %d, %Y')}", ln=True, align='C')
pdf.ln(10)

# 📉 Closing Prices
pdf.set_font("Arial", 'B', 14)
pdf.cell(200, 10, txt="Major Indices - Closing Prices", ln=True)
pdf.set_font("Arial", '', 12)
for name in index_data:
    pdf.cell(200, 10, txt=f"{name}: {index_data[name]['Close']}", ln=True)
pdf.ln(5)

# 🕘 Opening Prices
pdf.set_font("Arial", 'B', 14)
pdf.cell(200, 10, txt="Major Indices - Opening Prices", ln=True)
pdf.set_font("Arial", '', 12)
for name in index_data:
    pdf.cell(200, 10, txt=f"{name}: {index_data[name]['Open']}", ln=True)
pdf.ln(10)

# 📰 Economic Indicators
pdf.set_font("Arial", 'B', 14)
pdf.cell(200, 10, txt="Key Economic Indicators (FRED)", ln=True)
pdf.set_font("Arial", '', 12)
for label, value in economic_data.items():
    pdf.cell(200, 10, txt=f"{label}: {value}", ln=True)
pdf.ln(10)

# 💱 Exchange Rates
pdf.set_font("Arial", 'B', 14)
pdf.cell(200, 10, txt="Exchange Rates (FRED)", ln=True)
pdf.set_font("Arial", '', 12)
for label, value in exchange_data.items():
    pdf.cell(200, 10, txt=f"{label}: {value}", ln=True)

# Save PDF
pdf.output("PreMarket_Report.pdf")

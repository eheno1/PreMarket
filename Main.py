import yfinance as yf
from fpdf import FPDF
from datetime import datetime
from fredapi import Fred

# Define the index tickers
indices = {
    "NASDAQ": "^IXIC",
    "S&P 500": "^GSPC",
    "DOW": "^DJI",
    "FTSE 100": "^FTSE",
    "SSE Composite": "000001.SS"
}

# FRED API setup
FRED_API_KEY = '2b04594b42794b8526db7ad5ad7ac29f'
fred = Fred(api_key=FRED_API_KEY)

# Economic indicators to fetch from FRED
fred_series = {
    "Unemployment Rate": "UNRATE",
    "Consumer Price Index (CPI)": "CPIAUCSL",
    "Federal Funds Rate": "FEDFUNDS"
}

# Fetch index price data
index_data = {}
for name, symbol in indices.items():
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="2d")  # grab 2 days in case of holiday
    if not hist.empty:
        latest = hist.iloc[-1]
        index_data[name] = {
            "Open": round(latest["Open"], 2),
            "Close": round(latest["Close"], 2)
        }
    else:
        index_data[name] = {"Open": "N/A", "Close": "N/A"}

# Fetch economic indicators
economic_data = {}
for label, series_id in fred_series.items():
    try:
        series = fred.get_series(series_id)
        latest_value = series.dropna().iloc[-1]
        economic_data[label] = round(latest_value, 2)
    except Exception as e:
        economic_data[label] = f"Error: {e}"

# PDF generation
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", 'B', 16)
pdf.cell(200, 10, txt=f"Pre-Market Report: {datetime.today().strftime('%A, %B %d, %Y')}", ln=True, align='C')
pdf.ln(10)

# 📉 Closing Prices Table
pdf.set_font("Arial", 'B', 14)
pdf.cell(200, 10, txt="Major Indices - Closing Prices", ln=True)
pdf.set_font("Arial", '', 12)
for name in index_data:
    pdf.cell(200, 10, txt=f"{name}: {index_data[name]['Close']}", ln=True)

pdf.ln(10)

# 🕘 Opening Prices Table
pdf.set_font("Arial", 'B', 14)
pdf.cell(200, 10, txt="Major Indices - Opening Prices", ln=True)
pdf.set_font("Arial", '', 12)
for name in index_data:
    pdf.cell(200, 10, txt=f"{name}: {index_data[name]['Open']}", ln=True)

pdf.ln(10)

# 📰 Economic Indicators Section
pdf.set_font("Arial", 'B', 14)
pdf.cell(200, 10, txt="Key Economic Indicators (FRED)", ln=True)
pdf.set_font("Arial", '', 12)
for label, value in economic_data.items():
    pdf.cell(200, 10, txt=f"{label}: {value}", ln=True)

# Save PDF
pdf.output("PreMarket_Report.pdf")

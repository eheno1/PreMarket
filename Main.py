import yfinance as yf
from fpdf import FPDF
from datetime import datetime

# Define the index tickers
indices = {
    "NASDAQ": "^IXIC",
    "S&P 500": "^GSPC",
    "DOW": "^DJI",
    "FTSE 100": "^FTSE",
    "SSE Composite": "000001.SS"
}

# Fetch data
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

pdf.output("PreMarket_Report.pdf")

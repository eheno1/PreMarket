import yfinance as yf
from fpdf import FPDF
from datetime import datetime
from fredapi import Fred
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import matplotlib.pyplot as plt
import os

# --- Setup ---
FRED_API_KEY = '2b04594b42794b8526db7ad5ad7ac29f'
fred = Fred(api_key=FRED_API_KEY)

indices = {
    "NASDAQ": "^IXIC",
    "S&P 500": "^GSPC",
    "DOW": "^DJI",
    "FTSE 100": "^FTSE",
    "SSE Composite": "000001.SS"
}

fred_series = {
    "Consumer Price Index (CPI)": "CPIAUCSL",
    "Producer Price Index (PPI)": "PPIACO",
    "Real GDP": "GDPC1",
    "Industrial Production Index": "INDPRO",
    "Median Sales Price of New Houses": "MSPNHSUS",
    "Consumer Sentiment (UMich)": "UMCSENT"
}

import requests
from bs4 import BeautifulSoup
from datetime import datetime

def get_today_econ_calendar():
    url = "https://www.marketwatch.com/economy-politics/calendar"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    today = datetime.today().strftime('%A, %B %d, %Y')
    tables = soup.find_all("div", class_="element element--table")
    
    target = None
    for table in tables:
        header = table.find_previous_sibling("h3")
        if header and today in header.get_text():
            target = table
            break

    if not target:
        return []

    rows = target.select("table tr")[1:]
    data = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 6:
            data.append([
                cols[0].text.strip(),
                cols[1].text.strip(),
                cols[2].text.strip(),
                cols[3].text.strip(),
                cols[4].text.strip(),
                cols[5].text.strip(),
            ])
    return data

exchange_series = {
    "EUR/USD": "DEXUSEU",
    "GBP/USD": "DEXUSUK",
        "AUD/USD": "DEXUSAL",
    "USD/CAD": "DEXCAUS",
    "NZD/USD": "DEXUSNZ"
}

# --- Fetch Index Data ---
index_data = {}
for name, symbol in indices.items():
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="2d")
    if not hist.empty:
        latest = hist.iloc[-1]
        open_price = latest["Open"]
        close_price = latest["Close"]
        index_data[name] = {
            "Open": round(open_price, 2),
            "Close": round(close_price, 2)
        }
    else:
        index_data[name] = {"Open": "N/A", "Close": "N/A"}

# --- Scrape Earnings Calls ---
options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

url = "https://finance.yahoo.com/calendar/earnings"
driver.get(url)
time.sleep(5)

rows = driver.find_elements(By.XPATH, "//table//tbody/tr")[:10]

earnings_data = []
for row in rows:
    cols = row.find_elements(By.TAG_NAME, "td")
    if len(cols) >= 8:
        earnings_data.append([
            cols[0].text,
            cols[1].text,
            cols[7].text,
            cols[2].text
        ])

driver.quit()

earnings_df = pd.DataFrame(earnings_data, columns=["Symbol", "Company", "Market Cap", "Event"])
earnings_df["Event"] = earnings_df["Event"].str.replace("Release", "").str.strip()

# Add Open Prices for earnings tickers
def fetch_open_price(ticker):
    try:
        yf_ticker = yf.Ticker(ticker)
        hist = yf_ticker.history(period="1d")
        if not hist.empty:
            return round(hist.iloc[-1]["Open"], 2)
        return "N/A"
    except:
        return "N/A"

earnings_df["Open Price"] = earnings_df["Symbol"].apply(fetch_open_price)

# --- Fetch FRED Data ---
def get_latest_value(series_id):
    try:
        data = fred.get_series(series_id)
        value = data.dropna().iloc[-1]
        return round(value, 2)
    except Exception as e:
        return f"Error: {e}"

economic_data = {label: get_latest_value(series_id) for label, series_id in fred_series.items()}
exchange_data = {label: get_latest_value(series_id) for label, series_id in exchange_series.items()}

# --- Generate PDF ---
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", 'B', 16)
pdf.cell(200, 10, txt=f"Pre-Market Report: {datetime.today().strftime('%A, %B %d, %Y')}", ln=True, align='C')
pdf.ln(10)

# --- Indices Table ---
pdf.set_font("Arial", 'B', 14)
pdf.cell(200, 10, txt="Major Indices - Close vs Open", ln=True)
pdf.set_font("Arial", 'B', 12)
pdf.set_fill_color(200, 200, 200)
pdf.cell(50, 8, "Index", border=1, fill=True)
pdf.cell(40, 8, "Close", border=1, fill=True)
pdf.cell(40, 8, "Open", border=1, fill=True)
pdf.cell(40, 8, "% Change", border=1, ln=True, fill=True)

pdf.set_font("Arial", '', 12)
for name in index_data:
    data = index_data[name]
    close = data['Close']
    open_ = data['Open']

    close_str = f"${close}"
    open_str = f"${open_}"
    pct_str = "N/A"

    if isinstance(open_, float) and isinstance(close, float):
        pct_change = round(((open_ - close) / close) * 100, 2)
        pct_str = f"{pct_change:+.2f}%"

        pdf.set_text_color(0, 0, 0)
        pdf.cell(50, 8, name, border=1)
        pdf.cell(40, 8, close_str, border=1)

        pdf.set_text_color(0, 0, 0)
        pdf.cell(40, 8, open_str, border=1)

        if open_ > close:
            pdf.set_text_color(0, 128, 0)  # green
        elif open_ < close:
            pdf.set_text_color(255, 0, 0)  # red
        else:
            pdf.set_text_color(0, 0, 0)
        pdf.cell(40, 8, pct_str, border=1, ln=True)
    else:
        pdf.set_text_color(0, 0, 0)
        pdf.cell(50, 8, name, border=1)
        pdf.cell(40, 8, close_str, border=1)
        pdf.cell(40, 8, open_str, border=1)
        pdf.cell(40, 8, pct_str, border=1, ln=True)

pdf.set_text_color(0, 0, 0)

# --- Earnings Calls ---
pdf.ln(10)
pdf.set_font("Arial", 'B', 14)
pdf.cell(200, 10, txt="Top 10 Earnings Calls (Yahoo Finance)", ln=True)
pdf.set_font("Arial", '', 10)
pdf.set_fill_color(230, 230, 230)
pdf.cell(30, 8, "Open", border=1, fill=True)
pdf.cell(30, 8, "Symbol", border=1, fill=True)
pdf.cell(60, 8, "Company", border=1, fill=True)
pdf.cell(30, 8, "Market Cap", border=1, fill=True)
pdf.cell(40, 8, "Event", border=1, ln=True, fill=True)

for _, row in earnings_df.iterrows():
    pdf.cell(30, 8, f"${row['Open Price']}", border=1)
    pdf.cell(30, 8, str(row["Symbol"]), border=1)
    pdf.cell(60, 8, str(row["Company"])[:30], border=1)
    pdf.cell(30, 8, str(row["Market Cap"]), border=1)
    pdf.cell(40, 8, str(row["Event"]), border=1, ln=True)

# --- Economic Indicators ---
pdf.ln(10)
pdf.set_font("Arial", 'B', 14)
pdf.cell(200, 10, txt="Key Economic Indicators (FRED)", ln=True)
pdf.set_font("Arial", '', 12)

selected_indicators = {
    "Consumer Price Index (CPI)": "CPIAUCSL",
    "Producer Price Index (PPI)": "PPIACO",
    "Industrial Production Index (IPI)": "INDPRO"
}

# Generate and insert economic indicators chart
fig, ax = plt.subplots(figsize=(7, 3.5))
for label, series_id in selected_indicators.items():
    try:
        series = fred.get_series(series_id)
        series = series.dropna().last("5Y")
        ax.plot(series.index, series.values, label=label, linewidth=1.5)
    except:
        continue

ax.set_title("Key Economic Indicators 5Y (CPI, PPI, IPI)", fontsize=10)
ax.tick_params(axis='x', labelrotation=30, labelsize=7)
ax.tick_params(axis='y', labelsize=7)
ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
ax.legend(fontsize=7, loc='upper left', frameon=True)
fig.tight_layout()

econ_chart_path = "economic_indicators_chart.png"
plt.savefig(econ_chart_path)
plt.close(fig)

# Print values on the left
x_left = 10
x_right = 110
pdf.set_xy(x_left, pdf.get_y())
for label in selected_indicators:
    value = get_latest_value(selected_indicators[label])
    pdf.cell(90, 8, txt=f"{label}: {value}", ln=True)

# Insert chart on the right
pdf.set_xy(x_right, pdf.get_y() - (8 * len(selected_indicators)))
pdf.image(econ_chart_path, x=x_right, w=80)
pdf.set_xy(x_right, pdf.get_y())
pdf.set_font("Arial", '', 9)
pdf.set_xy(x_right, pdf.get_y() + 3)

# Clean up
if os.path.exists(econ_chart_path):
    os.remove(econ_chart_path)

calendar_data = get_today_econ_calendar()
if calendar_data:
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Today's Economic Calendar", ln=True)
    pdf.set_font("Arial", 'B', 10)
    headers = ["Time (ET)", "Report", "Period", "Actual", "Forecast", "Previous"]
    for h in headers:
        pdf.cell(33, 8, h, border=1, fill=True)
    pdf.ln()
    
    pdf.set_font("Arial", '', 10)
    for row in calendar_data:
        for item in row:
            pdf.cell(33, 8, item[:15], border=1)
        pdf.ln()
else:
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 10, txt="No economic calendar data available for today.", ln=True)


# --- Exchange Rates ---
pdf.ln(10)
pdf.set_font("Arial", 'B', 14)
pdf.cell(200, 10, txt="Exchange Rates (FRED)", ln=True)
pdf.set_font("Arial", '', 12)

# Generate and insert chart
import matplotlib.pyplot as plt
import os

def create_exchange_rate_chart(data):
    pairs = list(data.keys())
    fig, ax = plt.subplots(figsize=(7, 3.5))    
    for pair in pairs:
        if pair == "USD/JPY":
            continue
        try:
            series = fred.get_series(exchange_series[pair])
            series = series.dropna().last("3M")
            ax.plot(series.index[::5], series.values[::5], label=pair, linewidth=1.5)
        except:
            continue

    ax.set_title("Exchange Rates 3M", fontsize=10)
    ax.tick_params(axis='x', labelrotation=30, labelsize=7)
    ax.tick_params(axis='y', labelsize=7)
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
    ax.legend(fontsize=7, loc='upper left', frameon=True)
    fig.tight_layout()

    chart_path = "exchange_rates_chart.png"
    plt.savefig(chart_path)
    plt.close(fig)
    return chart_path

chart_path = create_exchange_rate_chart(exchange_data)

# Set X/Y for left/right layout
x_left = 10
x_right = 110
pdf.set_xy(x_left, pdf.get_y())

# Print rates on the left
for label, value in exchange_data.items():
    pdf.cell(90, 8, txt=f"{label}: {value}", ln=True)

# Insert chart on the right
pdf.set_xy(x_right, pdf.get_y() - (8 * len(exchange_data)))
pdf.image(chart_path, x=x_right, w=80)

# Clean up chart file
if os.path.exists(chart_path):
    os.remove(chart_path)

# --- Save PDF ---
pdf.output("PreMarket_Report.pdf")

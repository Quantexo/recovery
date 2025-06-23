import streamlit as st
import pandas as pd
import numpy as np
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import plotly.graph_objects as go

# --- EMAIL CONFIGURATION ---
EMAIL_SENDER = "quantexo2005@gmail.com"
EMAIL_PASSWORD = "itim rgcp ztsi cbef"  # Use Gmail App Password
EMAIL_RECEIVER = "prashantstha0912@gmail.com"  # Change to your actual email

# --- STREAMLIT PAGE SETTINGS ---
st.set_page_config(page_title="Quantexo - NEPSE Signal Scanner", layout="wide")
st.title("📊 Quantexo NEPSE Signal Scanner")
st.markdown("This app scans NEPSE OHLCV data for advanced confluence-based signals.")

# --- LOAD DATA ---
@st.cache_data
def load_data(sheet_url):
    try:
        url = sheet_url.replace("/edit?gid=", "/export?format=csv&gid=")
        df = pd.read_csv(url)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

sheet_url = "https://docs.google.com/spreadsheets/d/1Q_En7VGGfifDmn5xuiF-t_02doPpwl4PLzxb4TBCW0Q/edit?gid=0"
df = load_data(sheet_url)

# 🧼 Clean and convert columns
numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df.dropna(subset=numeric_cols, inplace=True)  # Drop rows with missing OHLCV

if df.empty:
    st.stop()

# --- SIGNAL DETECTION FUNCTION ---
def detect_signals(symbol_df):
    signals = []
    for i in range(3, len(symbol_df)):
        row = symbol_df.iloc[i]
        prev = symbol_df.iloc[i - 1]
        prev2 = symbol_df.iloc[i - 2]
        bos = row['Close'] > prev['High']
        liquidity_sweep = prev2['Low'] > row['Low']
        fvg = abs(prev['High'] - prev['Low']) > 2 * abs(row['High'] - row['Low'])
        if bos and liquidity_sweep and fvg:
            signals.append({
                "Date": row['Date'],
                "Signal": "Bullish Confluence",
                "Price": row['Close'],
                "Emoji": "🐂"  # You can change this based on signal type
            })
    return signals

# --- SYMBOL FILTER ---
symbols = df['Symbol'].unique()
selected_symbol = st.selectbox("Select Symbol", sorted(symbols))
symbol_df = df[df['Symbol'] == selected_symbol].sort_values("Date")

# --- SIGNAL SCANNER ---
st.subheader("📡 Detected Signals")
results = detect_signals(symbol_df)

# --- PLOTLY CHART WITH EMOJIS ---
fig = go.Figure()

# Price line
fig.add_trace(go.Scatter(
    x=symbol_df['Date'],
    y=symbol_df['Close'],
    mode='lines+markers',
    name='Close Price',
    line=dict(color='#A9EAFE'),
    marker=dict(color='white', size=6)
))

# Add emoji markers for signals
if results:
    signal_df = pd.DataFrame(results)
    fig.add_trace(go.Scatter(
        x=signal_df['Date'],
        y=signal_df['Price'],
        mode='text',
        text=signal_df['Emoji'],
        textfont=dict(size=24),
        name='Signals',
        showlegend=False
    ))

# Dark theme layout
fig.update_layout(
    plot_bgcolor='#2d4a4a',
    paper_bgcolor='#2d4a4a',
    font=dict(color='white', size=16),
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=False),
    title=dict(text=f"{selected_symbol}<br>Quantexo", x=0.5, font=dict(size=24)),
    margin=dict(l=40, r=40, t=80, b=40)
)

st.plotly_chart(fig, use_container_width=True)

# --- Show detected signals as table ---
if results:
    st.dataframe(pd.DataFrame(results))
else:
    st.info("No strong signals detected for this symbol.")

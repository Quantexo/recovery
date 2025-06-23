
import streamlit as st
import pandas as pd
import numpy as np
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- EMAIL CONFIGURATION ---
EMAIL_SENDER = "your-email@gmail.com"
EMAIL_PASSWORD = "your-app-password"  # Use Gmail App Password
EMAIL_RECEIVER = "receiver-email@example.com"  # Change to your actual email

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

if df.empty:
    st.stop()

# --- SIGNAL DETECTION FUNCTION ---
def detect_signals(symbol_df):
    signals = []

    for i in range(3, len(symbol_df)):
        row = symbol_df.iloc[i]
        prev = symbol_df.iloc[i - 1]
        prev2 = symbol_df.iloc[i - 2]

        # Example: Bullish Break of Structure + Liquidity Sweep + Fair Value Gap
        bos = row['Close'] > prev['High']
        liquidity_sweep = prev2['Low'] > row['Low']
        fvg = abs(prev['High'] - prev['Low']) > 2 * abs(row['High'] - row['Low'])

        if bos and liquidity_sweep and fvg:
            signals.append({
                "Date": row['Date'],
                "Signal": "Bullish Confluence",
                "Price": row['Close']
            })

    return signals

# --- SYMBOL FILTER ---
symbols = df['Symbol'].unique()
selected_symbol = st.selectbox("Select Symbol", sorted(symbols))

symbol_df = df[df['Symbol'] == selected_symbol].sort_values("Date")
st.line_chart(symbol_df.set_index("Date")[["Close"]])

# --- SIGNAL SCANNER ---
st.subheader("📡 Detected Signals")
results = detect_signals(symbol_df)

if results:
    result_df = pd.DataFrame(results)
    st.dataframe(result_df)

    if st.button("📤 Send Signal to Email"):
        try:
            msg = MIMEMultipart()
            msg["From"] = EMAIL_SENDER
            msg["To"] = EMAIL_RECEIVER
            msg["Subject"] = f"Quantexo Signal Alert for {selected_symbol}"

            body = result_df.to_string(index=False)
            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
            server.quit()
            st.success("Signal sent to email successfully!")
        except Exception as e:
            st.error(f"Failed to send email: {e}")
else:
    st.info("No strong signals detected for this symbol.")

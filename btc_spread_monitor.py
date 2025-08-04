import ccxt
import pandas as pd
import streamlit as st
import time

# === CONFIGURATION ===
SPOT_SYMBOL = 'BTC/USDT'
FUTURES_SYMBOL = 'BTC/USDT:USDT'  # Binance perpetual futures
UPPER_THRESHOLD = 50
LOWER_THRESHOLD = -50
REFRESH_INTERVAL = 60  # seconds

# === Initialize exchanges ===
binance_spot = ccxt.binance()
binance_futures = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'future'},
    'sandbox': False  # Set to True for testnet
})

# === Streamlit Layout ===
st.set_page_config(page_title="BTC Spread Monitor", layout="centered")
st.title("📊 Binance BTC Spot vs Futures Spread Monitor")
st.write("Real-time price monitoring and funding arbitrage signal")

# Initialize placeholders (only once)
spot_price_display = st.empty()
futures_price_display = st.empty()
spread_display = st.empty()
alert_display = st.empty()
chart_placeholder = st.empty()
funding_display = st.empty()
funding_status_display = st.empty()
history_display = st.empty()
funding_history_display = st.empty()
update_time_display = st.empty()

# Track price spread history
history = pd.DataFrame(columns=["Timestamp", "Spot", "Futures", "Spread"])
funding_history = pd.DataFrame(columns=["Timestamp", "Funding_Rate"])

# === Main Loop ===
while True:
    try:
        # Fetch prices
        spot_price = binance_spot.fetch_ticker(SPOT_SYMBOL)['last']
        futures_price = binance_futures.fetch_ticker(FUTURES_SYMBOL)['last']
        spread = futures_price - spot_price
        timestamp = pd.Timestamp.now()

        # Fetch funding rate using correct ccxt method
        try:
            # Method 1: Using ccxt's built-in funding rate fetch
            funding_info = binance_futures.fetch_funding_rate(FUTURES_SYMBOL)
            funding_rate = funding_info['fundingRate']
        except Exception as funding_error:
            try:
                # Method 2: Direct API call with correct method name
                funding_info = binance_futures.fapiPublicGetPremiumIndex({'symbol': 'BTCUSDT'})
                funding_rate = float(funding_info['lastFundingRate'])
            except Exception as backup_error:
                # Method 3: Set to None if both methods fail
                st.warning(f"Could not fetch funding rate: {funding_error}")
                funding_rate = None

        # Display funding rate if available
        if funding_rate is not None:
            funding_display.metric(
                label="Funding Rate",
                value=f"{funding_rate * 100:.5f}%",
                delta="Positive" if funding_rate > 0 else "Negative",
                delta_color="inverse" if funding_rate > 0 else "normal"
            )

            # Use placeholder to prevent stacking
            if funding_rate > 0:
                funding_status_display.success("🔴 Longs are paying shorts.")
            elif funding_rate < 0:
                funding_status_display.info("🟢 Shorts are paying longs.")
            else:
                funding_status_display.warning("⚪ Funding rate is neutral.")
        else:
            funding_display.metric("Funding Rate", "N/A")
            funding_status_display.empty()

        # Log values
        new_row = pd.DataFrame([[timestamp, spot_price, futures_price, spread]],
                               columns=history.columns)
        history = pd.concat([history, new_row], ignore_index=True).tail(5)

        # Log funding rate (only keep latest 5)
        if funding_rate is not None:
            funding_row = pd.DataFrame([[timestamp, funding_rate]],
                                     columns=funding_history.columns)
            funding_history = pd.concat([funding_history, funding_row], ignore_index=True).tail(5)

        # Display metrics
        spot_price_display.metric("Spot Price (BTC/USDT)", f"${spot_price:,.2f}")
        futures_price_display.metric("Futures Price (BTC/USDT:USDT)", f"${futures_price:,.2f}")
        spread_display.metric("Spread (Futures - Spot)", f"${spread:,.2f}")

        # Alert
        if spread > UPPER_THRESHOLD:
            alert_display.error(f"🚨 Spread ABOVE threshold: ${spread:.2f}")
        elif spread < LOWER_THRESHOLD:
            alert_display.warning(f"📉 Spread BELOW threshold: ${spread:.2f}")
        else:
            alert_display.success("✅ Spread is within range.")

        # Line chart
        if len(history) > 1:
            chart_placeholder.line_chart(history.set_index("Timestamp")[["Spread"]])

        # Display latest 5 history entries
        if len(history) > 0:
            with history_display.container():
                st.subheader("📋 Latest 5 Price Updates")
                display_history = history.tail(5).copy()
                display_history['Timestamp'] = display_history['Timestamp'].dt.strftime('%H:%M:%S')
                display_history['Spot'] = display_history['Spot'].apply(lambda x: f"${x:,.2f}")
                display_history['Futures'] = display_history['Futures'].apply(lambda x: f"${x:,.2f}")
                display_history['Spread'] = display_history['Spread'].apply(lambda x: f"${x:,.2f}")
                st.dataframe(display_history.iloc[::-1], use_container_width=True, hide_index=True)

        if len(funding_history) > 0:
            with funding_history_display.container():
                st.subheader("💰 Latest 5 Funding Rate Updates")
                display_funding = funding_history.copy()
                display_funding['Timestamp'] = display_funding['Timestamp'].dt.strftime('%H:%M:%S')
                display_funding['Funding_Rate'] = display_funding['Funding_Rate'].apply(lambda x: f"{x * 100:.5f}%")
                st.dataframe(display_funding.iloc[::-1], use_container_width=True, hide_index=True)

        # Refresh note
        update_time_display.caption(f"Updated at: {timestamp} (every {REFRESH_INTERVAL}s)")
        time.sleep(REFRESH_INTERVAL)

    except Exception as e:
        st.error(f"Error fetching data: {e}")
        time.sleep(REFRESH_INTERVAL)
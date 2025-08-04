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

# === MULTI-REGION DEPLOYMENT SUPPORT ===
import os


# Check if we're running in a restricted region
def check_region_access():
    """Test if we can access Binance from current region"""
    try:
        test_exchange = ccxt.binance({'enableRateLimit': True})
        test_exchange.fetch_ticker('BTC/USDT')
        return True, "Direct access available"
    except Exception as e:
        if "451" in str(e) or "restricted location" in str(e):
            return False, "Region restricted"
        else:
            return False, f"Connection error: {str(e)[:100]}"


# === EXCHANGE FALLBACK SYSTEM ===
def initialize_best_exchange():
    """Try exchanges in order of preference and regional availability"""

    exchange_options = [
        {
            'name': 'Binance',
            'init_spot': lambda: ccxt.binance({'enableRateLimit': True}),
            'init_futures': lambda: ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'future'}}),
            'spot_symbol': 'BTC/USDT',
            'futures_symbol': 'BTC/USDT:USDT',
            'funding_support': True
        },
        {
            'name': 'Bybit',
            'init_spot': lambda: ccxt.bybit({'enableRateLimit': True}),
            'init_futures': lambda: ccxt.bybit({'enableRateLimit': True, 'options': {'defaultType': 'linear'}}),
            'spot_symbol': 'BTC/USDT',
            'futures_symbol': 'BTC/USDT:USDT',
            'funding_support': True
        },
        {
            'name': 'OKX',
            'init_spot': lambda: ccxt.okx({'enableRateLimit': True}),
            'init_futures': lambda: ccxt.okx({'enableRateLimit': True, 'options': {'defaultType': 'swap'}}),
            'spot_symbol': 'BTC/USDT',
            'futures_symbol': 'BTC-USDT-SWAP',
            'funding_support': True
        },
        {
            'name': 'Coinbase',
            'init_spot': lambda: ccxt.coinbase({'enableRateLimit': True}),
            'init_futures': None,  # Coinbase doesn't have futures
            'spot_symbol': 'BTC/USD',
            'futures_symbol': None,
            'funding_support': False
        }
    ]

    for exchange_config in exchange_options:
        try:
            st.info(f"🔄 Trying {exchange_config['name']}...")

            # Initialize spot exchange
            spot_exchange = exchange_config['init_spot']()
            spot_price = spot_exchange.fetch_ticker(exchange_config['spot_symbol'])['last']

            # Initialize futures exchange if available
            futures_exchange = None
            futures_symbol = None
            if exchange_config['init_futures'] and exchange_config['futures_symbol']:
                futures_exchange = exchange_config['init_futures']()
                futures_price = futures_exchange.fetch_ticker(exchange_config['futures_symbol'])['last']
                futures_symbol = exchange_config['futures_symbol']

            st.success(f"✅ {exchange_config['name']} connected successfully!")

            return {
                'name': exchange_config['name'],
                'spot_exchange': spot_exchange,
                'futures_exchange': futures_exchange,
                'spot_symbol': exchange_config['spot_symbol'],
                'futures_symbol': futures_symbol,
                'funding_support': exchange_config['funding_support']
            }

        except Exception as e:
            error_msg = str(e)
            if "451" in error_msg or "restricted" in error_msg:
                st.warning(f"❌ {exchange_config['name']}: Region restricted")
            else:
                st.warning(f"❌ {exchange_config['name']}: {error_msg[:100]}...")
            continue

    st.error("❌ No exchanges available!")
    return None


# === Streamlit Layout ===
st.set_page_config(page_title="Multi-Exchange BTC Monitor", layout="centered")
st.title("📊 Multi-Exchange BTC Spread Monitor")
st.write("Automatic exchange selection based on regional availability")

# === Initialize best available exchange ===
with st.spinner("🔍 Finding best available exchange..."):
    active_exchange = initialize_best_exchange()

if not active_exchange:
    st.error("❌ No exchanges accessible from this region")

    # Show deployment recommendations
    st.subheader("🌍 Deployment Recommendations")
    st.info("**Option 1: Deploy to different regions**")
    st.write("• **Railway**: Supports multiple regions")
    st.write("• **DigitalOcean**: Choose Singapore/EU regions")
    st.write("• **AWS/GCP**: Deploy in Asia/Europe")

    st.info("**Option 2: Use API-friendly proxy services**")
    st.write("• **Smartproxy** ($12.5/month) - Good for APIs")
    st.write("• **ProxyMesh** ($10/month) - Reliable for trading")
    st.write("• **Bright Data** ($500/month) - Enterprise grade")

    st.stop()

# Display active exchange info
st.success(f"🚀 Using: **{active_exchange['name']}**")
if not active_exchange['futures_exchange']:
    st.warning("⚠️ Futures trading not available on this exchange - showing spot prices only")

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

# Track price spread history (keep only latest 5)
history = pd.DataFrame(columns=["Timestamp", "Spot", "Futures", "Spread"])
funding_history = pd.DataFrame(columns=["Timestamp", "Funding_Rate"])

# === Streamlit Layout ===
# st.set_page_config(page_title="BTC Spread Monitor", layout="centered")
# st.title("📊 Binance BTC Spot vs Futures Spread Monitor")
# st.write("Real-time price monitoring and funding arbitrage signal")
st.set_page_config(page_title="Multi-Exchange BTC Monitor", layout="centered")
st.title("📊 Multi-Exchange BTC Spread Monitor")
st.write("Automatic exchange selection based on regional availability")


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

while True:
    try:
        # Fetch prices from active exchange
        spot_price = active_exchange['spot_exchange'].fetch_ticker(active_exchange['spot_symbol'])['last']
        # Handle futures price (if available)
        futures_price = None
        spread = None
        if active_exchange['futures_exchange'] and active_exchange['futures_symbol']:
            futures_price = active_exchange['futures_exchange'].fetch_ticker(active_exchange['futures_symbol'])['last']
            spread = futures_price - spot_price

        timestamp = pd.Timestamp.now()

        # Fetch funding rate (if supported)
        funding_rate = None
        if active_exchange['funding_support'] and active_exchange['futures_exchange']:
            try:
                funding_info = active_exchange['futures_exchange'].fetch_funding_rate(active_exchange['futures_symbol'])
                funding_rate = funding_info['fundingRate']
            except Exception as funding_error:
                st.warning(f"Could not fetch funding rate: {funding_error}")

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

        # Log values (keep only latest 5 for display)
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

        # Display latest 5 history entries (simple approach)
        if len(history) > 0:
            with history_display.container():
                st.subheader("📋 Latest 5 Price Updates")
                display_history = history.copy()
                display_history['Timestamp'] = display_history['Timestamp'].dt.strftime('%H:%M:%S')
                display_history['Spot'] = display_history['Spot'].apply(lambda x: f"${x:,.2f}")
                display_history['Futures'] = display_history['Futures'].apply(lambda x: f"${x:,.2f}")
                display_history['Spread'] = display_history['Spread'].apply(lambda x: f"${x:,.2f}")
                st.dataframe(display_history.iloc[::-1], use_container_width=True, hide_index=True)

        # Display latest 5 funding rate updates (simple approach)
        if len(funding_history) > 0:
            with funding_history_display.container():
                st.subheader("💰 Latest 5 Funding Rate Updates")
                display_funding = funding_history.copy()
                display_funding['Timestamp'] = display_funding['Timestamp'].dt.strftime('%H:%M:%S')
                display_funding['Funding_Rate'] = display_funding['Funding_Rate'].apply(lambda x: f"{x * 100:.5f}%")
                st.dataframe(display_funding.iloc[::-1], use_container_width=True, hide_index=True)

        # Refresh note (using placeholder to prevent stacking)
        update_time_display.caption(f"Updated at: {timestamp} (every {REFRESH_INTERVAL}s)")
        time.sleep(REFRESH_INTERVAL)

    except Exception as e:
        error_msg = str(e)
        if "451" in error_msg or "restricted location" in error_msg:
            st.error("🚫 **Geographic Restriction Detected!**")
            st.error("Current exchange is not available in this region.")

            # Try to find alternative exchange
            st.info("🔄 Attempting to find alternative exchange...")
            new_exchange = initialize_best_exchange()
            if new_exchange:
                active_exchange = new_exchange
                st.success(f"✅ Switched to {active_exchange['name']}")
            else:
                st.error("❌ No alternative exchanges available")
        else:
            st.error(f"Error fetching data from {active_exchange['name']}: {e}")

        time.sleep(REFRESH_INTERVAL)
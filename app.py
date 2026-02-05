import streamlit as st
import pandas as pd
import uuid
import io
from datetime import datetime

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Temple to Bitwave Trade CSV Converter",
    page_icon="🔄",
    layout="centered",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap');

.stApp {
    font-family: 'DM Sans', sans-serif;
}

div.block-container {
    padding-top: 2rem;
}

h1 {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}

.metric-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid rgba(201, 169, 98, 0.2);
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    margin-bottom: 0.5rem;
}
.metric-card .label {
    color: #a0a0a0;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.3rem;
}
.metric-card .value {
    color: #C9A962;
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.5rem;
    font-weight: 700;
}

.fee-alert {
    background: rgba(230, 126, 34, 0.12);
    border: 1px solid rgba(230, 126, 34, 0.4);
    border-radius: 8px;
    padding: 0.8rem 1rem;
    color: #e67e22;
    font-size: 0.9rem;
    margin: 1rem 0;
}

.footer {
    text-align: center;
    color: #666;
    font-size: 0.75rem;
    margin-top: 3rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(255,255,255,0.06);
}
</style>
""", unsafe_allow_html=True)

# ── App Header ───────────────────────────────────────────────────────────────
st.title("🔄 Temple to Bitwave Trade CSV Converter")
st.caption("Upload a Temple platform trade fills export and convert it to Bitwave-compatible format.")

st.divider()

# ── File Upload ──────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Upload your Temple trade fills CSV",
    type=["csv"],
    help="This should be a trades_export file from the Temple platform.",
)

if uploaded_file is not None:
    # ── Read & Validate Input ────────────────────────────────────────────────
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Could not read the CSV file: {e}")
        st.stop()

    required_cols = [
        "trade_id", "symbol", "quantity", "price",
        "seller_fees", "buyer_fees", "seller_net", "buyer_net",
        "side", "created_at",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"Missing required columns: {', '.join(missing)}")
        st.stop()

    # ── Fee Check ────────────────────────────────────────────────────────────
    has_seller_fees = pd.to_numeric(df["seller_fees"], errors="coerce").fillna(0).sum() > 0
    has_buyer_fees = pd.to_numeric(df["buyer_fees"], errors="coerce").fillna(0).sum() > 0

    if has_seller_fees or has_buyer_fees:
        st.markdown(
            '<div class="fee-alert">⚠️ <strong>Fees detected!</strong> '
            "One or more rows contain non-zero values in the seller_fees or buyer_fees columns. "
            "Fee handling is not yet implemented — please review these transactions manually.</div>",
            unsafe_allow_html=True,
        )

    # ── Convert Numeric Columns ──────────────────────────────────────────────
    df["seller_net"] = pd.to_numeric(df["seller_net"], errors="coerce").fillna(0)
    df["buyer_net"] = pd.to_numeric(df["buyer_net"], errors="coerce").fillna(0)
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce")

    # ── Group by trade_id ────────────────────────────────────────────────────
    grouped = df.groupby("trade_id").agg(
        side=("side", "first"),
        seller_net_total=("seller_net", "sum"),
        buyer_net_total=("buyer_net", "sum"),
        earliest_time=("created_at", "min"),
    ).reset_index()

    # ── Build Output Rows ────────────────────────────────────────────────────
    output_rows = []
    trade_id_counter = 1

    for _, row in grouped.iterrows():
        side = row["side"].strip().lower()
        time_str = ""
        if pd.notna(row["earliest_time"]):
            t = row["earliest_time"]
            time_str = f"{t.month}/{t.day}/{str(t.year)[2:]} {t.strftime('%H:%M')}"

        blockchain_id = row["trade_id"]

        if side == "sell":
            # Selling CANTON, acquiring USDC
            acquire_amount = round(row["seller_net_total"], 6)
            acquire_ticker = "USDC"
            dispose_amount = round(row["buyer_net_total"], 6)
            dispose_ticker = "CANTON"
        else:
            # Buying: acquiring CANTON, disposing USDC
            acquire_amount = round(row["buyer_net_total"], 6)
            acquire_ticker = "CANTON"
            dispose_amount = round(row["seller_net_total"], 6)
            dispose_ticker = "USDC"

        # tradeAcquire row
        output_rows.append({
            "id": uuid.uuid4().hex,
            "remoteContactId": "",
            "amount": acquire_amount,
            "amountTicker": acquire_ticker,
            "cost": "",
            "costTicker": "",
            "fee": "",
            "feeTicker": "",
            "time": time_str,
            "blockchainId": blockchain_id,
            "memo": "",
            "transactionType": "tradeAcquire",
            "accountId": "",
            "contactId": "",
            "categoryId": "",
            "taxExempt": "FALSE",
            "tradeId": trade_id_counter,
            "description": "",
            "fromAddress": "",
            "toAddress": "",
            "groupId": "",
        })

        # tradeDispose row
        output_rows.append({
            "id": uuid.uuid4().hex,
            "remoteContactId": "",
            "amount": dispose_amount,
            "amountTicker": dispose_ticker,
            "cost": "",
            "costTicker": "",
            "fee": "",
            "feeTicker": "",
            "time": time_str,
            "blockchainId": blockchain_id,
            "memo": "",
            "transactionType": "tradeDispose",
            "accountId": "",
            "contactId": "",
            "categoryId": "",
            "taxExempt": "FALSE",
            "tradeId": trade_id_counter,
            "description": "",
            "fromAddress": "",
            "toAddress": "",
            "groupId": "",
        })

        trade_id_counter += 1

    output_df = pd.DataFrame(output_rows)

    # ── Summary Metrics ──────────────────────────────────────────────────────
    total_trades = len(grouped)
    sell_trades = len(grouped[grouped["side"].str.strip().str.lower() == "sell"])
    buy_trades = len(grouped[grouped["side"].str.strip().str.lower() == "buy"])
    total_output_rows = len(output_df)

    st.markdown("### Conversion Summary")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f'<div class="metric-card"><div class="label">Input Fills</div>'
            f'<div class="value">{len(df):,}</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="metric-card"><div class="label">Unique Trades</div>'
            f'<div class="value">{total_trades:,}</div></div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f'<div class="metric-card"><div class="label">Sells / Buys</div>'
            f'<div class="value">{sell_trades} / {buy_trades}</div></div>',
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f'<div class="metric-card"><div class="label">Output Rows</div>'
            f'<div class="value">{total_output_rows:,}</div></div>',
            unsafe_allow_html=True,
        )

    # ── Preview ──────────────────────────────────────────────────────────────
    st.markdown("### Output Preview")
    st.dataframe(
        output_df.head(10),
        use_container_width=True,
        hide_index=True,
    )

    # ── Download ─────────────────────────────────────────────────────────────
    csv_buffer = io.StringIO()
    output_df.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    today_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"bitwave_trades_{today_str}.csv"

    st.download_button(
        label="⬇️  Download Converted CSV",
        data=csv_bytes,
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
        type="primary",
    )

    st.markdown(
        '<div class="footer">Temple to Bitwave Trade CSV Converter · Temple Digital Group</div>',
        unsafe_allow_html=True,
    )

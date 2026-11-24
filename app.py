import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from pathlib import Path

st.set_page_config(
    page_title="GBP/USD | International Financial Management",
    page_icon="📈",
    layout="wide",
)

# ----------------------------- Styling ---------------------------------
st.markdown("""
<style>
    /* Force a consistent LIGHT theme even if the viewer's Streamlit preference is dark. */
    :root { color-scheme: light; }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"],
    [data-testid="stMainBlockContainer"], .stApp {
        background-color: #f4f7fb !important;
        color: #172033 !important;
    }
    [data-testid="stHeader"] {
        background-color: #f4f7fb !important;
    }
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div {
        background-color: #eaf0f7 !important;
    }
    [data-testid="stSidebar"] * {
        color: #243247 !important;
    }
    /* Main page typography */
    [data-testid="stMain"] h1, [data-testid="stMain"] h2,
    [data-testid="stMain"] h3, [data-testid="stMain"] h4,
    [data-testid="stMain"] p, [data-testid="stMain"] label,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] {
        color: #172033 !important;
    }
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] a {
        color: #1d4ed8 !important;
    }
    [data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid #dce4ef !important;
        padding: 14px 16px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    }
    [data-testid="stMetric"] label,
    [data-testid="stMetric"] [data-testid="stMetricLabel"],
    [data-testid="stMetric"] [data-testid="stMetricValue"],
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: #172033 !important;
    }
    .main-title { color: #14233b !important; font-weight: 800; }
    .sub-title { color: #52647d !important; }
    div[data-testid="stTabs"] button {
        color: #334155 !important;
        font-weight: 650;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #1d4ed8 !important;
    }
    [data-testid="stDataFrame"], [data-testid="stTable"] {
        background: #ffffff !important;
    }
    [data-testid="stAlert"] {
        color: #172033 !important;
    }
    .formula-card {
        background: #ffffff;
        border: 1px solid #dce4ef;
        border-radius: 10px;
        padding: 14px 16px;
        margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">GBP/USD Financial Modelling Dashboard</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-title">International Financial Management | Purchasing Power Parity, '
    'Interest Rate Parity & Carry Trade, and International Fisher Effect</p>',
    unsafe_allow_html=True,
)

# ----------------------------- Data ------------------------------------
DATA_PATH = Path(__file__).parent / "data" / "GBP_USD_IFM_Dataset.csv"

@st.cache_data
def load_data(path):
    data = pd.read_csv(path)
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data = data.dropna(subset=["Date"]).sort_values("Date").drop_duplicates("Date")
    numeric = [c for c in data.columns if c != "Date"]
    for col in numeric:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    return data

try:
    df = load_data(DATA_PATH)
except Exception as exc:
    st.error(f"Could not load the dataset: {exc}")
    st.info("Check that data/GBP_USD_IFM_Dataset.csv is present in the GitHub repository.")
    st.stop()

required = [
    "GBP_USD_Spot", "UK_CPI", "US_CPI",
    "UK_Interest_Rate_pct", "US_Interest_Rate_pct"
]
missing_cols = [c for c in required if c not in df.columns]
if missing_cols:
    st.error("Dataset is missing required columns: " + ", ".join(missing_cols))
    st.stop()

# Recalculate the core model variables from source series so the dashboard
# remains reproducible and does not rely on precomputed columns.
df = df.copy()
df["UK_Inflation_YoY_pct"] = df["UK_CPI"].pct_change(12) * 100
df["US_Inflation_YoY_pct"] = df["US_CPI"].pct_change(12) * 100
df["Inflation_Differential"] = df["UK_Inflation_YoY_pct"] - df["US_Inflation_YoY_pct"]
df["Interest_Differential"] = df["UK_Interest_Rate_pct"] - df["US_Interest_Rate_pct"]

base_rows = df.dropna(subset=["GBP_USD_Spot", "UK_CPI", "US_CPI"])
if base_rows.empty:
    st.error("There are no common valid observations for the exchange rate and CPI series.")
    st.stop()
base = base_rows.iloc[0]
df["PPP_Implied"] = (
    base["GBP_USD_Spot"]
    * (df["US_CPI"] / base["US_CPI"])
    / (df["UK_CPI"] / base["UK_CPI"])
)
df["Misalignment_pct"] = (df["GBP_USD_Spot"] / df["PPP_Implied"] - 1) * 100
df["FX_Change_YoY_pct"] = df["GBP_USD_Spot"].pct_change(12) * 100

# Effective monthly rates derived from annualized quoted rates.
uk_m = (1 + df["UK_Interest_Rate_pct"] / 100) ** (1 / 12) - 1
us_m = (1 + df["US_Interest_Rate_pct"] / 100) ** (1 / 12) - 1
df["Carry_Return_pct"] = (
    ((1 + uk_m) / (1 + us_m))
    * (df["GBP_USD_Spot"] / df["GBP_USD_Spot"].shift(1)) - 1
) * 100

# Missing monthly returns are not fabricated; the cumulative index holds
# its previous level for a missing month and compounds when observations resume.
df["Carry_Index"] = 100 * (1 + df["Carry_Return_pct"].fillna(0) / 100).cumprod()

# ----------------------------- Sidebar ---------------------------------
with st.sidebar:
    st.header("Dashboard controls")
    min_date = df["Date"].min().date()
    max_date = df["Date"].max().date()
    date_range = st.date_input(
        "Analysis period",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    st.caption("Quotation: USD per GBP. A rise in GBP/USD means GBP appreciation.")
    st.divider()
    st.markdown("**Data sources**")
    st.markdown(
        "- FRED: EXUSUK (GBP/USD)\n"
        "- FRED: GBRCPIALLMINMEI (UK CPI)\n"
        "- FRED: CPIAUCNS (US CPI)\n"
        "- FRED: IR3TIB01GBM156N (UK rate)\n"
        "- FRED: IR3TIB01USM156N (US rate)"
    )

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    view = df[(df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)].copy()
else:
    view = df.copy()

if view.empty:
    st.warning("No observations are available in the selected period.")
    st.stop()

start_label = view["Date"].min().strftime("%b %Y")
end_label = view["Date"].max().strftime("%b %Y")
st.caption(f"Selected period: {start_label} – {end_label} | {len(view)} monthly observations")

tab_ppp, tab_irp, tab_ife, tab_data = st.tabs([
    "1 · PPP & Currency Misalignment",
    "2 · IRP & Carry Trade",
    "3 · International Fisher Effect",
    "Data & Methodology",
])

# ----------------------------- TAB 1 -----------------------------------
with tab_ppp:
    st.subheader("Purchasing Power Parity (PPP)")
    ppp_valid = view.dropna(subset=["GBP_USD_Spot", "PPP_Implied", "Misalignment_pct"])
    if ppp_valid.empty:
        st.warning("Insufficient valid exchange-rate/CPI observations for PPP.")
    else:
        last = ppp_valid.iloc[-1]
        mis = last["Misalignment_pct"]
        status = "GBP OVERVALUED" if mis > 0.05 else ("GBP UNDERVALUED" if mis < -0.05 else "APPROXIMATELY FAIR VALUE")
        c1, c2, c3 = st.columns(3)
        c1.metric("Actual GBP/USD", f'{last["GBP_USD_Spot"]:.4f}')
        c2.metric("PPP-implied GBP/USD", f'{last["PPP_Implied"]:.4f}')
        c3.metric("Currency misalignment", f"{mis:+.2f}%", status)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ppp_valid["Date"], y=ppp_valid["GBP_USD_Spot"],
                                 mode="lines", name="Actual spot rate", line=dict(color="#2563eb", width=2.6)))
        fig.add_trace(go.Scatter(x=ppp_valid["Date"], y=ppp_valid["PPP_Implied"],
                                 mode="lines", name="PPP-implied spot rate", line=dict(color="#10b981", width=2.6, dash="dash")))
        fig.update_layout(title="Actual Spot Rate vs PPP-Implied Spot Rate",
                          xaxis_title="Month", yaxis_title="USD per GBP",
                          template="plotly_white", hovermode="x unified",
                          legend=dict(orientation="h", y=1.12))
        st.plotly_chart(fig, use_container_width=True)
        st.info(
            f"At {last['Date']:%B %Y}, the actual rate is {abs(mis):.2f}% "
            f"{'above' if mis > 0 else 'below'} the PPP-implied rate. "
            f"Under this quotation convention, a positive misalignment indicates an overvalued GBP; "
            f"a negative misalignment indicates an undervalued GBP."
        )

    with st.expander("PPP formulas and logical conditions"):
        st.markdown(r"""
**Quotation convention:** \(S_t\) is USD per GBP. The UK is the currency being valued.

**Relative PPP-implied exchange rate**

\[
S_t^{PPP}=S_0\times
\frac{USCPI_t/USCPI_0}{UKCPI_t/UKCPI_0}
\]

**Currency misalignment**

\[
Misalignment_t(\%)=
\frac{S_t^{Actual}-S_t^{PPP}}{S_t^{PPP}}\times100
\]

**Status logic**
- Misalignment > +0.05%: GBP overvalued relative to PPP.
- Misalignment < −0.05%: GBP undervalued relative to PPP.
- Between −0.05% and +0.05%: approximately fair value.

The first common valid observation in the dataset is the base period. PPP is a model benchmark, not a directly traded fair value.
""")

# ----------------------------- TAB 2 -----------------------------------
with tab_irp:
    st.subheader("Interest Rate Parity & Carry Trade Tracker")
    irp_valid = view.dropna(subset=[
        "Interest_Differential", "FX_Change_YoY_pct",
        "Carry_Return_pct", "Carry_Index"
    ])
    latest_rates = view.dropna(subset=["UK_Interest_Rate_pct", "US_Interest_Rate_pct"])
    if latest_rates.empty:
        st.warning("No common UK and US interest-rate observations in this period.")
    else:
        last_rate = latest_rates.iloc[-1]
        a, b, c = st.columns(3)
        a.metric("UK nominal rate", f'{last_rate["UK_Interest_Rate_pct"]:.2f}%')
        b.metric("US nominal rate", f'{last_rate["US_Interest_Rate_pct"]:.2f}%')
        b_delta = last_rate["Interest_Differential"]
        c.metric("UK − US yield differential", f"{b_delta:+.2f} pp")

    carry_valid = view.dropna(subset=["Carry_Index"])
    if not carry_valid.empty:
        first_index = carry_valid.iloc[0]["Carry_Index"]
        last_index = carry_valid.iloc[-1]["Carry_Index"]
        total_return = (last_index / first_index - 1) * 100
        d, e = st.columns(2)
        d.metric("Carry Trade Profitability Index", f"{last_index:.2f}", f"{total_return:+.2f}% since index start")
        e.metric("Latest annual GBP/USD change",
                 f'{view["FX_Change_YoY_pct"].dropna().iloc[-1]:+.2f}%' if view["FX_Change_YoY_pct"].notna().any() else "N/A")

    if not irp_valid.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=irp_valid["Date"], y=irp_valid["Interest_Differential"],
                             name="UK − US interest differential (pp)", marker_color="#2563eb", opacity=0.65))
        fig.add_trace(go.Scatter(x=irp_valid["Date"], y=irp_valid["FX_Change_YoY_pct"],
                                 name="Annual GBP/USD change (%)", mode="lines",
                                 line=dict(color="#f97316", width=2.5), yaxis="y2"))
        fig.update_layout(
            title="Yield Differential vs Annual Spot Rate Appreciation / Depreciation",
            xaxis_title="Month", yaxis=dict(title="Interest differential (percentage points)"),
            yaxis2=dict(title="Annual spot rate change (%)", overlaying="y", side="right"),
            template="plotly_white", hovermode="x unified",
            legend=dict(orientation="h", y=1.15)
        )
        st.plotly_chart(fig, use_container_width=True)

    if not carry_valid.empty:
        carry_fig = px.line(carry_valid, x="Date", y="Carry_Index",
                            title="Cumulative Unhedged Carry Trade Profitability Index",
                            labels={"Carry_Index": "Index (base = 100)", "Date": "Month"})
        carry_fig.add_hline(y=100, line_dash="dash", line_color="gray")
        carry_fig.update_layout(template="plotly_white")
        st.plotly_chart(carry_fig, use_container_width=True)

    with st.expander("IRP, UIP and carry trade formulas"):
        st.markdown(r"""
**Interest rate differential**

\[
IRD_t=i_{UK,t}-i_{US,t}
\]

**Annual spot-rate appreciation / depreciation**

\[
FXChange_t(\%)=\left(\frac{S_t}{S_{t-12}}-1\right)\times100
\]

Positive means GBP appreciation; negative means GBP depreciation.

**Convert annual rates to effective monthly rates**

\[
i_m=(1+i_a)^{1/12}-1
\]

where \(i_a\) is the annual rate in decimal form.

**Monthly unhedged carry return (borrow USD, invest GBP)**

\[
R_{carry,t}=
\left[\frac{1+i_{UK,m}}{1+i_{US,m}}
\times\frac{S_t}{S_{t-1}}\right]-1
\]

**Cumulative Carry Trade Profitability Index**

\[
CTPI_t=100\times\prod_{j=1}^{t}(1+R_{carry,j})
\]

- CTPI > 100: cumulative gain relative to the index base.
- CTPI < 100: cumulative loss relative to the index base.
- CTPI = 100: break-even.

**Theory and limitation:** Comparing interest differentials with subsequent spot-rate changes is an empirical check related to uncovered interest parity (UIP). A formal covered interest parity (CIP) test requires forward exchange rates; those are not part of this five-series dataset. Carry returns are illustrative, unhedged, and exclude transaction costs, taxes and funding frictions.
""")

# ----------------------------- TAB 3 -----------------------------------
with tab_ife:
    st.subheader("International Fisher Effect (IFE) Diagnostic")
    ife = view.dropna(subset=["Inflation_Differential", "Interest_Differential"])
    if len(ife) >= 3:
        x = ife["Inflation_Differential"].astype(float)
        y = ife["Interest_Differential"].astype(float)
        corr = stats.pearsonr(x, y)
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        m1, m2, m3 = st.columns(3)
        m1.metric("Pearson correlation", f"{corr.statistic:.3f}")
        m2.metric("Regression R²", f"{r_value**2:.3f}")
        m3.metric("Regression p-value", f"{p_value:.4f}")

        scatter = px.scatter(
            ife, x="Inflation_Differential", y="Interest_Differential",
            hover_data={"Date": True},
            labels={
                "Inflation_Differential": "UK − US inflation differential (pp)",
                "Interest_Differential": "UK − US nominal interest differential (pp)"
            },
            title="Inflation Differential vs Nominal Interest Rate Differential",
            trendline="ols"
        )
        scatter.update_layout(template="plotly_white")
        st.plotly_chart(scatter, use_container_width=True)

        st.markdown(
            f"**Estimated regression:** Nominal interest differential = "
            f"{intercept:.3f} + ({slope:.3f} × inflation differential)."
        )
        if p_value < 0.05:
            st.info("The estimated linear relationship is statistically significant at the 5% level. "
                    "Assess the sign and magnitude of the slope against the IFE prediction; "
                    "statistical association alone does not prove causation.")
        else:
            st.info("The estimated linear relationship is not statistically significant at the 5% level. "
                    "This sample does not provide strong evidence of a linear association.")
    else:
        st.warning("At least three complete monthly observations are required for the IFE regression.")

    with st.expander("IFE formulas and interpretation"):
        st.markdown(r"""
**Year-on-year inflation from monthly CPI**

\[
\pi_t=\left(\frac{CPI_t}{CPI_{t-12}}-1\right)\times100
\]

**Inflation differential**

\[
ID_t=\pi_{UK,t}-\pi_{US,t}
\]

**Nominal interest rate differential**

\[
NID_t=i_{UK,t}-i_{US,t}
\]

**International Fisher Effect approximation**

\[
NID_t\approx E(\pi_{UK,t})-E(\pi_{US,t})
\]

For this dashboard, realised year-on-year inflation is used as a proxy for expected inflation. This is an empirical approximation, not a direct measure of market inflation expectations.

**Regression**

\[
NID_t=\alpha+\beta ID_t+\epsilon_t
\]

The dashboard reports Pearson correlation, slope, intercept, R-squared and p-value. A positive association is consistent with the expected direction, but the coefficient need not equal one in a finite sample.
""")

# ----------------------------- DATA / METHODOLOGY ----------------------
with tab_data:
    st.subheader("Dataset, source mapping & methodology")
    st.markdown(
        f"**Observation window:** {df['Date'].min():%B %Y} to {df['Date'].max():%B %Y}  \n"
        f"**Frequency:** Monthly  \n"
        "**Exchange-rate quotation:** USD per GBP"
    )
    source_map = pd.DataFrame([
        ["GBP/USD spot exchange rate", "EXUSUK", "USD per GBP"],
        ["UK Consumer Price Index", "GBRCPIALLMINMEI", "CPI index"],
        ["US Consumer Price Index", "CPIAUCNS", "CPI index"],
        ["UK 3-month interbank rate", "IR3TIB01GBM156N", "Percent per annum"],
        ["US 3-month interbank rate", "IR3TIB01USM156N", "Percent per annum"],
    ], columns=["Variable", "FRED series ID", "Unit"])
    st.dataframe(source_map, use_container_width=True, hide_index=True)

    st.markdown("**Data-quality checks**")
    quality = pd.DataFrame({
        "Variable": required,
        "Missing observations": [int(df[c].isna().sum()) for c in required],
    })
    st.dataframe(quality, use_container_width=True, hide_index=True)
    st.caption("Missing source observations are retained as missing. The app does not interpolate or fabricate source data.")

    st.markdown("**Download the dataset used by this dashboard**")
    st.download_button(
        "Download consolidated CSV",
        data=(DATA_PATH).read_bytes(),
        file_name="GBP_USD_IFM_Dataset.csv",
        mime="text/csv",
    )
    st.markdown("**Academic interpretation**")
    st.write(
        "PPP compares the observed spot rate with a CPI-based relative PPP benchmark. "
        "The IRP tab compares the UK–US interest differential with spot-rate movements and "
        "illustrates an unhedged carry strategy. The IFE tab examines whether inflation "
        "differentials are associated with nominal interest differentials. Results are "
        "descriptive and depend on the sample period, proxy choices and data limitations."
    )

st.divider()
st.caption("Academic project dashboard | Data source: Federal Reserve Bank of St. Louis FRED | "
           "Model outputs are educational estimates, not trading recommendations.")

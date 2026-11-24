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

$$
\pi_t=\left(\frac{CPI_t}{CPI_{t-12}}-1\right)\times100
$$

**Inflation differential**

$$
ID_t=\pi_{UK,t}-\pi_{US,t}
$$

**Nominal interest rate differential**

$$
NID_t=i_{UK,t}-i_{US,t}
$$

**International Fisher Effect approximation**

$$
NID_t\approx E(\pi_{UK,t})-E(\pi_{US,t})
$$

For this dashboard, realised year-on-year inflation is used as a proxy for expected inflation. This is an empirical approximation, not a direct measure of market inflation expectations.

**Regression**

$$
NID_t=\alpha+\beta ID_t+\epsilon_t
$$

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

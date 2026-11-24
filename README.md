# GBP/USD International Financial Management Dashboard

A three-tab Streamlit dashboard for an undergraduate International Financial Management project.

## Dashboard tabs
1. **PPP & Currency Misalignment** — actual GBP/USD spot rate vs relative PPP-implied rate, misalignment percentage and valuation status.
2. **IRP & Carry Trade** — UK–US nominal interest differential, annual spot-rate change, illustrative unhedged carry return and cumulative profitability index.
3. **International Fisher Effect** — UK–US inflation differential vs nominal interest differential, scatter plot, Pearson correlation and OLS regression.
4. **Data & Methodology** — FRED series mapping, data-quality checks, and CSV download.

## Files
```text
GBP-USD-IFM-GitHub/
├── app.py
├── requirements.txt
├── README.md
└── data/
    └── GBP_USD_IFM_Dataset.csv
```

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Create a GitHub repository and upload all four project files, preserving the `data/` folder.
2. Go to https://share.streamlit.io/ and connect GitHub.
3. Select this repository, branch `main`, and main file path `app.py`.
4. Deploy.

## FRED source mapping
| Variable | FRED ID | Unit |
|---|---|---|
| GBP/USD spot exchange rate | EXUSUK | USD per GBP |
| UK CPI | GBRCPIALLMINMEI | CPI index |
| US CPI | CPIAUCNS | CPI index |
| UK 3-month interbank rate | IR3TIB01GBM156N | Percent per annum |
| US 3-month interbank rate | IR3TIB01USM156N | Percent per annum |

## Formula reference

### Relative PPP
Quotation is USD per GBP. The UK is the currency being valued.

`PPP_t = S_0 * (US_CPI_t / US_CPI_0) / (UK_CPI_t / UK_CPI_0)`

`Misalignment (%) = ((Actual_S_t - PPP_t) / PPP_t) * 100`

Positive misalignment means GBP is overvalued relative to the PPP benchmark; negative means undervalued. The first common valid observation is the base period.

### Inflation
`Inflation_t (%) = (CPI_t / CPI_(t-12) - 1) * 100`

`Inflation_Differential = UK_Inflation - US_Inflation`

### Interest rate differential and spot-rate change
`IRD = UK_Interest_Rate - US_Interest_Rate`

`Annual_FX_Change (%) = (S_t / S_(t-12) - 1) * 100`

Positive FX change means GBP appreciation because the quote is USD per GBP.

### Illustrative unhedged carry trade
Annual rates are converted to effective monthly rates:

`i_monthly = (1 + i_annual)^(1/12) - 1`

For a USD-funded investor borrowing USD and investing in GBP:

`Carry_Return_t = ((1 + UK_monthly_rate) / (1 + US_monthly_rate)) * (S_t / S_(t-1)) - 1`

`Carry_Index_t = 100 * product(1 + Carry_Return_j)`

The index starts at 100. Missing monthly carry returns are not fabricated; the cumulative index holds its previous level for a missing month and compounds when valid observations resume.

### International Fisher Effect diagnostic
`NID = UK_Nominal_Rate - US_Nominal_Rate`

`IFE approximation: NID ≈ Expected_UK_Inflation - Expected_US_Inflation`

This project uses realised year-on-year CPI inflation as a proxy for expected inflation. The empirical regression is:

`NID_t = alpha + beta * Inflation_Differential_t + error_t`

The dashboard reports Pearson correlation, regression slope, intercept, R-squared and p-value.

## Important academic limitations
- A formal covered interest parity (CIP) test requires forward exchange rates. The five-series dataset does not contain forward rates, so the IRP tab compares interest differentials and spot-rate movements as a UIP-related empirical diagnostic; it does not claim to prove CIP.
- Carry returns are illustrative, unhedged estimates before transaction costs, taxes and funding frictions.
- Realised year-on-year inflation is only a proxy for expected inflation; it is not a direct measure of market inflation expectations.
- Source observations are not interpolated or fabricated. Missing observations remain missing.
- PPP is a model benchmark, not a directly traded fair value.

## Data period
The supplied consolidated dataset contains the common monthly observations from January 2020 through March 2025. Its end date is determined by the available UK CPI series in the supplied data.

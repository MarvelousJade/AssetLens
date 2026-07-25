# Analytics methodology

Every analytics response includes its data date and calculation timestamp.
Values are expressed as decimal returns in the API and formatted as percentages
in the UI.

| Metric | Method |
|---|---|
| Market value | Latest available close × current quantity |
| Cost basis | Average cost × current quantity |
| Unrealized gain | Market value − cost basis |
| Time-weighted return | Ending unit value ÷ beginning unit value − 1 |
| Money-weighted return | Annualized beginning-to-ending value ratio; the seeded period has no interim cash flows |
| Annualized volatility | Sample standard deviation of daily returns × √252 |
| Sharpe ratio | (annualized arithmetic return − 2% risk-free rate) ÷ annualized volatility |
| Maximum drawdown | Minimum of value ÷ running peak − 1 |
| Holding contribution | Beginning portfolio weight × holding total return |

The seeded dataset uses 260 deterministic business-day closing observations and
static quantities. This makes screenshots, tests, and report outputs
reproducible. It is not intended to represent live exchange data.

## Scenario methodology

Scenarios apply percentage shocks to current market value by asset class, sector,
geography, or symbol. Shocks are instantaneous and independent. They exclude
liquidity, correlations, tax, convexity, trading, and second-order effects.
Results are estimates for software demonstration, not forecasts.

## Known MVP limitations

- No corporate actions, fees, dividends, tax lots, or intraday pricing.
- The seeded portfolio has no interim external cash flows.
- Foreign-exchange exposure uses security geography as a simplified proxy.
- Attribution excludes trading and interaction effects.

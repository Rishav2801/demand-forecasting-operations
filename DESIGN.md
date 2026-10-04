# Design review

## Business question

Can tomorrow’s rental demand be forecast more accurately than last week’s, with useful uncertainty for service capacity planning?

## Analytical contract

Forecasts are rolling one-day-ahead with actual history updated daily; they are not a fixed-origin multi-day forecast. Model parameters stay fixed after training. Time dependence and drift invalidate exchangeable conformal guarantees, so observed coverage is reported. Two years do not capture all regimes. Planning costs are hypothetical.

## Review prompts

1. Why are random train/test splits wrong for this task?
2. When is a lagged test-period actual available without leakage?
3. Why can an ostensibly 90% interval cover less than 90%?
4. Why are daily rentals not equal to the number of bicycles needed?

## Extension

Incorporate forecast-vintage weather, station-level stock/rebalancing constraints, and an adaptive calibration protocol evaluated before deployment.

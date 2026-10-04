# Results

## Decision

Validation selects ridge. Final-holdout MAE is 905 rentals/day, versus 1218 for seasonal naive. The reported nominal 90% interval covers 85.3% of holdout days. Compare these results before choosing a planning policy.

## Forecast contract

Each forecast is for the next day, assuming the preceding day has fully closed. Lagged actual observations update each day, but model parameters remain fixed after the training window. This is not a multi-step forecast from one fixed origin. Calendar variables are known in advance; same-day actual weather is excluded.

## Intervals

Absolute residuals from a disjoint 100-day calibration window determine a finite-sample corrected radius. Serial dependence and distribution shift violate exchangeability, so 90% coverage is a target, not a guarantee. No retraining follows calibration.

## Operations

Capacity is an abstract daily rental-service budget. Rentals are flows, not a count of bikes required at a station. Cost ratios are hypothetical and exclude rebalancing, bike reuse and lost-demand censoring. Policies are compared on holdout data for reporting, not selected using it.

## Limitations

Only two historical years and a changing demand level. No station-level inventory, advance weather forecasts or real costs. Interval undercoverage or a weak model is retained in the report rather than hidden.

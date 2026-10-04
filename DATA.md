# Data provenance

Hadi Fanaee-T (2013), Bike Sharing. UCI Machine Learning Repository. DOI: https://doi.org/10.24432/C5W894. Dataset page: https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset. CC BY 4.0. Uses day.csv from the original archive; raw data are downloaded at runtime, not republished.

## Data dictionary

`dteday`: day. `cnt`: observed daily rental count. `casual`, `registered`: components used only for reconciliation. `holiday`, `workingday`: known calendar indicators. `lag_1/7/14`: prior observed target values. `mean_7/28`, `std_7`: shifted rolling summaries. Cyclic day/week features and trend are calendar-derived. Forecast outputs are rental flows, not station inventory.

## Reproducibility

Source downloads are cached locally and excluded from version control. The pipeline records source content hashes in metrics.json. Reproduce with the pinned requirements and fixed random seeds. Generated summaries may contain transformed aggregates; they do not inherit the project code license when the underlying dataset has separate terms.

-- Load test_predictions.csv as forecasts. Daily, one-step evaluation.
SELECT substr(date,1,7) AS month, COUNT(*) AS days,
 AVG(ABS(actual-forecast)) AS mae,
 SUM(ABS(actual-forecast))*1.0/NULLIF(SUM(actual),0) AS wape,
 AVG(CASE WHEN actual BETWEEN lower_90 AND upper_90 THEN 1.0 ELSE 0.0 END) AS coverage,
 AVG(upper_90-lower_90) AS mean_interval_width
FROM forecasts GROUP BY 1 ORDER BY 1;

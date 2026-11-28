# G3 NYC taxi forecasting baseline

This milestone evaluates two interpretable daily trip-count baselines using the
existing local NYC TLC Yellow Taxi Gold reporting snapshot.

```powershell
python scripts/evaluate_nyc_taxi_forecast.py --snapshot data/dev/nyc_tlc/silver_gold_2024_01/reporting_preview.json --output data/dev/nyc_tlc/forecast_baseline.json
```

The evaluator uses accepted pickup trips within the source month and requires
one observation per calendar day. It holds out the last seven days and freezes
both forecasts at the end of the training period. The seasonal forecast repeats
the final seven training days in order. The last-observation forecast repeats
the final training day's count. The held-out actuals are used only to score the
forecasts.

The output lists the input SHA-256, dates, actuals and predictions, mean absolute
error (MAE), weighted absolute percentage error (WAPE), and signed mean error
(prediction minus actual). WAPE is undefined when the total actual trip count
is zero.

Keep the source and the evaluation output local. A single month and one holdout
provide a baseline for further evaluation. Production model selection,
deployment, drift monitoring and acceptance remain separate work.

# Detroit Crime & Weather — analysis pipeline

How daily temperature, rain, snow and wind shape reported crime in Detroit
(2017 → mid-2026). Produces a narrative HTML report, an interactive per-category
explorer, and a landing page.

## Reproduce from scratch

Requires Python 3 with: `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `requests`.

```bash
python3 00_fetch_data.py        # download crime CSV (~305 MB) + weather (Open-Meteo)
python3 01_build_datasets.py    # all aggregate CSVs + profile_data.json (no pickle)
python3 02_make_figures.py      # 16 charts -> figs/
python3 build_report.py         # detroit_crime_temperature_report.html
python3 build_interactive.py    # detroit_crime_weather_explorer.html
python3 build_index.py          # index.html  (landing page)
```

Or run everything: `bash run_all.sh`. Then open **index.html**.

Steps 1–6 are deterministic and depend only on the raw files from step 0, so if
you already have the four raw CSVs you can skip the (slow) download and start at
step 1.

## Pipeline

| Script | Reads | Writes |
|---|---|---|
| `00_fetch_data.py` | — (network) | `detroit_crime.csv`, `detroit_weather.csv`, `detroit_weather_full.csv`, `detroit_weather_hourly.csv` |
| `01_build_datasets.py` | the 4 raw CSVs | `incident_points.csv`, `daily_*.csv`, `*_stats.csv`, `*_violent*.csv`, `weather_cond_stats.csv`, `heat_norm.csv`, `profile_data.json` |
| `02_make_figures.py` | step-1 outputs | `figs/fig1…fig16_*.png` |
| `build_report.py` | step-1 CSVs + `figs/` | `detroit_crime_temperature_report.html` |
| `build_interactive.py` | `profile_data.json` | `detroit_crime_weather_explorer.html` |
| `build_index.py` | `profile_data.json`, `category_stats.csv`, `bin_stats.csv` | `index.html` |

## Outputs (cross-linked mini-site)

- **index.html** — landing page → links to both
- **detroit_crime_temperature_report.html** — narrative report (11 sections, 16 charts)
- **detroit_crime_weather_explorer.html** — interactive per-category weather profiles

## Method notes

- Incident UTC timestamps are converted to **America/Detroit** local time before
  assigning a calendar day/hour. Analysis window: 2017-01-01 to 2026-06-03 (the
  period with consistent reporting).
- Weather is from the **Open-Meteo** historical reanalysis archive for downtown
  Detroit (42.33 N, 83.05 W), temperatures in °F, precipitation in inches.
- Daily crime is modelled as a count with a **Poisson regression (log link, PML)**;
  point estimates are consistent for the conditional mean even under over-dispersion.
  OLS is kept only for the deseasonalised "anomaly" check, where the series can go
  negative. All precipitation, wind and heat-wave effects **control for temperature**,
  so the weather signal is not just the season.
- Daily crime series are autocorrelated and over-dispersed, so all p-values and
  significance flags use **Newey-West (HAC)** robust standard errors rather than
  i.i.d. errors, and families of tests are corrected for multiple comparisons with
  **Benjamini-Hochberg FDR** q-values.
- Incidents stamped exactly at midnight or noon are unknown-time placeholders and
  are excluded from hour-of-day analyses (kept in daily counts).
- Every intermediate file is plain text (CSV / JSON) — no pickle or other
  code-bearing formats are read or written anywhere in the pipeline.

## Data sources

- Crime: [Detroit Open Data Portal](https://data.detroitmi.gov/)
- Weather: [Open-Meteo](https://open-meteo.com/) historical archive

## License

Code in this repository is released under the [MIT License](LICENSE).
The license covers the pipeline and build scripts only — the underlying crime
and weather data are not redistributed here and remain subject to their
providers' own terms.

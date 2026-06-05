#!/usr/bin/env python3
"""
Step 1 — Build every derived dataset from the raw inputs.

Reads:  detroit_crime.csv, detroit_weather.csv, detroit_weather_full.csv,
        detroit_weather_hourly.csv
Writes: incident_points.csv, daily_merged.csv, daily_precip_merged.csv, daily_master.csv,
        bin_stats.csv, month_stats.csv, heat_norm.csv, category_stats.csv,
        category_precip.csv, neighborhood_stats.csv, precinct_stats.csv,
        tod_violent_profile.csv, hourlytemp_violent_rate.csv,
        weekday_weekend_stats.csv, weekend_violent_bins.csv,
        precip_strat_violent.csv, weather_cond_stats.csv, profile_data.json
"""
import json
import numpy as np
import pandas as pd
from scipy import stats

WIN_START, WIN_END = "2017-01-01", "2026-06-04"   # [start, end) local time
VIOL = {'AGGRAVATED ASSAULT', 'ASSAULT', 'WEAPONS OFFENSES', 'ROBBERY', 'HOMICIDE',
        'SEX OFFENSES', 'SEXUAL ASSAULT', 'ARSON', 'DISORDERLY CONDUCT',
        'OBSTRUCTING THE POLICE'}
PROP = {'DAMAGE TO PROPERTY', 'LARCENY', 'STOLEN VEHICLE', 'BURGLARY', 'STOLEN PROPERTY'}
TBINS = [-100, 20, 32, 45, 60, 75, 200]
TLABELS = ['<20', '20–32', '32–45', '45–60', '60–75', '75+']
BLABELS_LONG = ['<20°F', '20–32°F', '32–45°F', '45–60°F', '60–75°F', '75°F+']


def family(c):
    return 'Violent' if c in VIOL else ('Property' if c in PROP else 'Other')


def ols(y, X, want_p=True):
    """OLS with intercept; returns (beta, pvalues)."""
    X = np.column_stack([np.ones(len(y))] + X)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    n, k = X.shape
    s2 = (resid @ resid) / (n - k)
    se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
    p = 2 * (1 - stats.t.cdf(np.abs(beta / se), n - k))
    return beta, p


# ----------------------------------------------------------- incident-level frame
# Built in memory and reused throughout this script. The only incident-level file
# written to disk is incident_points.csv (coordinates for the density map); all
# intermediates are plain CSV/JSON, never a code-bearing format.
print("Loading & enriching incidents …")
raw = pd.read_csv('detroit_crime.csv', low_memory=False,
    usecols=['offense_category', 'incident_occurred_at', 'neighborhood',
             'police_precinct', 'council_district', 'latitude', 'longitude'])
dt = pd.to_datetime(raw['incident_occurred_at'], utc=True, errors='coerce').dt.tz_convert('America/Detroit')
mask = (dt >= WIN_START) & (dt < WIN_END)
inc = raw[mask].copy(); dt = dt[mask]
inc['ldt'] = dt.dt.tz_localize(None)
inc['date'] = dt.dt.normalize().dt.tz_localize(None)
inc['hour'] = dt.dt.hour
inc['dow'] = dt.dt.dayofweek
inc['is_weekend'] = inc['dow'].isin([5, 6])
inc['cat'] = inc['offense_category'].str.strip()
inc['family'] = inc['cat'].map(family)
print(f"  {len(inc):,} incidents")

# ------------------------------------------------------------------ weather load
wd = pd.read_csv('detroit_weather.csv', parse_dates=['time']).set_index('time')
wf = pd.read_csv('detroit_weather_full.csv', parse_dates=['time']).set_index('time')
wh = pd.read_csv('detroit_weather_hourly.csv', parse_dates=['time'])
temp = wd['temperature_2m_mean']
doy = temp.index.dayofyear


def climo_anom(s):
    return s - s.groupby(doy).transform('mean')


# --------------------------------------------------- daily category / family tables
dcat = inc.groupby(['date', 'cat']).size().unstack(fill_value=0); dcat.index = pd.to_datetime(dcat.index)
dfam = inc.groupby(['date', 'family']).size().unstack(fill_value=0); dfam.index = pd.to_datetime(dfam.index)
dtot = inc.groupby('date').size(); dtot.index = pd.to_datetime(dtot.index)

# daily_merged.csv : categories + total + daily weather
daily = dcat.copy(); daily['total_crimes'] = dtot
daily = daily.join(wd, how='inner')
daily.index.name = 'date'
daily.to_csv('daily_merged.csv')

# daily_precip_merged.csv : family + total + full weather
fam = dfam.copy(); fam['total'] = fam.sum(axis=1)
M_precip = fam.join(wf, how='inner'); M_precip.index.name = 'date'
M_precip.to_csv('daily_precip_merged.csv')

# daily_master.csv : family + total + full weather + temp_max
master = fam.join(wf, how='inner').join(wd[['temperature_2m_max']], how='inner')
master.index.name = 'date'
master.to_csv('daily_master.csv')

# ----------------------------------------------------------- temperature aggregates
m = daily.copy()
m['tbin'] = pd.cut(m['temperature_2m_mean'], bins=TBINS, labels=BLABELS_LONG)
binstats = m.groupby('tbin', observed=True).agg(
    days=('total_crimes', 'size'), mean_total=('total_crimes', 'mean'),
    mean_temp=('temperature_2m_mean', 'mean'))
binstats.to_csv('bin_stats.csv')

mo = m.groupby(m.index.month).agg(mean_total=('total_crimes', 'mean'),
                                  mean_temp=('temperature_2m_mean', 'mean'))
mo.to_csv('month_stats.csv')

cat_cols = [c for c in dcat.columns]
totals = dcat.sum().sort_values(ascending=False)
top12 = totals.head(12).index.tolist()
heat = m.groupby('tbin', observed=True)[top12].mean()
heat_norm = heat / m[top12].mean()
heat_norm.T.to_csv('heat_norm.csv')

# ------------------------------------------------------ category_stats.csv (temp)
big = totals[totals >= 2000].index.tolist()
rows = []
for c in ['total_crimes'] + big:
    s = (daily[c] if c == 'total_crimes' else dcat[c]).reindex(temp.index).fillna(0).astype(float)
    r, p = stats.pearsonr(temp, s)
    rho, _ = stats.spearmanr(temp, s)
    slope, _ = np.polyfit(temp, s, 1)
    sa = climo_anom(s); ra, pa = stats.pearsonr(climo_anom(temp), sa)
    rows.append(dict(category=c, total=int(s.sum()), mean_per_day=round(s.mean(), 2),
        pearson_r=r, spearman=rho, p=p, slope_per_F=slope,
        pct_per_10F=slope * 10 / s.mean() * 100, anom_r=ra, anom_p=pa))
pd.DataFrame(rows).to_csv('category_stats.csv', index=False)

# ----------------------------------------------- category_precip.csv (temp-controlled)
Mc = dcat.join(wf, how='inner')
Tc = Mc['temperature_2m_mean'].values; Rc = Mc['rain_sum'].values
Sc = Mc['snowfall_sum'].values; Wc = (Mc['precipitation_sum'] >= 0.01).astype(float).values
prows = []
for c in cat_cols:
    y = Mc[c].values.astype(float); mean = y.mean()
    if mean < 0.3:
        continue
    b, p = ols(y, [Tc, Wc]); b2, p2 = ols(y, [Tc, Rc, Sc])
    prows.append(dict(category=c, total=int(y.sum()), mean=mean,
        wet_pct=b[2] / mean * 100, wet_p=p[2],
        rain_pct=b2[2] / mean * 100, rain_p=p2[2],
        snow_pct=b2[3] / mean * 100, snow_p=p2[3]))
pd.DataFrame(prows).sort_values('wet_pct').to_csv('category_precip.csv', index=False)

# --------------------------------------------------------------- geography
geo = inc[inc['latitude'].between(42.20, 42.50) & inc['longitude'].between(-83.30, -82.85)]
# coordinates for the density hexbin (step 2); rounded to ~1 m, plenty for a city map
geo[['latitude', 'longitude']].round(5).to_csv('incident_points.csv', index=False)
nb_vol = geo['neighborhood'].value_counts()
nb_rows = []
for nb in nb_vol[nb_vol >= 3000].index:
    sub = geo[geo.neighborhood == nb]
    d = sub.groupby('date').size(); d.index = pd.to_datetime(d.index)
    d = d.reindex(temp.index).fillna(0)
    r, _ = stats.pearsonr(temp, d); b, _ = np.polyfit(temp, d, 1)
    nb_rows.append(dict(neighborhood=nb, total=len(sub), per_day=d.mean(),
        lat=sub.latitude.median(), lon=sub.longitude.median(),
        r=r, pct10=b * 10 / d.mean() * 100))
pd.DataFrame(nb_rows).sort_values('total', ascending=False).to_csv('neighborhood_stats.csv', index=False)

geo = geo.copy(); geo['police_precinct'] = geo['police_precinct'].astype(str).str.zfill(2)
pc_rows = []
for pc, sub in geo.groupby('police_precinct'):
    if len(sub) < 2000:
        continue
    d = sub.groupby('date').size(); d.index = pd.to_datetime(d.index)
    d = d.reindex(temp.index).fillna(0)
    r, _ = stats.pearsonr(temp, d); b, _ = np.polyfit(temp, d, 1)
    pc_rows.append(dict(precinct=pc, total=len(sub), per_day=round(d.mean(), 1),
        pct_violent=round((sub.family == 'Violent').mean() * 100, 1),
        pct10=round(b * 10 / d.mean() * 100, 1), r=round(r, 2)))
pd.DataFrame(pc_rows).sort_values('total', ascending=False).to_csv('precinct_stats.csv', index=False)

# --------------------------------------------------------- time-of-day aggregates
q = temp.quantile([1/3, 2/3])
daygrp = temp.map(lambda t: 'cold' if t < q.iloc[0] else ('hot' if t > q.iloc[1] else 'mild'))
ndg = daygrp.value_counts()
incd = inc.copy(); incd['daygrp'] = incd['date'].map(daygrp)
prof = incd[incd.family == 'Violent'].groupby(['daygrp', 'hour']).size().unstack(0).fillna(0)
for g in ['cold', 'hot']:
    prof[g + '_perday'] = prof[g] / ndg[g]
prof[['cold_perday', 'hot_perday']].to_csv('tod_violent_profile.csv')

wh2 = wh.copy(); wh2['tbin'] = pd.cut(wh2['temperature_2m'], TBINS, labels=TLABELS)
exposure = wh2['tbin'].value_counts().reindex(TLABELS)
hh = inc.copy(); hh['hourkey'] = hh['ldt'].dt.floor('h')
hh = hh.merge(wh[['time', 'temperature_2m']], left_on='hourkey', right_on='time', how='left')
vh = hh[hh.family == 'Violent'].copy()
vh['tbin'] = pd.cut(vh['temperature_2m'], TBINS, labels=TLABELS)
rate = vh['tbin'].value_counts().reindex(TLABELS) / exposure
rate.to_csv('hourlytemp_violent_rate.csv')

# --------------------------------------------------------- weekday / weekend
dd = pd.DataFrame({'n': dtot.reindex(temp.index).fillna(0)})
dd['wknd'] = dd.index.dayofweek >= 5; dd['temp'] = temp
ww = {}
for lab, sub in [('Weekday', dd[~dd.wknd]), ('Weekend', dd[dd.wknd])]:
    r, _ = stats.pearsonr(sub.temp, sub.n); b, a = np.polyfit(sub.temp, sub.n, 1)
    ww[lab] = dict(r=r, slope=b, intercept=a, mean=sub.n.mean(), pct10=b * 10 / sub.n.mean() * 100)
pd.DataFrame(ww).T.to_csv('weekday_weekend_stats.csv')

vd = dfam['Violent'].reindex(temp.index).fillna(0)
vdf = pd.DataFrame({'n': vd, 'temp': temp, 'wknd': temp.index.dayofweek >= 5})
vdf['tbin'] = pd.cut(vdf.temp, TBINS, labels=TLABELS)
vpiv = vdf.groupby(['tbin', 'wknd'], observed=True)['n'].mean().unstack()
vpiv.columns = ['Weekday', 'Weekend']
vpiv.to_csv('weekend_violent_bins.csv')

# ------------------------------------------------- precipitation stratified / cond
mp = M_precip.copy()
mp['tbin'] = pd.cut(mp['temperature_2m_mean'], [-100, 32, 45, 60, 75, 200],
                    labels=['<32°F', '32–45°F', '45–60°F', '60–75°F', '75°F+'])
mp['wet'] = np.where(mp['precipitation_sum'] >= 0.01, 'Wet', 'Dry')
mp.groupby(['tbin', 'wet'], observed=True)['Violent'].mean().unstack().to_csv('precip_strat_violent.csv')

def cond(c):
    if c in (0, 1): return 'Clear'
    if c in (2, 3): return 'Cloudy'
    if c in (45, 48): return 'Fog'
    if c in (51, 53, 55, 56, 57): return 'Drizzle'
    if c in (61, 63, 65, 66, 67, 80, 81, 82): return 'Rain'
    if c in (71, 73, 75, 77, 85, 86): return 'Snow'
    if c in (95, 96, 99): return 'Storm'
    return 'Other'
mp['cond'] = mp['weather_code'].map(cond)
order = ['Clear', 'Cloudy', 'Fog', 'Drizzle', 'Rain', 'Snow', 'Storm']
mp.groupby('cond').agg(days=('total', 'size'), temp=('temperature_2m_mean', 'mean'),
    total=('total', 'mean'), viol=('Violent', 'mean'), prop=('Property', 'mean')
    ).reindex(order).dropna().to_csv('weather_cond_stats.csv')

# ------------------------------------------------------------- profile_data.json
print("Building profile_data.json …")
tbin_s = pd.cut(temp, bins=TBINS, labels=TLABELS)
T = temp.values; R = wf['rain_sum'].values; S = wf['snowfall_sum'].values
WET = (wf['precipitation_sum'] >= 0.01).astype(float).values

def profile(series_daily, hourly_counts):
    s = series_daily.reindex(temp.index).fillna(0).astype(float); mean = s.mean()
    rel = s.groupby(tbin_s, observed=True).mean().reindex(TLABELS)
    monthly = s.groupby(s.index.month).mean().reindex(range(1, 13)).round(2).tolist()
    b, _ = ols(s.values, [T]); pct10 = b[1] * 10 / mean * 100
    r_p, _ = stats.pearsonr(T, s.values)
    sa = climo_anom(s).values; ta = climo_anom(temp).values
    anom_r, _ = stats.pearsonr(ta, sa)
    bw, pw = ols(s.values, [T, WET]); br, pr = ols(s.values, [T, R, S])
    hr = hourly_counts.reindex(range(24)).fillna(0)
    hshare = (hr / hr.sum() * 100).round(2).tolist()
    peak_hr = int(hr.drop([0, 12]).idxmax())
    relrate = (rel / mean).round(3).tolist()
    return dict(total=int(s.sum()), per_day=round(mean, 2), relrate=relrate,
        absrate=rel.round(2).tolist(), monthly=monthly, hourly=hshare,
        pct10=round(pct10, 1), r=round(r_p, 2), anom_r=round(anom_r, 2),
        wet_pct=round(bw[2] / mean * 100, 1), wet_sig=bool(pw[2] < 0.05),
        rain_pct=round(br[2] / mean * 100, 1), rain_sig=bool(pr[2] < 0.05),
        snow_pct=round(br[3] / mean * 100, 1), snow_sig=bool(pr[3] < 0.05),
        peak_hr=peak_hr, peak_month=int(np.argmax(monthly)) + 1,
        hot_cold=round(relrate[-1] / relrate[0], 2) if relrate[0] else None,
        wknd=round(s[s.index.dayofweek >= 5].mean(), 2),
        wkdy=round(s[s.index.dayofweek < 5].mean(), 2))

items = {}
items['__ALL__'] = dict(name='All crime', family='All', **profile(dtot, inc.groupby('hour').size()))
for f in ['Violent', 'Property', 'Other']:
    items['__' + f.upper() + '__'] = dict(name=f + ' crime (all)', family=f,
        **profile(dfam[f], inc[inc.family == f].groupby('hour').size()))
for c in totals.index:
    if totals[c] < 2000:
        continue
    items[c] = dict(name=c.title(), family=family(c),
        **profile(dcat[c], inc[inc.cat == c].groupby('hour').size()))
out = dict(meta=dict(n_days=len(temp), d0=str(temp.index.min().date()),
    d1=str(temp.index.max().date()), tbins=TLABELS), items=items)
json.dump(out, open('profile_data.json', 'w'))

print(f"Done — {len(items)} profiles. Next: python3 02_make_figures.py")

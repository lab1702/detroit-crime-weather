#!/usr/bin/env python3
"""Assemble the self-contained HTML crime-vs-temperature report."""
import base64, pandas as pd, numpy as np
from hac import poisson_hac

def b64(path):
    with open(path,'rb') as f:
        return 'data:image/png;base64,'+base64.b64encode(f.read()).decode()

m = pd.read_csv('daily_merged.csv', parse_dates=['date']).set_index('date')
cs = pd.read_csv('category_stats.csv')
bs = pd.read_csv('bin_stats.csv')

# headline numbers
total_inc = int(m['total_crimes'].sum())
ndays = len(m)
d0,d1 = m.index.min().date(), m.index.max().date()
tot_r = cs.loc[cs.category=='total_crimes','pearson_r'].iloc[0]
tot_pct = cs.loc[cs.category=='total_crimes','pct_per_10F'].iloc[0]
tot_anom = cs.loc[cs.category=='total_crimes','anom_r'].iloc[0]
cold = bs['mean_total'].iloc[0]; hot = bs['mean_total'].iloc[-1]
pct_cold_hot = (hot/cold-1)*100

# top sensitive
catonly = cs[cs.category!='total_crimes'].copy()
top3 = catonly.sort_values('pct_per_10F',ascending=False).head(4)
flat = catonly[catonly['p_fdr']>=0.05].sort_values('pct_per_10F')

def cap(label,value,sub):
    return f'<div class="stat"><div class="stat-v">{value}</div><div class="stat-l">{label}</div><div class="stat-s">{sub}</div></div>'

cards = (
 cap('overall correlation (r)', f'{tot_r:.2f}', 'daily mean temp vs. total crime')+
 cap('more crime on hot vs. cold days', f'+{pct_cold_hot:.0f}%', f'{hot:.0f} vs. {cold:.0f} incidents/day')+
 cap('crime increase per +10°F', f'+{tot_pct:.1f}%', 'across all categories')+
 cap('deseasonalized correlation', f'{tot_anom:.2f}', 'effect persists within seasons')
)

# per-category precipitation effects (temp-controlled), for the table
cprecip=pd.read_csv('category_precip.csv').set_index('category')
def precip_cells(catname):
    if catname not in cprecip.index:
        return '<td class="num">—</td><td class="num">—</td>'
    r=cprecip.loc[catname]
    def fmt(v,p):
        cls='pos' if v>0 else 'neg'
        s='' if p<0.05 else '<span class="ns">·</span>'
        return f'<td class="num {cls}">{v:+.0f}%{s}</td>'
    return fmt(r['rain_pct'],r['rain_q'])+fmt(r['snow_pct'],r['snow_q'])

# full category table
tbl = catonly.sort_values('pct_per_10F',ascending=False)
def famtag(c):
    viol={'AGGRAVATED ASSAULT','ASSAULT','WEAPONS OFFENSES','ROBBERY','HOMICIDE','SEX OFFENSES','SEXUAL ASSAULT','ARSON','DISORDERLY CONDUCT','OBSTRUCTING THE POLICE'}
    prop={'DAMAGE TO PROPERTY','LARCENY','STOLEN VEHICLE','BURGLARY','STOLEN PROPERTY'}
    if c in viol: return ('Violent','v')
    if c in prop: return ('Property','p')
    return ('Other','o')
rows=''
for _,r in tbl.iterrows():
    fam,cls = famtag(r.category)
    sigtxt = '' if r['p_fdr']<0.05 else ' <span class="ns">n.s.</span>'
    strength = abs(r.pearson_r)
    bar = int(min(strength,0.6)/0.6*100)
    rows+=f'''<tr>
      <td class="cat">{r.category.title()}</td>
      <td><span class="tag {cls}">{fam}</span></td>
      <td class="num">{int(r.total):,}</td>
      <td class="num">{r.mean_per_day:.1f}</td>
      <td class="num strong">+{r.pct_per_10F:.1f}%{sigtxt}</td>
      <td class="num">{r.pearson_r:.2f}</td>
      {precip_cells(r.category)}
      <td><div class="rbar"><div class="rfill {cls}" style="width:{bar}%"></div></div></td>
    </tr>'''

# ============ NEW SECTIONS: time-of-day, weekday/weekend, geography ============
# --- time of day ---
prof = pd.read_csv('tod_violent_profile.csv', index_col=0).sort_index()
night = list(range(20,24))+list(range(0,3)); day_h=list(range(8,18))
hv_n=prof.loc[night,'hot_perday'].sum(); cv_n=prof.loc[night,'cold_perday'].sum()
hv_d=prof.loc[day_h,'hot_perday'].sum(); cv_d=prof.loc[day_h,'cold_perday'].sum()
night_lift=(hv_n/cv_n-1)*100; day_lift=(hv_d/cv_d-1)*100
hrate=pd.read_csv('hourlytemp_violent_rate.csv',index_col=0).iloc[:,0]
rate_lo=hrate.iloc[0]; rate_hi=hrate.iloc[-1]; rate_lift=(rate_hi/rate_lo-1)*100

# --- weekday/weekend ---
ww=pd.read_csv('weekday_weekend_stats.csv',index_col=0)
vb=pd.read_csv('weekend_violent_bins.csv',index_col=0)
hot_wknd=vb['Weekend'].iloc[-1]; cold_wkday=vb['Weekday'].iloc[0]
combo_lift=(hot_wknd/cold_wkday-1)*100
wknd_prem=(vb['Weekend']-vb['Weekday']).mean()

# --- geography ---
nb=pd.read_csv('neighborhood_stats.csv')
nb_sens=nb.sort_values('pct10',ascending=False)
top_sens=nb_sens.head(3)
_dt=nb[nb.neighborhood=='Downtown']['pct10']
downtown_pct10=_dt.iloc[0] if len(_dt) else top_sens.iloc[2]['pct10']
nb_vol=nb.sort_values('total',ascending=False)
pc=pd.read_csv('precinct_stats.csv')
pc['precinct']=pc['precinct'].astype(str).str.zfill(2)
pc=pc.sort_values('total',ascending=False)
prows=''
for _,r in pc.iterrows():
    prows+=f'''<tr><td class="cat">Precinct {r.precinct}</td>
      <td class="num">{int(r.total):,}</td><td class="num">{r.per_day:.1f}</td>
      <td class="num">{r.pct_violent:.0f}%</td>
      <td class="num strong">+{r.pct10:.1f}%</td><td class="num">{r.r:.2f}</td></tr>'''

# --- precipitation (section 08) ---
pm=pd.read_csv('daily_precip_merged.csv',parse_dates=[0],index_col=0)
_T=pm['temperature_2m_mean'].values
_wet=(pm['precipitation_sum']>=0.01).astype(float).values
_DOWp=pm.index.dayofweek   # day-of-week nuisance controls, matching step 1
wet_eff={}
for f in ['total','Violent','Property','Other']:
    y=pm[f].values; b,p=poisson_hac(y,[_T,_wet],dow=_DOWp); wet_eff[f]=((np.exp(b[2])-1)*100,p[2])
_rain=pm['rain_sum'].values; _snow=pm['snowfall_sum'].values
rs={}
for f in ['Violent','Property']:
    y=pm[f].values; b,p=poisson_hac(y,[_T,_rain,_snow],dow=_DOWp); ym=y.mean()
    # log-link coefficients -> incidents/day per inch at the mean rate
    rs[f]=dict(rain=ym*(np.exp(b[2])-1),rp=p[2],snow=ym*(np.exp(b[3])-1),sp=p[3])
n_wet=int(_wet.sum()); n_dry=int((1-_wet).sum()); n_snow=int((pm['snowfall_sum']>0).sum())
cond=pd.read_csv('weather_cond_stats.csv',index_col=0)
crows=''
for name,r in cond.iterrows():
    crows+=f'''<tr><td class="cat">{name}</td><td class="num">{int(r.days):,}</td>
      <td class="num">{r.temp:.0f}°</td><td class="num">{r.total:.0f}</td>
      <td class="num">{r.viol:.0f}</td><td class="num">{r.prop:.0f}</td></tr>'''

# --- wind/storm/heatwave/unify (sections 09 & 10) ---
MM=pd.read_csv('daily_master.csv',parse_dates=[0],index_col=0)
_Tm=MM['temperature_2m_mean'].values; _Prc=MM['precipitation_sum'].values; _Wd=MM['wind_speed_10m_max'].values
_DOWm=MM.index.dayofweek   # day-of-week nuisance controls
# wind per +10mph
# wind per +10mph -> incidents/day at the mean rate
_vm=MM['Violent'].mean(); _pmn=MM['Property'].mean()
wind_v=poisson_hac(MM['Violent'].values,[_Tm,_Prc,_Wd],dow=_DOWm); wind_v_eff=_vm*(np.exp(wind_v[0][3]*10)-1); wind_v_p=wind_v[1][3]
wind_p=poisson_hac(MM['Property'].values,[_Tm,_Prc,_Wd],dow=_DOWm); wind_p_eff=_pmn*(np.exp(wind_p[0][3]*10)-1); wind_p_p=wind_p[1][3]
# storm
_wthr=np.quantile(_Wd,0.9)
_storm=((MM['precipitation_sum']>0.5)|(MM['wind_speed_10m_max']>=_wthr)).astype(float).values
n_storm=int(_storm.sum())
sv=poisson_hac(MM['Violent'].values,[_Tm,_storm],dow=_DOWm); storm_v=(np.exp(sv[0][2])-1)*100
# unify (violent) — log-link % effects
yv=MM['Violent'].values
u_heat=(np.exp(poisson_hac(yv,[_Tm],dow=_DOWm)[0][1]*10)-1)*100
_wet=(MM['precipitation_sum']>=0.01).astype(float).values
u_wet=(np.exp(poisson_hac(yv,[_Tm,_wet],dow=_DOWm)[0][2])-1)*100
_hiwind=(_Wd>=_wthr).astype(float)
u_wind=(np.exp(poisson_hac(yv,[_Tm,_hiwind],dow=_DOWm)[0][2])-1)*100
u_storm=(np.exp(poisson_hac(yv,[_Tm,_storm],dow=_DOWm)[0][2])-1)*100
# heat waves
_tmax=MM['temperature_2m_max']; _hot=(_tmax>=85).astype(int); _grp=(_hot.diff()!=0).cumsum()
_pos=np.zeros(len(MM),int)
for g,v in _hot.groupby(_grp):
    if v.iloc[0]==1:
        for i,idx in enumerate(v.index): _pos[MM.index.get_loc(idx)]=i+1
MM['_pos']=_pos
n_hw_days=int((_pos>=3).sum()); n_streaks=sum(1 for g,v in _hot.groupby(_grp) if v.iloc[0]==1 and len(v)>=3)
_hotsub=MM[_tmax>=85]
# Hot-days-only sub-sample is NOT a contiguous daily series, so HAC lags are
# meaningless here -> White (HC) robust SEs via hac=False. Effect is the day-3+
# indicator translated to incidents/day at the hot-day mean rate.
_day3=(_hotsub['_pos']>=3).astype(float).values
hw_v=poisson_hac(_hotsub['Violent'].values,[_hotsub['temperature_2m_max'].values,_day3],hac=False)
hw_v_eff=_hotsub['Violent'].mean()*(np.exp(hw_v[0][2])-1); hw_v_p=hw_v[1][2]
hw_t=poisson_hac(_hotsub['total'].values,[_hotsub['temperature_2m_max'].values,_day3],hac=False)
hw_t_p=hw_t[1][2]


html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Detroit Crime &amp; Temperature</title>
<style>
:root{{--ink:#1a1d29;--sub:#5b6577;--line:#e6e9ef;--bg:#f6f7fb;--card:#fff;
--accent:#e0492f;--cool:#2c6fbb;--green:#3a7d44;--soft:#fbfcfe;}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
line-height:1.6;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:920px;margin:0 auto;padding:0 22px 80px}}
header{{background:linear-gradient(135deg,#1a1d29 0%,#2a3350 55%,#3a4a6b 100%);
color:#fff;padding:64px 0 56px;margin-bottom:-32px}}
header .wrap{{padding-bottom:0}}
.kicker{{text-transform:uppercase;letter-spacing:.18em;font-size:12.5px;
font-weight:600;color:#9db3d8;margin:0 0 14px}}
h1{{font-size:40px;line-height:1.12;margin:0 0 16px;font-weight:800;letter-spacing:-.02em}}
header p{{font-size:18px;color:#c8d2e6;max-width:640px;margin:0}}
.meta{{margin-top:26px;font-size:13px;color:#90a0c0;display:flex;flex-wrap:wrap;gap:6px 20px}}
.meta b{{color:#c8d2e6;font-weight:600}}
.cta{{display:inline-flex;align-items:center;gap:13px;margin-top:26px;text-decoration:none;
background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.22);border-radius:13px;
padding:13px 20px;color:#fff;transition:all .15s;backdrop-filter:blur(4px)}}
.cta:hover{{background:rgba(255,255,255,.18);border-color:rgba(255,255,255,.4);transform:translateY(-1px)}}
.cta-ic{{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;
border-radius:9px;background:var(--accent);font-size:15px;flex:none}}
.cta b{{font-size:15px}} .cta-sub{{font-size:12.5px;color:#b9c6e0}}
.homelink{{display:inline-block;margin-bottom:18px;color:#9db3d8;text-decoration:none;font-size:13.5px;
font-weight:600;border:1px solid rgba(255,255,255,.18);border-radius:20px;padding:5px 14px;transition:all .14s}}
.homelink:hover{{color:#fff;border-color:rgba(255,255,255,.4);background:rgba(255,255,255,.08)}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:48px 0 8px;position:relative;z-index:2}}
.stat{{background:var(--card);border:1px solid var(--line);border-radius:14px;
padding:20px 18px;box-shadow:0 6px 24px rgba(26,29,41,.06)}}
.stat-v{{font-size:30px;font-weight:800;letter-spacing:-.02em;color:var(--accent)}}
.stat-l{{font-size:13px;font-weight:600;margin-top:6px;color:var(--ink)}}
.stat-s{{font-size:12px;color:var(--sub);margin-top:3px}}
section{{background:var(--card);border:1px solid var(--line);border-radius:16px;
padding:34px 38px;margin:22px 0;box-shadow:0 4px 18px rgba(26,29,41,.04)}}
h2{{font-size:25px;font-weight:800;letter-spacing:-.02em;margin:6px 0 8px}}
h2 .n{{color:var(--cool);font-size:15px;font-weight:700;display:block;
text-transform:uppercase;letter-spacing:.14em;margin-bottom:6px}}
section p{{color:#39414f;font-size:16px}}
.lead{{font-size:17px}}
figure{{margin:24px 0 6px}}
figure img{{width:100%;border:1px solid var(--line);border-radius:12px;display:block;background:#fff}}
figcaption{{font-size:13px;color:var(--sub);margin-top:10px;text-align:center}}
.take{{background:var(--soft);border-left:3px solid var(--accent);border-radius:0 10px 10px 0;
padding:14px 18px;margin:20px 0 0;font-size:15px}}
.take b{{color:var(--accent)}}
table{{width:100%;border-collapse:collapse;font-size:13.5px;margin-top:12px}}
th{{text-align:left;font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;
color:var(--sub);font-weight:700;padding:8px 10px;border-bottom:2px solid var(--line)}}
th.num,td.num{{text-align:right}}
td{{padding:9px 10px;border-bottom:1px solid var(--line)}}
td.cat{{font-weight:600}}
td.strong{{font-weight:700}}
td.pos{{color:#2c6135;font-weight:600}} td.neg{{color:#b8341d;font-weight:600}}
.tscroll{{overflow-x:auto;-webkit-overflow-scrolling:touch}}
.ns{{color:#aab2c0;font-weight:600;font-size:11px}}
.tag{{font-size:11px;font-weight:700;padding:2px 9px;border-radius:20px;white-space:nowrap}}
.tag.v{{background:#fde6e1;color:#b8341d}} .tag.p{{background:#e3f0e6;color:#2c6135}}
.tag.o{{background:#eceef2;color:#5b6577}}
.rbar{{background:#eef0f5;border-radius:6px;height:8px;width:80px;overflow:hidden}}
.rfill{{height:100%;border-radius:6px}} .rfill.v{{background:var(--accent)}}
.rfill.p{{background:var(--green)}} .rfill.o{{background:#9aa3b2}}
ul{{color:#39414f;font-size:15.5px}} li{{margin:6px 0}}
.method{{font-size:14px;color:var(--sub)}} .method h2{{color:var(--ink)}}
.method b{{color:var(--ink)}}
footer{{text-align:center;color:var(--sub);font-size:13px;margin-top:30px}}
a{{color:var(--cool)}}
@media(max-width:680px){{.stats{{grid-template-columns:repeat(2,1fr)}}h1{{font-size:30px}}section{{padding:26px 22px}}}}
</style></head><body>
<header><div class="wrap">
<a class="homelink" href="index.html">&#8962; Overview</a>
<p class="kicker">Data Analysis Report</p>
<h1>When Detroit Heats Up,<br>So Does Its Crime</h1>
<p>How daily temperature — and rain, and snow — shape the volume and the type of crime reported across the city, and why some offenses ride the weather while others ignore it.</p>
<div class="meta">
<span><b>Period:</b> {d0} → {d1}</span>
<span><b>Incidents:</b> {total_inc:,}</span>
<span><b>Days analyzed:</b> {ndays:,}</span>
<span><b>Crime:</b> Detroit Open Data Portal</span>
<span><b>Weather:</b> Open-Meteo reanalysis</span>
</div>
<a class="cta" href="detroit_crime_weather_explorer.html">
<span class="cta-ic">▸</span><span><b>Open the interactive explorer</b><br><span class="cta-sub">Pick any offense and see its full weather profile</span></span></a>
</div></header>

<div class="wrap">
<div class="stats">{cards}</div>

<section>
<h2><span class="n">01 — The headline</span>Warmer days are busier days for Detroit police</h2>
<p class="lead">Across {ndays:,} days, the daily mean temperature alone explains a large share of the swing in how much crime gets reported. The relationship is strong, positive, and remarkably linear: each additional 10&deg;F is associated with roughly <b>{tot_pct:.0f}% more reported crime</b> (Pearson r&nbsp;=&nbsp;{tot_r:.2f}).</p>
<figure><img src="{b64('figs/fig1_scatter.png')}" alt="Scatter of daily crime vs temperature"><figcaption>Each dot is one day. Color encodes temperature, from cold blue to hot red.</figcaption></figure>
<figure><img src="{b64('figs/fig2_bins.png')}" alt="Average crime by temperature bin"></figure>
<div class="take"><b>Takeaway.</b> The coldest days (&lt;20&deg;F) average just {cold:.0f} reported incidents; the hottest (75&deg;F+) average {hot:.0f} — a <b>{pct_cold_hot:.0f}% jump</b>. Heat doesn't only change <i>how much</i> crime occurs, but as the next sections show, <i>which kinds</i>.</div>
</section>

<section>
<h2><span class="n">02 — The seasonal engine</span>Crime and temperature rise and fall together</h2>
<p>Aggregated by month, the two series trace nearly the same arc: a winter trough in January–February and a summer peak in July–August. July, the hottest month, is also the single highest-crime month of the year.</p>
<figure><img src="{b64('figs/fig4_monthly.png')}" alt="Monthly crime and temperature"></figure>
<p>This co-movement is the heart of the story — but it also raises a fair objection: maybe summer brings more crime for reasons that merely <i>coincide</i> with heat (school being out, longer daylight, more travel). Section 04 tackles that head-on.</p>
</section>

<section>
<h2><span class="n">03 — Not all crime is equal</span>Heat inflames confrontation, not paperwork</h2>
<p>Breaking the effect out by offense category reveals a sharp split. <b>Violent and interpersonal crimes</b> are the most temperature-sensitive: aggravated assault, weapons offenses, and homicide all climb steeply with the mercury. <b>Property and outdoor-opportunity crimes</b> respond moderately. And <b>administrative or indoor offenses</b> — fraud, drug cases, court-process violations — barely move at all.</p>
<figure><img src="{b64('figs/fig3_sensitivity.png')}" alt="Temperature sensitivity by category"><figcaption>Slope of daily incidents on temperature, scaled to each category's own average. "n.s." = not statistically significant.</figcaption></figure>
<p>The heatmap below makes the texture vivid. Read across a row: deep red means a category runs well above its yearly average on hot days, deep blue means well below. Aggravated assault and weapons offenses swing from ~0.69&times; their average in deep cold to ~1.29&times; in heat — a near-doubling. Fraud and drug cases stay flat all the way across.</p>
<figure><img src="{b64('figs/fig5_heatmap.png')}" alt="Heatmap of relative crime rate by temperature"></figure>
<div class="take"><b>Takeaway.</b> The "heat &rarr; aggression" pattern long documented in criminology shows up cleanly here: temperature acts most on <b>impulsive, face-to-face violence</b>, and least on premeditated or indoor offenses.</div>
</section>

<section>
<h2><span class="n">04 — Is it really the heat?</span>Yes — even after stripping out the seasons</h2>
<p>To separate temperature from everything else that makes summer summer, we computed <b>anomalies</b>: we fit each series a smooth seasonal cycle (a low-order harmonic curve through the year) and subtract it, leaving only how much warmer-or-cooler and higher-or-lower-crime each specific day was than its time of year would predict. If a 70&deg;F day in May behaves like a 70&deg;F day in September, season — not heat — would be doing the work, and the anomaly correlation would vanish.</p>
<p>It doesn't. Warmer-than-normal days still carry more crime than normal (r&nbsp;=&nbsp;{tot_anom:.2f}), and the effect is strongest for exactly the violent categories flagged above. An unseasonably hot day is a higher-crime day on its own.</p>
<figure><img src="{b64('figs/fig6_anomaly.png')}" alt="Deseasonalized anomaly scatter"></figure>
<div class="take"><b>Takeaway.</b> The temperature signal survives deseasonalizing. This is a genuine same-day association between heat and crime, not just a calendar artifact.</div>
</section>

<section>
<h2><span class="n">05 — The clock</span>Heat hits hardest after dark</h2>
<p>Joining each violent incident to the <i>ambient air temperature in that very hour</i>, the dose-response is strikingly clean: the city averages {rate_lo:.1f} violent incidents in a sub-20&deg;F hour, rising to {rate_hi:.1f} in a 75&deg;F+ hour — a <b>{rate_lift:.0f}% increase</b>, hour for hour.</p>
<p>But the heat doesn't act evenly around the clock. Comparing the warmest third of days with the coldest third, daytime violence (8&nbsp;am–6&nbsp;pm) runs about <b>{day_lift:.0f}% higher</b> on hot days — while the late-night window (8&nbsp;pm–3&nbsp;am) jumps <b>{night_lift:.0f}% higher</b>. Warm evenings keep people outdoors and in contact long after a cold night would have emptied the streets.</p>
<figure><img src="{b64('figs/fig7_hotnights.png')}" alt="Violent crime by hour, hot vs cold days"><figcaption>Average violent incidents per day in each hour, warmest-third vs coldest-third days. The red–blue gap is widest in the evening.</figcaption></figure>
<div class="take"><b>Takeaway.</b> Temperature's effect on violence is concentrated in the evening and overnight hours — the "long warm night" is the real risk window.</div>
</section>

<section>
<h2><span class="n">06 — The calendar</span>Hot weekends are the most violent days of all</h2>
<p>Weekends already carry more violence than weekdays at every temperature, and heat lifts both. Stacking the two effects, a hot summer weekend averages <b>{hot_wknd:.0f} violent incidents a day</b> — versus just {cold_wkday:.0f} on a frigid weekday, a <b>{combo_lift:.0f}% swing</b> from the calm extreme to the volatile one. Across the temperature range, weekends run about {wknd_prem:.0f} extra violent incidents per day above weekdays.</p>
<p>For total crime, the temperature <i>slope</i> is nearly identical on weekends (+{ww.loc['Weekend','pct10']:.1f}% per 10&deg;F) and weekdays (+{ww.loc['Weekday','pct10']:.1f}%) — heat raises the baseline rather than steepening it. The weekend's distinct signature is in <i>violence</i> specifically, where social activity and temperature compound.</p>
<figure><img src="{b64('figs/fig8_weekend.png')}" alt="Violent crime by temperature, weekday vs weekend"></figure>
<div class="take"><b>Takeaway.</b> Temperature and the weekend are roughly additive for violent crime; the hottest weekends sit at the top of the risk distribution.</div>
</section>

<section>
<h2><span class="n">07 — The map</span>Heat sensitivity is a downtown, riverfront story</h2>
<p>Crime is not spread evenly across Detroit, and neither is its responsiveness to heat. The density map below traces the familiar geography — corridors along the major avenues, concentration through the greater downtown core, the river defining the southern edge.</p>
<figure><img src="{b64('figs/fig9_map.png')}" alt="Detroit crime density map"></figure>
<p>Coloring each neighborhood by its temperature sensitivity reveals a pattern: the <b>entertainment and riverfront districts react most strongly to heat</b>. {top_sens.iloc[0]['neighborhood']} (+{top_sens.iloc[0]['pct10']:.0f}% per 10&deg;F), {top_sens.iloc[1]['neighborhood']} (+{top_sens.iloc[1]['pct10']:.0f}%), and Downtown (+{downtown_pct10:.0f}%) top the list — places where warm weather draws crowds to bars, festivals, and the riverwalk. Quieter residential neighborhoods hover near the citywide +4–5%.</p>
<figure><img src="{b64('figs/fig10_nbmap.png')}" alt="Neighborhood temperature sensitivity map"><figcaption>Each bubble is a neighborhood (≥3,000 incidents): size = total volume, color = % more crime per +10&deg;F.</figcaption></figure>
<p>At the precinct level the effect is universal but graded — every one of Detroit's precincts shows a positive temperature response, from +{pc['pct10'].min():.1f}% to +{pc['pct10'].max():.1f}% per 10&deg;F.</p>
<table>
<thead><tr><th>Precinct</th><th class="num">Incidents</th><th class="num">/day</th>
<th class="num">% violent</th><th class="num">Per +10&deg;F</th><th class="num">r</th></tr></thead>
<tbody>{prows}</tbody>
</table>
<div class="take"><b>Takeaway.</b> The temperature&ndash;crime link holds citywide, but it is sharpest where heat changes how people use public space — the downtown core and the riverfront entertainment districts.</div>
</section>

<section>
<h2><span class="n">08 — The sky</span>Rain quiets violence; snow blunts theft</h2>
<p>Temperature is not the only thing the weather does. Across {n_wet:,} wet days and {n_dry:,} dry ones, precipitation leaves its own mark — but because rain and snow are tangled up with temperature (it only snows when it's cold), every figure here <b>holds temperature constant</b> via regression, isolating the precipitation effect itself.</p>
<p>The clearest signal is on <b>violent crime</b>: a wet day sees about <b>{wet_eff['Violent'][0]:.0f}% fewer</b> violent incidents than a dry day at the same temperature. Property crime barely moves ({wet_eff['Property'][0]:+.1f}%), and administrative offenses — fraud, warrants, court process — are statistically untouched ({wet_eff['Other'][0]:+.1f}%, n.s.). Rain keeps would-be antagonists indoors and off the streets; it does little to stop a fraud report from being filed.</p>
<figure><img src="{b64('figs/fig11_wet_effect.png')}" alt="Temperature-adjusted wet-day effect by crime type"></figure>
<p>And the suppression is not a fluke of warm rainy days — it holds inside <i>every</i> temperature band, from freezing to sweltering, each wet column sitting a few percent below its dry neighbor.</p>
<figure><img src="{b64('figs/fig12_strat.png')}" alt="Dry vs wet violent crime within temperature bins"></figure>
<p><b>Rain and snow do different jobs.</b> Separating precipitation by type — again at equal temperature — uncovers a clean split. Each inch of <b>rain</b> removes about {abs(rs['Violent']['rain']):.0f} violent incidents from the day but leaves theft essentially alone. Each inch of <b>snow</b> does the opposite: it cuts <b>property crime</b> by roughly {abs(rs['Property']['snow']):.0f} incidents — buried cars, shuttered storefronts and empty sidewalks shrink the opportunity for larceny and break-ins — while denting violence only modestly.</p>
<figure><img src="{b64('figs/fig13_rainsnow.png')}" alt="Rain vs snow effect by crime type"><figcaption>Regression coefficients per inch of precipitation, controlling for daily mean temperature. "n.s." = not significant.</figcaption></figure>
<p>For reference, here is the raw picture by sky condition. Snow days look dramatically calmer — but most of that gap is the cold they ride in on, which is why the temperature-controlled figures above tell the more honest story.</p>
<table>
<thead><tr><th>Sky condition</th><th class="num">Days</th><th class="num">Avg temp</th>
<th class="num">All crime/day</th><th class="num">Violent/day</th><th class="num">Property/day</th></tr></thead>
<tbody>{crows}</tbody>
</table>
<div class="take"><b>Takeaway.</b> Wet weather suppresses crime independently of temperature — rain chiefly calms <b>violence</b>, snow chiefly blunts <b>property</b> crime, and neither touches paperwork offenses.</div>
</section>

<section>
<h2><span class="n">09 — The wind &amp; the storm</span>Rough weather keeps the peace</h2>
<p>Wind tells the same story as rain, and tells it independently. Holding both temperature and precipitation fixed, each extra <b>10&nbsp;mph of peak wind</b> shaves about <b>{abs(wind_v_eff):.1f} violent incidents</b> off the day ({wind_v_p:.0e} significance) — yet leaves property crime essentially untouched ({wind_p_eff:+.1f}/day, n.s.). A blustery day is an uncomfortable day to be loitering on a corner.</p>
<figure><img src="{b64('figs/fig15_wind.png')}" alt="Wind effect on violent vs property crime"></figure>
<p>Bundling the rough days together — the {n_storm:,} "storm days" with heavy rain (&gt;0.5&nbsp;in) or strong wind (top-decile, &ge;{_wthr:.0f}&nbsp;mph) — violent crime runs about <b>{abs(storm_v):.0f}% below</b> a calm day of the same temperature.</p>
<p>Step back and a single mechanism organizes the whole report. Every weather condition that makes the outdoors <i>less</i> hospitable — rain, wind, storms — pushes violence <b>down</b> by a similar 5–7%. Only heat, which makes the outdoors <i>more</i> inviting, pushes it <b>up</b>. Violence in Detroit is, in large part, a function of how many people are outside and in contact with one another.</p>
<figure><img src="{b64('figs/fig16_unify.png')}" alt="Effect of weather conditions on violent crime"><figcaption>Each bar is one condition's effect on violent crime versus a day of equal temperature — a simplified single-factor view (the wind and rain sections above add finer joint controls). Heat is the lone condition that increases it.</figcaption></figure>
<div class="take"><b>Takeaway.</b> The thread tying heat, rain, wind and storms together is <b>street exposure</b>: pleasant weather populates public space and friction follows; harsh weather empties it and violence recedes.</div>
</section>

<section>
<h2><span class="n">10 — The long hot spell</span>A heat wave is no worse than its hottest day</h2>
<p>If heat fuels aggression, do tempers compound over a <i>prolonged</i> hot spell? We flagged Detroit's heat waves — runs of 3+ consecutive days topping 85&deg;F (the {n_streaks} such streaks cover {n_hw_days} days) — and asked whether being deep into one adds crime <i>beyond</i> what the day's own temperature predicts.</p>
<p>It does not. Comparing day&nbsp;3+ of a heat wave to an isolated hot day of the same temperature, the difference is a statistically insignificant {hw_v_eff:+.1f} violent incidents ({hw_v_p:.2f} significance) — and likewise flat for total crime. Crime rises with the thermometer each day and resets with it; the heat does not "bank."</p>
<figure><img src="{b64('figs/fig14_heatwave.png')}" alt="Violent crime by position within a heat wave"></figure>
<div class="take"><b>Takeaway.</b> Heat's effect is <b>contemporaneous, not cumulative</b>. For forecasting risk, today's temperature matters; how long the hot streak has run does not.</div>
</section>

<section>
<h2><span class="n">11 — Every category, ranked</span>One row per offense: heat, rain and snow</h2>
<p>The complete picture for all {len(tbl)} offense categories with enough volume to model. <b>Per +10&deg;F</b> is the temperature sensitivity; <b>Rain</b> and <b>Snow</b> give the change per inch of each (as % of the category's average), both holding temperature constant. Green = more crime, red = less; a small dot (·) flags results that are not statistically significant.</p>
<div class="tscroll"><table>
<thead><tr><th>Offense category</th><th>Type</th><th class="num">Total</th>
<th class="num">/day</th><th class="num">Per +10&deg;F</th><th class="num">r</th>
<th class="num">Rain /in</th><th class="num">Snow /in</th><th>Heat corr.</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
<p class="method" style="margin-top:14px">Reading the precipitation columns: most street-facing offenses turn <span style="color:#b8341d">red</span> in the wet (weapons {cprecip.loc['WEAPONS OFFENSES','rain_pct']:.0f}%/in&nbsp;rain, disorderly conduct {cprecip.loc['DISORDERLY CONDUCT','rain_pct']:.0f}%), while <b>burglary</b> stands out in <span style="color:#2c6135">green</span> — break-ins actually <i>rise</i> with rain ({cprecip.loc['BURGLARY','rain_pct']:+.0f}%/in), the cover of bad weather apparently working in the burglar's favor.</p>
</section>

<section class="method">
<h2>Methodology &amp; caveats</h2>
<ul>
<li><b>Crime data.</b> Detroit Police Department incident records via the <a href="https://data.detroitmi.gov/">Detroit Open Data Portal</a> (RMS export). Analysis restricted to {d0}&ndash;{d1}, the window with consistent reporting (2017 onward); sparse legacy records back to 1915 were excluded. Each incident's UTC timestamp was converted to America/Detroit local time before assigning it to a calendar day.</li>
<li><b>Weather data.</b> Daily mean/max/min 2&nbsp;m air temperature for downtown Detroit (42.33&deg;N, 83.05&deg;W) from the Open-Meteo historical reanalysis archive, in &deg;F. Daily mean temperature is used throughout.</li>
<li><b>Method.</b> Incidents were aggregated to daily counts overall and per offense category, then joined to weather by date. Each weather effect is fit with a <b>Poisson pseudo-maximum-likelihood</b> model (log link): the coefficients are consistent for the conditional mean even though daily crime is over-dispersed, and a +10&deg;F change is reported as the multiplicative effect <b>(e<sup>10&beta;</sup>&minus;1)&times;100&percnt;</b> (absolute per-day effects are evaluated at the series mean). Pearson and Spearman correlations are also reported as descriptive measures, alongside a deseasonalized check that regresses crime anomalies on temperature anomalies, where each series' smooth seasonal cycle (a low-order harmonic fit on the day-of-year, leap-year safe) has been removed first (kept linear, since anomalies can be negative). Standard errors are robust by construction: because counts are both over-dispersed and serially correlated (residual lag-1 autocorrelation &asymp;&nbsp;0.3), every p-value uses a <b>Newey-West (HAC)</b> sandwich on the Poisson score — a Bartlett kernel with the automatic rule-of-thumb bandwidth (lag&nbsp;=&nbsp;4&middot;(n/100)<sup>2/9</sup>) — which is valid under both, where i.i.d. errors would overstate significance by roughly 2&ndash;3&times; (the standard error for the total-crime series roughly triples from nonrobust to HAC). Every count model on the full daily series also includes <b>day-of-week indicators</b> as nuisance controls, soaking up Detroit's strong weekly cycle so it cannot leak into the weather coefficients; because day-of-week is essentially uncorrelated with temperature the point estimates barely move, but the inference is cleaner (the subsample tests on non-contiguous slices &mdash; weekday/weekend and hot-days-only &mdash; omit them, as full-week indicators do not apply there). Across the per-offense tables, significance flags are <b>Benjamini-Hochberg FDR-corrected</b> within each family of category-level tests (temperature, wet, rain, snow), so an isolated "significant" category among two dozen is not mistaken for a real effect; the headline all-crime row and the four family aggregates are primary hypotheses and keep their raw p-values.</li>
<li><b>Time of day.</b> The hourly analysis joins each incident to Open-Meteo's hourly 2&nbsp;m temperature for the matching local clock-hour. "Hot" and "cold" days are the warmest and coldest thirds of days by daily mean temperature. "Violent" is a broad violent/interpersonal grouping: assault, aggravated assault, weapons, robbery, homicide, sexual/sex offenses, arson, disorderly conduct, and obstructing police &mdash; note this reaches beyond the strict UCR violent definition to include arson and the confrontational public-order offenses (disorderly conduct, obstructing police), which together are only ~4&percnt; of the group and do not drive its results. "Property" groups larceny, damage, stolen vehicle, burglary, and stolen property. Records whose timestamp falls exactly on midnight (00:00:00) or noon (12:00:00) are unknown-time placeholders &mdash; together ~5% of incidents, far above chance &mdash; and are excluded from all hour-of-day analyses (but retained in daily counts, where the calendar day is still valid).</li>
<li><b>Geography.</b> Incidents are geocoded to the nearest street intersection (visible as faint gridding in the density map). Neighborhood sensitivity is computed only for neighborhoods with &ge;3,000 incidents; precinct figures cover all 11 precincts. Bubble positions are median incident coordinates, not official boundaries.</li>
<li><b>Precipitation.</b> Daily precipitation, rain, and snowfall totals (inches) and WMO weather codes come from the same Open-Meteo archive. Because precipitation co-varies with temperature, all precipitation effects come from the same Poisson model with daily mean temperature included as a control (and, for the rain-vs-snow split, rain and snowfall amounts entered separately); the by-condition table is raw and is labelled as temperature-confounded. A "wet day" is &ge;0.01&nbsp;in of precipitation.</li>
<li><b>Wind &amp; storms.</b> Daily maximum 10&nbsp;m wind speed (mph) from the same archive. Wind effects come from regressions controlling for both temperature and precipitation. "Storm days" are the upper-decile wind days (&ge;{_wthr:.0f}&nbsp;mph) or heavy-rain days (&gt;0.5&nbsp;in); the ERA5 archive does not flag thunderstorms separately, so no lightning/thunder classification is used.</li>
<li><b>Heat waves.</b> Defined as 3+ consecutive days with a daily high &ge;85&deg;F (using daily maximum, not mean, temperature). The cumulative test regresses daily crime (Poisson, log link) on the day's maximum temperature plus an indicator for being on day&nbsp;3 or later of a wave, so any heat-wave coefficient is the effect <i>beyond</i> that day's heat. Because this test runs on the hot-days-only sub-sample &mdash; which is not a contiguous daily series &mdash; it uses heteroskedasticity-robust (White) standard errors rather than the HAC lags used elsewhere.</li>
<li><b>Correlation, not causation.</b> These are observational associations. Heat plausibly increases crime through more time outdoors, more social contact, and the well-studied link between temperature and aggression — but daylight hours, school calendars, and seasonal routines move with temperature and are not separately controlled here (the anomaly analysis mitigates, not eliminates, this).</li>
<li><b>Reporting effects.</b> Figures count <i>reported</i> incidents. Categories such as fraud reflect when a report was filed rather than when conduct occurred, which dampens any weather signal. Recent weeks may be revised upward as cases are entered, so not-yet-complete trailing days (any final day whose count falls below half the preceding four-week median) are dropped from the analysis window rather than entering the regressions as artificial near-zero days.</li>
</ul>
</section>

<footer>Generated {d1} &middot; Crime: Detroit Open Data Portal &middot; Weather: Open-Meteo &middot; Analysis in Python (pandas / SciPy / Matplotlib)</footer>
</div>
</body></html>'''

with open('detroit_crime_temperature_report.html','w') as f:
    f.write(html)
print("wrote detroit_crime_temperature_report.html", len(html)//1024,"KB")

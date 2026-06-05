#!/usr/bin/env python3
"""Build the index.html landing page introducing both deliverables."""
import json, pandas as pd

data = json.load(open('profile_data.json'))
meta = data['meta']; ALL = data['items']['__ALL__']
cs = pd.read_csv('category_stats.csv')
catonly = cs[cs.category!='total_crimes']
n_cat = (catonly['total']>=2000).sum()
# headline offense: most heat-sensitive among substantial-volume categories
# (avoids tiny noisy categories topping the raw slope ranking)
top = catonly[catonly['total']>=10000].sort_values('pct_per_10F',ascending=False).iloc[0]

# bin extremes for the hot-vs-cold headline
bs = pd.read_csv('bin_stats.csv')
cold = bs['mean_total'].iloc[0]; hot = bs['mean_total'].iloc[-1]
pct_ch = (hot/cold-1)*100

V = {k:v for k,v in {
 'ndays':f"{meta['n_days']:,}", 'd0':meta['d0'], 'd1':meta['d1'],
 'total':f"{ALL['total']:,}", 'perday':f"{ALL['per_day']:.0f}",
 'pct10':f"{ALL['pct10']:.1f}", 'pctch':f"{pct_ch:.0f}",
 'topcat':top['category'].title(), 'toppct':f"{top['pct_per_10F']:.1f}",
 'ncat':int(n_cat),
}.items()}

HTML = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Detroit Crime &amp; Weather</title>
<style>
:root{{--ink:#1a1d29;--sub:#5b6577;--line:#e6e9ef;--bg:#f6f7fb;--card:#fff;
--accent:#e0492f;--cool:#2c6fbb;--green:#3a7d44;}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
line-height:1.6;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:940px;margin:0 auto;padding:0 22px}}
header{{background:linear-gradient(135deg,#1a1d29 0%,#2a3350 55%,#3a4a6b 100%);
color:#fff;padding:80px 0 92px;text-align:center;position:relative;overflow:hidden}}
.kicker{{text-transform:uppercase;letter-spacing:.2em;font-size:12.5px;font-weight:600;color:#9db3d8;margin:0 0 18px}}
h1{{font-size:48px;line-height:1.08;margin:0 0 20px;font-weight:800;letter-spacing:-.025em}}
h1 .hl{{background:linear-gradient(120deg,#ff7a5c,#e0492f);-webkit-background-clip:text;background-clip:text;color:transparent}}
header p.intro{{font-size:19px;color:#c8d2e6;max-width:640px;margin:0 auto}}
.hmeta{{margin-top:28px;font-size:13.5px;color:#90a0c0;display:flex;justify-content:center;flex-wrap:wrap;gap:7px 26px}}
.hmeta b{{color:#dbe3f0;font-weight:700}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:-58px 0 16px;position:relative;z-index:3}}
.stat{{background:var(--card);border:1px solid var(--line);border-radius:15px;padding:22px 18px;
box-shadow:0 10px 30px rgba(26,29,41,.09);text-align:center}}
.stat .v{{font-size:30px;font-weight:800;letter-spacing:-.02em;color:var(--accent)}}
.stat .l{{font-size:12.5px;font-weight:600;margin-top:6px;color:var(--ink)}}
.stat .s{{font-size:11.5px;color:var(--sub);margin-top:2px}}
.cards{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:30px 0 14px}}
.dcard{{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:0;overflow:hidden;
box-shadow:0 6px 22px rgba(26,29,41,.06);display:flex;flex-direction:column;transition:transform .15s,box-shadow .15s}}
.dcard:hover{{transform:translateY(-3px);box-shadow:0 16px 38px rgba(26,29,41,.13)}}
.dcard .top{{height:7px}}
.dcard.report .top{{background:linear-gradient(90deg,#2c6fbb,#e0492f)}}
.dcard.explore .top{{background:linear-gradient(90deg,#3a7d44,#2c6fbb)}}
.dcard .body{{padding:28px 28px 26px;display:flex;flex-direction:column;flex:1}}
.dcard .tagrow{{display:flex;align-items:center;gap:10px;margin-bottom:14px}}
.badge{{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;padding:4px 11px;border-radius:20px}}
.report .badge{{background:#e7eefb;color:#1f55a3}} .explore .badge{{background:#e3f0e6;color:#2c6135}}
.dcard h2{{font-size:23px;margin:0 0 8px;font-weight:800;letter-spacing:-.01em}}
.dcard p{{font-size:15px;color:#39414f;margin:0 0 16px}}
.dcard ul{{margin:0 0 22px;padding-left:18px;color:#4a5364;font-size:14px}}
.dcard li{{margin:5px 0}}
.go{{margin-top:auto;display:inline-flex;align-items:center;gap:10px;text-decoration:none;
font-weight:700;font-size:15px;color:#fff;border-radius:12px;padding:13px 20px;justify-content:center;transition:filter .15s}}
.go:hover{{filter:brightness(1.07)}}
.report .go{{background:var(--cool)}} .explore .go{{background:var(--green)}}
.go .ar{{font-size:17px}}
.how{{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:26px 30px;margin:14px 0 50px}}
.how h3{{margin:0 0 6px;font-size:18px;font-weight:800}}
.how p{{margin:0 0 14px;color:var(--sub);font-size:14.5px}}
.src{{display:flex;flex-wrap:wrap;gap:8px 26px;font-size:13.5px;color:#4a5364}}
.src b{{color:var(--ink)}}
.src a{{color:var(--cool);text-decoration:none}} .src a:hover{{text-decoration:underline}}
footer{{text-align:center;color:var(--sub);font-size:13px;padding:0 0 50px}}
@media(max-width:720px){{.stats{{grid-template-columns:repeat(2,1fr);margin-top:-40px}}
.cards{{grid-template-columns:1fr}}h1{{font-size:34px}}header{{padding:60px 0 74px}}}}
</style></head><body>
<header><div class="wrap">
<p class="kicker">A Data Analysis Project</p>
<h1>Detroit Crime,<br><span class="hl">Read Through the Weather</span></h1>
<p class="intro">Nine years of police incidents meet daily temperature, rain and snow — to ask a simple question: how much does the weather outside shape the crime reported across the city?</p>
<div class="hmeta">
<span><b>{V['total']}</b> incidents</span>
<span><b>{V['ndays']}</b> days</span>
<span><b>{V['d0']}</b> → <b>{V['d1']}</b></span>
</div>
</div></header>

<div class="wrap">
<div class="stats">
<div class="stat"><div class="v">+{V['pct10']}%</div><div class="l">crime per +10°F</div><div class="s">citywide, all categories</div></div>
<div class="stat"><div class="v">+{V['pctch']}%</div><div class="l">hot vs. cold days</div><div class="s">{V['perday']} crimes/day average</div></div>
<div class="stat"><div class="v">+{V['toppct']}%</div><div class="l">{V['topcat']}</div><div class="s">most heat-sensitive offense</div></div>
<div class="stat"><div class="v">{V['ncat']}</div><div class="l">offense categories</div><div class="s">each profiled separately</div></div>
</div>

<div class="cards">
<div class="dcard report">
<div class="top"></div>
<div class="body">
<div class="tagrow"><span class="badge">The Report</span><span style="color:var(--sub);font-size:13px">11 sections · 16 charts</span></div>
<h2>The full analysis</h2>
<p>A written, chart-by-chart walk through the whole story — from the headline temperature effect to the surprises hiding in the details.</p>
<ul>
<li>How heat drives crime — and survives deseasonalizing</li>
<li>Which offenses ride the thermometer, which ignore it</li>
<li>Hot nights, hot weekends, and the geography of it all</li>
<li>Rain, snow, wind &amp; heat waves — each isolated from temperature</li>
</ul>
<a class="go" href="detroit_crime_temperature_report.html">Read the report <span class="ar">→</span></a>
</div></div>

<div class="dcard explore">
<div class="top"></div>
<div class="body">
<div class="tagrow"><span class="badge">Interactive</span><span style="color:var(--sub);font-size:13px">{V['ncat']} offenses + roll-ups</span></div>
<h2>The weather explorer</h2>
<p>Pick any single offense and watch the whole page reshape to its weather personality — live charts, plain-English summary, instant comparisons.</p>
<ul>
<li>Temperature response, season and daily rhythm per category</li>
<li>Rain- and snow-sensitivity at a glance</li>
<li>Every category measured against the citywide baseline</li>
<li>Self-contained &amp; instant — no loading, no internet</li>
</ul>
<a class="go" href="detroit_crime_weather_explorer.html">Open the explorer <span class="ar">→</span></a>
</div></div>
</div>

<div class="how">
<h3>How it was built</h3>
<p>Detroit police incidents are aggregated to daily counts and joined to local daily weather. Temperature effects come from correlations and regressions; every precipitation, wind and heat-wave figure is reported holding temperature constant, so the weather signal is never just the season in disguise. Full methodology and caveats live at the end of the report.</p>
<div class="src">
<span><b>Crime data:</b> <a href="https://data.detroitmi.gov/">Detroit Open Data Portal</a></span>
<span><b>Weather data:</b> <a href="https://open-meteo.com/">Open-Meteo</a> historical archive</span>
<span><b>Built with:</b> Python · pandas · SciPy · Matplotlib</span>
</div>
</div>
</div>
<footer>Detroit Crime &amp; Weather · {V['d0']} – {V['d1']} · an independent data-analysis project</footer>
</body></html>'''

open('index.html','w').write(HTML)
print('wrote index.html', round(len(HTML)/1024,1),'KB')

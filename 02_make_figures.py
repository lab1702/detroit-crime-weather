#!/usr/bin/env python3
"""
Step 2 — Render all 16 figures into figs/ from the step-1 datasets.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mc
from matplotlib.patches import Patch
from scipy import stats
from hac import poisson_hac, deseasonalize

os.makedirs('figs', exist_ok=True)
INK = '#1a1d29'; SUB = '#5b6577'; GRID = '#e6e9ef'; CARD = '#ffffff'
ACCENT = '#e0492f'; COOL = '#2c6fbb'; GREEN = '#3a7d44'
RAIN = '#2c8fbb'; SNOW = '#7d8ca8'; WIND = '#5b8a72'

BASE = {
 'figure.facecolor': CARD, 'axes.facecolor': CARD, 'savefig.facecolor': CARD,
 'font.family': 'DejaVu Sans', 'font.size': 11, 'text.color': INK,
 'axes.edgecolor': GRID, 'axes.labelcolor': SUB, 'axes.titlecolor': INK,
 'xtick.color': SUB, 'ytick.color': SUB, 'axes.grid': True, 'grid.color': GRID,
 'axes.spines.top': False, 'axes.spines.right': False,
 'xtick.bottom': False, 'ytick.left': False, 'figure.dpi': 130}
plt.rcParams.update(BASE)


def tcol(t):
    cm = mc.LinearSegmentedColormap.from_list('t',
        ['#2c6fbb', '#7fb0d8', '#d8d8d8', '#e8a35a', '#e0492f'])
    return cm(np.clip(t, 0, 90) / 90)


# load shared data
m = pd.read_csv('daily_merged.csv', parse_dates=['date']).set_index('date')
master = pd.read_csv('daily_master.csv', parse_dates=[0], index_col=0)
temp = m['temperature_2m_mean']; tot = m['total_crimes']

# ---- FIG 1 : scatter
fig, ax = plt.subplots(figsize=(9, 5.2))
ax.scatter(temp, tot, s=9, c=[tcol(t) for t in temp], alpha=0.45, edgecolors='none')
b, a = np.polyfit(temp, tot, 1); xs = np.linspace(temp.min(), temp.max(), 100)
ax.plot(xs, a + b * xs, color=INK, lw=2.4, label=f'Trend: +{b:.1f} crimes per °F')
r, _ = stats.pearsonr(temp, tot)
ax.set_xlabel('Daily mean temperature (°F)'); ax.set_ylabel('Reported crimes per day')
ax.set_title('Daily crime rises with temperature in Detroit', fontsize=15, fontweight='bold', pad=12)
ax.text(0.02, 0.96, f'Pearson r = {r:.2f}   •   n = {len(temp):,} days (2017–2026)',
        transform=ax.transAxes, va='top', color=SUB, fontsize=10.5)
ax.legend(loc='lower right', frameon=False, fontsize=10.5)
plt.tight_layout(); plt.savefig('figs/fig1_scatter.png', bbox_inches='tight'); plt.close()

# ---- FIG 2 : temperature bins
bs = pd.read_csv('bin_stats.csv')
fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.bar(bs['tbin'], bs['mean_total'], color=[tcol(t) for t in bs['mean_temp']],
              width=0.72, edgecolor='white')
for bar, v, d in zip(bars, bs['mean_total'], bs['days']):
    ax.text(bar.get_x() + bar.get_width() / 2, v + 2, f'{v:.0f}', ha='center', va='bottom',
            fontweight='bold', color=INK, fontsize=11)
    ax.text(bar.get_x() + bar.get_width() / 2, 8, f'{d} days', ha='center', va='bottom',
            color='white', fontsize=8.5)
base, topv = bs['mean_total'].iloc[0], bs['mean_total'].iloc[-1]
ax.set_ylabel('Average crimes per day'); ax.set_xlabel('Daily mean temperature')
ax.set_title(f'Hot days see {(topv/base-1)*100:.0f}% more crime than the coldest days',
             fontsize=15, fontweight='bold', pad=12); ax.set_ylim(0, 290)
plt.tight_layout(); plt.savefig('figs/fig2_bins.png', bbox_inches='tight'); plt.close()

# ---- FIG 3 : per-category sensitivity
cs = pd.read_csv('category_stats.csv')
cs = cs[cs.category != 'total_crimes'].sort_values('pct_per_10F')
def fam_color(c):
    viol = {'AGGRAVATED ASSAULT','ASSAULT','WEAPONS OFFENSES','ROBBERY','HOMICIDE',
            'SEX OFFENSES','SEXUAL ASSAULT','ARSON','DISORDERLY CONDUCT','OBSTRUCTING THE POLICE'}
    prop = {'DAMAGE TO PROPERTY','LARCENY','STOLEN VEHICLE','BURGLARY','STOLEN PROPERTY'}
    return ACCENT if c in viol else ('#3a7d44' if c in prop else '#9aa3b2')
# The bars are the RAW per-10°F slope, but the significance encoding reflects the
# within-season test (anom_p_fdr): a category is shown full-strength only if its
# heat effect survives deseasonalizing. Three tiers — within-season significant
# (solid), detectable on the raw slope but seasonal-only (faded, "seasonal"), and
# not significant at all (faded, "n.s.") — so the chart cannot over-read a slope
# that is really just the calendar.
sig = cs['p_fdr'] < 0.05            # raw temperature slope clears FDR
within = cs['anom_p_fdr'] < 0.05    # effect persists within season
colors = [mc.to_rgba(fam_color(c), 1 if w else 0.32) for c, w in zip(cs.category, within)]
fig, ax = plt.subplots(figsize=(9.5, 8))
ax.barh(cs.category, cs.pct_per_10F, color=colors, edgecolor='white')
for y, (v, s, w) in enumerate(zip(cs.pct_per_10F, sig, within)):
    tag = '' if w else ('  seasonal' if s else '  n.s.')
    ax.text(v + 0.12, y, f'{v:+.1f}%' + tag, va='center',
            fontsize=9, color=INK if w else SUB)
ax.set_xlabel('Change in daily incidents per +10°F  (% of category average)')
ax.set_title('Which crimes are most temperature-sensitive?', fontsize=15, fontweight='bold', pad=12)
ax.axvline(0, color=SUB, lw=1); ax.set_xlim(min(0, cs.pct_per_10F.min() - 0.8), 11.5)
ax.legend(handles=[Patch(color=ACCENT, label='Violent / interpersonal'),
    Patch(color='#3a7d44', label='Property'), Patch(color='#9aa3b2', label='Other / administrative')],
    loc='lower right', frameon=False, fontsize=10)
plt.tight_layout(); plt.savefig('figs/fig3_sensitivity.png', bbox_inches='tight'); plt.close()

# ---- FIG 4 : monthly dual axis
mo = pd.read_csv('month_stats.csv'); names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
fig, ax = plt.subplots(figsize=(9.5, 5))
ax.bar(names, mo.mean_total, color='#c9d6e8', width=0.62, zorder=2)
ax.set_ylabel('Average crimes per day', color=SUB); ax.set_ylim(0, 290)
ax2 = ax.twinx(); ax2.grid(False)
ax2.plot(names, mo.mean_temp, color=ACCENT, lw=2.8, marker='o', ms=6, zorder=3)
ax2.set_ylabel('Average temperature (°F)', color=ACCENT); ax2.set_ylim(0, 90)
ax2.spines['top'].set_visible(False)
ax.set_title('Crime and temperature move together through the year', fontsize=15, fontweight='bold', pad=12)
ax.set_zorder(1); ax.patch.set_visible(False)
plt.tight_layout(); plt.savefig('figs/fig4_monthly.png', bbox_inches='tight'); plt.close()

# ---- FIG 5 : heatmap
hn = pd.read_csv('heat_norm.csv', index_col=0)
order = ['<20°F','20–32°F','32–45°F','45–60°F','60–75°F','75°F+']; hn = hn[order]
hn = hn.reindex((hn['75°F+'] / hn['<20°F']).sort_values(ascending=False).index)
fig, ax = plt.subplots(figsize=(9.5, 7))
cmap = mc.LinearSegmentedColormap.from_list('d', ['#2c6fbb', '#eef2f7', '#e0492f'])
im = ax.imshow(hn.values, cmap=cmap, vmin=0.6, vmax=1.4, aspect='auto')
ax.set_xticks(range(len(order))); ax.set_xticklabels(order)
ax.set_yticks(range(len(hn))); ax.set_yticklabels([c.title() for c in hn.index])
for i in range(hn.shape[0]):
    for j in range(hn.shape[1]):
        v = hn.values[i, j]
        ax.text(j, i, f'{v:.2f}', ha='center', va='center', fontsize=8.5,
                color='white' if (v < 0.78 or v > 1.22) else INK)
ax.set_title('Crime rate relative to category average, by temperature', fontsize=14, fontweight='bold', pad=12)
ax.grid(False)
cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
cb.set_label('Rate vs. average  (1.00 = typical day)', fontsize=9); cb.outline.set_visible(False)
plt.tight_layout(); plt.savefig('figs/fig5_heatmap.png', bbox_inches='tight'); plt.close()

# ---- FIG 6 : anomaly (smooth, leap-year-safe harmonic deseasonalization)
ta, ca = deseasonalize(temp), deseasonalize(tot)
fig, ax = plt.subplots(figsize=(9, 5.2))
ax.scatter(ta, ca, s=8, c='#2c6fbb', alpha=0.28, edgecolors='none')
b, a = np.polyfit(ta, ca, 1); xs = np.linspace(ta.min(), ta.max(), 100)
ax.plot(xs, a + b * xs, color=ACCENT, lw=2.6)
r, _ = stats.pearsonr(ta, ca)
ax.axhline(0, color=SUB, lw=0.8); ax.axvline(0, color=SUB, lw=0.8)
ax.set_xlabel('Temperature anomaly (°F vs. the smooth seasonal normal)')
ax.set_ylabel('Crime anomaly (vs. seasonal normal)')
ax.set_title('Even within a season, warmer-than-normal days bring more crime', fontsize=14, fontweight='bold', pad=12)
ax.text(0.02, 0.96, f'Deseasonalized r = {r:.2f}   •   +{b:.1f} crimes per °F above normal',
        transform=ax.transAxes, va='top', color=SUB, fontsize=10.5)
plt.tight_layout(); plt.savefig('figs/fig6_anomaly.png', bbox_inches='tight'); plt.close()

# ---- FIG 7 : hot nights
prof = pd.read_csv('tod_violent_profile.csv', index_col=0).sort_index(); hrs = prof.index
fig, ax = plt.subplots(figsize=(9.5, 5.2))
ax.axvspan(20, 24, color='#f0f3f8', zorder=0); ax.axvspan(-0.5, 3, color='#f0f3f8', zorder=0)
ax.plot(hrs, prof['hot_perday'], color=ACCENT, lw=2.8, marker='o', ms=4, label='Hot days (warmest third)')
ax.plot(hrs, prof['cold_perday'], color=COOL, lw=2.8, marker='o', ms=4, label='Cold days (coldest third)')
ax.fill_between(hrs, prof['cold_perday'], prof['hot_perday'], color=ACCENT, alpha=0.08)
ax.set_xticks(range(0, 24, 3)); ax.set_xticklabels(['12a','3a','6a','9a','12p','3p','6p','9p'])
ax.set_xlim(-0.5, 23.5); ax.set_xlabel('Hour of day (local)')
ax.set_ylabel('Violent incidents per day, per hour')
ax.set_title('Heat hits hardest after dark', fontsize=15, fontweight='bold', pad=12)
ax.text(0.5, 0.93, 'Shaded = night (8 pm–3 am)', transform=ax.transAxes, color=SUB, fontsize=9.5, ha='center')
ax.legend(loc='upper left', frameon=False, fontsize=10.5)
plt.tight_layout(); plt.savefig('figs/fig7_hotnights.png', bbox_inches='tight'); plt.close()

# ---- FIG 8 : weekend violent bins
vp = pd.read_csv('weekend_violent_bins.csv', index_col=0); x = np.arange(len(vp))
fig, ax = plt.subplots(figsize=(9.5, 5))
ax.plot(x, vp['Weekend'], color=ACCENT, lw=2.8, marker='o', ms=7, label='Weekend')
ax.plot(x, vp['Weekday'], color='#6b7689', lw=2.8, marker='o', ms=7, label='Weekday')
for i in x:
    ax.annotate(f"+{vp['Weekend'].iloc[i]-vp['Weekday'].iloc[i]:.0f}", (i, vp['Weekend'].iloc[i]),
        textcoords='offset points', xytext=(0, 9), ha='center', fontsize=9, color=ACCENT, fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels([f'{l}°F' for l in vp.index])
ax.set_xlabel('Daily mean temperature'); ax.set_ylabel('Violent incidents per day')
ax.set_title('Hot weekends are Detroit’s most violent days', fontsize=15, fontweight='bold', pad=12)
ax.legend(loc='upper left', frameon=False, fontsize=10.5); ax.set_ylim(55, 130)
ax.text(0.99, 0.04, 'Labels = weekend premium over weekday', transform=ax.transAxes,
        color=SUB, fontsize=9, ha='right')
plt.tight_layout(); plt.savefig('figs/fig8_weekend.png', bbox_inches='tight'); plt.close()

# ---- FIG 9 & 10 : maps
# incident_points.csv holds bbox-filtered coordinates written by 01_build_datasets.py
g = pd.read_csv('incident_points.csv')
fig, ax = plt.subplots(figsize=(8.6, 7.4)); ax.set_facecolor('#0f1320')
cmap = mc.LinearSegmentedColormap.from_list('h',
    ['#0f1320','#27305a','#3f5fa0','#5b97c9','#8fd0c0','#e8e06a','#f2a93b','#e0492f'])
hb = ax.hexbin(g['longitude'], g['latitude'], gridsize=78, cmap=cmap, bins='log', mincnt=1, linewidths=0.2)
ax.set_aspect(1 / np.cos(np.radians(42.35))); ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values(): s.set_visible(False)
ax.set_title('Where Detroit crime concentrates', fontsize=15, fontweight='bold', pad=10)
ax.text(0.5, -0.045, '791k incidents, 2017–2026 · brighter = denser (log scale)',
        transform=ax.transAxes, ha='center', color=SUB, fontsize=10)
cb = fig.colorbar(hb, ax=ax, fraction=0.04, pad=0.02); cb.set_label('incidents (log)', fontsize=9); cb.outline.set_visible(False)
plt.tight_layout(); plt.savefig('figs/fig9_map.png', bbox_inches='tight'); plt.close()

nb = pd.read_csv('neighborhood_stats.csv')
fig, ax = plt.subplots(figsize=(8.6, 7.4)); ax.set_facecolor('#f7f8fb')
norm = mc.Normalize(vmin=2, vmax=10)
cmap2 = mc.LinearSegmentedColormap.from_list('s', ['#2c6fbb', '#cfd8e6', '#e8a35a', '#e0492f'])
sizes = (nb['per_day'] / nb['per_day'].max() * 900) + 30
sc = ax.scatter(nb['lon'], nb['lat'], s=sizes, c=nb['pct10'], cmap=cmap2, norm=norm,
                alpha=0.85, edgecolors='white', linewidths=1.1)
offs = {'Downtown': (8,-12),'Greektown': (8,6),'Rivertown': (10,-2),'Riverbend': (8,4),
        'Grixdale Farms': (8,5),'Warrendale': (-4,-14),'Midtown': (-10,10)}
lab = pd.concat([nb.sort_values('pct10', ascending=False).head(4),
                 nb.sort_values('per_day', ascending=False).head(3)]).drop_duplicates('neighborhood')
for _, r in lab.iterrows():
    ox, oy = offs.get(r['neighborhood'], (5, 5))
    ax.annotate(r['neighborhood'], (r['lon'], r['lat']), fontsize=8.5, fontweight='bold',
                color=INK, xytext=(ox, oy), textcoords='offset points')
ax.set_aspect(1 / np.cos(np.radians(42.35))); ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values(): s.set_color(GRID)
ax.set_title('Which neighborhoods heat up most', fontsize=15, fontweight='bold', pad=10)
ax.text(0.5, -0.045, 'Bubble size = crime volume · color = temperature sensitivity (%/+10°F)',
        transform=ax.transAxes, ha='center', color=SUB, fontsize=10)
cb = fig.colorbar(sc, ax=ax, fraction=0.04, pad=0.02); cb.set_label('% more crime per +10°F', fontsize=9); cb.outline.set_visible(False)
plt.tight_layout(); plt.savefig('figs/fig10_nbmap.png', bbox_inches='tight'); plt.close()

# ---- FIG 11 : wet-day effect by family (labels inside bars)
mp = pd.read_csv('daily_precip_merged.csv', parse_dates=[0], index_col=0)
T = mp['temperature_2m_mean'].values; wet = (mp['precipitation_sum'] >= 0.01).astype(float).values
DOW = mp.index.dayofweek   # day-of-week nuisance controls, matching step 1
labels = ['Violent', 'Property', 'Other / admin', 'All crime']; cols = [ACCENT, GREEN, '#9aa3b2', INK]
pcts, ps = [], []
for f in ['Violent', 'Property', 'Other', 'total']:
    y = mp[f].values; b, p = poisson_hac(y, [T, wet], dow=DOW); pcts.append((np.exp(b[2]) - 1) * 100); ps.append(p[2])
fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.bar(labels, pcts, color=cols, width=0.6, edgecolor='white')
for bar, v, p in zip(bars, pcts, ps):
    s = '' if p < 0.05 else ' n.s.'
    if v < -0.8:
        ax.text(bar.get_x() + bar.get_width() / 2, v / 2, f'{v:+.1f}%{s}', ha='center',
                va='center', color='white', fontweight='bold', fontsize=11)
    else:
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.12, f'{v:+.1f}%{s}', ha='center',
                va='bottom', color=SUB, fontweight='bold', fontsize=11)
ax.axhline(0, color=SUB, lw=1)
ax.set_ylabel('Change in crime on wet days\n(holding temperature constant)')
ax.set_title('Rain dampens violence most — and paperwork not at all', fontsize=15, fontweight='bold', pad=12)
ax.set_ylim(-6.2, 1.4)
plt.tight_layout(); plt.savefig('figs/fig11_wet_effect.png', bbox_inches='tight'); plt.close()

# ---- FIG 12 : stratified dry/wet violent
st = pd.read_csv('precip_strat_violent.csv', index_col=0); x = np.arange(len(st)); w = 0.38
fig, ax = plt.subplots(figsize=(9, 5))
ax.bar(x - w/2, st['Dry'], w, color='#d7b15a', label='Dry day', edgecolor='white')
ax.bar(x + w/2, st['Wet'], w, color=RAIN, label='Wet day', edgecolor='white')
for i in x:
    d, we = st['Dry'].iloc[i], st['Wet'].iloc[i]
    ax.text(i + w/2, we + 0.6, f'{(we/d-1)*100:+.0f}%', ha='center', fontsize=9, color=RAIN, fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels(st.index)
ax.set_ylabel('Violent incidents per day'); ax.set_xlabel('Daily mean temperature')
ax.set_title('Within every temperature band, wet days are calmer', fontsize=15, fontweight='bold', pad=12)
ax.legend(frameon=False, fontsize=10.5, loc='upper left'); ax.set_ylim(0, 125)
plt.tight_layout(); plt.savefig('figs/fig12_strat.png', bbox_inches='tight'); plt.close()

# ---- FIG 13 : rain vs snow
R = mp['rain_sum'].values; S = mp['snowfall_sum'].values
eff = {'rain': [], 'snow': []}; sg = {'rain': [], 'snow': []}
for f in ['Violent', 'Property']:
    y = mp[f].values; b, p = poisson_hac(y, [T, R, S], dow=DOW); ym = y.mean()
    # log-link coefficient -> incidents/day per +1 inch, evaluated at the mean rate
    eff['rain'].append(ym * (np.exp(b[2]) - 1)); sg['rain'].append(p[2])
    eff['snow'].append(ym * (np.exp(b[3]) - 1)); sg['snow'].append(p[3])
x = np.arange(2); w = 0.38
fig, ax = plt.subplots(figsize=(9, 5))
b1 = ax.bar(x - w/2, eff['rain'], w, color=RAIN, label='Per +1 in. rain', edgecolor='white')
b2 = ax.bar(x + w/2, eff['snow'], w, color=SNOW, label='Per +1 in. snow', edgecolor='white')
for bars, key in [(b1, 'rain'), (b2, 'snow')]:
    for bar, v, p in zip(bars, eff[key], sg[key]):
        s = '' if p < 0.05 else ' n.s.'
        ax.text(bar.get_x() + bar.get_width() / 2, v - 0.3, f'{v:.1f}{s}', ha='center',
                va='top', color='white', fontweight='bold', fontsize=10)
ax.axhline(0, color=SUB, lw=1); ax.set_xticks(x); ax.set_xticklabels(['Violent crime', 'Property crime'])
ax.set_ylabel('Change in incidents/day per inch\n(holding temperature constant)')
ax.set_title('Rain quiets violence; snow blunts theft', fontsize=15, fontweight='bold', pad=12)
ax.legend(frameon=False, fontsize=10.5, loc='lower right'); ax.set_ylim(-12.5, 1)
plt.tight_layout(); plt.savefig('figs/fig13_rainsnow.png', bbox_inches='tight'); plt.close()

# ---- FIG 14 : heat-wave streak position
master['tmax'] = master['temperature_2m_max']
hot = (master['tmax'] >= 85).astype(int); grp = (hot.diff() != 0).cumsum()
pos = np.zeros(len(master), int)
for gp, v in hot.groupby(grp):
    if v.iloc[0] == 1:
        for i, idx in enumerate(v.index): pos[master.index.get_loc(idx)] = i + 1
master['pos'] = pos
cool = master[(master.tmax < 85) & (master.tmax >= 70)]
groups = [cool['Violent'], master[master.pos == 1]['Violent'],
          master[master.pos == 2]['Violent'], master[master.pos >= 3]['Violent']]
tmaxg = [cool['tmax'].mean(), master[master.pos == 1]['tmax'].mean(),
         master[master.pos == 2]['tmax'].mean(), master[master.pos >= 3]['tmax'].mean()]
means = [grp_.mean() for grp_ in groups]; x = np.arange(4)
fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.bar(x, means, color=['#c9d6e8', ACCENT, ACCENT, ACCENT], width=0.62, edgecolor='white')
for b, v in zip(bars, means): ax.text(b.get_x() + b.get_width()/2, v + 0.8, f'{v:.0f}', ha='center', fontweight='bold', fontsize=11)
ax2 = ax.twinx(); ax2.grid(False); ax2.plot(x, tmaxg, color='#9a4a1a', lw=2.4, marker='o', ms=6, zorder=5)
ax2.set_ylabel('Avg daily high (°F)', color='#9a4a1a'); ax2.set_ylim(60, 100); ax2.spines['top'].set_visible(False)
ax.set_xticks(x); ax.set_xticklabels(['Cooler\nday', 'Heat-wave\nDay 1', 'Day 2', 'Day 3+'])
ax.set_ylabel('Violent incidents per day'); ax.set_ylim(0, 125)
ax.set_title('A heat wave is no worse than its hottest day', fontsize=15, fontweight='bold', pad=12)
ax.text(0.5, 0.93, 'Crime tracks each day’s heat — it does not pile up over a multi-day wave',
        transform=ax.transAxes, ha='center', color=SUB, fontsize=10)
ax.set_zorder(1); ax.patch.set_visible(False)
plt.tight_layout(); plt.savefig('figs/fig14_heatwave.png', bbox_inches='tight'); plt.close()

# ---- FIG 15 : wind (labels inside bars)
Tm = master['temperature_2m_mean'].values; Pr = master['precipitation_sum'].values; Wd = master['wind_speed_10m_max'].values
DOWm = master.index.dayofweek   # day-of-week nuisance controls
eff2, sg2 = [], []
for f in ['Violent', 'Property']:
    y = master[f].values; b, p = poisson_hac(y, [Tm, Pr, Wd], dow=DOWm)
    eff2.append(y.mean() * (np.exp(b[3] * 10) - 1)); sg2.append(p[3])   # incidents/day per +10 mph at the mean
fig, ax = plt.subplots(figsize=(8.4, 5))
bars = ax.bar(['Violent crime', 'Property crime'], eff2, color=[ACCENT, GREEN], width=0.5, edgecolor='white')
for b, v, p in zip(bars, eff2, sg2):
    s = '' if p < 0.05 else ' n.s.'
    if v < -0.5:
        ax.text(b.get_x() + b.get_width()/2, v/2, f'{v:+.1f}{s}', ha='center', va='center', color='white', fontweight='bold', fontsize=11)
    else:
        ax.text(b.get_x() + b.get_width()/2, 0.05, f'{v:+.1f}{s}', ha='center', va='bottom', color=SUB, fontweight='bold', fontsize=11)
ax.axhline(0, color=SUB, lw=1)
ax.set_ylabel('Change in incidents/day per +10 mph wind\n(holding temperature & rain constant)')
ax.set_title('Windy days quiet violence — but not theft', fontsize=15, fontweight='bold', pad=12); ax.set_ylim(-3.4, 0.7)
plt.tight_layout(); plt.savefig('figs/fig15_wind.png', bbox_inches='tight'); plt.close()

# ---- FIG 16 : unifying  (log-link % effects: (exp(beta)-1)*100)
y = master['Violent'].values
heat = (np.exp(poisson_hac(y, [Tm], dow=DOWm)[0][1] * 10) - 1) * 100
wet_ = (master['precipitation_sum'] >= 0.01).astype(float).values
weteff = (np.exp(poisson_hac(y, [Tm, wet_], dow=DOWm)[0][2]) - 1) * 100
wthr = np.quantile(Wd, 0.9); hiwind = (Wd >= wthr).astype(float)
windeff = (np.exp(poisson_hac(y, [Tm, hiwind], dow=DOWm)[0][2]) - 1) * 100
storm = ((master['precipitation_sum'] > 0.5) | (master['wind_speed_10m_max'] >= wthr)).astype(float).values
stormeff = (np.exp(poisson_hac(y, [Tm, storm], dow=DOWm)[0][2]) - 1) * 100
vals = [heat, weteff, windeff, stormeff]
fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.bar(['+10°F\nwarmer', 'Wet\nday', 'Windy\nday', 'Storm\nday'], vals,
              color=[ACCENT, RAIN, WIND, '#41607a'], width=0.6, edgecolor='white')
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width()/2, v + (0.25 if v > 0 else -0.25), f'{v:+.1f}%',
            ha='center', va='bottom' if v > 0 else 'top', fontweight='bold', color=INK)
ax.axhline(0, color=SUB, lw=1.2); ax.set_ylabel('Change in violent crime (%)')
ax.set_title('It’s about who’s outside: heat draws people out, bad weather keeps them in',
             fontsize=13.5, fontweight='bold', pad=12); ax.set_ylim(-9, 11)
plt.tight_layout(); plt.savefig('figs/fig16_unify.png', bbox_inches='tight'); plt.close()

print("Wrote 16 figures to figs/. Next: build the HTML pages.")

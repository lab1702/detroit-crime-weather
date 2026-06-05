#!/usr/bin/env python3
"""Build the self-contained interactive category weather explorer."""
import json

data = json.load(open('profile_data.json'))
DATA_JS = json.dumps(data, separators=(',',':'))
meta = data['meta']

HTML = '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Detroit Crime · Weather Explorer</title>
<style>
:root{--ink:#1a1d29;--sub:#5b6577;--line:#e6e9ef;--bg:#f6f7fb;--card:#fff;
--accent:#e0492f;--cool:#2c6fbb;--green:#3a7d44;--soft:#fbfcfe;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:1000px;margin:0 auto;padding:0 22px 80px}
header{background:linear-gradient(135deg,#1a1d29 0%,#2a3350 55%,#3a4a6b 100%);color:#fff;padding:52px 0 44px}
.kicker{text-transform:uppercase;letter-spacing:.18em;font-size:12.5px;font-weight:600;color:#9db3d8;margin:0 0 12px}
h1{font-size:34px;line-height:1.12;margin:0 0 12px;font-weight:800;letter-spacing:-.02em}
header p{font-size:17px;color:#c8d2e6;max-width:680px;margin:0}
.meta{margin-top:20px;font-size:13px;color:#90a0c0;display:flex;flex-wrap:wrap;gap:6px 20px}
.meta b{color:#c8d2e6;font-weight:600}
.cta{display:inline-flex;align-items:center;gap:13px;margin-top:24px;text-decoration:none;
background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.22);border-radius:13px;
padding:13px 20px;color:#fff;transition:all .15s}
.cta:hover{background:rgba(255,255,255,.18);border-color:rgba(255,255,255,.4);transform:translateY(-1px)}
.cta-ic{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;
border-radius:9px;background:var(--cool);font-size:16px;flex:none}
.cta b{font-size:15px} .cta-sub{font-size:12.5px;color:#b9c6e0}
.homelink{display:inline-block;margin-bottom:18px;color:#9db3d8;text-decoration:none;font-size:13.5px;
font-weight:600;border:1px solid rgba(255,255,255,.18);border-radius:20px;padding:5px 14px;transition:all .14s}
.homelink:hover{color:#fff;border-color:rgba(255,255,255,.4);background:rgba(255,255,255,.08)}
.picker{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px 22px;
margin:26px 0 22px;box-shadow:0 4px 18px rgba(26,29,41,.05)}
.picker h3{margin:0 0 4px;font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--sub)}
.grp{margin-top:12px}
.glabel{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--sub);margin:0 0 7px}
.chips{display:flex;flex-wrap:wrap;gap:7px}
.chip{border:1px solid var(--line);background:#fff;color:var(--ink);border-radius:20px;
padding:6px 14px;font-size:13px;font-weight:600;cursor:pointer;transition:all .12s;user-select:none}
.chip:hover{border-color:#b9c2d4;background:#f3f5fa}
.chip.on{color:#fff;border-color:transparent}
.chip.on.v{background:var(--accent)} .chip.on.p{background:var(--green)}
.chip.on.o{background:#6b7689} .chip.on.a{background:var(--ink)}
.dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:6px;vertical-align:middle}
.dot.v{background:var(--accent)} .dot.p{background:var(--green)} .dot.o{background:#9aa3b2} .dot.a{background:var(--ink)}
.lead{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:0 14px 14px 0;
padding:20px 24px;margin:0 0 22px;font-size:17px;box-shadow:0 4px 18px rgba(26,29,41,.04)}
.lead .nm{font-weight:800;font-size:21px;letter-spacing:-.01em}
.lead .tag{font-size:11px;font-weight:700;padding:2px 10px;border-radius:20px;margin-left:8px;vertical-align:middle}
.tag.v{background:#fde6e1;color:#b8341d} .tag.p{background:#e3f0e6;color:#2c6135}
.tag.o{background:#eceef2;color:#5b6577} .tag.a{background:#e7eaf1;color:#3a4a6b}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:22px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:15px 16px;box-shadow:0 3px 14px rgba(26,29,41,.04)}
.stat .v{font-size:23px;font-weight:800;letter-spacing:-.02em}
.stat .l{font-size:12px;font-weight:600;margin-top:3px;color:var(--ink)}
.stat .s{font-size:11.5px;color:var(--sub);margin-top:2px}
.pos{color:var(--accent)} .neg{color:var(--cool)} .neu{color:var(--sub)}
.charts{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.panel{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px 14px;box-shadow:0 3px 14px rgba(26,29,41,.04)}
.panel.full{grid-column:1/-1}
.panel h4{margin:0 0 2px;font-size:15px;font-weight:700}
.panel .sub{font-size:12.5px;color:var(--sub);margin:0 0 6px}
svg{width:100%;height:auto;display:block;overflow:visible}
.legend{font-size:11.5px;color:var(--sub);display:flex;gap:16px;margin-top:6px;flex-wrap:wrap}
.legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:middle}
footer{text-align:center;color:var(--sub);font-size:13px;margin-top:30px}
.note{font-size:11.5px;color:#94a0b2;margin-top:6px;font-style:italic}
@media(max-width:760px){.stats{grid-template-columns:repeat(2,1fr)}.charts{grid-template-columns:1fr}h1{font-size:27px}}
</style></head><body>
<header><div class="wrap">
<a class="homelink" href="index.html">&#8962; Overview</a>
<p class="kicker">Interactive · Detroit Crime &amp; Weather</p>
<h1>The Weather Profile of Detroit Crime</h1>
<p>Pick any offense category to see how heat, rain, snow, season and the clock shape it. Every figure is built from __NDAYS__ days of incidents, __D0__ to __D1__.</p>
<div class="meta"><span><b>Crime:</b> Detroit Open Data Portal</span><span><b>Weather:</b> Open-Meteo archive</span><span><b>Categories:</b> 23 offenses + 4 roll-ups</span></div>
<a class="cta" href="detroit_crime_temperature_report.html">
<span class="cta-ic">&#8592;</span><span><b>Back to the full report</b><br><span class="cta-sub">The narrative analysis — 11 sections, 16 charts</span></span></a>
</div></header>
<div class="wrap">
<div class="picker">
<h3>Choose a category</h3>
<div id="groups"></div>
</div>
<div class="lead" id="lead"></div>
<div class="stats" id="statcards"></div>
<div class="charts">
<div class="panel"><h4>Temperature response</h4><p class="sub">Crime rate vs. the citywide average (1.0×), by daily temperature</p><div id="tempchart"></div>
<div class="legend"><span><i style="background:#9aa3b2"></i>All crime</span><span id="tcleg"></span></div></div>
<div class="panel"><h4>Through the year</h4><p class="sub">Each month vs. this category's own average (100 = typical)</p><div id="monthchart"></div>
<div class="legend"><span><i style="background:#9aa3b2"></i>All crime</span><span id="mleg"></span></div></div>
<div class="panel full"><h4>The daily rhythm</h4><p class="sub">Share of this category's incidents by hour of day</p><div id="hourchart"></div>
<div class="legend"><span><i style="background:#9aa3b2"></i>All crime</span><span id="hleg"></span></div>
<p class="note">Note: midnight and noon are inflated by reports filed with an unknown exact time; the "busiest hour" stat above ignores both.</p></div>
</div>
</div>
<footer>Detroit Open Data Portal &amp; Open-Meteo · Temperature-controlled effects via Poisson regression (log link, HAC-robust) · Companion to the full Detroit crime &amp; temperature report</footer>
<script>
const DATA = __DATA__;
const ITEMS = DATA.items, TB = DATA.meta.tbins;
const ALL = ITEMS["__ALL__"];
const FAMCLASS = {Violent:'v',Property:'p',Other:'o',All:'a'};
const MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function hourLabel(h){const ap=h<12?'AM':'PM';let x=h%12;if(x===0)x=12;return x+' '+ap;}
function tempColor(i,n){ // blue->red across bins
  const t=i/(n-1); const stops=[[44,111,187],[127,176,216],[216,216,216],[232,163,90],[224,73,47]];
  const p=t*(stops.length-1); const a=Math.floor(p), b=Math.min(a+1,stops.length-1), f=p-a;
  const c=stops[a].map((v,k)=>Math.round(v+(stops[b][k]-v)*f)); return `rgb(${c[0]},${c[1]},${c[2]})`;}

// ---- SVG helpers ----
const NS='http://www.w3.org/2000/svg';
function el(t,a){const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);return e;}
function svgBase(W,H){const s=el('svg',{viewBox:`0 0 ${W} ${H}`,'font-family':'inherit'});return s;}

function barChart(host, values, refValues, labels){
  host.innerHTML='';
  const W=460,H=230,L=34,R=10,Tp=14,B=34;
  const s=svgBase(W,H); const max=Math.max(1.05,...values,...refValues)*1.08;
  const ph=H-Tp-B, pw=W-L-R;
  // baseline at 1.0
  const y1=Tp+ph-(1/max)*ph;
  s.appendChild(el('line',{x1:L,x2:W-R,y1:y1,y2:y1,stroke:'#c7cedb','stroke-dasharray':'4 4','stroke-width':1}));
  s.appendChild(el('text',{x:W-R,y:y1-4,'text-anchor':'end','font-size':10,fill:'#94a0b2'})).textContent='citywide avg';
  // y ticks
  for(let g=0;g<=Math.ceil(max);g+=(max>2?1:0.5)){const yy=Tp+ph-(g/max)*ph;
    s.appendChild(el('text',{x:L-6,y:yy+3,'text-anchor':'end','font-size':9.5,fill:'#94a0b2'})).textContent=g.toFixed(max>2?0:1)+'×';}
  const n=values.length, bw=pw/n*0.62, gap=pw/n;
  values.forEach((v,i)=>{
    const x=L+gap*i+(gap-bw)/2, h=(v/max)*ph, y=Tp+ph-h;
    s.appendChild(el('rect',{x:x,y:y,width:bw,height:h,rx:3,fill:tempColor(i,n)}));
    s.appendChild(el('text',{x:x+bw/2,y:y-4,'text-anchor':'middle','font-size':10.5,'font-weight':700,fill:'#1a1d29'})).textContent=v.toFixed(2);
    // ref marker (all crime)
    const ry=Tp+ph-(refValues[i]/max)*ph;
    s.appendChild(el('line',{x1:x-2,x2:x+bw+2,y1:ry,y2:ry,stroke:'#9aa3b2','stroke-width':2}));
    s.appendChild(el('text',{x:L+gap*i+gap/2,y:H-12,'text-anchor':'middle','font-size':10,fill:'#5b6577'})).textContent=labels[i];
  });
  s.appendChild(el('text',{x:(L+W-R)/2,y:H-1,'text-anchor':'middle','font-size':9.5,fill:'#94a0b2'})).textContent='daily mean temperature (°F)';
  host.appendChild(s);
}

function lineChart(host, series, refSeries, labels, color, opts){
  opts=opts||{}; host.innerHTML='';
  const W=opts.wide?940:460, H=opts.wide?250:230, L=34,R=12,Tp=14,B=30;
  const s=svgBase(W,H); const all=series.concat(refSeries);
  let lo=Math.min(...all), hi=Math.max(...all); const pad=(hi-lo)*0.15||1; lo-=pad; hi+=pad;
  if(opts.fromZero){lo=Math.min(lo,0);}
  const ph=H-Tp-B, pw=W-L-R, n=series.length;
  const X=i=>L+pw*i/(n-1), Y=v=>Tp+ph-(v-lo)/(hi-lo)*ph;
  // baseline (100 for monthly index)
  if(opts.base!=null){const yb=Y(opts.base);s.appendChild(el('line',{x1:L,x2:W-R,y1:yb,y2:yb,stroke:'#dfe3ea','stroke-width':1}));}
  // gridline labels
  const ticks=opts.yticks||[lo+(hi-lo)*0.2,opts.base!=null?opts.base:(lo+hi)/2,hi-(hi-lo)*0.1];
  // ref line
  const refPath=refSeries.map((v,i)=>(i?'L':'M')+X(i)+' '+Y(v)).join(' ');
  s.appendChild(el('path',{d:refPath,fill:'none',stroke:'#9aa3b2','stroke-width':1.6,'stroke-dasharray':'5 4'}));
  // area + line
  const path=series.map((v,i)=>(i?'L':'M')+X(i)+' '+Y(v)).join(' ');
  if(opts.area){const ap=path+` L ${X(n-1)} ${Tp+ph} L ${X(0)} ${Tp+ph} Z`;
    s.appendChild(el('path',{d:ap,fill:color,'fill-opacity':0.10}));}
  s.appendChild(el('path',{d:path,fill:'none',stroke:color,'stroke-width':2.6,'stroke-linejoin':'round'}));
  series.forEach((v,i)=>{ if(!opts.wide || i%2===0) s.appendChild(el('circle',{cx:X(i),cy:Y(v),r:opts.wide?2.6:3.2,fill:color})); });
  // x labels
  const step=opts.wide?2:1;
  labels.forEach((lb,i)=>{ if(i%step===0) s.appendChild(el('text',{x:X(i),y:H-10,'text-anchor':'middle','font-size':9.5,fill:'#5b6577'})).textContent=lb; });
  host.appendChild(s);
}

// ---- rendering ----
function descTemp(d){const p=d.pct10;if(p>=6)return['strongly heat-driven','pos'];if(p>=3)return['rises with heat','pos'];if(p>=1.2)return['mildly warm-leaning','neu'];return['largely weather-resistant','neu'];}
function statCard(v,l,s,cls){return `<div class="stat"><div class="v ${cls||''}">${v}</div><div class="l">${l}</div><div class="s">${s||''}</div></div>`;}
function sgn(x){return (x>0?'+':'')+x;}

function render(key){
  const d=ITEMS[key], fc=FAMCLASS[d.family];
  document.querySelectorAll('.chip').forEach(c=>{c.className='chip'+(c.dataset.k===key?' on '+FAMCLASS[ITEMS[c.dataset.k].family]:'');});
  // lead sentence
  const [td,tc]=descTemp(d);
  const rainTxt = d.rain_sig ? (d.rain_pct<0?`rain damps it down (${d.rain_pct}%/in)`:`it climbs in the rain (+${d.rain_pct}%/in)`) : 'rain barely moves it';
  const snowTxt = d.snow_sig ? (d.snow_pct<0?`snow ${Math.abs(d.snow_pct)>Math.abs(d.rain_pct)?'cuts it more sharply':'cools it'} (${d.snow_pct}%/in)`:`snow nudges it up`) : 'snow leaves it flat';
  const wk = d.wknd>d.wkdy*1.06?'a weekend offense':(d.wkdy>d.wknd*1.06?'a weekday offense':'evenly split across the week');
  document.getElementById('lead').innerHTML=
    `<span class="nm">${d.name}</span><span class="tag ${fc}">${d.family}</span><br>`+
    `<span style="font-size:15px">A <b>${td}</b> category — about <b>${sgn(d.pct10)}%</b> per +10&deg;F, running <b>${d.hot_cold}×</b> as often on the hottest days as the coldest. `+
    `On wet days ${rainTxt}; ${snowTxt}. It is <b>${wk}</b>, busiest in <b>${MON[d.peak_month-1]}</b> and around <b>${hourLabel(d.peak_hr)}</b>.</span>`;
  // stat cards
  const rc=d.rain_sig?(d.rain_pct<0?'neg':'pos'):'neu', sc=d.snow_sig?(d.snow_pct<0?'neg':'pos'):'neu';
  document.getElementById('statcards').innerHTML=
    statCard(sgn(d.pct10)+'%','per +10°F','temperature sensitivity',d.pct10>0?'pos':'neu')+
    statCard(d.hot_cold+'×','hot vs. cold days','rate on 75°F+ vs <20°F',d.hot_cold>1?'pos':'neu')+
    statCard((d.rain_sig?sgn(d.rain_pct)+'%':'~0'),'per inch of rain',d.rain_sig?'':'not significant',rc)+
    statCard((d.snow_sig?sgn(d.snow_pct)+'%':'~0'),'per inch of snow',d.snow_sig?'':'not significant',sc)+
    statCard(d.total.toLocaleString(),'total incidents',d.per_day+'/day on average','neu')+
    statCard(MON[d.peak_month-1],'peak month','seasonal high','neu')+
    statCard(hourLabel(d.peak_hr),'busiest hour','excl. midnight/noon','neu')+
    statCard('r = '+d.anom_r,'deseasonalized','heat link beyond season',Math.abs(d.anom_r)>=0.1?'pos':'neu');
  // charts
  barChart(document.getElementById('tempchart'), d.relrate, ALL.relrate, TB);
  // monthly normalized to own average (index 100)
  const mAvg=d.monthly.reduce((a,b)=>a+b,0)/12, mIdx=d.monthly.map(v=>v/mAvg*100);
  const allMAvg=ALL.monthly.reduce((a,b)=>a+b,0)/12, allMIdx=ALL.monthly.map(v=>v/allMAvg*100);
  lineChart(document.getElementById('monthchart'), mIdx, allMIdx, MON, famHex(d.family), {area:true,base:100});
  // hourly share
  const hL=Array.from({length:24},(_,i)=>i%6===0?hourLabel(i):'');
  lineChart(document.getElementById('hourchart'), d.hourly, ALL.hourly, hL, famHex(d.family), {wide:true,area:true,fromZero:true});
  const nm=d.name;
  document.getElementById('tcleg').innerHTML=`<i style="background:${famHex(d.family)}"></i>${nm} (bars)`;
  document.getElementById('mleg').innerHTML=`<i style="background:${famHex(d.family)}"></i>${nm}`;
  document.getElementById('hleg').innerHTML=`<i style="background:${famHex(d.family)}"></i>${nm}`;
}
function famHex(f){return {Violent:'#e0492f',Property:'#3a7d44',Other:'#6b7689',All:'#1a1d29'}[f];}

// build picker
const groups={Aggregate:[],Violent:[],Property:[],Other:[]};
for(const k in ITEMS){const d=ITEMS[k]; if(k.startsWith('__'))groups.Aggregate.push(k); else groups[d.family].push(k);}
const order={Aggregate:0,Violent:1,Property:2,Other:3};
const ghost=document.getElementById('groups');
Object.keys(groups).sort((a,b)=>order[a]-order[b]).forEach(g=>{
  const keys=groups[g]; if(!keys.length)return;
  keys.sort((a,b)=>ITEMS[b].total-ITEMS[a].total);
  const div=document.createElement('div'); div.className='grp';
  div.innerHTML=`<p class="glabel">${g==='Aggregate'?'Roll-ups':g}</p>`;
  const cw=document.createElement('div'); cw.className='chips';
  keys.forEach(k=>{const c=document.createElement('div');c.className='chip';c.dataset.k=k;
    c.innerHTML=`<span class="dot ${FAMCLASS[ITEMS[k].family]}"></span>${ITEMS[k].name}`;
    c.onclick=()=>render(k); cw.appendChild(c);});
  div.appendChild(cw); ghost.appendChild(div);
});
render('__ALL__');
</script>
</body></html>'''

HTML = (HTML.replace('__DATA__', DATA_JS)
            .replace('__NDAYS__', f"{meta['n_days']:,}")
            .replace('__D0__', meta['d0']).replace('__D1__', meta['d1']))
open('detroit_crime_weather_explorer.html','w').write(HTML)
print('wrote detroit_crime_weather_explorer.html', round(len(HTML)/1024,1),'KB')

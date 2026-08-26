
import json, logging
from uk_housing_dashboard.data.datasets import (
    REGIONAL, HPI, COHORTS, HPI_TREND, HPI_YEARS,
    RENTAL_YIELD, MONTHLY_RENT, LAD_DATA, CITIES, CPIH_INDEX,
)
from uk_housing_dashboard.config import FORECAST_YEARS, DEFAULT_DEPOSIT_PCT, CV_FOLDS

log = logging.getLogger(__name__)

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
     background:#f0efeb;color:#1a1a18;font-size:13px;height:100vh;
     display:flex;flex-direction:column;overflow:hidden}
header{background:#1a3a6b;color:#fff;padding:10px 18px;display:flex;
       align-items:center;gap:10px;flex-shrink:0;flex-wrap:wrap}
header h1{font-size:13px;font-weight:500;flex:1}
header p{font-size:10px;opacity:.7;width:100%;margin-top:1px}
.badge{display:inline-block;padding:2px 7px;border-radius:3px;font-size:9px;
       font-weight:600;margin-left:4px}
.badge-live{background:#1baf7a;color:#fff}
.badge-emb{background:#888780;color:#fff}
.badge-ml{background:#2a78d6;color:#fff}
.hdr-btn{padding:4px 10px;font-size:10px;background:rgba(255,255,255,.15);
          color:#fff;border:1px solid rgba(255,255,255,.3);border-radius:4px;cursor:pointer}
.hdr-btn:hover{background:rgba(255,255,255,.25)}
#app{display:flex;flex:1;overflow:hidden}
#sidebar{width:340px;flex-shrink:0;background:#fff;border-right:1px solid #e2e0d8;
         display:flex;flex-direction:column;overflow:hidden}
#tabs{display:flex;border-bottom:1px solid #e2e0d8;flex-shrink:0}
.tab{flex:1;padding:7px 4px;text-align:center;font-size:10px;font-weight:500;
     color:#6b6966;cursor:pointer;border-bottom:2px solid transparent;transition:.15s}
.tab.active{color:#1a3a6b;border-bottom-color:#1a3a6b}
.tab-pane{display:none;padding:11px;overflow-y:auto;flex:1}
.tab-pane.active{display:flex;flex-direction:column;gap:8px}
#panel-pane,#forecast-pane{overflow-y:auto;flex:1;padding:11px}
.ctrl-label{font-size:10px;color:#6b6966;font-weight:600;text-transform:uppercase;
            letter-spacing:.04em;display:block;margin-bottom:3px}
.ctrl-group{margin-bottom:9px}
select{width:100%;padding:6px 8px;font-size:12px;border:1px solid #e2e0d8;
       border-radius:6px;background:#fff}
.slider-row{display:flex;align-items:center;gap:8px}
.slider-row input[type=range]{flex:1}
.sval{font-size:11px;font-weight:600;min-width:36px;text-align:right;color:#1a3a6b}
.income-row{display:flex;gap:5px}
.income-row input{flex:1;padding:6px 8px;font-size:12px;
                  border:1px solid #e2e0d8;border-radius:6px}
.income-row button{padding:5px 10px;font-size:10px;background:#1a3a6b;color:#fff;
                   border:none;border-radius:6px;cursor:pointer}
.help-box{background:#e8eef8;border-radius:7px;padding:9px;
          font-size:11px;color:#1a3a6b;line-height:1.6}
.hint{color:#b0ada6;text-align:center;padding:28px 10px;font-size:12px;line-height:1.7}
.rname{font-size:16px;font-weight:700;color:#1a3a6b;margin-bottom:3px}
.rtag{display:inline-block;background:#e8eef8;color:#1a3a6b;font-size:10px;
      padding:2px 7px;border-radius:4px;margin-bottom:9px}
.kpi-grid{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-bottom:11px}
.kpi{background:#f8f7f4;border-radius:6px;padding:6px 8px}
.kpi-l{font-size:9px;color:#6b6966;margin-bottom:1px;text-transform:uppercase;letter-spacing:.03em}
.kpi-v{font-size:15px;font-weight:700}
.kpi-s{font-size:9px;color:#b0ada6;margin-top:1px}
.sec-hdr{font-size:10px;font-weight:700;color:#6b6966;text-transform:uppercase;
         letter-spacing:.04em;margin:11px 0 5px;border-top:1px solid #e8e6e0;padding-top:9px}
.spark-wrap{background:#f8f7f4;border-radius:6px;padding:7px;margin-bottom:3px}
.spark-wrap svg{width:100%;height:54px;display:block}
.spark-footer{display:flex;justify-content:space-between;font-size:9px;color:#6b6966;margin-top:2px}
.cohort-row{display:flex;align-items:center;gap:5px;margin-bottom:4px}
.c-name{font-size:11px;width:120px;flex-shrink:0}
.c-bar{flex:1;background:#eeecea;border-radius:3px;height:11px;overflow:hidden}
.c-fill{height:100%;border-radius:3px;transition:width .4s ease}
.c-yrs{font-size:10px;font-weight:700;width:40px;text-align:right;flex-shrink:0}
.gap-note{font-size:9px;color:#e34948;margin-top:-3px;margin-bottom:3px;padding-left:125px}
.sdlt-row{display:flex;justify-content:space-between;padding:3px 0;
          border-bottom:1px solid #f0efeb;font-size:11px}
.sdlt-band{color:#6b6966}.sdlt-amt{font-weight:600}
.sdlt-total{display:flex;justify-content:space-between;background:#1a3a6b;color:#fff;
            padding:5px 8px;border-radius:4px;margin-top:3px;font-size:11px;font-weight:600}
.ftb-sdlt{margin-top:4px;padding:5px 8px;background:#e8f5ee;border-radius:4px;
          font-size:10px;color:#0f6e56}
.ftb-row{display:flex;align-items:center;gap:5px;margin-bottom:4px}
.ftb-lbl{font-size:11px;width:72px;flex-shrink:0}
.ftb-outer{flex:1;background:#eeecea;border-radius:3px;height:13px;overflow:hidden}
.ftb-inner{height:100%;border-radius:3px}
.ftb-val{font-size:10px;font-weight:600;width:68px;text-align:right;flex-shrink:0}
.rvb-row{display:flex;justify-content:space-between;padding:3px 0;
         border-bottom:1px solid #f0efeb;font-size:11px}
.rvb-row span:first-child{color:#6b6966}
.rvb-row span:last-child{font-weight:600}
.verdict{margin-top:7px;padding:6px;border-radius:5px;font-size:10px;
         font-weight:500;text-align:center}
.note{font-size:10px;color:#1baf7a;margin-top:2px;margin-bottom:3px}
.src{margin-top:10px;font-size:9px;color:#c0bdb6;border-top:1px solid #e8e6e0;
     padding-top:7px;line-height:1.6}
/* Forecast pane */
.fc-header{background:#1a3a6b;color:#fff;border-radius:8px;padding:12px;margin-bottom:12px}
.fc-title{font-size:15px;font-weight:600;margin-bottom:3px}
.fc-sub{font-size:10px;opacity:.75;line-height:1.5}
.fc-metric-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:12px}
.fc-metric{background:#fff;border:1px solid #e2e0d8;border-radius:7px;padding:8px 10px}
.fc-m-lbl{font-size:9px;color:#6b6966;text-transform:uppercase;letter-spacing:.03em}
.fc-m-val{font-size:17px;font-weight:700;margin:2px 0}
.fc-m-sub{font-size:9px;color:#b0ada6}
.up{color:#e34948}.dn{color:#1baf7a}.neu{color:#eda100}
.fc-section{background:#fff;border:1px solid #e2e0d8;border-radius:7px;
            padding:12px;margin-bottom:10px}
.fc-sec-title{font-size:12px;font-weight:600;color:#1a3a6b;margin-bottom:9px}
canvas{width:100%!important}
table{width:100%;border-collapse:collapse;font-size:11px}
th{background:#1a3a6b;color:#fff;padding:5px 7px;text-align:left;
   font-size:9px;text-transform:uppercase;letter-spacing:.04em}
td{padding:5px 7px;border-bottom:1px solid #f0efeb}
tr:hover td{background:#f8f7f4}
.model-info{background:#e8eef8;border-radius:6px;padding:9px;
            font-size:10px;color:#1a3a6b;margin-bottom:10px;line-height:1.7}
#year-badge{position:absolute;top:10px;right:10px;z-index:999;
            background:rgba(26,58,107,.9);color:#fff;padding:4px 9px;
            border-radius:5px;font-size:11px;font-weight:600;pointer-events:none}
#legend{position:absolute;bottom:22px;left:4px;z-index:999;
        background:rgba(255,255,255,.93);border-radius:7px;padding:7px 11px;
        font-size:10px;color:#6b6966;box-shadow:0 1px 5px rgba(0,0,0,.14);min-width:158px}
#legend-bar{height:8px;border-radius:3px;margin:3px 0;
            background:linear-gradient(to right,#1baf7a,#a8d150,#eda100,#eb6834,#e34948)}
#legend-ticks{display:flex;justify-content:space-between;font-size:9px}
.leaflet-popup-content-wrapper{border-radius:7px!important}
.leaflet-popup-content{margin:9px 11px!important;font-size:12px}
.popup-name{font-weight:700;font-size:13px;color:#1a3a6b;margin-bottom:2px}
.popup-r{font-size:17px;font-weight:700}
@media(max-width:900px){#app{flex-direction:column}#sidebar{width:100%;max-height:50vh}}
"""

JS_PANEL = r"""
function fmt(n){return Math.round(n).toLocaleString('en-GB');}

function ratioColor(r){
  if(!r||isNaN(r))return'#cccccc';
  const stops=[[3,'#1baf7a'],[6,'#a8d150'],[9,'#eda100'],[13,'#eb6834'],[35,'#e34948']];
  for(let i=1;i<stops.length;i++){
    if(r<=stops[i][0]){
      const lo=stops[i-1],hi=stops[i],t=(r-lo[0])/(hi[0]-lo[0]);
      const ah=parseInt(lo[1].slice(1),16),bh=parseInt(hi[1].slice(1),16);
      const lerp=(a,b)=>Math.round((a>>16&255)+(((b>>16&255)-(a>>16&255))*t))<<16|
                        Math.round((a>>8&255)+(((b>>8&255)-(a>>8&255))*t))<<8|
                        Math.round((a&255)+(((b&255)-(a&255))*t));
      return'#'+(lerp(ah,bh)+0x1000000).toString(16).slice(1);
    }
  }
  return stops[stops.length-1][1];
}

function calcSDLT(price,isFTB,jur){
  if(jur==='SDLT'&&isFTB&&price>625000)isFTB=false;
  let bands;
  if(jur==='LTT')bands=[[0,225000,0],[225000,400000,.06],[400000,750000,.075],[750000,1500000,.10],[1500000,99999999,.12]];
  else if(jur==='LBTT')bands=isFTB?[[0,175000,0],[175000,250000,.02],[250000,325000,.05],[325000,750000,.10],[750000,99999999,.12]]:[[0,145000,0],[145000,250000,.02],[250000,325000,.05],[325000,750000,.10],[750000,99999999,.12]];
  else bands=isFTB?[[0,425000,0],[425000,625000,.05]]:[[0,250000,0],[250000,925000,.05],[925000,1500000,.10],[1500000,99999999,.12]];
  let tax=0,rows=[];
  for(const[lo,hi,rate]of bands){
    if(price<=lo)break;
    const amt=(Math.min(price,hi)-lo)*rate;
    tax+=amt;
    rows.push({band:'\u00a3'+fmt(lo)+'-\u00a3'+fmt(hi),rate:(rate*100).toFixed(0)+'%',amount:amt});
  }
  return{total:tax,rows};
}

function getJur(region){
  return region==='Wales'?'LTT':region==='Scotland'?'LBTT':'SDLT';
}

function buildSparkline(region,yearIdx){
  const trend=HPI_TREND[region];
  if(!trend)return'';
  const base=(HPI[region]||{})['Semi-Detached']||200000;
  const prices=trend.map(i=>(i/100)*base);
  const mn=Math.min(...prices),mx=Math.max(...prices);
  const W=300,H=52,p=4;
  const xs=prices.map((_,i)=>p+(i/(prices.length-1))*(W-p*2));
  const ys=prices.map(v=>H-p-(v-mn)/(mx-mn)*(H-p*2));
  const pts=xs.map((x,i)=>x.toFixed(1)+','+ys[i].toFixed(1)).join(' ');
  const L=prices.length-1;
  const area='M'+xs[0].toFixed(1)+','+ys[0].toFixed(1)+' '+
    xs.slice(1).map((x,i)=>'L'+x.toFixed(1)+','+ys[i+1].toFixed(1)).join(' ')+
    ' L'+xs[L].toFixed(1)+','+(H-p)+' L'+xs[0].toFixed(1)+','+(H-p)+' Z';
  const pct=((prices[9]-prices[0])/prices[0]*100).toFixed(0);
  return`<div class="sec-hdr">Price trend 2015-2024</div>
  <div class="spark-wrap">
    <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">
      <defs><linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#2a78d6" stop-opacity=".22"/>
        <stop offset="100%" stop-color="#2a78d6" stop-opacity=".02"/>
      </linearGradient></defs>
      <path d="${area}" fill="url(#sg)"/>
      <polyline points="${pts}" fill="none" stroke="#2a78d6" stroke-width="1.8" stroke-linejoin="round"/>
      <circle cx="${xs[yearIdx].toFixed(1)}" cy="${ys[yearIdx].toFixed(1)}" r="3.5" fill="#2a78d6" stroke="#fff" stroke-width="1.5"/>
    </svg>
    <div class="spark-footer">
      <span>\u00a3${fmt(prices[0])} (2015)</span>
      <span style="color:#2a78d6;font-weight:600">+${pct}% since 2015</span>
      <span>\u00a3${fmt(prices[9])} (2024)</span>
    </div>
  </div>`;
}

function buildCohortBars(price,income,dep){
  return COHORTS.map(c=>{
    const y=(price*dep)/(income*c.rate),pct=Math.min(100,(y/40)*100).toFixed(1);
    return`<div class="cohort-row"><span class="c-name">${c.label}</span>
      <div class="c-bar"><div class="c-fill" style="width:${pct}%;background:${c.color}"></div></div>
      <span class="c-yrs">${y.toFixed(1)} yrs</span></div>`;
  }).join('');
}

function buildDepositGap(price,income,dep){
  const needed=price*dep;
  return COHORTS.map(c=>{
    const saved=income*c.rate*5,gap=Math.max(0,needed-saved),pct=Math.min(100,(saved/needed)*100).toFixed(0);
    return`<div class="cohort-row"><span class="c-name">${c.label}</span>
      <div class="c-bar"><div class="c-fill" style="width:${pct}%;background:${c.color}"></div></div>
      <span class="c-yrs">${pct}%</span></div>
      <div class="gap-note">${gap>0?'Gap: \u00a3'+fmt(gap):'Sufficient after 5 yrs'}</div>`;
  }).join('');
}

function buildSDLT(price,region){
  const jur=getJur(region);
  const std=calcSDLT(price,false,jur),ftb=calcSDLT(price,true,jur);
  const saving=std.total-ftb.total;
  const jurLabel={'SDLT':'SDLT (England)','LTT':'LTT (Wales)','LBTT':'LBTT (Scotland)'}[jur]||jur;
  const rows=std.rows.map(r=>`<div class="sdlt-row"><span class="sdlt-band">${r.band} @ ${r.rate}</span><span class="sdlt-amt">\u00a3${fmt(r.amount)}</span></div>`).join('');
  return`<div class="sec-hdr">${jurLabel} (2024)</div>${rows}
  <div class="sdlt-total"><span>Standard buyer</span><span>\u00a3${fmt(std.total)}</span></div>
  <div class="ftb-sdlt">First-time buyer: \u00a3${fmt(ftb.total)} ${saving>0?'(saving \u00a3'+fmt(saving)+')':'(no relief)'}</div>`;
}

function buildFTBBar(region){
  const h=HPI[region]||{},ftb=h.FTB,all=h.All;
  if(!ftb||!all)return'';
  const mx=Math.max(ftb,all)*1.05;
  return`<div class="sec-hdr">First-time buyer vs all buyers</div>
  <div class="ftb-row"><span class="ftb-lbl">FTB median</span>
    <div class="ftb-outer"><div class="ftb-inner" style="width:${(ftb/mx*100).toFixed(1)}%;background:#2a78d6"></div></div>
    <span class="ftb-val">\u00a3${fmt(ftb)}</span></div>
  <div class="ftb-row"><span class="ftb-lbl">All buyers</span>
    <div class="ftb-outer"><div class="ftb-inner" style="width:${(all/mx*100).toFixed(1)}%;background:#888780"></div></div>
    <span class="ftb-val">\u00a3${fmt(all)}</span></div>
  <div class="note">FTB properties typically cost \u00a3${fmt(all-ftb)} less</div>`;
}

function buildRentVsBuy(region,price,income,dep){
  const rent=MONTHLY_RENT[region]||900,yld=RENTAL_YIELD[region]||5;
  const mort=(price*(1-dep)*0.045)/12;
  const rp=(rent*12/income*100).toFixed(1),mp=(mort*12/income*100).toFixed(1);
  const diff=parseFloat(mp)-parseFloat(rp);
  const[vc,vb,vt]=diff<5?['#0f6e56','#e8f5ee','Buying comparable to renting']:
    parseFloat(mp)>50?['#a32d2d','#fce8e8','Mortgage severely unaffordable']:
    ['#854f0b','#fef5e0','Renting may be preferable short-term'];
  return`<div class="sec-hdr">Rent vs buy</div>
  <div class="rvb-row"><span>Avg monthly rent</span><span>\u00a3${fmt(rent)}</span></div>
  <div class="rvb-row"><span>Est. monthly mortgage (4.5%)</span><span>\u00a3${fmt(mort)}</span></div>
  <div class="rvb-row"><span>Rent as % income</span><span>${rp}%</span></div>
  <div class="rvb-row"><span>Mortgage as % income</span><span>${mp}%</span></div>
  <div class="rvb-row"><span>Gross rental yield</span><span>${yld.toFixed(1)}%</span></div>
  <div class="verdict" style="color:${vc};background:${vb}">${vt}</div>`;
}

// ---- State ----
let depositPct=0.10,yearIdx=9,personalIncome=null,currentName=null,currentRegion=null,ladLayer=null;
const cityGroup=L.layerGroup();

function getLAD(name){
  if(LAD_DATA[name])return LAD_DATA[name];
  const s=name.replace(', City of','').replace(' City','').trim().toLowerCase();
  for(const[k,v]of Object.entries(LAD_DATA))
    if(k.toLowerCase().includes(s)||s.includes(k.toLowerCase()))return v;
  return null;
}
function getYearRatio(region,base){
  const t=HPI_TREND[region];return t?base*(t[yearIdx]/t[9]):base;
}
function applyStyle(f){
  const reg=f.properties.region||'',d=getLAD(f.properties.name);
  const base=d?d.ratio:(REGIONAL[reg]||{}).ratio||7;
  const hidden=document.getElementById('sel-region').value!=='all'&&
               document.getElementById('sel-region').value!==reg;
  return{fillColor:ratioColor(getYearRatio(reg,base)),weight:hidden?.2:.5,
         opacity:1,color:'#fff',fillOpacity:hidden?.05:.75};
}

function showPanel(name,region,ratio,price){
  currentName=name;currentRegion=region||'';
  const rd=REGIONAL[region]||{},income=personalIncome||rd.income||29000;
  const h=HPI[region]||{},prop=document.getElementById('sel-proptype').value;
  const base=price||h[prop]||(ratio||8)*income;
  const t=HPI_TREND[region],usePrice=t?base*(t[yearIdx]/t[9]):base;
  const deposit=usePrice*depositPct,yearRatio=(usePrice/income).toFixed(1);
  switchTab('panel');
  document.getElementById('panel-pane').innerHTML=`
    <div class="rname">${name}</div>
    <div class="rtag">${region||'UK'}</div>
    <div class="kpi-grid">
      <div class="kpi"><div class="kpi-l">Affordability ratio ${HPI_YEARS[yearIdx]}</div>
        <div class="kpi-v" style="color:${ratioColor(parseFloat(yearRatio))}">${yearRatio}x</div>
        <div class="kpi-s">Median price / earnings</div></div>
      <div class="kpi"><div class="kpi-l">Median price (${HPI_YEARS[yearIdx]})</div>
        <div class="kpi-v">\u00a3${fmt(usePrice)}</div>
        <div class="kpi-s">HM Land Registry HPI</div></div>
      <div class="kpi"><div class="kpi-l">${personalIncome?'Your income':'Regional income'}</div>
        <div class="kpi-v">\u00a3${fmt(income)}</div>
        <div class="kpi-s">${personalIncome?'Personal input':'ONS GDHI 2023'}</div></div>
      <div class="kpi"><div class="kpi-l">${Math.round(depositPct*100)}% deposit required</div>
        <div class="kpi-v">\u00a3${fmt(deposit)}</div>
        <div class="kpi-s">On ${prop} median</div></div>
      <div class="kpi"><div class="kpi-l">Homeownership rate</div>
        <div class="kpi-v">${rd.own||'N/A'}%</div>
        <div class="kpi-s">ONS LFS 2023</div></div>
      <div class="kpi"><div class="kpi-l">Rent as % income</div>
        <div class="kpi-v">${rd.rent_pct||'N/A'}%</div>
        <div class="kpi-s">ONS private rental 2024</div></div>
    </div>
    ${buildSparkline(region,yearIdx)}
    ${buildFTBBar(region)}
    <div class="sec-hdr">Years to save ${Math.round(depositPct*100)}% deposit - ${prop}</div>
    ${buildCohortBars(usePrice,income,depositPct)}
    <div class="sec-hdr">Deposit gap after 5 years saving</div>
    ${buildDepositGap(usePrice,income,depositPct)}
    ${buildSDLT(usePrice,region)}
    ${buildRentVsBuy(region,usePrice,income,depositPct)}
    <div style="margin-top:8px;padding:7px;background:#e8eef8;border-radius:6px;
                font-size:10px;color:#1a3a6b;cursor:pointer" onclick="switchTab('forecast');updateForecast()">
      View 5-year ML price forecast for ${region} \u2192
    </div>
    <div class="src">ONS GDHI 2023 &middot; HM Land Registry HPI &middot; ONS WAS Wave 7
    &middot; ONS Private Rental 2024 &middot; Resolution Foundation 2023 &middot; Savills 2024</div>`;
}

// ---- Map init ----
const map=L.map('map',{center:[54.5,-3.5],zoom:6});
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png',
  {attribution:'&copy; OpenStreetMap &copy; CARTO',maxZoom:13}).addTo(map);
cityGroup.addTo(map);

if(GEOJSON){
  ladLayer=L.geoJSON(GEOJSON,{
    style:f=>applyStyle(f),
    onEachFeature:(f,layer)=>{
      const name=f.properties.name,reg=f.properties.region||'';
      const d=getLAD(name),rd=REGIONAL[reg]||{},base=d?d.ratio:rd.ratio||7;
      layer.on({
        mouseover:e=>e.target.setStyle({weight:2,color:'#1a3a6b',fillOpacity:.9}),
        mouseout:e=>ladLayer.resetStyle(e.target),
        click:()=>{
          const income=rd.income||29000;
          showPanel(name,reg,getYearRatio(reg,base),d?d.median_price:base*income);
          map.fitBounds(layer.getBounds(),{padding:[20,20]});
        }
      });
      layer.bindTooltip(`<strong>${name}</strong><br>Ratio: ${base?base.toFixed(1)+'x':'N/A'}`,{sticky:true,opacity:.92});
    }
  }).addTo(map);
}

function buildCities(filter){
  cityGroup.clearLayers();
  if(filter==='none')return;
  CITIES.forEach(city=>{
    if(filter==='large'&&city.pop<500000)return;
    const rd=REGIONAL[city.region]||{};
    const dot=L.divIcon({html:'<div style="width:9px;height:9px;background:#1a3a6b;border-radius:50%;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.4)"></div>',className:'',iconSize:[9,9],iconAnchor:[4,4]});
    const m=L.marker([city.lat,city.lng],{icon:dot});
    m.bindTooltip(`<div class="popup-name">${city.name}</div>
      <div class="popup-r" style="color:${ratioColor(rd.ratio||7)}">${rd.ratio||7}x</div>
      <div>Pop: ${(city.pop/1000).toFixed(0)}k</div>`,{opacity:.95});
    m.on('click',()=>showPanel(city.name,city.region,rd.ratio,
      (HPI[city.region]||{})['Semi-Detached']||(rd.ratio||7)*(rd.income||29000)));
    const lbl=L.marker([city.lat,city.lng],{icon:L.divIcon({
      html:`<div style="font-size:9px;font-weight:600;color:#1a3a6b;text-shadow:0 0 3px #fff;white-space:nowrap;transform:translate(7px,-4px)">${city.name}</div>`,
      className:'',iconSize:[0,0]})});
    cityGroup.addLayer(m);cityGroup.addLayer(lbl);
  });
}
buildCities('all');

function onYearChange(idx){
  yearIdx=parseInt(idx);
  document.getElementById('year-disp').textContent=HPI_YEARS[yearIdx];
  document.getElementById('year-badge').textContent=HPI_YEARS[yearIdx];
  if(ladLayer)ladLayer.eachLayer(l=>{if(l.feature)ladLayer.resetStyle(l);});
  refreshPanel();
}
function onDepositChange(val){
  depositPct=parseInt(val)/100;
  document.getElementById('dep-disp').textContent=val+'%';
  refreshPanel();updateForecast();
}
function applyRegionFilter(){
  const f=document.getElementById('sel-region').value;
  if(ladLayer)ladLayer.eachLayer(l=>{if(l.feature)ladLayer.resetStyle(l);});
  if(f!=='all'&&REGIONAL[f]){
    const rd=REGIONAL[f];
    showPanel(f+' (region)',f,rd.ratio,(HPI[f]||{})['Semi-Detached']||rd.ratio*rd.income);
  }
}
function applyPersonalIncome(){
  const v=parseInt(document.getElementById('personal-income').value);
  if(v>0){personalIncome=v;refreshPanel();updateForecast();}
}
function refreshPanel(){
  if(!currentName||!currentRegion)return;
  const rd=REGIONAL[currentRegion]||{},h=HPI[currentRegion]||{};
  const prop=document.getElementById('sel-proptype').value;
  const price=h[prop]||(rd.ratio*rd.income)||200000;
  const d=getLAD(currentName);
  showPanel(currentName,currentRegion,getYearRatio(currentRegion,d?d.ratio:rd.ratio||8),price);
}
function switchTab(tab){
  document.querySelectorAll('.tab').forEach(t=>
    t.classList.toggle('active',t.dataset.tab===tab));
  ['filters-pane','panel-pane','forecast-pane'].forEach(id=>{
    const el=document.getElementById(id);
    if(el)el.style.display='none';
  });
  const pane=document.getElementById(tab+'-pane');
  if(pane)pane.style.display=tab==='filters'?'flex':'block';
}
document.getElementById('filters-pane').style.display='flex';
document.getElementById('panel-pane').style.display='none';
document.getElementById('forecast-pane').style.display='none';
"""

JS_FORECAST = r"""
// ---- 5-Year Forecast Panel ----
let priceChart=null,gapChart=null,cohortChart=null;

function updateForecast(){
  const region  = currentRegion || document.getElementById('fc-region').value;
  const ptype   = document.getElementById('fc-proptype').value;
  const depPct  = depositPct;
  const income  = personalIncome || (REGIONAL[region]||{}).income || 29000;

  if(!ML_FORECASTS||!ML_FORECASTS[region]||!ML_FORECASTS[region][ptype]){
    document.getElementById('forecast-pane').innerHTML=
      '<div class="hint">ML forecasts not available.<br>Ensure scikit-learn is installed and rerun.</div>';
    return;
  }

  const f     = ML_FORECASTS[region][ptype];
  const base  = (HPI[region]||{})[ptype]||(REGIONAL[region]||{}).ratio*income||200000;
  const f2029 = f[FORECAST_YEARS[FORECAST_YEARS.length-1].toString()];
  const pct   = f2029?f2029.pct_change:0;
  const arrow = pct>=0?'\u2191':'\u2193';
  const cls   = pct>=0?'up':'dn';

  // Update region selector to match current region
  const sel=document.getElementById('fc-region');
  if(sel&&region&&sel.value!==region){
    for(let i=0;i<sel.options.length;i++){
      if(sel.options[i].value===region){sel.selectedIndex=i;break;}
    }
  }

  // KPIs
  document.getElementById('fc-kpis').innerHTML=`
    <div class="fc-metric"><div class="fc-m-lbl">Current price (2024)</div>
      <div class="fc-m-val">\u00a3${fmt(base)}</div><div class="fc-m-sub">${ptype}</div></div>
    <div class="fc-metric"><div class="fc-m-lbl">Forecast 2029</div>
      <div class="fc-m-val ${cls}">${arrow} \u00a3${fmt(f2029?f2029.pred:0)}</div>
      <div class="fc-m-sub">${pct>=0?'+':''}${pct.toFixed(1)}% from 2024</div></div>
    <div class="fc-metric"><div class="fc-m-lbl">90% CI (2029)</div>
      <div class="fc-m-val" style="font-size:12px">\u00a3${fmt(f2029?f2029.low:0)} &ndash; \u00a3${fmt(f2029?f2029.high:0)}</div>
      <div class="fc-m-sub">Residual-based analytical CI</div></div>
    <div class="fc-metric"><div class="fc-m-lbl">Real price 2029</div>
      <div class="fc-m-val">\u00a3${fmt(f2029?f2029.real_price:0)}</div>
      <div class="fc-m-sub">2024 GBP (CPIH-adjusted)</div></div>
  `;

  // Price chart (historical + forecast)
  const idx      = HPI_TREND[region]||[];
  const histNom  = HPI_YEARS.map((y,i)=>idx[i]?base*(idx[i]/idx[idx.length-1]):base);
  const fyStrs   = FORECAST_YEARS.map(String);
  const fcNom    = fyStrs.map(y=>f[y]?f[y].pred:null).filter(Boolean);
  const fcLo     = fyStrs.map(y=>f[y]?f[y].low:null).filter(Boolean);
  const fcHi     = fyStrs.map(y=>f[y]?f[y].high:null).filter(Boolean);
  const fcReal   = fyStrs.map(y=>f[y]?f[y].real_price:null).filter(Boolean);
  const allYears = [...HPI_YEARS,...FORECAST_YEARS];
  const joinPt   = histNom[histNom.length-1];

  if(priceChart)priceChart.destroy();
  const ctx=document.getElementById('price-chart').getContext('2d');
  priceChart=new Chart(ctx,{
    type:'line',
    data:{
      labels:allYears,
      datasets:[
        {label:'Historical (nominal)',data:[...histNom,...Array(FORECAST_YEARS.length).fill(null)],
         borderColor:'#2a78d6',borderWidth:2.5,pointRadius:3,tension:.3,fill:false},
        {label:'Forecast (nominal)',data:[...Array(HPI_YEARS.length-1).fill(null),joinPt,...fcNom],
         borderColor:'#2a78d6',borderWidth:2.5,borderDash:[6,3],pointRadius:3,tension:.3,fill:false},
        {label:'Forecast real (2024 GBP)',data:[...Array(HPI_YEARS.length-1).fill(null),joinPt,...fcReal],
         borderColor:'#1baf7a',borderWidth:1.8,borderDash:[3,3],pointRadius:2,tension:.3,fill:false},
        {label:'90% CI low',data:[...Array(HPI_YEARS.length-1).fill(null),joinPt,...fcLo],
         borderColor:'rgba(42,120,214,.25)',borderWidth:1,pointRadius:0,fill:false},
        {label:'90% CI high',data:[...Array(HPI_YEARS.length-1).fill(null),joinPt,...fcHi],
         borderColor:'rgba(42,120,214,.25)',borderWidth:1,pointRadius:0,
         fill:'-1',backgroundColor:'rgba(42,120,214,.07)'},
      ]
    },
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:'bottom',labels:{font:{size:9},boxWidth:12}}},
      scales:{y:{ticks:{callback:v=>'\u00a3'+Math.round(v/1000)+'k',font:{size:9}}},
              x:{ticks:{font:{size:9}}}}}
  });

  // Intergenerational gap chart 2024-2029
  if(gapChart)gapChart.destroy();
  const gapYears=[2024,...FORECAST_YEARS];
  function yts(price,inc,rate){return(price*depPct)/(inc*rate);}
  const inc24=income;
  const genZ=[yts(base,inc24,COHORTS[0].rate)];
  const boom =[yts(base,inc24,COHORTS[3].rate)];
  FORECAST_YEARS.forEach(yr=>{
    const inc=inc24*(1.025**(yr-2024));
    const af=ML_AFFORD[region]&&ML_AFFORD[region][String(yr)]&&ML_AFFORD[region][String(yr)][ptype];
    const pr=af?af.price:(f[String(yr)]?f[String(yr)].pred:base);
    genZ.push(yts(pr,inc,COHORTS[0].rate));
    boom.push(yts(pr,inc,COHORTS[3].rate));
  });
  const ctx2=document.getElementById('gap-chart').getContext('2d');
  gapChart=new Chart(ctx2,{
    type:'line',
    data:{labels:gapYears,datasets:[
      {label:'Gen Z (18-27)',data:genZ,borderColor:'#e34948',borderWidth:2.2,
       fill:'+1',backgroundColor:'rgba(227,73,72,.1)',pointRadius:4},
      {label:'Baby Boomers (60-78)',data:boom,borderColor:'#1baf7a',borderWidth:2.2,pointRadius:4},
    ]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:'bottom',labels:{font:{size:9},boxWidth:12}}},
      scales:{y:{title:{display:true,text:'Years to save deposit',font:{size:9}},
                 ticks:{font:{size:9}}},x:{ticks:{font:{size:9}}}}}
  });

  // Cohort comparison chart for all 4 cohorts in 2029
  if(cohortChart)cohortChart.destroy();
  const ctx3=document.getElementById('cohort-chart').getContext('2d');
  const coYrs=FORECAST_YEARS.map(yr=>{
    const inc=inc24*(1.025**(yr-2024));
    const af=ML_AFFORD[region]&&ML_AFFORD[region][String(yr)]&&ML_AFFORD[region][String(yr)][ptype];
    const pr=af?af.price:(f[String(yr)]?f[String(yr)].pred:base);
    return COHORTS.map(c=>parseFloat(yts(pr,inc,c.rate).toFixed(1)));
  });
  cohortChart=new Chart(ctx3,{
    type:'bar',
    data:{
      labels:FORECAST_YEARS,
      datasets:COHORTS.map((c,ci)=>({
        label:c.label,
        data:coYrs.map(row=>row[ci]),
        backgroundColor:c.color+'cc',
        borderColor:c.color,
        borderWidth:1,
      }))
    },
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:'bottom',labels:{font:{size:9},boxWidth:12}}},
      scales:{y:{title:{display:true,text:'Years to save 10% deposit',font:{size:9}},
                 ticks:{font:{size:9}}},x:{ticks:{font:{size:9}}}}}
  });

  // Forecast detail table
  let tbody='';
  FORECAST_YEARS.forEach(yr=>{
    const fyr=f[String(yr)];if(!fyr)return;
    const inc=inc24*(1.025**(yr-2024));
    const af=ML_AFFORD[region]&&ML_AFFORD[region][String(yr)]&&ML_AFFORD[region][String(yr)][ptype];
    const ratio=af?af.ratio:(fyr.pred/inc).toFixed(1);
    const gz=(fyr.pred*depPct)/(inc*COHORTS[0].rate);
    const dir=fyr.pct_change>=0?'\u2191':'down';
    const cls=fyr.pct_change>=0?'up':'dn';
    tbody+=`<tr>
      <td><strong>${yr}</strong></td>
      <td>\u00a3${fmt(fyr.pred)}</td>
      <td class="${cls}">${fyr.pct_change>=0?'+':''}${fyr.pct_change.toFixed(1)}%</td>
      <td class="neu">\u00a3${fmt(fyr.low)} &ndash; \u00a3${fmt(fyr.high)}</td>
      <td>\u00a3${fmt(fyr.real_price)}</td>
      <td>${parseFloat(ratio).toFixed(1)}x</td>
      <td>${gz.toFixed(1)} yrs</td>
    </tr>`;
  });
  document.getElementById('fc-tbody').innerHTML=tbody;
}

function onFcRegionChange(){
  const r=document.getElementById('fc-region').value;
  currentRegion=r;
  updateForecast();
}
"""


def build(geojson_str, forecasts=None, afford=None, metrics=None, data_notes=None):
    """Build and return the complete dashboard HTML."""
    forecasts  = forecasts  or {}
    afford     = afford     or {}
    metrics    = metrics    or {}
    data_notes = data_notes or {}

    def badge(key, label):
        is_live = "live" in data_notes.get(key, "").lower()
        cls     = "badge-live" if is_live else "badge-emb"
        return f'<span class="badge {cls}">{label}: {"LIVE" if is_live else "EMBEDDED"}</span>'

    ml_badge = (f'<span class="badge badge-ml">ML: R\u00b2={metrics.get("r2_mean","?")} '
                f'MAE=GBP{metrics.get("mae_mean","?"):,}</span>'
                if forecasts and metrics.get("r2_mean") else
                '<span class="badge badge-emb">ML: OFF</span>')

    js_data = "\n".join([
        f"const REGIONAL={json.dumps(REGIONAL)};",
        f"const HPI={json.dumps(HPI)};",
        f"const COHORTS={json.dumps(COHORTS)};",
        f"const HPI_TREND={json.dumps(HPI_TREND)};",
        f"const HPI_YEARS={json.dumps(HPI_YEARS)};",
        f"const RENTAL_YIELD={json.dumps(RENTAL_YIELD)};",
        f"const MONTHLY_RENT={json.dumps(MONTHLY_RENT)};",
        f"const LAD_DATA={json.dumps(LAD_DATA)};",
        f"const CITIES={json.dumps(CITIES)};",
        f"const GEOJSON={geojson_str};",
        f"const ML_FORECASTS={json.dumps(forecasts)};",
        f"const ML_AFFORD={json.dumps(afford)};",
        f"const ML_METRICS={json.dumps(metrics)};",
        f"const FORECAST_YEARS={json.dumps(FORECAST_YEARS)};",
    ])

    region_opts = "\n".join(f'<option value="{r}">{r}</option>' for r in REGIONAL)

    log.info("Building HTML dashboard (forecasts=%s, metrics=%s)", bool(forecasts), bool(metrics))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>UK Housing Affordability Dashboard</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>{CSS}</style>
</head>
<body>
<header>
  <div style="flex:1">
    <h1>UK Housing Affordability Dashboard &mdash; Regional &amp; LAD Map + 5-Year Forecast
      {badge("income","Income")}{badge("hpi","Prices")}{ml_badge}
    </h1>
    <p>MSc Big Data with Banking and Finance &middot; Sheffield Hallam University &middot; Joseph Richards 2026
    &middot; Data: ONS GDHI 2023 | HM Land Registry HPI 2015-2024 | ONS WAS Wave 7</p>
  </div>
</header>
<div id="app">
  <div id="sidebar">
    <div id="tabs">
      <div class="tab active" data-tab="filters" onclick="switchTab('filters')">Filters</div>
      <div class="tab"        data-tab="panel"   onclick="switchTab('panel')">Data Panel</div>
      <div class="tab"        data-tab="forecast" onclick="switchTab('forecast');updateForecast()">5-Yr Forecast</div>
    </div>

    <!-- FILTERS TAB -->
    <div class="tab-pane active" id="filters-pane">
      <div class="ctrl-group">
        <span class="ctrl-label">Region filter</span>
        <select id="sel-region" onchange="applyRegionFilter()">
          <option value="all">All regions</option>
          {region_opts}
        </select>
      </div>
      <div class="ctrl-group">
        <span class="ctrl-label">Year (2015&ndash;2024)</span>
        <div class="slider-row">
          <input type="range" id="sel-year" min="0" max="9" value="9" step="1"
                 oninput="onYearChange(this.value)">
          <span class="sval" id="year-disp">2024</span>
        </div>
      </div>
      <div class="ctrl-group">
        <span class="ctrl-label">Deposit % (5&ndash;25%)</span>
        <div class="slider-row">
          <input type="range" id="sel-deposit" min="5" max="25" value="10" step="1"
                 oninput="onDepositChange(this.value)">
          <span class="sval" id="dep-disp">10%</span>
        </div>
      </div>
      <div class="ctrl-group">
        <span class="ctrl-label">Property type</span>
        <select id="sel-proptype" onchange="refreshPanel()">
          <option value="Semi-Detached">Semi-Detached</option>
          <option value="Detached">Detached</option>
          <option value="Terraced">Terraced</option>
          <option value="Flat">Flat</option>
        </select>
      </div>
      <div class="ctrl-group">
        <span class="ctrl-label">Your personal income (optional)</span>
        <div class="income-row">
          <input type="number" id="personal-income" placeholder="e.g. 35000"
                 min="10000" max="500000" step="1000">
          <button onclick="applyPersonalIncome()">Apply</button>
        </div>
      </div>
      <div class="ctrl-group">
        <span class="ctrl-label">City markers</span>
        <select id="sel-cities" onchange="buildCities(this.value)">
          <option value="all">All major cities</option>
          <option value="large">Large (500k+)</option>
          <option value="none">Hide</option>
        </select>
      </div>
      <div class="help-box">
        <strong>How to use:</strong><br>
        Click any district or city to load its data panel.<br>
        Use <strong>5-Yr Forecast</strong> tab for ML price predictions.<br>
        Year slider replays price history 2015&ndash;2024.<br>
        Enter your salary for a personalised calculator.
      </div>
    </div>

    <!-- DATA PANEL TAB -->
    <div id="panel-pane">
      <div class="hint">Click a region, district,<br>or city to explore its data</div>
    </div>

    <!-- FORECAST TAB -->
    <div id="forecast-pane">
      <div class="fc-header">
        <div class="fc-title">5-Year ML Price Forecast (2025-2029)</div>
        <div class="fc-sub">
          Gradient Boosting | {CV_FOLDS}-fold CV
          {f'| R&sup2;={metrics.get("r2_mean","?")} &plusmn; {metrics.get("r2_std","?")}' if metrics.get("r2_mean") else ''}
          {f'| MAE: GBP{metrics.get("mae_mean","?"):,}' if metrics.get("mae_mean") else ''}
          <br>90% CI | Mean-reverting momentum | Real-terms prices (CPIH-adjusted)
        </div>
      </div>

      <div class="ctrl-group">
        <span class="ctrl-label">Region</span>
        <select id="fc-region" onchange="onFcRegionChange()">
          {region_opts}
        </select>
      </div>
      <div class="ctrl-group">
        <span class="ctrl-label">Property type</span>
        <select id="fc-proptype" onchange="updateForecast()">
          <option value="Semi-Detached">Semi-Detached</option>
          <option value="Detached">Detached</option>
          <option value="Terraced">Terraced</option>
          <option value="Flat">Flat</option>
        </select>
      </div>

      <div class="fc-metric-grid" id="fc-kpis"></div>

      <div class="fc-section">
        <div class="fc-sec-title">Price 2015-2029 (nominal &amp; real-terms)</div>
        <div style="height:200px"><canvas id="price-chart"></canvas></div>
      </div>

      <div class="fc-section">
        <div class="fc-sec-title">Intergenerational gap 2024-2029 (years to save)</div>
        <div style="height:180px"><canvas id="gap-chart"></canvas></div>
      </div>

      <div class="fc-section">
        <div class="fc-sec-title">All cohorts: years to save by year</div>
        <div style="height:180px"><canvas id="cohort-chart"></canvas></div>
      </div>

      <div class="fc-section">
        <div class="fc-sec-title">Forecast detail</div>
        <table>
          <thead><tr><th>Year</th><th>Price</th><th>Change</th>
            <th>90% CI</th><th>Real (2024 GBP)</th>
            <th>Ratio</th><th>Gen Z yrs</th></tr></thead>
          <tbody id="fc-tbody"></tbody>
        </table>
      </div>

      {'<div class="model-info"><strong>Feature importances:</strong><br>' + '<br>'.join(f'{k}: {v:.3f}' for k,v in sorted(metrics.get("importance",{}).items(),key=lambda x:-x[1])[:6]) + '</div>' if metrics.get("importance") else ''}

      <div class="src" style="padding:8px">
        HM Land Registry HPI 2015-2024 | ONS GDHI 2023 | ONS WAS Wave 7 |
        ONS CPIH 2024 | Gradient Boosting (scikit-learn) | Joseph Richards 2026
      </div>
    </div>
  </div>

  <div style="position:relative;flex:1">
    <div id="map" style="width:100%;height:100%"></div>
    <div id="year-badge">2024</div>
    <div id="legend">
      <strong style="font-size:10px;color:#1a1a18">Affordability ratio</strong>
      <div id="legend-bar"></div>
      <div id="legend-ticks"><span>3x</span><span>9x</span><span>35x</span></div>
      <div style="margin-top:3px;color:#b0ada6;font-size:9px">Median price / median earnings</div>
    </div>
  </div>
</div>
<script>
{js_data}
{JS_PANEL}
{JS_FORECAST}
</script>
</body>
</html>"""

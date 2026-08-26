"""
panels.py
=========
JavaScript source for all panel section builders and dashboard logic.
Extended with ML forecast panel and user evaluation form integration.
"""

JS = r"""
// ---- Utilities ----
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

function calcSDLT(price,isFTB){
  if(isFTB&&price>625000)isFTB=false;
  const bands=isFTB?[[0,425000,0],[425000,625000,.05]]:
    [[0,250000,0],[250000,925000,.05],[925000,1500000,.10],[1500000,99999999,.12]];
  let tax=0,rows=[];
  for(const[lo,hi,rate]of bands){
    if(price<=lo)break;
    const amt=(Math.min(price,hi)-lo)*rate;
    tax+=amt;
    rows.push({band:'\u00a3'+fmt(lo)+'-\u00a3'+fmt(hi),rate:(rate*100).toFixed(0)+'%',amount:amt});
  }
  return{total:tax,rows};
}

// ---- Sparkline ----
function buildSparkline(region,yearIdx){
  const trend=HPI_TREND[region];
  if(!trend)return'';
  const base=(HPI[region]||{})['Semi-Detached']||200000;
  const prices=trend.map(i=>(i/100)*base);
  const mn=Math.min(...prices),mx=Math.max(...prices);
  const W=310,H=58,p=4;
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
      <circle cx="${xs[yearIdx].toFixed(1)}" cy="${ys[yearIdx].toFixed(1)}" r="4" fill="#2a78d6" stroke="#fff" stroke-width="1.5"/>
    </svg>
    <div class="spark-footer">
      <span>\u00a3${fmt(prices[0])} (2015)</span>
      <span style="color:#2a78d6;font-weight:600">+${pct}% since 2015</span>
      <span>\u00a3${fmt(prices[9])} (2024)</span>
    </div>
  </div>`;
}

// ---- ML Forecast panel ----
function buildMLForecast(region,prop){
  const rf=ML_FORECASTS[region];
  if(!rf||!rf[prop])return'';
  const years=['2025','2026','2027'];
  const preds=years.map(y=>rf[prop][y]);
  if(!preds[0])return'';
  const maxP=Math.max(...preds.map(p=>p.high))*1.05;
  const bars=years.map((y,i)=>{
    const d=preds[i];
    const predPct=(d.pred/maxP*100).toFixed(1);
    const lowPct=(d.low/maxP*100).toFixed(1);
    const highPct=(d.high/maxP*100).toFixed(1);
    return`<div class="ml-row">
      <span class="ml-yr">${y}</span>
      <div class="ml-bar-outer">
        <div class="ml-ci" style="left:${lowPct}%;width:${(highPct-lowPct)}%"></div>
        <div class="ml-pred" style="left:${predPct}%"></div>
      </div>
      <span class="ml-val">\u00a3${fmt(d.pred)}</span>
    </div>`;
  }).join('');
  const m=ML_METRICS;
  const metricStr=m&&m.r2?`R\u00b2=${m.r2} | MAE=\u00a3${fmt(m.mae)} | RMSE=\u00a3${fmt(m.rmse)}`:'';
  return`<div class="sec-hdr">ML price forecast 2025-2027 (Gradient Boosting)</div>
  <div style="font-size:10px;color:#6b6966;margin-bottom:6px">
    Central prediction with 10% confidence interval &middot; ${prop}
  </div>
  ${bars}
  ${metricStr?`<div class="ml-metrics">${metricStr}</div>`:''}
  <div style="font-size:9px;color:#b0ada6;margin-top:4px">
    Assumes 3% annual price growth, 2.5% income growth prior &middot; Not financial advice
  </div>`;
}

// ---- FTB vs All buyers ----
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

// ---- Cohort bars ----
function buildCohortBars(price,income,dep){
  return COHORTS.map(c=>{
    const y=(price*dep)/(income*c.rate),pct=Math.min(100,(y/40)*100).toFixed(1);
    return`<div class="cohort-row"><span class="c-name">${c.label}</span>
      <div class="c-bar"><div class="c-fill" style="width:${pct}%;background:${c.color}"></div></div>
      <span class="c-yrs">${y.toFixed(1)} yrs</span></div>`;
  }).join('');
}

// ---- Deposit gap ----
function buildDepositGap(price,income,dep){
  const needed=price*dep;
  return COHORTS.map(c=>{
    const saved=income*c.rate*5,gap=Math.max(0,needed-saved);
    const pct=Math.min(100,(saved/needed)*100).toFixed(0);
    return`<div class="cohort-row"><span class="c-name">${c.label}</span>
      <div class="c-bar"><div class="c-fill" style="width:${pct}%;background:${c.color}"></div></div>
      <span class="c-yrs">${pct}%</span></div>
      <div class="gap-note">${gap>0?'Gap: \u00a3'+fmt(gap):'Sufficient after 5 yrs'}</div>`;
  }).join('');
}

// ---- Stamp duty ----
function buildSDLT(price){
  const std=calcSDLT(price,false),ftb=calcSDLT(price,true),saving=std.total-ftb.total;
  const rows=std.rows.map(r=>`<div class="sdlt-row"><span class="sdlt-band">${r.band} @ ${r.rate}</span><span class="sdlt-amt">\u00a3${fmt(r.amount)}</span></div>`).join('');
  return`<div class="sec-hdr">Stamp duty (England 2024)</div>${rows}
  <div class="sdlt-total"><span>Standard buyer</span><span>\u00a3${fmt(std.total)}</span></div>
  <div class="ftb-sdlt">First-time buyer: \u00a3${fmt(ftb.total)} ${saving>0?'(saving \u00a3'+fmt(saving)+')':'(no relief at this price)'}</div>
  ${price>625000?'<div class="sdlt-warn">Above \u00a3625k FTB cap - standard rates apply</div>':''}`;
}

// ---- Rent vs buy ----
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
  <div class="rvb-row"><span>Rent as % of income</span><span>${rp}%</span></div>
  <div class="rvb-row"><span>Mortgage as % of income</span><span>${mp}%</span></div>
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
  const t=HPI_TREND[region];
  return t?base*(t[yearIdx]/t[9]):base;
}

function applyStyle(f){
  const reg=f.properties.region||'',d=getLAD(f.properties.name);
  const base=d?d.ratio:(REGIONAL[reg]||{}).ratio||7;
  const hidden=document.getElementById('sel-region').value!=='all'&&
               document.getElementById('sel-region').value!==reg;
  return{fillColor:ratioColor(getYearRatio(reg,base)),weight:hidden?.2:.5,
         opacity:1,color:'#fff',fillOpacity:hidden?.05:.75};
}

// ---- Main panel renderer ----
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
      <div class="kpi"><div class="kpi-l">Rent as % of income</div>
        <div class="kpi-v">${rd.rent_pct||'N/A'}%</div>
        <div class="kpi-s">ONS private rental 2024</div></div>
    </div>
    ${buildSparkline(region,yearIdx)}
    ${buildMLForecast(region,prop)}
    ${buildFTBBar(region)}
    <div class="sec-hdr">Years to save ${Math.round(depositPct*100)}% deposit - ${prop}</div>
    ${buildCohortBars(usePrice,income,depositPct)}
    <div class="sec-hdr">Deposit gap after 5 years saving</div>
    <div style="font-size:10px;color:#6b6966;margin-bottom:6px">% of \u00a3${fmt(deposit)} saved after 5 years</div>
    ${buildDepositGap(usePrice,income,depositPct)}
    ${buildSDLT(usePrice)}
    ${buildRentVsBuy(region,usePrice,income,depositPct)}
    <div class="src">ONS Housing Affordability 2023 &middot; HM Land Registry HPI &middot;
      ONS GDHI 2023 &middot; ONS WAS Wave 7 &middot; Resolution Foundation 2023 &middot;
      ONS Private Rental 2024 &middot; Savills 2024 &middot; ML: Gradient Boosting (Joe Richards 2026)</div>`;
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
    const dot=L.divIcon({html:'<div style="width:10px;height:10px;background:#1a3a6b;border-radius:50%;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.4)"></div>',className:'',iconSize:[10,10],iconAnchor:[5,5]});
    const m=L.marker([city.lat,city.lng],{icon:dot});
    m.bindTooltip(`<div class="popup-name">${city.name}</div>
      <div class="popup-r" style="color:${ratioColor(rd.ratio||7)}">${rd.ratio||7}x</div>
      <div>Pop: ${(city.pop/1000).toFixed(0)}k &middot; \u00a3${fmt(rd.income||0)}/yr</div>`,{opacity:.95});
    m.on('click',()=>showPanel(city.name,city.region,rd.ratio,
      (HPI[city.region]||{})['Semi-Detached']||(rd.ratio||7)*(rd.income||29000)));
    const lbl=L.marker([city.lat,city.lng],{icon:L.divIcon({
      html:`<div style="font-size:9px;font-weight:600;color:#1a3a6b;text-shadow:0 0 3px #fff;white-space:nowrap;transform:translate(8px,-4px)">${city.name}</div>`,
      className:'',iconSize:[0,0]})});
    cityGroup.addLayer(m);cityGroup.addLayer(lbl);
  });
}
buildCities('all');

// ---- Controls ----
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
  refreshPanel();
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
  if(v>0){personalIncome=v;refreshPanel();}
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
    t.classList.toggle('active',t.textContent.toLowerCase().replace(' ','').includes(tab.replace(' ',''))));
  ['filters-pane','panel-pane','eval-pane'].forEach(id=>{
    const el=document.getElementById(id);
    if(el)el.style.display='none';
  });
  const target=document.getElementById(tab+'-pane')||document.getElementById('eval-pane');
  if(target)target.style.display=tab==='filters'?'flex':'block';
}

// ---- Evaluation form submission ----
async function submitEval(){
  const form=document.getElementById('eval-form');
  const data={};
  new FormData(form).forEach((v,k)=>{data[k]=v;});
  document.querySelectorAll('textarea[name]').forEach(el=>{
    if(el.value.trim())data[el.name]=el.value.trim();
  });
  const msg=document.getElementById('eval-msg');
  try{
    const resp=await fetch('/save_evaluation',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(data)
    });
    if(resp.ok){
      const r=await resp.json();
      msg.textContent='Response '+r.id+' saved. Thank you!';
      msg.style.color='#0f6e56';
    } else {
      // Fallback: download as JSON file
      downloadEval(data);
    }
  }catch{
    downloadEval(data);
  }
}

function downloadEval(data){
  data._timestamp=new Date().toISOString();
  const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  a.download='evaluation_response_'+Date.now()+'.json';
  a.click();
  const msg=document.getElementById('eval-msg');
  msg.textContent='Downloaded as JSON - send this file to the researcher.';
  msg.style.color='#2a78d6';
}

document.getElementById('filters-pane').style.display='flex';
document.getElementById('panel-pane').style.display='none';
"""

# ---------------------------------------------------------------------------
# EXTRA JS - appended after main JS block
# Postcode search, year animation, PDF export, accessibility, feature importance
# ---------------------------------------------------------------------------

JS_EXTRAS = r"""
// ---- Postcode search ----
async function searchPostcode(){
  const pc=document.getElementById('postcode-input').value.trim();
  if(!pc)return;
  const msg=document.getElementById('pc-msg');
  msg.textContent='Looking up...';
  try{
    const r=await fetch('https://api.postcodes.io/postcodes/'+encodeURIComponent(pc));
    const d=await r.json();
    if(d.status!==200){msg.textContent='Postcode not found.';return;}
    const res=d.result;
    map.setView([res.latitude,res.longitude],12);
    L.popup().setLatLng([res.latitude,res.longitude])
      .setContent('<strong>'+res.postcode+'</strong><br>'+res.admin_district)
      .openOn(map);
    msg.textContent='';
    if(ladLayer){
      ladLayer.eachLayer(l=>{
        if(l.getBounds&&l.getBounds().contains([res.latitude,res.longitude])){
          l.fire('click');
        }
      });
    }
  }catch(e){msg.textContent='Lookup failed - check connection.';}
}

// ---- Year animation (play/pause) ----
let animTimer=null;
function toggleAnimation(){
  const btn=document.getElementById('anim-btn');
  if(animTimer){
    clearInterval(animTimer);animTimer=null;
    btn.textContent='Play';return;
  }
  btn.textContent='Pause';
  animTimer=setInterval(()=>{
    const slider=document.getElementById('sel-year');
    let v=parseInt(slider.value);
    if(v>=9){clearInterval(animTimer);animTimer=null;btn.textContent='Play';return;}
    slider.value=v+1;
    onYearChange(v+1);
  },800);
}

// ---- PDF export ----
function exportPDF(){
  const panel=document.getElementById('panel-pane');
  const original=document.body.innerHTML;
  const printContent=`
    <style>
      body{font-family:Arial,sans-serif;font-size:12pt;color:#000;margin:2cm}
      .kpi-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px}
      .kpi{border:1px solid #ccc;padding:8px;border-radius:4px}
      .kpi-l{font-size:9pt;color:#666;text-transform:uppercase}
      .kpi-v{font-size:16pt;font-weight:bold}
      .sec-hdr{font-size:9pt;font-weight:bold;color:#666;text-transform:uppercase;
               border-top:1px solid #ccc;margin-top:12px;padding-top:8px}
      .cohort-row{display:flex;gap:8px;margin-bottom:4px;align-items:center}
      .c-name{width:130px}.c-yrs{width:50px;text-align:right;font-weight:bold}
      .c-bar{flex:1;height:10px;background:#eee}
      .sdlt-row,.rvb-row{display:flex;justify-content:space-between;
                          padding:3px 0;border-bottom:1px solid #eee;font-size:10pt}
      .sdlt-total,.verdict{padding:6px;font-weight:bold}
      @media print{button,select,input{display:none}}
    </style>
    <h2>UK Housing Affordability Dashboard</h2>
    <p>MSc Big Data with Banking and Finance - Sheffield Hallam University - Joseph Richards 2026</p>
    <hr>
    ${panel.innerHTML}
  `;
  const w=window.open('','_blank');
  w.document.write(printContent);
  w.document.close();
  w.focus();
  setTimeout(()=>{w.print();},500);
}

// ---- Colour-blind mode toggle ----
let cbMode=false;
function toggleColourBlind(){
  cbMode=!cbMode;
  document.getElementById('cb-btn').textContent=cbMode?'Standard colours':'Colour-blind mode';
  if(ladLayer)ladLayer.eachLayer(l=>{if(l.feature)ladLayer.resetStyle(l);});
}

function ratioColorCB(r){
  if(!cbMode)return ratioColor(r);
  // Blue-orange diverging palette (Okabe-Ito, colour-blind safe)
  if(!r||isNaN(r))return'#cccccc';
  const stops=[[3,'#0072B2'],[8,'#F0E442'],[15,'#E69F00'],[35,'#D55E00']];
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

// Override applyStyle to use CB-aware colour
const _origApplyStyle=applyStyle;
function applyStyle(f){
  const s=_origApplyStyle(f);
  if(cbMode){
    const reg=f.properties.region||'',d=getLAD(f.properties.name);
    const base=d?d.ratio:(REGIONAL[reg]||{}).ratio||7;
    s.fillColor=ratioColorCB(getYearRatio(reg,base));
  }
  return s;
}

// ---- Feature importance chart in panel ----
function buildFeatureImportance(metrics){
  if(!metrics||!metrics.importance)return'';
  const imp=metrics.importance;
  const entries=Object.entries(imp).sort((a,b)=>b[1]-a[1]);
  const maxV=entries[0][1];
  const rows=entries.map(([k,v])=>`
    <div class="cohort-row">
      <span class="c-name" style="font-size:10px">${k}</span>
      <div class="c-bar"><div class="c-fill"
        style="width:${(v/maxV*100).toFixed(1)}%;background:#2a78d6"></div></div>
      <span class="c-yrs" style="font-size:10px">${(v*100).toFixed(1)}%</span>
    </div>`).join('');
  return`<div class="sec-hdr">Feature importance (Gradient Boosting)</div>${rows}`;
}

// ---- Evaluation summary auto-trigger ----
function checkEvalCount(){
  const badge=document.getElementById('eval-count-badge');
  if(!badge)return;
  // Count is injected server-side; just show it
}
"""

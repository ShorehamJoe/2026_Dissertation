"""
styles.py
=========
CSS stylesheet for the dashboard. Extended with ML forecast and evaluation form styles.
"""

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f0efeb;color:#1a1a18;font-size:13px;height:100vh;display:flex;flex-direction:column;overflow:hidden}
header{background:#1a3a6b;color:#fff;padding:10px 18px;display:flex;align-items:center;gap:12px;flex-shrink:0}
header h1{font-size:14px;font-weight:500}
header p{font-size:10px;opacity:.7;margin-top:1px}
.data-badge{font-size:9px;padding:2px 7px;border-radius:3px;margin-left:8px;font-weight:600}
.badge-live{background:#1baf7a;color:#fff}
.badge-embedded{background:#888780;color:#fff}
#app{display:flex;flex:1;overflow:hidden}
#sidebar{width:360px;flex-shrink:0;background:#fff;border-right:1px solid #e2e0d8;display:flex;flex-direction:column;overflow:hidden}
#tabs{display:flex;border-bottom:1px solid #e2e0d8;flex-shrink:0}
.tab{flex:1;padding:8px 2px;text-align:center;font-size:11px;font-weight:500;color:#6b6966;cursor:pointer;border-bottom:2px solid transparent;transition:.15s}
.tab.active{color:#1a3a6b;border-bottom-color:#1a3a6b}
.tab-pane{display:none;padding:12px;overflow-y:auto;flex:1}
.tab-pane.active{display:flex;flex-direction:column;gap:8px}
#panel-pane,#eval-pane{overflow-y:auto;flex:1;padding:12px}
.ctrl-label{font-size:10px;color:#6b6966;font-weight:600;text-transform:uppercase;letter-spacing:.04em;display:block;margin-bottom:4px}
.ctrl-group{margin-bottom:10px}
select{width:100%;padding:6px 8px;font-size:12px;border:1px solid #e2e0d8;border-radius:6px;background:#fff}
.slider-row{display:flex;align-items:center;gap:8px}
.slider-row input{flex:1}
.sval{font-size:12px;font-weight:600;min-width:40px;text-align:right;color:#1a3a6b}
.income-row{display:flex;gap:6px}
.income-row input[type=number]{flex:1;padding:6px 8px;font-size:12px;border:1px solid #e2e0d8;border-radius:6px}
.income-row button{padding:6px 12px;font-size:11px;background:#1a3a6b;color:#fff;border:none;border-radius:6px;cursor:pointer}
.help-box{background:#e8eef8;border-radius:8px;padding:10px;font-size:11px;color:#1a3a6b;line-height:1.6}
.hint{color:#b0ada6;text-align:center;padding:30px 10px;font-size:12px;line-height:1.7}
.rname{font-size:17px;font-weight:700;color:#1a3a6b;margin-bottom:4px}
.rtag{display:inline-block;background:#e8eef8;color:#1a3a6b;font-size:10px;padding:2px 7px;border-radius:4px;margin-bottom:10px}
.kpi-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:12px}
.kpi{background:#f8f7f4;border-radius:6px;padding:7px 9px}
.kpi-l{font-size:9px;color:#6b6966;margin-bottom:1px;text-transform:uppercase;letter-spacing:.03em}
.kpi-v{font-size:16px;font-weight:700}
.kpi-s{font-size:9px;color:#b0ada6;margin-top:1px}
.sec-hdr{font-size:10px;font-weight:700;color:#6b6966;text-transform:uppercase;letter-spacing:.04em;margin:12px 0 6px;border-top:1px solid #e8e6e0;padding-top:10px}
.spark-wrap{background:#f8f7f4;border-radius:6px;padding:8px;margin-bottom:4px}
.spark-wrap svg{width:100%;height:58px;display:block}
.spark-footer{display:flex;justify-content:space-between;font-size:9px;color:#6b6966;margin-top:2px}
.ml-row{display:flex;align-items:center;gap:8px;margin-bottom:6px}
.ml-yr{font-size:11px;font-weight:600;width:32px;color:#1a3a6b;flex-shrink:0}
.ml-bar-outer{flex:1;height:16px;background:#eeecea;border-radius:3px;position:relative;overflow:hidden}
.ml-ci{position:absolute;top:0;height:100%;background:rgba(42,120,214,.2);border-radius:3px}
.ml-pred{position:absolute;top:2px;height:12px;width:3px;background:#2a78d6;border-radius:2px;transform:translateX(-50%)}
.ml-val{font-size:11px;font-weight:600;width:80px;text-align:right;flex-shrink:0}
.ml-metrics{font-size:9px;color:#6b6966;margin-top:4px;background:#f0efeb;padding:4px 6px;border-radius:4px}
.ftb-row{display:flex;align-items:center;gap:6px;margin-bottom:5px}
.ftb-lbl{font-size:11px;width:72px;flex-shrink:0}
.ftb-outer{flex:1;background:#eeecea;border-radius:3px;height:14px;overflow:hidden}
.ftb-inner{height:100%;border-radius:3px}
.ftb-val{font-size:11px;font-weight:600;width:70px;text-align:right;flex-shrink:0}
.note{font-size:10px;color:#1baf7a;margin-top:2px;margin-bottom:4px}
.cohort-row{display:flex;align-items:center;gap:6px;margin-bottom:5px}
.c-name{font-size:11px;width:125px;flex-shrink:0}
.c-bar{flex:1;background:#eeecea;border-radius:3px;height:12px;overflow:hidden}
.c-fill{height:100%;border-radius:3px;transition:width .4s ease}
.c-yrs{font-size:11px;font-weight:700;width:42px;text-align:right;flex-shrink:0}
.gap-note{font-size:10px;color:#e34948;margin-top:-3px;margin-bottom:4px;padding-left:131px}
.sdlt-row{display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #f0efeb;font-size:11px}
.sdlt-band{color:#6b6966}
.sdlt-amt{font-weight:600}
.sdlt-total{display:flex;justify-content:space-between;background:#1a3a6b;color:#fff;padding:6px 8px;border-radius:4px;margin-top:4px;font-size:12px;font-weight:600}
.ftb-sdlt{margin-top:5px;padding:6px 8px;background:#e8f5ee;border-radius:4px;font-size:10px;color:#0f6e56}
.sdlt-warn{font-size:10px;color:#e34948;margin-top:4px}
.rvb-row{display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #f0efeb;font-size:11px}
.rvb-row span:first-child{color:#6b6966}
.rvb-row span:last-child{font-weight:600}
.verdict{margin-top:8px;padding:7px;border-radius:6px;font-size:11px;font-weight:500;text-align:center}
.src{margin-top:12px;font-size:9px;color:#c0bdb6;border-top:1px solid #e8e6e0;padding-top:8px;line-height:1.6}
#year-badge{position:absolute;top:10px;right:10px;z-index:999;background:rgba(26,58,107,.9);color:#fff;padding:5px 10px;border-radius:6px;font-size:12px;font-weight:600;pointer-events:none}
#legend{position:absolute;bottom:24px;left:4px;z-index:999;background:rgba(255,255,255,.93);border-radius:8px;padding:8px 12px;font-size:10px;color:#6b6966;box-shadow:0 1px 6px rgba(0,0,0,.15);min-width:165px}
#legend-bar{height:9px;border-radius:3px;margin:4px 0;background:linear-gradient(to right,#1baf7a,#a8d150,#eda100,#eb6834,#e34948)}
#legend-ticks{display:flex;justify-content:space-between;font-size:9px}
.leaflet-popup-content-wrapper{border-radius:8px!important}
.leaflet-popup-content{margin:10px 12px!important;font-size:12px}
.popup-name{font-weight:700;font-size:14px;color:#1a3a6b;margin-bottom:3px}
.popup-r{font-size:18px;font-weight:700}
.eval-header{background:#e8eef8;border-radius:8px;padding:12px;margin-bottom:12px}
.eval-title{font-size:14px;font-weight:700;color:#1a3a6b;margin-bottom:4px}
.eval-sub{font-size:11px;color:#6b6966;line-height:1.5}
.eval-section{margin-bottom:14px}
.eval-sec-hdr{font-size:10px;font-weight:700;color:#1a3a6b;text-transform:uppercase;letter-spacing:.05em;padding:6px 0 4px;border-bottom:1px solid #e2e0d8;margin-bottom:8px}
.eval-q{margin-bottom:10px}
.eval-q-text{font-size:12px;color:#1a1a18;margin-bottom:5px;line-height:1.4}
.eval-opt{display:flex;align-items:center;gap:6px;font-size:12px;color:#6b6966;margin-bottom:3px;cursor:pointer}
.eval-opt:hover{color:#1a1a18}
.eval-scale-wrap{display:flex;align-items:center;gap:6px}
.eval-anchor{font-size:10px;color:#b0ada6;flex-shrink:0;max-width:70px}
.eval-num{display:flex;flex-direction:column;align-items:center;font-size:11px;color:#6b6966;gap:2px;cursor:pointer}
.eval-textarea{width:100%;padding:6px 8px;font-size:12px;border:1px solid #e2e0d8;border-radius:6px;resize:vertical;font-family:inherit;color:#1a1a18}
.eval-submit-row{margin-top:14px;display:flex;flex-direction:column;gap:8px}
.eval-submit{padding:9px;background:#1a3a6b;color:#fff;border:none;border-radius:6px;font-size:13px;font-weight:600;cursor:pointer;width:100%}
.eval-submit:hover{background:#2a4a8b}
.eval-msg{font-size:11px;text-align:center}
"""

# -- Header buttons (appended)
CSS += """
.hdr-btn{padding:5px 10px;font-size:11px;background:rgba(255,255,255,.15);
          color:#fff;border:1px solid rgba(255,255,255,.3);border-radius:5px;
          cursor:pointer;white-space:nowrap}
.hdr-btn:hover{background:rgba(255,255,255,.25)}
"""

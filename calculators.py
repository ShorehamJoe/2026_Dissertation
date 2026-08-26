"""
calculators.py - Stamp duty calculator (England/Wales/Scotland 2024).

>>> calc_sdlt(300_000, False, 'SDLT')[0]
2500.0
>>> calc_sdlt(300_000, True,  'SDLT')[0]
0.0
>>> calc_sdlt(500_000, False, 'SDLT')[0]
12500.0
"""
from uk_housing_dashboard.config import SDLT_STANDARD_BANDS, SDLT_FTB_BANDS, SDLT_FTB_CAP

LTT_STANDARD  = [(0,225000,0.0),(225000,400000,0.06),(400000,750000,0.075),(750000,1500000,0.10),(1500000,99999999,0.12)]
LBTT_STANDARD = [(0,145000,0.0),(145000,250000,0.02),(250000,325000,0.05),(325000,750000,0.10),(750000,99999999,0.12)]
LBTT_FTB      = [(0,175000,0.0),(175000,250000,0.02),(250000,325000,0.05),(325000,750000,0.10),(750000,99999999,0.12)]

JURISDICTION  = {
    "Wales":"LTT","Scotland":"LBTT","Northern Ireland":"SDLT",
    **{r:"SDLT" for r in ["London","South East","East of England","South West",
                           "West Midlands","East Midlands","Yorkshire and The Humber",
                           "North West","North East","East Midlands"]},
}

def calc_sdlt(price, is_ftb=False, jurisdiction="SDLT"):
    """Returns (total, rows) for stamp duty / LTT / LBTT."""
    jur = jurisdiction.upper()
    if jur == "SDLT":
        if is_ftb and price > SDLT_FTB_CAP: is_ftb = False
        bands = SDLT_FTB_BANDS if is_ftb else SDLT_STANDARD_BANDS
    elif jur == "LTT":
        bands = LTT_STANDARD
    elif jur == "LBTT":
        bands = LBTT_FTB if is_ftb else LBTT_STANDARD
    else:
        bands = SDLT_STANDARD_BANDS

    total, rows = 0.0, []
    for lo, hi, rate in bands:
        if price <= lo: break
        amt = (min(price, hi) - lo) * rate
        total += amt
        rows.append({"band": f"GBP{lo:,}-GBP{hi:,}", "rate": f"{rate*100:.0f}%", "amount": amt})
    return total, rows

def get_jurisdiction(region):
    return JURISDICTION.get(region, "SDLT")

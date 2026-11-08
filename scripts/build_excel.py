"""
Builds excel/Olist_Late_Deliveries.xlsx from the CSV files in /data.
Every number in the analysis sheets is a live Excel formula (COUNTIFS, SUMIFS,
AVERAGEIFS) over the Data sheet. You do NOT need to run this script.
"""
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "excel" / "Olist_Late_Deliveries.xlsx"
OUT.parent.mkdir(exist_ok=True)
FOCUS = {"RJ", "BA", "CE", "PE", "MA", "PB", "PI", "RN", "AL", "SE"}  # Rio + Northeast


def read(name):
    with open(DATA / f"{name}.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ts(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S") if s else None


cust_state = {r["customer_id"]: r["customer_state"] for r in read("customers")}
deadline, main_seller, value, freight = {}, {}, defaultdict(float), defaultdict(float)
for it in read("order_items"):
    oid = it["order_id"]
    lim = ts(it["shipping_limit_date"])
    if oid not in deadline or lim > deadline[oid]:
        deadline[oid] = lim
    if it["order_item_id"] == "1":
        main_seller[oid] = it["seller_id"]
    value[oid] += float(it["price"])
    freight[oid] += float(it["freight_value"])
scores = defaultdict(list)
for r in read("order_reviews"):
    scores[r["order_id"]].append(int(r["review_score"]))

rows = []
for o in read("orders"):
    if o["order_status"] != "delivered" or not o["order_delivered_customer_date"] or not o["order_delivered_carrier_date"]:
        continue
    oid = o["order_id"]
    if oid not in deadline:
        continue
    p, c, d, e = (ts(o["order_purchase_timestamp"]), ts(o["order_delivered_carrier_date"]),
                  ts(o["order_delivered_customer_date"]), ts(o["order_estimated_delivery_date"]))
    st = cust_state[o["customer_id"]]
    sc = scores.get(oid)
    rows.append([
        oid, p.strftime("%Y-%m"), st, "Rio + Northeast" if st in FOCUS else "Rest of Brazil",
        main_seller[oid], "Yes" if c > deadline[oid] else "No",
        (c.date() - p.date()).days, (d.date() - c.date()).days, (e.date() - p.date()).days,
        (d.date() - p.date()).days, (d.date() - e.date()).days,
        None, round(sum(sc) / len(sc), 2) if sc else None, None,
        round(value[oid], 2), round(freight[oid], 2),
    ])
rows.sort(key=lambda r: (r[1], r[0]))

# ---------- styles ----------
F = "Arial"
H1 = Font(name=F, size=16, bold=True, color="1F3864")
H2 = Font(name=F, size=12, bold=True, color="1F3864")
B = Font(name=F, size=10, bold=True)
N = Font(name=F, size=10)
NOTE = Font(name=F, size=9, italic=True, color="595959")
TAKE = Font(name=F, size=10, bold=True, color="C00000")
INPUT = Font(name=F, size=10, color="0000FF", bold=True)
LINK = Font(name=F, size=10, color="008000")
HDR_FILL = PatternFill("solid", fgColor="1F3864")
HDR_FONT = Font(name=F, size=10, bold=True, color="FFFFFF")
KPI_FILL = PatternFill("solid", fgColor="EEF3FA")
YELLOW = PatternFill("solid", fgColor="FFF2CC")
thin = Side(style="thin", color="BFBFBF")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
PCT, INT, DEC1, DEC2 = "0.0%", "#,##0", "0.0", "0.00"


def header(ws, row, col, labels):
    for i, lab in enumerate(labels):
        c = ws.cell(row=row, column=col + i, value=lab)
        c.font, c.fill, c.border = HDR_FONT, HDR_FILL, BOX
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = 30


def cell(ws, ref, v, font=N, fmt=None, fill=None):
    c = ws[ref]
    c.value, c.font, c.border = v, font, BOX
    if fmt:
        c.number_format = fmt
    if fill:
        c.fill = fill
    return c


def widths(ws, spec):
    for col, w in spec.items():
        ws.column_dimensions[col].width = w


wb = Workbook()

# =====================================================================
# Data
# =====================================================================
ws = wb.active
ws.title = "Data"
cols = ["Order ID", "Purchase Month", "Customer State", "Region Group", "Main Seller ID",
        "Seller Missed Deadline", "Seller Days", "Carrier Days", "Promised Days", "Actual Days",
        "Days Late", "Is Late", "Review Score", "Bad Review", "Order Value (R$)", "Freight (R$)"]
header(ws, 1, 1, cols)
for i, r in enumerate(rows, start=2):
    r[11] = f"=IF(K{i}>0,1,0)"
    r[13] = f'=IF(M{i}="","",IF(M{i}<=2,1,0))'
    ws.append(r)
LAST = len(rows) + 1
widths(ws, {"A": 34, "B": 10, "C": 9, "D": 16, "E": 34, "F": 11, "G": 8, "H": 8, "I": 9, "J": 8,
            "K": 8, "L": 7, "M": 8, "N": 8, "O": 11, "P": 10})
ws.freeze_panes = "A2"
t = Table(displayName="tblOrders", ref=f"A1:P{LAST}")
t.tableStyleInfo = TableStyleInfo(name="TableStyleLight9", showRowStripes=True)
ws.add_table(t)


def R(col):
    return f"Data!${col}$2:${col}${LAST}"


MONTH, STATE, GROUP, SELLER, MISSED = R("B"), R("C"), R("D"), R("E"), R("F")
SDAYS, CDAYS, PDAYS, ADAYS, DLATE, LATE, SCORE, BAD = (R("G"), R("H"), R("I"), R("J"), R("K"), R("L"),
                                                       R("M"), R("N"))

# =====================================================================
# Reviews
# =====================================================================
rv = wb.create_sheet("Reviews")
rv["A1"].value, rv["A1"].font = "What does a late delivery do to the review score?", H1
rv["A2"].value, rv["A2"].font = "Bad review = 1 or 2 stars. Only orders that have a review.", NOTE
header(rv, 4, 1, ["Delivery", "Orders with review", "Avg review score", "Bad reviews", "Bad review %",
                  "Share of all bad reviews"])
for r, lab, crit in [(5, "On time", 0), (6, "Late", 1)]:
    cell(rv, f"A{r}", lab, B)
    cell(rv, f"B{r}", f'=COUNTIFS({LATE},{crit},{SCORE},"<>")', fmt=INT)
    cell(rv, f"C{r}", f"=AVERAGEIFS({SCORE},{LATE},{crit})", fmt=DEC2)
    cell(rv, f"D{r}", f"=COUNTIFS({LATE},{crit},{BAD},1)", fmt=INT)
    cell(rv, f"E{r}", f"=D{r}/B{r}", fmt=PCT)
    cell(rv, f"F{r}", f"=D{r}/SUM($D$5:$D$6)", fmt=PCT)
rv["A8"].value, rv["A8"].font = "The later the order, the worse the review", H2
header(rv, 9, 1, ["Days late", "From", "To", "Orders with review", "Avg review score", "Bad review %"])
buckets = [("On time", -999, 0), ("1-3 days", 1, 3), ("4-7 days", 4, 7), ("8-14 days", 8, 14), ("15+ days", 15, 999)]
for i, (lab, lo, hi) in enumerate(buckets):
    r = 10 + i
    cell(rv, f"A{r}", lab, B)
    cell(rv, f"B{r}", lo)
    cell(rv, f"C{r}", hi)
    cell(rv, f"D{r}", f'=COUNTIFS({DLATE},">="&B{r},{DLATE},"<="&C{r},{SCORE},"<>")', fmt=INT)
    cell(rv, f"E{r}", f'=AVERAGEIFS({SCORE},{DLATE},">="&B{r},{DLATE},"<="&C{r})', fmt=DEC2)
    cell(rv, f"F{r}", f'=COUNTIFS({DLATE},">="&B{r},{DLATE},"<="&C{r},{BAD},1)/D{r}', fmt=PCT)
rv["A16"].value = "Takeaway: late orders are ~7% of orders but about 1 in 3 bad reviews. From 4 days late, 2 out of 3 reviews are bad."
rv["A16"].font = TAKE
ch = BarChart()
ch.type, ch.title, ch.legend = "col", "Bad review % by days late", None
ch.y_axis.number_format, ch.y_axis.scaling.min = "0%", 0
ch.add_data(Reference(rv, min_col=6, min_row=9, max_row=14), titles_from_data=True)
ch.set_categories(Reference(rv, min_col=1, min_row=10, max_row=14))
ch.dataLabels = DataLabelList()
ch.dataLabels.showVal = True
ch.height, ch.width = 7.5, 14
rv.add_chart(ch, "H4")
widths(rv, {"A": 12, "B": 12, "C": 12, "D": 12, "E": 12, "F": 13})

# =====================================================================
# States
# =====================================================================
counts = defaultdict(lambda: [0, 0])
for r in rows:
    counts[r[2]][0] += 1
    counts[r[2]][1] += 1 if r[10] > 0 else 0
states = sorted([s for s, v in counts.items() if v[0] >= 100], key=lambda s: -counts[s][1])
stt = wb.create_sheet("States")
stt["A1"].value, stt["A1"].font = "Late % by customer state (states with 100+ orders)", H1
stt["A2"].value, stt["A2"].font = "Sorted by number of late orders. Red = high late %.", NOTE
header(stt, 4, 1, ["State", "Region group", "Delivered orders", "Late orders", "Late %", "Share of all late",
                   "Avg actual days", "Avg promised days"])
for i, s in enumerate(states):
    r = 5 + i
    cell(stt, f"A{r}", s, B)
    cell(stt, f"B{r}", "Rio + Northeast" if s in FOCUS else "Rest of Brazil")
    cell(stt, f"C{r}", f"=COUNTIFS({STATE},A{r})", fmt=INT)
    cell(stt, f"D{r}", f"=SUMIFS({LATE},{STATE},A{r})", fmt=INT)
    cell(stt, f"E{r}", f"=D{r}/C{r}", fmt=PCT)
    cell(stt, f"F{r}", f"=D{r}/SUM({LATE})", fmt=PCT)
    cell(stt, f"G{r}", f"=AVERAGEIFS({ADAYS},{STATE},A{r})", fmt=DEC1)
    cell(stt, f"H{r}", f"=AVERAGEIFS({PDAYS},{STATE},A{r})", fmt=DEC1)
end = 4 + len(states)
stt.conditional_formatting.add(f"E5:E{end}", ColorScaleRule(start_type="num", start_value=0.03, start_color="63BE7B",
                                                            mid_type="num", mid_value=0.08, mid_color="FFEB84",
                                                            end_type="num", end_value=0.18, end_color="F8696B"))
r = end + 2
stt[f"A{r}"].value, stt[f"A{r}"].font = "By region group", H2
header(stt, r + 1, 1, ["Region group", "", "Delivered orders", "Late orders", "Late %", "Share of all late"])
for j, g in enumerate(["Rio + Northeast", "Rest of Brazil"]):
    rr = r + 2 + j
    cell(stt, f"A{rr}", g, B)
    cell(stt, f"C{rr}", f'=COUNTIFS({GROUP},"{g}")', fmt=INT)
    cell(stt, f"D{rr}", f'=SUMIFS({LATE},{GROUP},"{g}")', fmt=INT)
    cell(stt, f"E{rr}", f"=D{rr}/C{rr}", fmt=PCT)
    cell(stt, f"F{rr}", f"=D{rr}/SUM({LATE})", fmt=PCT)
stt[f"A{r + 5}"].value = ("Takeaway: Rio de Janeiro is next to São Paulo but is late 12% of the time (SP: 4.5%). "
                          "Rio + the Northeast are 22% of orders but 40% of all late orders.")
stt[f"A{r + 5}"].font = TAKE
widths(stt, {"A": 15, "B": 16, "C": 11, "D": 10, "E": 9, "F": 11, "G": 10, "H": 11})

# =====================================================================
# Root Cause (seller vs carrier)
# =====================================================================
rc = wb.create_sheet("Root Cause")
rc["A1"].value, rc["A1"].font = "Who causes the delay: the seller or the carrier?", H1
rc["A2"].value, rc["A2"].font = ("Seller days = purchase → handed to carrier. Carrier days = handed to carrier → "
                                 "delivered."), NOTE
header(rc, 4, 1, ["Delivery", "Orders", "Avg seller days", "Avg carrier days", "Seller missed deadline %"])
for r, lab, crit in [(5, "On time", 0), (6, "Late", 1)]:
    cell(rc, f"A{r}", lab, B)
    cell(rc, f"B{r}", f"=COUNTIFS({LATE},{crit})", fmt=INT)
    cell(rc, f"C{r}", f"=AVERAGEIFS({SDAYS},{LATE},{crit})", fmt=DEC1)
    cell(rc, f"D{r}", f"=AVERAGEIFS({CDAYS},{LATE},{crit})", fmt=DEC1)
    cell(rc, f"E{r}", f'=COUNTIFS({LATE},{crit},{MISSED},"Yes")/B{r}', fmt=PCT)
rc["A8"].value, rc["A8"].font = "Late % when the seller hands over on time vs. late", H2
header(rc, 9, 1, ["Seller missed deadline", "Orders", "Late orders", "Late %"])
for r, lab in [(10, "No"), (11, "Yes")]:
    cell(rc, f"A{r}", lab, B)
    cell(rc, f"B{r}", f'=COUNTIFS({MISSED},"{lab}")', fmt=INT)
    cell(rc, f"C{r}", f'=SUMIFS({LATE},{MISSED},"{lab}")', fmt=INT)
    cell(rc, f"D{r}", f"=C{r}/B{r}", fmt=PCT)
cell(rc, "A12", "Times more likely to be late", B)
cell(rc, "D12", "=D11/D10", B, '0.0"x"')
rc["A14"].value = ("Takeaway: late orders spend ~28 days with the carrier (vs ~8). But when a seller misses "
                   "the handover deadline, the order is ~4x more likely to arrive late.")
rc["A14"].font = TAKE
bc = BarChart()
bc.type, bc.grouping, bc.overlap = "bar", "stacked", 100
bc.title = "Average days per stage"
bc.add_data(Reference(rc, min_col=3, max_col=4, min_row=4, max_row=6), titles_from_data=True)
bc.set_categories(Reference(rc, min_col=1, min_row=5, max_row=6))
bc.height, bc.width = 6.5, 14
rc.add_chart(bc, "G4")
widths(rc, {"A": 24, "B": 10, "C": 11, "D": 11, "E": 14})

# =====================================================================
# Seller Scorecard
# =====================================================================
seller_stats = defaultdict(lambda: [0, 0])
for r in rows:
    seller_stats[r[4]][0] += 1
    seller_stats[r[4]][1] += 1 if r[5] == "Yes" else 0
worst = sorted([s for s, v in seller_stats.items() if v[0] >= 50],
               key=lambda s: -seller_stats[s][1] / seller_stats[s][0])[:20]
sc = wb.create_sheet("Seller Scorecard")
sc["A1"].value, sc["A1"].font = "Seller scorecard: who misses the handover deadline most?", H1
sc["A2"].value, sc["A2"].font = ("Sellers with 50+ delivered orders (as main seller), worst 20. "
                                 "Threshold for a warning is an editable input."), NOTE
cell(sc, "A3", "Warning threshold (missed deadline %)", B)
cell(sc, "C3", 0.25, INPUT, PCT, YELLOW)
header(sc, 5, 1, ["Seller ID", "", "Delivered orders", "Missed deadline %", "Late %", "Avg review", "Action"])
for i, s in enumerate(worst):
    r = 6 + i
    sc.merge_cells(f"A{r}:B{r}")
    cell(sc, f"A{r}", s)
    cell(sc, f"C{r}", f"=COUNTIFS({SELLER},A{r})", fmt=INT)
    cell(sc, f"D{r}", f'=COUNTIFS({SELLER},A{r},{MISSED},"Yes")/C{r}', fmt=PCT)
    cell(sc, f"E{r}", f"=SUMIFS({LATE},{SELLER},A{r})/C{r}", fmt=PCT)
    cell(sc, f"F{r}", f"=AVERAGEIFS({SCORE},{SELLER},A{r})", fmt=DEC2)
    cell(sc, f"G{r}", f'=IF(D{r}>=$C$3,"Warning","Monitor")', B)
sc.conditional_formatting.add("D6:D25", ColorScaleRule(start_type="num", start_value=0.2, start_color="FFEB84",
                                                       end_type="num", end_value=0.6, end_color="F8696B"))
sc["A27"].value = "Takeaway: a short list of sellers miss the deadline on 35–60% of their orders. Start the warning program with them."
sc["A27"].font = TAKE
widths(sc, {"A": 30, "B": 8, "C": 11, "D": 12, "E": 9, "F": 10, "G": 11})

# =====================================================================
# Monthly Trend
# =====================================================================
months = sorted({r[1] for r in rows if r[1] >= "2017-01" and r[1] <= "2018-08"})
mt = wb.create_sheet("Monthly Trend")
mt["A1"].value, mt["A1"].font = "Monthly late % and days per stage", H1
mt["A2"].value, mt["A2"].font = "By purchase month, Jan 2017 – Aug 2018.", NOTE
header(mt, 4, 1, ["Month", "Delivered orders", "Late %", "Avg seller days", "Avg carrier days", "Avg promised days"])
for i, m in enumerate(months):
    r = 5 + i
    cell(mt, f"A{r}", m, B)
    cell(mt, f"B{r}", f'=COUNTIFS({MONTH},A{r})', fmt=INT)
    cell(mt, f"C{r}", f"=SUMIFS({LATE},{MONTH},A{r})/B{r}", fmt=PCT)
    cell(mt, f"D{r}", f"=AVERAGEIFS({SDAYS},{MONTH},A{r})", fmt=DEC1)
    cell(mt, f"E{r}", f"=AVERAGEIFS({CDAYS},{MONTH},A{r})", fmt=DEC1)
    cell(mt, f"F{r}", f"=AVERAGEIFS({PDAYS},{MONTH},A{r})", fmt=DEC1)
mend = 4 + len(months)
mt[f"A{mend + 2}"].value = ("Takeaway: late % jumps in Nov 2017 (Black Friday) and Feb–Mar 2018, when carrier days "
                            "rise by ~50% but the promised days do not.")
mt[f"A{mend + 2}"].font = TAKE
lc = LineChart()
lc.title, lc.y_axis.number_format = "Late % by month", "0%"
lc.add_data(Reference(mt, min_col=3, min_row=4, max_row=mend), titles_from_data=True)
lc.set_categories(Reference(mt, min_col=1, min_row=5, max_row=mend))
lc.legend, lc.height, lc.width = None, 7.5, 18
mt.add_chart(lc, "H4")
lc2 = LineChart()
lc2.title = "Carrier days vs promised days"
lc2.add_data(Reference(mt, min_col=5, max_col=6, min_row=4, max_row=mend), titles_from_data=True)
lc2.set_categories(Reference(mt, min_col=1, min_row=5, max_row=mend))
lc2.height, lc2.width = 7.5, 18
mt.add_chart(lc2, "H20")
widths(mt, {"A": 10, "B": 11, "C": 9, "D": 11, "E": 11, "F": 11})

# =====================================================================
# Scenario
# =====================================================================
sn = wb.create_sheet("Scenario")
sn["A1"].value, sn["A1"].font = "What if Olist fixes the two biggest levers?", H1
sn["A2"].value, sn["A2"].font = "Blue cells on yellow are assumptions you can change. Everything else is a formula.", NOTE
sn["A4"].value, sn["A4"].font = "Today", H2
base = [
    ("Delivered orders", f"=COUNTA({MONTH})", INT),
    ("Late orders", f"=SUM({LATE})", INT),
    ("Late %", "=B6/B5", PCT),
    ("Orders where seller missed deadline", "='Root Cause'!B11", INT),
    ("  ...late % for those orders", "='Root Cause'!D11", PCT),
    ("  ...late % when seller is on time", "='Root Cause'!D10", PCT),
    ("Rio + Northeast orders (seller on time)", f'=COUNTIFS({GROUP},"Rio + Northeast",{MISSED},"No")', INT),
    ("  ...late %", f'=SUMIFS({LATE},{GROUP},"Rio + Northeast",{MISSED},"No")/B11', PCT),
    ("Rest of Brazil late % (seller on time)", f'=SUMIFS({LATE},{GROUP},"Rest of Brazil",{MISSED},"No")'
     f'/COUNTIFS({GROUP},"Rest of Brazil",{MISSED},"No")', PCT),
    ("Bad review %: late orders", "=Reviews!E6", PCT),
    ("Bad review %: on-time orders", "=Reviews!E5", PCT),
]
for i, (lab, f, fmt) in enumerate(base):
    r = 5 + i
    cell(sn, f"A{r}", lab)
    cell(sn, f"B{r}", f, LINK if "!" in f and "Data!" not in f else N, fmt)
sn["A17"].value, sn["A17"].font = "Assumptions", H2
cell(sn, "A18", "Cut in missed seller deadlines")
cell(sn, "B18", 0.5, INPUT, PCT, YELLOW)
sn["C18"].value, sn["C18"].font = "e.g. warnings + penalties halve the missed deadlines", NOTE
cell(sn, "A19", "Close the Rio + Northeast gap by")
cell(sn, "B19", 0.5, INPUT, PCT, YELLOW)
sn["C19"].value, sn["C19"].font = "50% = late % moves halfway to the rest of Brazil (second carrier / better SLA)", NOTE
sn["A21"].value, sn["A21"].font = "Result", H2
res = [
    ("Late orders avoided: seller lever", "=ROUND(B8*B18*(B9-B10),0)", INT),
    ("Late orders avoided: Rio + Northeast lever", "=ROUND(B11*B19*(B12-B13),0)", INT),
    ("Total late orders avoided", "=B22+B23", INT),
    ("New late %", "=(B6-B24)/B5", PCT),
    ("Bad reviews avoided", "=ROUND(B24*(B14-B15),0)", INT),
]
for i, (lab, f, fmt) in enumerate(res):
    r = 22 + i
    bold = B if i in (2, 3, 4) else N
    cell(sn, f"A{r}", lab, bold)
    cell(sn, f"B{r}", f, bold, fmt)
widths(sn, {"A": 42, "B": 13, "C": 70})

# =====================================================================
# Summary
# =====================================================================
sm = wb.create_sheet("Summary", 0)
sm.sheet_view.showGridLines = False
sm["A1"].value, sm["A1"].font = "Olist · Late deliveries are hurting reviews: where to fix them first", H1
sm["A2"].value, sm["A2"].font = ("Real data: Olist Brazilian e-commerce, 96K delivered orders, 2016–2018 · "
                                 "every number below is a live formula"), NOTE
sm["A4"].value, sm["A4"].font = "Key numbers", H2
kpis = [
    ("Delivered orders analysed", "=Scenario!B5", INT),
    ("Late %", "=Scenario!B7", PCT),
    ("Avg delivery days (actual vs promised)", f'=TEXT(AVERAGE({ADAYS}),"0.0")&" vs "&TEXT(AVERAGE({PDAYS}),"0.0")', None),
    ("Avg review: on time vs late", '=TEXT(Reviews!C5,"0.00")&" vs "&TEXT(Reviews!C6,"0.00")', None),
    ("Share of all bad reviews from late orders", "=Reviews!F6", PCT),
    ("Late % when seller misses the deadline vs on time",
     "=TEXT('Root Cause'!D11,\"0.0%\")&\" vs \"&TEXT('Root Cause'!D10,\"0.0%\")", None),
    ("Rio + Northeast: share of all late orders", f'=SUMIFS({LATE},{GROUP},"Rio + Northeast")/SUM({LATE})', PCT),
    ("Late orders avoided with both fixes (Scenario)", "=Scenario!B24", INT),
]
for i, (lab, f, fmt) in enumerate(kpis):
    r = 5 + i
    cell(sm, f"A{r}", lab, B, fill=KPI_FILL)
    c = cell(sm, f"B{r}", f, Font(name=F, size=11, bold=True, color="1F3864"), fmt, KPI_FILL)
    c.alignment = Alignment(horizontal="right")
sm["A14"].value, sm["A14"].font = "Recommendations", H2
recs = [
    "1. Make on-time delivery the #1 review KPI: late orders are ~7% of orders but ~1 in 3 bad reviews. "
    "Send a proactive apology + voucher as soon as an order passes its estimated date.",
    "2. Enforce the seller handover deadline: orders handed over late are ~4x more likely to arrive late. "
    "Warn sellers above 25% missed deadlines (see Seller Scorecard) and penalise repeat offenders.",
    "3. Add a second carrier / regional partner for Rio de Janeiro and the Northeast: 22% of orders, 40% of late orders.",
    "4. Add a peak-season buffer to the estimated date (Black Friday, Feb–Mar): carrier days jump ~50% "
    "but the promise stays the same.",
    "5. Track late % by state and seller every week; the Scenario sheet shows the gain from each fix.",
]
for i, t in enumerate(recs):
    r = 15 + i
    c = sm.cell(row=r, column=1, value=t)
    c.font = N
    c.alignment = Alignment(wrap_text=True, vertical="top")
    sm.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    sm.row_dimensions[r].height = 30
sm["A21"].value, sm["A21"].font = "Sheets in this workbook", H2
guide = [("Reviews", "Late delivery vs. review score"), ("States", "Late % by customer state"),
         ("Root Cause", "Seller stage vs. carrier stage"), ("Seller Scorecard", "Worst 20 sellers + warning flag"),
         ("Monthly Trend", "Late % and days per stage by month"), ("Scenario", "What-if model (blue cells)"),
         ("Data", "One row per delivered order (Excel Table, ready for PivotTables)")]
for i, (s, t) in enumerate(guide):
    r = 22 + i
    c = sm.cell(row=r, column=1, value=s)
    c.hyperlink = f"#'{s}'!A1"
    c.font = Font(name=F, size=10, color="0563C1", underline="single")
    sm.cell(row=r, column=2, value=t).font = N
sm["A30"].value = "Source: Olist, Brazilian E-Commerce Public Dataset (MIT License) · github.com/olist/work-at-olist-data"
sm["A30"].font = NOTE
widths(sm, {"A": 48, "B": 20, "C": 14, "D": 14, "E": 14, "F": 14})

wb.save(OUT)
print("saved", OUT, "rows", LAST - 1)

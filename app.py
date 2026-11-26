import io, csv
from datetime import date, timedelta
import pandas as pd
import streamlit as st
from core import CATEGORIES, validate_record, calculate_total, enrich_record, summarize, category_totals
from data_manager import DataManager

st.set_page_config(page_title="Trip Budget Calculator", page_icon="🧳", layout="wide")
st.markdown("""
<style>
.main {background:#f7f9fc;}
.block-container {padding-top:2rem; padding-bottom:2rem;}
.hero {padding:1.5rem 1.8rem;border-radius:18px;background:linear-gradient(115deg,#14213d,#245b8f);color:white;margin-bottom:1.2rem;}
.hero h1 {color:white;margin:0;font-size:2.2rem;}
.hero p {color:#e5eef8;margin:.35rem 0 0 0;}
div[data-testid="stMetric"] {background:white;padding:14px;border:1px solid #e7edf5;border-radius:12px;}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_manager():
    return DataManager()
dm = get_manager()

def refresh():
    st.session_state.records = dm.load_records()

if "records" not in st.session_state:
    refresh()

st.sidebar.title("🧳 Trip Budget Calculator")
st.sidebar.caption("CampusSolve • Project #51")
page = st.sidebar.radio("Navigation", ["Dashboard", "Add Trip", "Trip Records", "Analytics & Reports", "Bulk CSV Import", "About Project"])
st.sidebar.divider()
st.sidebar.caption("Local storage: data/trips.csv + data/trips.json")
st.sidebar.caption("Changes are saved automatically.")

def money(value):
    return f"₹{float(value):,.2f}"

def show_table(records):
    if not records:
        st.info("No trip records found.")
        return
    rows = []
    for r in records:
        e = enrich_record(r)
        rows.append({"ID":r.get("id",""), "Trip":r.get("trip_name",""), "Destination":r.get("destination",""),
                     "Start":r.get("start_date",""), "End":r.get("end_date",""), "Travelers":r.get("travelers",1),
                     "Transport":money(r.get("transport",0)), "Stay":money(r.get("stay",0)),
                     "Food":money(r.get("food",0)), "Activities":money(r.get("activities",0)),
                     "Total":money(e["total_cost"]), "Budget":money(r.get("budget_limit",0)),
                     "Status":e["budget_status"]})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

if page == "Dashboard":
    st.markdown('<div class="hero"><h1>🧳 Trip Budget Calculator</h1><p>Plan smarter. Track every expense. Travel within your budget.</p></div>', unsafe_allow_html=True)
    records = [enrich_record(r) for r in st.session_state.records]
    stats = summarize(records)
    a,b,c,d = st.columns(4)
    a.metric("Total Trips", stats["trip_count"])
    b.metric("Total Estimated Spend", money(stats["total_spend"]))
    c.metric("Average Trip Cost", money(stats["average_spend"]))
    d.metric("Over-budget Trips", stats["over_budget"])
    st.subheader("Recent Trips")
    show_table(list(reversed(records[-8:])))
    st.subheader("Budget alerts")
    over = [r for r in records if r["budget_status"] == "Over Budget"]
    if over:
        for r in over[:5]:
            st.warning(f'{r.get("trip_name")} ({r.get("destination")}): {money(r["total_cost"])} spend vs {money(r.get("budget_limit",0))} budget.')
    else:
        st.success("No trips are currently over their defined budget.")

elif page == "Add Trip":
    st.title("➕ Add a Trip")
    st.write("Enter the trip details and estimated expenses. All amounts are in Indian Rupees (₹).")
    with st.form("add_trip_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        trip_name = c1.text_input("Trip name *", placeholder="e.g. Hyderabad Weekend")
        destination = c2.text_input("Destination *", placeholder="e.g. Goa")
        c3,c4,c5 = st.columns(3)
        start_date = c3.date_input("Start date", value=date.today())
        end_date = c4.date_input("End date", value=date.today()+timedelta(days=2))
        travelers = c5.number_input("Number of travelers", min_value=1, max_value=100, value=1, step=1)
        st.markdown("#### Estimated expenses")
        x1,x2,x3,x4 = st.columns(4)
        transport = x1.number_input("Transport (₹)", min_value=0.0, value=0.0, step=100.0)
        stay = x2.number_input("Stay (₹)", min_value=0.0, value=0.0, step=100.0)
        food = x3.number_input("Food (₹)", min_value=0.0, value=0.0, step=100.0)
        activities = x4.number_input("Activities (₹)", min_value=0.0, value=0.0, step=100.0)
        budget_limit = st.number_input("Total budget limit (₹, 0 = not set)", min_value=0.0, value=0.0, step=500.0)
        notes = st.text_area("Notes (optional)")
        total = transport+stay+food+activities
        st.info(f"Estimated total: **{money(total)}**")
        submitted = st.form_submit_button("Save Trip", type="primary", use_container_width=True)
    if submitted:
        record = {"trip_name":trip_name.strip(), "destination":destination.strip(),
                  "start_date":start_date.isoformat(), "end_date":end_date.isoformat(),
                  "travelers":int(travelers), "transport":transport, "stay":stay, "food":food,
                  "activities":activities, "budget_limit":budget_limit, "notes":notes}
        errors = validate_record(record)
        if errors:
            for error in errors: st.error(error)
        else:
            saved = dm.add_record(record)
            refresh()
            st.success(f"Trip saved successfully with ID {saved['id']}.")
            if saved["total_cost"] > budget_limit > 0:
                st.warning("This trip is over the defined budget.")

elif page == "Trip Records":
    st.title("🔎 Trip Records")
    records = st.session_state.records
    destinations = ["All"] + sorted(set(str(r.get("destination","")) for r in records if r.get("destination")))
    f1,f2,f3 = st.columns([2,1,1])
    keyword = f1.text_input("Search by trip, destination, ID or notes")
    destination = f2.selectbox("Destination", destinations)
    status = f3.selectbox("Budget status", ["All","Within Budget","Over Budget"])
    filtered = dm.search(records, keyword, destination, status)
    st.caption(f"{len(filtered)} matching record(s)")
    show_table(filtered)
    if filtered:
        options = {f'{r.get("id")} — {r.get("trip_name")} ({r.get("destination")})':r.get("id") for r in filtered}
        selected = st.selectbox("Select a record to inspect or delete", list(options))
        chosen_id = options[selected]
        chosen = next(r for r in filtered if str(r.get("id")) == str(chosen_id))
        with st.expander("Record details"):
            st.json(enrich_record(chosen))
        if st.button("Delete selected trip", type="secondary"):
            dm.delete_record(chosen_id)
            refresh()
            st.success(f"{chosen_id} deleted.")
            st.rerun()

elif page == "Analytics & Reports":
    st.title("📊 Analytics & Reports")
    records = [enrich_record(r) for r in st.session_state.records]
    stats = summarize(records)
    x1,x2,x3,x4 = st.columns(4)
    x1.metric("Trips",stats["trip_count"])
    x2.metric("Total Spend",money(stats["total_spend"]))
    x3.metric("Average Spend",money(stats["average_spend"]))
    x4.metric("Over Budget",stats["over_budget"])
    if records:
        st.subheader("Expense breakdown")
        cats = category_totals(records)
        chart_df = pd.DataFrame({"Category":[k.title() for k in cats], "Amount":[v for v in cats.values()]})
        st.bar_chart(chart_df.set_index("Category"))
        st.subheader("Trip-wise spending")
        trip_df = pd.DataFrame([{"Trip":r.get("trip_name"),"Total":r["total_cost"],"Budget":float(r.get("budget_limit",0) or 0)} for r in records])
        st.bar_chart(trip_df.set_index("Trip")[["Total","Budget"]])
        st.subheader("Summary metrics")
        st.dataframe(pd.DataFrame([{"Metric":"Total trips","Value":stats["trip_count"]},
                                   {"Metric":"Total spend","Value":money(stats["total_spend"])},
                                   {"Metric":"Average spend","Value":money(stats["average_spend"])},
                                   {"Metric":"Highest trip cost","Value":money(stats["highest_spend"])},
                                   {"Metric":"Lowest trip cost","Value":money(stats["lowest_spend"])},
                                   {"Metric":"Trips over budget","Value":stats["over_budget"]},
                                   {"Metric":"Combined budget limits","Value":money(stats["total_budget"])}]), hide_index=True, use_container_width=True)
    else:
        st.info("Add or import trips to see analytics.")
    st.subheader("Export reports")
    records = [enrich_record(r) for r in st.session_state.records]
    if records:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(records[0].keys()))
        writer.writeheader(); writer.writerows(records)
        st.download_button("⬇ Download CSV report", output.getvalue(), "trip_budget_report.csv", "text/csv")
        lines = ["# Trip Budget Calculator — Executive Summary", "",
                 f"- Total trips: {stats['trip_count']}", f"- Total spend: {money(stats['total_spend'])}",
                 f"- Average spend: {money(stats['average_spend'])}", f"- Over-budget trips: {stats['over_budget']}", "",
                 "## Expense totals"]
        lines += [f"- {k.title()}: {money(v)}" for k,v in category_totals(records).items()]
        lines += ["", "## Trip records"]
        lines += [f"- {r.get('trip_name')} — {r.get('destination')}: {money(r['total_cost'])} ({r['budget_status']})" for r in records]
        report = "\n".join(lines)
        st.download_button("⬇ Download Markdown report", report, "trip_budget_summary.md", "text/markdown")
        st.download_button("⬇ Download plain-text audit report", report.replace("#","").replace("**",""), "trip_budget_audit.txt", "text/plain")

elif page == "Bulk CSV Import":
    st.title("📥 Bulk CSV Import")
    st.write("Upload a CSV containing multiple trips. Each row is validated independently; valid rows are saved and invalid rows are reported.")
    st.caption("Required columns: trip_name, destination, start_date, end_date, travelers, transport, stay, food, activities. Optional: budget_limit, notes.")
    uploaded = st.file_uploader("Choose CSV file", type=["csv"])
    if uploaded and st.button("Validate and import CSV", type="primary"):
        try:
            count, errors = dm.import_csv(uploaded)
            refresh()
            st.success(f"{count} valid record(s) imported.")
            if errors:
                st.error(f"{len(errors)} row(s) could not be imported.")
                st.dataframe(pd.DataFrame(errors), use_container_width=True, hide_index=True)
        except Exception as exc:
            st.error(f"Could not process this CSV: {exc}")

elif page == "About Project":
    st.title("About this Project")
    st.markdown("""
**CampusSolve — Project #51: Trip Budget Calculator**  
**Domain:** Travel & Transport

### Objective
Estimate transport, stay, food and activity costs for a planned trip, with input validation, local CSV/JSON persistence and clear summary reporting.

### Core requirements covered
- Interactive menu-driven workflow (Streamlit navigation plus terminal menu in `cli.py`)
- Defensive input validation and range checks
- Cost calculation engine
- Local CSV and JSON persistence
- Keyword and destination/category search
- Executive summary with totals, averages, status indicators and trends

### Additional capabilities
- CSV, Markdown and plain-text report exports
- Budget threshold warnings
- Bulk CSV import with row-by-row validation
- Charts and graphical interface
""")
    st.info("Data is stored locally in the project's data folder. Back up data/trips.csv and data/trips.json to preserve records.")

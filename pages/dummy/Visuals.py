# pages/Visuals.py David Park
import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt
from pathlib import Path

st.set_page_config(page_title="Visuals", page_icon="📈")
st.title("Visualizations (CSV + JSON)")

base = Path(__file__).resolve().parent.parent
csv_path = base / "data.csv"
json_path = base / "data.json"

# Load data
# CSV
if csv_path.exists():
    df = pd.read_csv(csv_path)
else:
    df = pd.DataFrame(columns=["timestamp", "label", "value"])

# JSON
try:
    with open(json_path, "r", encoding="utf-8") as f:
        jdata = json.load(f)
except Exception:
    jdata = {"chart_title": "JSON Chart", "data_points": []}

# Session state defaults
if "selected_labels" not in st.session_state:
    st.session_state.selected_labels = sorted(df["label"].dropna().unique().tolist())
if "agg" not in st.session_state:
    st.session_state.agg = "sum"
if "window" not in st.session_state:
    st.session_state.window = 1
# Graph A (DYNAMIC): CSV → aggregate by label with controls
st.subheader("A) CSV Aggregate by Label (Dynamic)")
left, right = st.columns([2, 1])

with right:
    all_labels = sorted(df["label"].dropna().unique().tolist())
    st.session_state.selected_labels = st.multiselect(
        "Filter labels", options=all_labels, default=st.session_state.selected_labels
    )
    st.session_state.agg = st.selectbox("Aggregation", ["sum", "mean", "count"], index=["sum", "mean", "count"].index(st.session_state.agg))

with left:
    if not df.empty and st.session_state.selected_labels:
        dff = df[df["label"].isin(st.session_state.selected_labels)]
        if st.session_state.agg == "sum":
            plot_df = dff.groupby("label")["value"].sum().sort_values()
        elif st.session_state.agg == "mean":
            plot_df = dff.groupby("label")["value"].mean().sort_values()
        else:
            plot_df = dff.groupby("label")["value"].count().sort_values()
        st.bar_chart(plot_df)
        st.caption("Dynamic bar chart from CSV with label filter + aggregation.")
    else:
        st.warning("Add rows in Survey or select at least one label.")
# Graph B (DYNAMIC): CSV → time series with moving-average control
st.subheader("B) Stacked Activity Over Time by Label (Dynamic)")

if df.empty:
    st.warning("No CSV data yet. Add rows in Survey to see this chart.")
else:
    # --- Controls (stored in session_state) ---
    if "freq" not in st.session_state:
        st.session_state.freq = "W"  # D, W, or M
    if "topn" not in st.session_state:
        st.session_state.topn = 5
    if "cumulative" not in st.session_state:
        st.session_state.cumulative = False

    # parse timestamps & bounds
    dft = df.copy()
    dft["timestamp"] = pd.to_datetime(dft["timestamp"], errors="coerce")
    dft = dft.dropna(subset=["timestamp"])
    if dft.empty:
        st.warning("Timestamps are missing/invalid. Add data via Survey.")
    else:
        min_dt, max_dt = dft["timestamp"].min(), dft["timestamp"].max()
        colL, colM, colR = st.columns([1.2, 1, 1])

        start = colL.date_input("Start date", value=min_dt.date(), min_value=min_dt.date(), max_value=max_dt.date())
        end   = colM.date_input("End date",   value=max_dt.date(),   min_value=min_dt.date(), max_value=max_dt.date())
        st.session_state.freq = colR.selectbox("Frequency", ["D","W","M"], index=["D","W","M"].index(st.session_state.freq))

        c1, c2, c3 = st.columns([1,1,1])
        st.session_state.topn = c1.slider("Top-N labels", 1, 10, st.session_state.topn)
        st.session_state.cumulative = c2.toggle("Cumulative totals", value=st.session_state.cumulative)
        # optional filter by labels
        all_labels = sorted(dft["label"].dropna().unique().tolist())
        chosen = c3.multiselect("Filter labels (optional)", options=all_labels, default=all_labels)

        # --- Filter, group, resample ---
        mask = (dft["timestamp"].dt.date >= start) & (dft["timestamp"].dt.date <= end)
        dff = dft.loc[mask].copy()
        if chosen:
            dff = dff[dff["label"].isin(chosen)]

        if dff.empty:
            st.info("No rows in the selected range/labels.")
        else:
            # sum values per timestamp+label, then resample to chosen frequency
            dff = dff.set_index("timestamp")
            per_period = dff.groupby([pd.Grouper(freq=st.session_state.freq), "label"])["value"].sum()
            wide = per_period.unstack(fill_value=0)

            # keep only top-N labels by total; bucket rest as "Other"
            totals = wide.sum(axis=0).sort_values(ascending=False)
            keep = totals.head(st.session_state.topn).index.tolist()
            other = [c for c in wide.columns if c not in keep]
            if other:
                wide["Other"] = wide[other].sum(axis=1)
                wide = wide[keep + (["Other"] if other else [])]

            if st.session_state.cumulative:
                wide = wide.cumsum()

            st.area_chart(wide)
            st.caption(
                "Dynamic stacked area chart from CSV. Controls: date range, frequency (D/W/M), "
                "top-N labels, and cumulative toggle."
            )
# Graph C (STATIC): JSON → static bar using matplotlib
st.subheader("C) JSON Bar Chart (Editable)")

# Prepare session copy so we can edit safely
if "json_points" not in st.session_state:
    st.session_state.json_points = list(jdata.get("data_points", []))
if "json_title" not in st.session_state:
    st.session_state.json_title = jdata.get("chart_title", "My JSON Visualization")

st.text_input("Chart title (from JSON)", key="json_title")

# Editor rows
to_delete = []
for i, item in enumerate(st.session_state.json_points):
    c1, c2, c3 = st.columns([2.5, 1, 0.4])
    item["label"] = c1.text_input(f"Label {i+1}", value=item.get("label", ""), key=f"jlabel_{i}")
    item["value"] = c2.number_input(f"Value {i+1}", value=float(item.get("value", 0)), step=1.0, key=f"jvalue_{i}")
    if c3.button("🗑", key=f"jdel_{i}"):
        to_delete.append(i)

# Apply deletions
for idx in reversed(to_delete):
    st.session_state.json_points.pop(idx)

# Add new row
if st.button("➕ Add item"):
    st.session_state.json_points.append({"label": "", "value": 0})

# Optional: Sync from CSV (e.g., current totals by label)
if not df.empty and st.button("↔ Sync from CSV (sum by label)"):
    agg = df.groupby("label")["value"].sum().reset_index()
    st.session_state.json_points = [{"label": r["label"], "value": float(r["value"])} for _, r in agg.iterrows()]

# Save back to data.json
json_path = base / "data.json"
if st.button("💾 Save to data.json"):
    payload = {
        "chart_title": st.session_state.json_title,
        "data_points": st.session_state.json_points
    }
    with open(json_path, "w", encoding="utf-8") as f:
        import json
        json.dump(payload, f, ensure_ascii=False, indent=2)
    st.success(f"Saved {json_path.name}. (If needed, click Rerun)")

# Draw the chart (matplotlib or Streamlit bar_chart)
points = st.session_state.json_points
if points:
    labels = [p.get("label", "") for p in points]
    vals = [p.get("value", 0) for p in points]

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.bar(labels, vals)
    ax.set_title(st.session_state.json_title)
    ax.set_ylabel("Value")
    ax.set_xlabel("Label")
    st.pyplot(fig)
    st.caption("JSON-backed chart. Edit above and optionally save to data.json.")
else:
    st.info("No items yet. Add some rows above or sync from CSV.")

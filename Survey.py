# pages/Survey.py David Park
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
st.set_page_config(page_title="Survey", page_icon="📝")
st.title("Survey → Append to data.csv")
st.write("Enter a label and a numeric value. Submitted rows are appended to **data.csv**.")
csv_path = Path(__file__).resolve().parent.parent / "data.csv"
if not csv_path.exists():
    pd.DataFrame(columns=["timestamp", "label", "value"]).to_csv(csv_path, index=False)

with st.form("survey_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    label = col1.text_input("Label (e.g., 'Study', 'Sleep', 'Workout')", "")
    value = col2.number_input("Value (number)", value=0.0, step=1.0, format="%.2f")
    submitted = st.form_submit_button("Add row")

    if submitted:
        if label.strip() == "":
            st.error("Please enter a non-empty label.")
        else:
            new_row = {"timestamp": datetime.now().isoformat(timespec="seconds"),
                       "label": label.strip(),
                       "value": float(value)}
            df = pd.read_csv(csv_path)
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(csv_path, index=False)
            st.success(f"Added: {new_row}")

st.subheader("Current data.csv (last 20 rows)")
df_show = pd.read_csv(csv_path)
st.dataframe(df_show.tail(20), use_container_width=True)

st.info("Tip: Add enough rows to make your dynamic charts interesting. (The rubric requires using the CSV.)")

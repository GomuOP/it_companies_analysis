"""Streamlit app: Compare tab (R1) + Ask tab (R2).

Owner: Member C
Run:   streamlit run app.py
"""
import json

import pymupdf as fitz
import pandas as pd
import plotly.express as px
import streamlit as st

from src.config import COMPANIES, METRICS_PATH, PDF_DIR, FISCAL_YEAR

st.set_page_config(page_title="Annual Report Intelligence", layout="wide")
st.title("Annual Report Intelligence")
st.caption(f"Tech Mahindra · Wipro · HCLTech · Annual Reports {FISCAL_YEAR}. Answers come only from these reports, with page citations.")


@st.cache_data
def page_image(company: str, page: int):
    doc = fitz.open(PDF_DIR / COMPANIES[company]["file"])
    return doc[page - 1].get_pixmap(dpi=110).tobytes("png")


def show_page(company, page, key):
    if st.toggle(f"View {company} p.{page}", key=key):
        st.image(page_image(company, page))


compare_tab, ask_tab = st.tabs(["📊 Compare", "💬 Ask the reports"])

# ---------------- R1: comparison chart from verified metrics ----------------
with compare_tab:
    data = json.loads(METRICS_PATH.read_text())
    df = pd.DataFrame(data["metrics"])
    metric = st.radio("Metric", df["metric"].unique().tolist(), horizontal=True)
    sub = df[(df["metric"] == metric) & df["value"].notna()]

    if sub.empty:
        st.info("No verified values for this metric yet. Fill data/metrics.json.")
    else:
        unit = sub["unit"].iloc[0]
        fig = px.bar(sub, x="company", y="value", color="company", text="value",
                     hover_data={"page": True, "quote": True, "company": False},
                     labels={"value": f"{metric} ({unit})", "company": ""})
        fig.update_layout(showlegend=False, height=420)
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"All values: {data['fy']}, {data['basis'].lower()}, unit = {unit}. Page = PDF page of the annual report.")
        if not sub["verified"].all():
            st.warning("Some values are not yet hand-verified.")
        st.dataframe(sub[["company", "value", "unit", "page", "quote", "verified"]], hide_index=True,
                     use_container_width=True)
        for _, r in sub.iterrows():
            if r["page"]:
                show_page(r["company"], int(r["page"]), key=f"m-{r['company']}-{metric}")

# ---------------- R2: grounded Q&A ----------------
with ask_tab:
    from src.answer import answer

    q = st.text_input("Ask a question about the three annual reports",
                      placeholder="e.g. What was the attrition rate at Wipro in FY2023-24?")
    if q:
        with st.spinner("Searching the reports..."):
            r = answer(q)
        if r["found"]:
            st.success(r["answer"])
            st.markdown("**Sources**")
            for i, c in enumerate(r["citations"]):
                st.markdown(f"- **{c['company']}** Annual Report {c['fy']}, **page {c['page']}**")
                show_page(c["company"], c["page"], key=f"c-{i}")
        else:
            st.error(r["answer"])
            st.caption(f"Reason: {r.get('reason', '')}")

        with st.expander("Show retrieved chunks (what the model saw)"):
            for c in r["retrieved"]:
                st.markdown(f"`{c['id']}` · similarity {c['cosine']:.2f}")
                st.text(c["text"][:800])

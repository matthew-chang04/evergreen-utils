import streamlit as st

st.navigation(
    [
       st.Page("pages/allocation.py", title="Strategic Asset Allocation", default=True),
       st.Page("pages/performance.py", title="Portfolio ")
    ]
)
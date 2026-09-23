import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import os
import sys

import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from frontend.session_state import ensure_app_state

ensure_app_state()

st.sidebar.header("Global portfolio settings")
st.sidebar.slider("Horizon (years)", min_value=1, max_value=50, value=st.session_state.horizon, key="horizon")
st.sidebar.number_input("Monte Carlo paths", min_value=100, max_value=20000, value=st.session_state.mc_paths, step=100, key="mc_paths")
st.sidebar.number_input("Sample paths to plot", min_value=10, max_value=500, value=st.session_state.sample_paths, step=10, key="sample_paths")

pages = [
    st.Page("frontend/pages/allocation.py", title="Allocation Research", default=True),
    st.Page("frontend/pages/performance.py", title="Performance Metrics"),
]

st.navigation(pages).run()
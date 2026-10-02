import streamlit as st


benchmark_col, test_col = st.columns(2)


with benchmark_col:

    ptf = st.session_state.benchmark_ptf

with test_col:

    if st.session_state.test_weights == st.session_state.benchmark_weights:
        st.info("Set a test portfolio to see stress test comparison")

    else:
        ptf = st.session_state.test_ptf

        


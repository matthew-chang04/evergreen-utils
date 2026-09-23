from pathlib import Path


def test_dashboard_uses_shared_session_state_for_pages():
    source = Path('dashboard.py').read_text()
    assert 'st.navigation(' in source
    assert '.run()' in source
    assert 'st.session_state' in source


def test_pages_share_a_single_benchmark_portfolio():
    allocation = Path('frontend/pages/allocation.py').read_text()
    performance = Path('frontend/pages/performance.py').read_text()

    assert 'benchmark' in allocation.lower()
    assert 'benchmark' in performance.lower()
    assert 'st.session_state' in allocation
    assert 'st.session_state' in performance

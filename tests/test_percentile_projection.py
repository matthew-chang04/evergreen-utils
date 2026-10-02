import numpy as np

from frontend.percentile_projection import build_percentile_projection_figure


def test_build_percentile_projection_figure_renders_all_percentile_paths():
    times = np.array([0.0, 1.0, 2.0])
    percentile_values = {
        10: np.array([100.0, 110.0, 120.0]),
        25: np.array([105.0, 115.0, 125.0]),
        50: np.array([110.0, 120.0, 130.0]),
        75: np.array([115.0, 125.0, 135.0]),
        90: np.array([120.0, 130.0, 140.0]),
    }
    liability_values = np.array([100.0, 120.0, 130.0])
    liability_years = np.array([0.0, 1.0, 2.0])

    fig = build_percentile_projection_figure(
        times=times,
        percentile_values=percentile_values,
        liability_values=liability_values,
        liability_years=liability_years,
    )

    names = {trace.name for trace in fig.data}
    assert "10th percentile" in names
    assert "25th percentile" in names
    assert "50th percentile" in names
    assert "75th percentile" in names
    assert "90th percentile" in names
    assert "Liabilities" in names

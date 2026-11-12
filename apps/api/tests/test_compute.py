import pytest
import pandas as pd
import numpy as np
from src.compute.normalise import map_confidence, generate_det_id
from src.compute.calibrate import fit_sensor_calibration

def test_confidence_mapping():
    # MODIS mapping: <30 -> 0, 30..79 -> 1, >=80 -> 2
    r_low = pd.Series({"confidence": 20})
    r_nom = pd.Series({"confidence": 50})
    r_high = pd.Series({"confidence": 85})
    
    assert map_confidence(r_low, is_modis=True) == (0, "low")
    assert map_confidence(r_nom, is_modis=True) == (1, "nominal")
    assert map_confidence(r_high, is_modis=True) == (2, "high")

    # VIIRS mapping: l -> 0, n -> 1, h -> 2
    r_v_l = pd.Series({"confidence": "l"})
    r_v_n = pd.Series({"confidence": "n"})
    r_v_h = pd.Series({"confidence": "h"})
    
    assert map_confidence(r_v_l, is_modis=False) == (0, "low")
    assert map_confidence(r_v_n, is_modis=False) == (1, "nominal")
    assert map_confidence(r_v_h, is_modis=False) == (2, "high")

def test_generate_det_id():
    row = pd.Series({
        "latitude": 23.8103,
        "longitude": 90.4125,
        "acq_date": "2025-03-15",
        "acq_time": 630,
        "sensor_family": "VIIRS"
    })
    det_id = generate_det_id(row)
    assert isinstance(det_id, str)
    assert len(det_id) == 16  # SHA-256 first 16 chars

def test_sensor_calibration():
    # Synthetic cluster dataframe with random Poisson distributed counts
    np.random.seed(42)
    m = np.random.poisson(lam=5, size=50) + 1
    v = np.random.poisson(lam=25, size=50) + 1
    frp = np.random.uniform(10, 100, size=50)
    
    df = pd.DataFrame([
        {"local_date": f"2025-03-{(i%28)+1:02d}", "n_modis": int(m[i]), "n_viirs": int(v[i]), "max_frp": float(frp[i])}
        for i in range(50)
    ])
    res = fit_sensor_calibration(df)
    assert "ratio" in res
    assert "ci_lo" in res
    assert "ci_hi" in res
    assert res["ratio"] > 0

import numpy as np

RETURNS = {
    "cash" : 0.024,
    "can_equity" : 0.063,
    "us_equity" : 0.064,
    "em_equity" : 0.075,
    "id_equity" : 0.066,
    "fixed_income" : 0.035,
    "private_equity" : 0.084,
    "infrastructure" : 0.067,
    "real_estate" : 0.082,
}

STD_DEV = {
    "cash" : 0.017,
    "fixed_income" : 0.0582,
    "can_equity" : 0.1349,
    "us_equity" : 0.1368,
    "id_equity" : 0.1098,
    "em_equity" : 0.1411,
    "real_estate" : 0.1139,
    "infrastructure" : 0.1025,
    "private_equity" : 0.1978,
}

ASSET_ORDER = STD_DEV.keys()

CORRELATION = [
    [1.0, 0.22, 0.13, 0.33, 0.31, 0.15, -0.12, 0.04, -0.01],
    [0.22, 1.0, 0.3, 0.58, 0.48, 0.58, -0.15, 0.06, 0.01],
    [0.13, 0.3, 1.0, 0.57, 0.65, 0.5, 0.32, 0.55, 0.66],
    [0.33, 0.58, 0.57, 1.0, 0.58, 0.41, 0.35, 0.47, 0.68],
    [0.31, 0.48, 0.65, 0.58, 1.0, 0.72, 0.26, 0.58, 0.63],
    [0.15, 0.58, 0.5, 0.41, 0.72, 1.0, 0.28, 0.58, 0.63],
    [-0.12, -0.15, 0.32, 0.35, 0.26, 0.28, 1.0, 0.29, 0.59],
    [0.04, 0.06, 0.55, 0.47, 0.58, 0.58, 0.29, 1.0, 0.5],
    [-0.01, 0.01, 0.66, 0.68, 0.63, 0.63, 0.59, 0.5, 1.0]
]
asset_names = list(STD_DEV.keys())
COVARIANCE = np.array([
    [
        CORRELATION[i][j] * STD_DEV[asset_names[i]] * STD_DEV[asset_names[j]]
        for j in range(len(asset_names))
    ]
    for i in range(len(asset_names))
], dtype=float)

COVARIANCE = (COVARIANCE + COVARIANCE.T) / 2.0
evals, evecs = np.linalg.eigh(COVARIANCE)
evals = np.clip(evals, 1e-8, None)
COVARIANCE = (evecs * evals) @ evecs.T
COVARIANCE = (COVARIANCE + COVARIANCE.T) / 2.0

BASE_SAA = {
    "cash" : 0.03,
    "cad_equity" : 0.09,
    "usd_equity" : 0.09,
    "em_equity" : 0.05,
    "id_equity" : 0.04,
    "fixed_income" : 0.28,
    "private_equity" : 0.13,
    "infrastructure" : 0.13,
    "real_estate" : 0.16,
}

SCENARIO_DELTAS = {
    "base" : {
        "returns" : {
            "cash" : 0.0,
            "fixed_income" : 0.0,
            "can_equity" : 0.0,
            "us_equity" : 0.0,
            "id_equity" : 0.0,
            "em_equity" : 0.0,
            "real_estate" : 0.0,
            "infrastructure" : 0.0,
            "private_equity" : 0.0,
        },
        "std_dev" : {
            "cash" : 0.0,
            "fixed_income" : 0.0,
            "can_equity" : 0.0,
            "us_equity" : 0.0,
            "id_equity" : 0.0,
            "em_equity" : 0.0,
            "real_estate" : 0.0,
            "infrastructure" : 0.0,
            "private_equity" : 0.0,
        }
    },
    "bull" : {
        "returns" : {
            "cash" : -0.001,
            "fixed_income" : -0.005,
            "can_equity" : 0.005,
            "us_equity" : 0.005,
            "id_equity" : 0.003,
            "em_equity" : 0.003,
            "real_estate" : 0.005,
            "infrastructure" : 0.003,
            "private_equity" : 0.005,
        },
        "std_dev" : {
            "cash" : 0.0,
            "fixed_income" : 0.0,
            "can_equity" : 0.0,
            "us_equity" : 0.0,
            "id_equity" : 0.0,
            "em_equity" : 0.0,
            "real_estate" : 0.0,
            "infrastructure" : 0.0,
            "private_equity" : 0.0,
        }
    },
    "bear" : {
        "returns" : {
            "cash" : 0.0,
            "fixed_income" : 0.0,
            "can_equity" : 0.0,
            "us_equity" : 0.0,
            "id_equity" : 0.0,
            "em_equity" : 0.0,
            "real_estate" : 0.0,
            "infrastructure" : 0.0,
            "private_equity" : 0.0,
        },
        "std_dev" : {
            "cash" : 0.0,
            "fixed_income" : 0.0,
            "can_equity" : 0.0,
            "us_equity" : 0.0,
            "id_equity" : 0.0,
            "em_equity" : 0.0,
            "real_estate" : 0.0,
            "infrastructure" : 0.0,
            "private_equity" : 0.0,
        }
    },
    "stagflation" : {
        "returns" : {
            "cash" : 0.0,
            "fixed_income" : 0.0,
            "can_equity" : 0.0,
            "us_equity" : 0.0,
            "id_equity" : 0.0,
            "em_equity" : 0.0,
            "real_estate" : 0.0,
            "infrastructure" : 0.0,
            "private_equity" : 0.0,
        },
        "std_dev" : {
            "cash" : 0.0,
            "fixed_income" : 0.0,
            "can_equity" : 0.0,
            "us_equity" : 0.0,
            "id_equity" : 0.0,
            "em_equity" : 0.0,
            "real_estate" : 0.0,
            "infrastructure" : 0.0,
            "private_equity" : 0.0,
        }
    },
    "gfc" : {
        "returns" : {
            "cash" : 0.0,
            "fixed_income" : 0.0,
            "can_equity" : 0.0,
            "us_equity" : 0.0,
            "id_equity" : 0.0,
            "em_equity" : 0.0,
            "real_estate" : 0.0,
            "infrastructure" : 0.0,
            "private_equity" : 0.0,
        },
        "std_dev" : {
            "cash" : 0.0,
            "fixed_income" : 0.0,
            "can_equity" : 0.0,
            "us_equity" : 0.0,
            "id_equity" : 0.0,
            "em_equity" : 0.0,
            "real_estate" : 0.0,
            "infrastructure" : 0.0,
            "private_equity" : 0.0,
        }
    },
}

AUM = 1_000_000_000.0
LIABILITIES = 1_060_000_000.0
ACTUARIAL_DF = 0.06
LT_CPI = 0.021
WAGE_GROWTH = 0.031

ACTIVE_MEMBERS = 12_000
RETIRED_MEMBERS = 4_000
AVG_SALARY = 75_000.0
EMPLOYEE_CONTRIBUTION_RATE = 0.085
EMLOYER_CONTRIBUTION_RATE = 0.0115

STARTING_BENEFIT=80_000_000
BENEFIT_GROWTH_RATE = 0.04
INTEREST_RATE = 0.03
SERVICE_COST_RATE = 0.14
ANNUAL_DURATION_DECLINE = 0.15
ACTIVE_MEMBER_DECLINE = 50 # per year
RETIRED_MEMBERS_GROWTH = 100 # per year
MIN_ACTIVE_MEMBERS = 8_000
INITIAL_DURATION = 14.5



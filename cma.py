

RETURNS = {
    "cash" : 0.024,
    "cad_equity" : 0.063,
    "usd_equity" : 0.064,
    "em_equity" : 0.075,
    "id_equity" : 0.066,
    "fixed_income" : 0.032,
    "private_equity" : 0.084,
    "infrastructure" : 0.067,
    "real_estate" : 0.082,
}

COVARIANCE = [
    [1,2,3,4,5],
    [1,2,3,4,5],
    [1,2,3,4,5],
    [1,2,3,4,5],
    [1,2,3,4,5],
]

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

BENEFIT_GROWTH_RATE = 0.04
RFR = 0.03
SERVICE_COST_RATE = 0.014
ANNUAL_DURATION_DECLINE = 0.15
ACTIVE_MEMBER_DECLINE = 50 # per year
RETIRED_MEMBERS_GROWTH = 100 # per year
MIN_ACTIVE_MEMBERS = 8_000
INITIAL_DURATION = 14.5

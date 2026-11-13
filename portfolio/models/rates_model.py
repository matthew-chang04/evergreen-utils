from rateslib import Curve, Solver, add_tenor, IRS
from datetime import datetime as dt




TMP_CORRA_CURVE = ["1M", "2M", "3M", "6M", "1Y", "2Y", "3Y", "4Y", "5Y", "6Y", "7Y", "8Y", "9Y", "10Y", "12Y", "15Y", "20Y", "25Y", "30Y", "35Y", "40Y", "45Y", "50Y"]
CORRA_QUOTES = {
    "tenor" : TMP_CORRA_CURVE,
    "quotes" : [0.025 + i * 0.0005 for i in range(len(TMP_CORRA_CURVE))]
}


class RatesConfig: 
    
    dx = 1/12
    dy = 1/12

    def __init__(self, anchor_dt : dt, ccy : str):

        match ccy:
            case "USD" | "CAD":
                quotes = CORRA_QUOTES
            case _:
                raise ValueError(f"Unsupported currency for rates model: {ccy}")

        mats = [add_tenor(anchor_dt, tenor, "MF") for tenor in quotes["tenor"]]

        self.df_curve = Curve(
            interpolation="log_linear",
            nodes={
                anchor_dt: 1.0,
                **{d: 1.0 for d in mats},
            },
            convention="Act365F", 
        )

        solver = Solver(
            curves=[self.df_curve],
            instruments=[
                IRS(anchor_dt, mat, spec=f"{ccy.lower()}_irs", curves=self.df_curve)
                for mat in mats
            ],
            s=quotes["quotes"],
        )

    


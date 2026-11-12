from rateslib import Curve
from datetime import date as dt

class RatesConfig: 
    
    dx = 1/12
    dy = 1/12

    def __init__(self, anchor_dt : dt, ):

        self.df_curve = Curve(
            nodes={

            } 
        )


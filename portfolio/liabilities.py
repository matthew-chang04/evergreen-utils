from dataclasses import dataclass

@dataclass
class Liabilities:

    retired_members : int
    active_members : int
    average_salary : float

    min_active_members : int
    active_members_decline : int

    retired_members_growth : int

    wage_growth_rate : float
    starting_duration : float
    actuarial_df : float
    service_cost : float

    starting_liabilities : float

    starting_benefit : float
    benefit_growth_rate : float

    # maps years to value
    liabilities_cache : dict[int, float]

    def __post_init__(self):
        self.liabilities_cache[0] = self.starting_liabilities

    def get_active_members(self, t: int) -> int:        
        return max(self.active_members - (t * self.active_members_decline), self.min_active_members)

    def get_retired_members(self, t: int) -> int:
        return self.retired_members + (t * self.retired_members_growth)

    def get_total_members(self, t: int) -> int:
        return self.get_active_members(t) + self.get_retired_members(t)

    def get_payroll(self, t: int) -> float:
        payroll = self.get_active_members(t) * self.average_salary
        return payroll * ((1 + self.wage_growth_rate) ** t)

    def get_service_cost(self, t: int)  -> float:
        if t <= 0:
            return 0.0
        
        p = self.get_payroll(t)
        return self.service_cost * p

    def get_interest_cost(self, t: int) -> float:
        if t <= 0:
            return 0.0

        liabilities = self.get_closing_liabilities(t - 1)
        return liabilities * self.actuarial_df

    def benefits_paid(self, t) -> float:
        if t <= 0:
            return 0.0
        
        return self.starting_benefit * ((1 + self.benefit_growth_rate) ** t)

    def get_closing_liabilities(self, t: int) -> float:
        if t <= 0:
            return self.liabilities_cache[0]
        elif t in self.liabilities_cache:
            return self.liabilities_cache[t]
        else:
            t_1_liabilities = self.get_closing_liabilities(t-1)
            closing_liabilities = t_1_liabilities + self.get_service_cost(t) + self.get_interest_cost(t) - self.benefits_paid(t)
            self.liabilities_cache[t] = closing_liabilities
            return closing_liabilities

    
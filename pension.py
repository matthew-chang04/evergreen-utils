from dataclasses import dataclass


class Liabilities:

    retired_members : int
    active_members : int
    average_salary : float

    min_active_members : int
    active_members_decline : int

    retired_members_growth : int

    wage_growth_rate : float
    starting_duration : float
    rfr : float
    service_cost : float

    starting_liabilities : float


    def get_active_members(self, t: int) -> int:
        return max(self.active_members - (t * self.active_members_decline), self.min_active_members)

    def get_retired_members(self, t: int) -> int:
        return self.retired_members + (t * self.retired_members_growth)

    def get_total_members(self, t: int) -> int:
        return self.get_active_members(t) + self.get_retired_members(t)

    def get_payroll(self, t: int) -> float:
        payroll = self.active_members * self.average_salary

        return payroll * ((1 + self.wage_growth_rate) ** t)

    def get_service_cost(self, t: int)  -> float:

        p = self.get_payroll(t)

        return self.service_cost * p
    
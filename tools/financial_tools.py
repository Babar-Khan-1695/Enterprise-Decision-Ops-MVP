def roi_percent(investment, annual_net_benefit):
    if not investment:
        return None
    return round((annual_net_benefit / investment) * 100, 2)


def payback_years(investment, annual_net_benefit):
    if annual_net_benefit <= 0:
        return None
    return round(investment / annual_net_benefit, 2)

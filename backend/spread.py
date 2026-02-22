def check_arbitrage(event, k_yes, k_no, p_yes, p_no, volume=100):
    # the whole issue with calculating regular arbitrage is that kalsi and PM have fees.
    # so we need to be able to calculate our arbitrage WITH the fees included such that we know that it is a pure market opportunity

    # using kalshi as 0.07 * price * (1 - price)
    # using 0.10% hard cap for pm (theirs is dynamic tho)
    opportunities = []

    # yes kalshi, no PM
    gross_1 = k_yes + p_no
    if gross_1 < 1.00:
        k_fee = 0.07 * k_yes * (1 - k_yes)
        p_fee = 0.0010 * p_no

        net_1 = gross_1 + k_fee + p_fee
        if net_1 < 1.00:
            profit = 1.00 - net_1
            opportunities.append({
                "event": event,
                "strategy": "Buy Kalshi YES, Buy Poly NO",
                "net_cost": round(net_1, 4),
                "profit_per_contract": round(profit, 4),
                "total_expected_profit": round(profit * volume, 2)
            })

    # no on kalshi, yes on pm
    gross_2 = k_no + p_yes

    if gross_2 < 1.00:
        k_fee = 0.07 * k_no * (1 - k_no)
        p_fee = 0.0010 * p_yes

        net_2 = gross_2 + k_fee + p_fee
        if net_2 < 1.00:
            profit = 1.00 - net_2
            opportunities.append({
                "event": event,
                "strategy": "Buy Kalshi NO, Buy Poly YES",
                "net_cost": round(net_2, 4),
                "profit_per_contract": round(profit, 4),
                "total_expected_profit": round(profit * volume, 2)
            })

    return opportunities

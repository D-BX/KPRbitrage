def get_poly_blend(asks, target_volume):
    if not asks:
        return None
    
    # we essentially need to buy all the volume at our best price, and if there's remaining we move slowly down
    tot_cost = 0.0
    volume_filled = 0.0
    
    for order in asks:
        price = float(order["price"])
        size = float(order["size"])
        
        if volume_filled + size >= target_volume:
            remaining_vol = target_volume - volume_filled
            tot_cost += remaining_vol * price
            volume_filled = target_volume
            break
        else:
            tot_cost += size * price
            volume_filled += size
    
    # abort trade if the book if empty before we fill the volume
    if volume_filled < target_volume:
        return None 
        
    return tot_cost / target_volume

def get_kalshi_blend(opposing_bids, target_volume):
    if not opposing_bids:
        return None
    # same as PM
    total_cost = 0.0
    volume_filled = 0.0
    
    # iterate backwards because the best bid is at the very end of the array
    for i in range(len(opposing_bids) - 1, -1, -1):
        bid_price_cents = opposing_bids[i][0]
        size = opposing_bids[i][1]
        
        ask_price_dollars = (100 - bid_price_cents) / 100.0
        
        if volume_filled + size >= target_volume:
            remaining_vol = target_volume - volume_filled
            total_cost += remaining_vol * ask_price_dollars
            volume_filled = target_volume
            break
        else:
            total_cost += size * ask_price_dollars
            volume_filled += size
            
    if volume_filled < target_volume:
        return None
        
    return total_cost / target_volume


def check_arbitrage(event, k_book, p_yes_book, p_no_book, volume=100):
    # the whole issue with calculating regular arbitrage is that kalsi and PM have fees.
    # so we need to be able to calculate our arbitrage WITH the fees included such that we know that it is a pure market opportunity

    # using kalshi as 0.07 * price * (1 - price)
    # using 0.10% hard cap for pm (theirs is dynamic tho)
    opportunities = []
    k_yes_ask = get_kalshi_blend(k_book.get("no", []), volume)
    p_no_ask = get_poly_blend(p_no_book.get("asks", []), volume)



    # yes kalshi, no PM
    if k_yes_ask is not None and p_no_ask is not None:
        gross_1 = k_yes_ask + p_no_ask
        
        if gross_1 < 1.00:
            k_fee = 0.07 * k_yes_ask * (1 - k_yes_ask)
            p_fee = 0.0010 * p_no_ask 
            
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
    k_no_ask = get_kalshi_blend(k_book.get("yes", []), volume)
    p_yes_ask = get_poly_blend(p_yes_book.get("asks", []), volume)

    if k_no_ask is not None and p_yes_ask is not None:
        gross_2 = k_no_ask + p_yes_ask
        
        if gross_2 < 1.00:
            k_fee = 0.07 * k_no_ask * (1 - k_no_ask)
            p_fee = 0.0010 * p_yes_ask 
            
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

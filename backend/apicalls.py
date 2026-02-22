import asyncio
import aiohttp

async def get_kalshi(session):
    url = "https://api.elections.kalshi.com/trade-api/v2/markets?status=open"
    async with session.get(url) as response:
        data = await response.json()
        return [{"id": m["ticker"], "question": m["title"]} for m in data.get("markets", [])]
    
async def get_polymarket(session):
    # limiting the market for now - testing ts out
    url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100"
    async with session.get(url) as response:
        markets = await response.json()
        
        return [{
            "id": m.get("condition_id"), 
            "question": m.get("question"),
            "yes_token": m.get("clobTokenIds", [None, None])[0] if m.get("clobTokenIds") else None,
            "no_token": m.get("clobTokenIds", [None, None])[1] if len(m.get("clobTokenIds", [])) > 1 else None
        } for m in markets]

async def call_markets():
    # running both requests concurrently
    async with aiohttp.ClientSession() as session:
        k_task = asyncio.create_task(get_kalshi(session))
        p_task = asyncio.create_task(get_polymarket(session))

        k_data, p_data = await asyncio.gather(k_task, p_task)
        return k_data, p_data
    
async def kalshi_books(session, ticker):
    # full order book from kalshi
    url = f"https://api.elections.kalshi.com/trade-api/v2/markets/{ticker}/orderbook"    
    async with session.get(url) as response:
        if response.status == 200:
            data = await response.json()
            return data.get("orderbook", {"yes": [], "no": []})
        
        return {"yes": [], "no": []}

async def polymarket_books(session, token_id):
    url = f"https://clob.polymarket.com/book?token_id={token_id}"
    async with session.get(url) as response:
        if response.status == 200:
            data = await response.json()
            return {
                "bids": data.get("bids", []),
                "asks": data.get("asks", [])
            }
        return {"bids": [], "asks": []}

if __name__ == "__main__":
    k_markets, p_markets = asyncio.run(call_markets())
    print(f"got {len(k_markets)} kalshi books")
    print(f"got {len(p_markets)} polymarket books")
    if p_markets:
        print(f"test polymarket tokens: yah={p_markets[0]['yes_token']}, naur={p_markets[0]['no_token']}")
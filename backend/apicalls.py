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
        return [{"id": m["condition_id"], "question": m["question"]} for m in markets]

async def call_markets():
    # running both requests concurrently
    async with aiohttp.ClientSession() as session:
        k_task = asyncio.create_task(get_kalshi(session))
        p_task = asyncio.create_task(get_polymarket(session))

        k_data, p_data = await asyncio.gather(k_task, p_task)
        return k_data, p_data
    
k_markets, p_markets = asyncio.run(call_markets())


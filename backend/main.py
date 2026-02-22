import asyncio
import aiohttp
from apicalls import call_markets, kalshi_books, polymarket_books
from nlpsem import market_match
from spread import check_arbitrage
from alerts import discord_alerts
from database import init_db, get_cached_matches, save_new_matches

WEBHOOK_URL = "https://discord.com/api/webhooks/1475157685904216115/Ehv4kth_mHbSjTWa6wLusYvQ3fdOgk18Dg9gY3pTcok4LtSUqLxEmHzBg6ENbJsMhjDN"

async def runner(volume_size=100, interval=30):
    print("starting bot")

    await init_db()

    # using one session to reuse connection for speed >:)
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                print("getting live market")
                k_markets, p_markets = await call_markets()

                cached_matches = await get_cached_matches()
                unmapped_k_markets = [m for m in k_markets if m["id"] not in cached_matches]


                if unmapped_k_markets:
                    print(f"running nlp on {len(unmapped_k_markets)} new markets")
                    new_matches = market_match(unmapped_k_markets, p_markets, threshold=0.85)
                    # arbitrary threshold for profits imma stick w 0.85 for now

                    if new_matches:
                        print(f"found {len(new_matches)} new matches to save to DB")
                        await save_new_matches(new_matches)
                        cached_matches = await get_cached_matches()
                else:
                    print("all markets cached - skipping NLP")

                print(f"checking the spread and books for {len(cached_matches)} cached markets")

                # checking the spread and books using the cache
                for kalshi_id, match_data in cached_matches.items():
                    
                    yes_token = match_data.get("poly_yes_token")               
                    no_token = match_data.get("poly_no_token")

                    # pm token ids are missing
                    if not yes_token or not no_token:
                        continue

                    k_book_task = asyncio.create_task(kalshi_books(session, kalshi_id))
                    p_yes_task = asyncio.create_task(polymarket_books(session, yes_token))
                    p_no_task = asyncio.create_task(polymarket_books(session, no_token))

                    k_book, p_yes_book, p_no_book = await asyncio.gather(k_book_task, p_yes_task, p_no_task)

                    # spread calc
                    arbs = check_arbitrage(
                        event = match_data["kalshi_question"],
                        k_book = k_book,
                        p_yes_book = p_yes_book,
                        p_no_book = p_no_book,
                        volume=volume_size
                    )

                    if arbs:
                        for arb in arbs:
                            print("found profit")
                            print(f"event: {arb['event']}")
                            print(f"strat: {arb['strategy']}")
                            print(f"net cost: ${arb['net_cost']}")
                            print(f"money makin: ${arb['total_expected_profit']}\n")

                            # async discord alert
                            await discord_alerts(session, WEBHOOK_URL, arb)

            except Exception as e:
                print(f"network or parsing error {e}")
            
            print(f"done scanning, sleeping for {interval}")
            await asyncio.sleep(interval)

if __name__ == "__main__":
    asyncio.run(runner(volume_size=20, interval=10))
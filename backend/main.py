import asyncio
import aiohttp
from apicalls import call_markets, kalshi_books, polymarket_books
from nlpsem import market_match
from spread import check_arbitrage
from alerts import discord_alerts

WEBHOOK_URL = "https://discord.com/api/webhooks/1475157685904216115/Ehv4kth_mHbSjTWa6wLusYvQ3fdOgk18Dg9gY3pTcok4LtSUqLxEmHzBg6ENbJsMhjDN"

async def runner(volume_size=100, interval=30):
    print("starting bot")

    # using one session to reuse connection for speed >:)
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                print("getting live market")
                k_markets, p_markets = await call_markets()

                print("NLP semantics")
                matches = market_match(k_markets, p_markets, threshold=0.85)
                # arbitrary threshold for profits imma stick w 0.85 for now

                print(f"found {len(matches)} markets")

                # checking the spread and books
                for match in matches:
                    k_event = match["kalshi_event"]
                    p_event = match["poly_event"]

                    yes_token = p_event.get("yes_token")               
                    no_token = p_event.get("no_token")

                    # pm token ids are missing
                    if not yes_token or not no_token:
                        continue

                    k_book_task = asyncio.create_task(kalshi_books(session, k_event["id"]))
                    p_yes_task = asyncio.create_task(polymarket_books(session, yes_token))
                    p_no_task = asyncio.create_task(polymarket_books(session, no_token))

                    k_book, p_yes_book, p_no_book = await asyncio.gather(k_book_task, p_yes_task, p_no_task)

                    # spread calc
                    arbs = check_arbitrage(
                        event = k_event["question"],
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
    asyncio.run(runner(volume_size=20, interval=2))
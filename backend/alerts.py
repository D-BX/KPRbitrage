import aiohttp

async def discord_alerts(session, webhook, arb_data):
    if not webhook:
        return

    message = (
        f"Found Profit\n"
        f"Event {arb_data['event']}\n"
        f"Action {arb_data['strategy']}\n"
        f"Total Net Cost${arb_data['net_cost']}\n"
        f"**Total Profit:** ${arb_data['total_expected_profit']}\n"
        f"-----------------------------------------"
    )

    payload = {"content": message}

    try:
        async with session.post(webhook, json=payload) as response:
            if response.status not in (200, 204):
                print(f"Failed to send Discord alert error: {response.status}")
    except Exception as e:
        print(f"Discord Webhook error: {e}")
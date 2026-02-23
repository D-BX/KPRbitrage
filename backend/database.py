import asyncpg
import os

DB_URI = os.getenv("DB_URI", "postgresql://app:arb_secret@localhost:5432/vectordb")

async def init_db():
    # creating a caching table
    conn = await asyncpg.connect(DB_URI)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS market_cache (
            kalshi_id TEXT PRIMARY KEY,
            kalshi_question TEXT,
            poly_yes_token TEXT,
            poly_no_token TEXT,
            confidence_score FLOAT
        );
    ''')
    print("cache table is good")
    await conn.close()

async def get_cached_matches():
    conn = await asyncpg.connect(DB_URI)
    rows = await conn.fetch("SELECT kalshi_id, kalshi_question, poly_yes_token, poly_no_token FROM market_cache")
    await conn.close()
    
    return {row["kalshi_id"]: dict(row) for row in rows}

async def save_new_matches(matches):
    if not matches:
        return
        
    conn = await asyncpg.connect(DB_URI)
    for match in matches:
        k_event = match["kalshi_event"]
        p_event = match["poly_event"]
        score = match["confidence_score"]
        
        await conn.execute('''
            INSERT INTO market_cache (kalshi_id, kalshi_question, poly_yes_token, poly_no_token, confidence_score)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (kalshi_id) DO NOTHING;
        ''', k_event["id"], k_event["question"], p_event["yes_token"], p_event["no_token"], score)
        
    await conn.close()
    print(f"New {len(matches)} market pairs saved to the db")

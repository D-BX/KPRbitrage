import asyncio
import asyncpg
from pgvector.asyncpg import register_vector

DB_URI = "postgresql://app:arb_secret@localhost:5432/vectordb"

async def init_db_and_insert(matches):
    conn = await asyncpg.connect(DB_URI)
    
    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    await register_vector(conn)
    
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS kalshi_events (
            id TEXT PRIMARY KEY,
            question TEXT,
            embedding vector(384)
        );
        
        CREATE TABLE IF NOT EXISTS polymarket_events (
            id TEXT PRIMARY KEY,
            question TEXT,
            embedding vector(384)
        );
        
        CREATE TABLE IF NOT EXISTS event_mapping (
            kalshi_id TEXT REFERENCES kalshi_events(id),
            poly_id TEXT REFERENCES polymarket_events(id),
            confidence_score FLOAT,
            mapped_at TIMESTAMPTZ DEFAULT NOW(),
            PRIMARY KEY (kalshi_id, poly_id)
        );
    ''')
    print("Schema initialized.")

    for match in matches:
        kalshi = match["kalshi_event"]
        poly = match["poly_event"]
        score = match["confidence_score"]
        
        await conn.execute(
            "INSERT INTO kalshi_events (id, question) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            kalshi["id"], kalshi["question"]
        )
        
        await conn.execute(
            "INSERT INTO polymarket_events (id, question) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            poly["id"], poly["question"]
        )
        
        await conn.execute(
            "INSERT INTO event_mapping (kalshi_id, poly_id, confidence_score) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
            kalshi["id"], poly["id"], score
        )
        
    print(f"Successfully inserted {len(matches)} matched event pairs into the database.")
    await conn.close()

asyncio.run(init_db_and_insert(matched_pairs))
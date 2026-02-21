from sentence_transformers import SentenceTransformer, util

# gonna use a model from hugging-face, sentence-transformers which is pretty lightweight

model = SentenceTransformer('all-MiniLM-L6-v2')

def market_match(kalshi_markets, poly_markets, threshold=0.85):
    # we need to be above a certain threshold when we compare a question from kalshi and polymarket
    k_questions = [m["question"] for m in kalshi_markets]
    p_questions = [m["question"] for m in poly_markets]

    print("testing generating embeddings")

    k_embed = model.encode(k_questions, convert_to_tensor=True)
    p_embed = model.encode(p_questions, convert_to_tensor=True)

    # computing cosine similarity btwn pairs -> returns a matrix of size len(k quest) * len(p quest)
    cosine_scores = util.cos_sim(k_embed, p_embed)

    matches = []
    
    # finding pairs that exceed the similarity threshold
    for i in range(len(kalshi_markets)):
        for j in range(len(poly_markets)):
            score = cosine_scores[i][j].item()

            if score >= threshold:
                matches.append({
                    "kalshi_event": kalshi_markets[i],
                    "poly_event": poly_markets[j],
                    "confidence_score": round(score, 4)
                })

                
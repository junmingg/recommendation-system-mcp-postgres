import os
import pickle

_M = None


def _load():
    global _M
    if _M is None:
        path = os.environ.get("RECS_MODEL", "models/als.pkl")
        if not os.path.exists(path):
            raise RuntimeError("Recommender not trained. Run scripts/train_recs.py first.")
        with open(path, "rb") as f:
            _M = pickle.load(f)
    return _M


def recommend_for_user(customer_id: str, k: int = 10) -> list[dict]:
    d = _load()
    if customer_id not in d["u_idx"]:
        return []   # cold-start user: no history
    u = d["u_idx"][customer_id]
    ids, scores = d["model"].recommend(u, d["matrix"][u], N=k, filter_already_liked_items=True)
    return [{"stock_code": d["items"][i], "score": float(s)} for i, s in zip(ids, scores)]


def similar_items(stock_code: str, k: int = 10) -> list[dict]:
    d = _load()
    if stock_code not in d["i_idx"]:
        return []
    it = d["i_idx"][stock_code]
    ids, scores = d["model"].similar_items(it, N=k)
    return [{"stock_code": d["items"][i], "score": float(s)} for i, s in zip(ids, scores)]

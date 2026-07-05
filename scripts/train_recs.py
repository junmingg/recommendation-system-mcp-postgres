import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")   # avoid BLAS thread oversubscription
import pickle
import scipy.sparse as sp
import psycopg
from implicit.als import AlternatingLeastSquares

DSN = os.environ.get("DATABASE_URL", "postgresql://readonly:readonly@localhost:5432/demo")
MODEL_PATH = os.environ.get("RECS_MODEL", "models/als.pkl")
FACTORS, REG, ITERS, K = 64, 0.05, 20, 10


def fetch():
    with psycopg.connect(DSN) as c, c.cursor() as cur:
        cur.execute("""SELECT customer_id, stock_code, SUM(quantity)::float AS qty
                       FROM transactions
                       WHERE customer_id IS NOT NULL AND quantity > 0
                       GROUP BY customer_id, stock_code""")
        return cur.fetchall()


def build(rows):
    users = sorted({r[0] for r in rows}); items = sorted({r[1] for r in rows})
    u_idx = {u: i for i, u in enumerate(users)}; i_idx = {it: j for j, it in enumerate(items)}
    ui, ij, val = [], [], []
    for u, it, q in rows:
        ui.append(u_idx[u]); ij.append(i_idx[it]); val.append(1.0 + 0.5 * q)   # confidence
    mat = sp.csr_matrix((val, (ui, ij)), shape=(len(users), len(items)))
    return mat, users, items, u_idx, i_idx


def leave_last_out(mat):
    """Hold out one interaction per user (>=2 interactions) for eval."""
    train = mat.tolil(copy=True); test = {}
    m = mat.tocsr()
    for u in range(m.shape[0]):
        cols = m.indices[m.indptr[u]:m.indptr[u+1]]
        if len(cols) >= 2:
            test[u] = cols[-1]; train[u, cols[-1]] = 0
    return train.tocsr(), test


def evaluate(model, train, test, k=K):
    hits = 0
    for u, held in test.items():
        ids, _ = model.recommend(u, train[u], N=k, filter_already_liked_items=True)
        hits += int(held in ids)
    n = len(test)
    # with 1 held-out item per user, recall@k == hit-rate@k
    return {"users": n, f"recall@{k}": round(hits/n, 4), f"precision@{k}": round(hits/(n*k), 4)}


def main():
    rows = fetch()
    mat, users, items, u_idx, i_idx = build(rows)
    train, test = leave_last_out(mat)
    m = AlternatingLeastSquares(factors=FACTORS, regularization=REG, iterations=ITERS, random_state=42)
    m.fit(train)
    print("EVAL:", evaluate(m, train, test))
    # retrain on the full matrix for serving
    final = AlternatingLeastSquares(factors=FACTORS, regularization=REG, iterations=ITERS, random_state=42)
    final.fit(mat)
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump({"model": final, "items": items, "u_idx": u_idx, "i_idx": i_idx, "matrix": mat}, f)
    print("Saved", MODEL_PATH)


if __name__ == "__main__":
    main()

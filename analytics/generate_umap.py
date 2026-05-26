"""
UMAP projections — VISUALIZATION ONLY, not for analytics.
Generates 2D projections for each space + composite.
"""
import os, sys, json
import numpy as np
import pyarrow.parquet as pq
import umap

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

PARQUET_PATH = "ecosystem_graph/frontier_ecosystem.parquet"
OUTPUT_DIR = "ecosystem_graph/projections"


def load_data():
    table = pq.read_table(PARQUET_PATH)
    ids = table.column("project_id").to_pylist()
    names = table.column("project_name").to_pylist()
    archetypes = table.column("primary_archetype").to_pylist()
    countries = table.column("country").to_pylist()
    categories = table.column("category").to_pylist()
    product = np.array([v.as_py() for v in table.column("product_vector")], dtype=np.float32)
    technical = np.array([v.as_py() for v in table.column("technical_vector")], dtype=np.float32)
    market = np.array([v.as_py() for v in table.column("market_vector")], dtype=np.float32)
    return ids, names, archetypes, countries, categories, product, technical, market


def run_umap(vectors, space_name, n_neighbors=15, min_dist=0.1, metric='cosine'):
    print(f"  Projecting {space_name} to 2D...")
    reducer = umap.UMAP(
        n_components=2,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        metric=metric,
        random_state=42,
        verbose=False
    )
    coords = reducer.fit_transform(vectors)
    return coords


def main():
    print("=" * 60)
    print("UMAP PROJECTIONS (visualization only)")
    print("=" * 60)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    ids, names, archetypes, countries, categories, product, technical, market = load_data()

    # Load cluster labels if available
    clusters = {}
    for space in ["product", "technical", "market"]:
        cl_path = os.path.join("../ecosystem_graph/clusters", f"{space}_clusters.json")
        if os.path.exists(cl_path):
            with open(cl_path, "r") as f:
                data = json.load(f)
            clusters[space] = {d["project_id"]: d["cluster"] for d in data}

    for space_name, vectors in [("product", product), ("technical", technical), ("market", market)]:
        coords = run_umap(vectors, space_name)

        points = []
        for i, pid in enumerate(ids):
            point = {
                "project_id": pid,
                "project_name": names[i],
                "archetype": archetypes[i],
                "country": countries[i],
                "category": categories[i],
                "x": float(coords[i, 0]),
                "y": float(coords[i, 1]),
            }
            if space_name in clusters and pid in clusters[space_name]:
                point["cluster"] = clusters[space_name][pid]
            points.append(point)

        out_path = os.path.join(OUTPUT_DIR, f"{space_name}_umap.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(points, f, ensure_ascii=False)
        print(f"    -> {out_path} ({len(points)} points)")

    # Composite UMAP: concatenate normalized vectors
    print(f"  Projecting composite to 2D...")
    from sklearn.preprocessing import normalize
    composite = np.hstack([
        normalize(product) * 0.5,
        normalize(technical) * 0.3,
        normalize(market) * 0.2
    ])
    coords = run_umap(composite, "composite", metric='euclidean')
    points = []
    for i, pid in enumerate(ids):
        points.append({
            "project_id": pid,
            "project_name": names[i],
            "archetype": archetypes[i],
            "country": countries[i],
            "category": categories[i],
            "x": float(coords[i, 0]),
            "y": float(coords[i, 1]),
        })
    out_path = os.path.join(OUTPUT_DIR, "composite_umap.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(points, f, ensure_ascii=False)
    print(f"    -> {out_path}")

    print(f"\n{'=' * 60}")
    print("DONE — 4 UMAP projections generated")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

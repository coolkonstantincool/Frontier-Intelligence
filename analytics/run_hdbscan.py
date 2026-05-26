"""
HDBSCAN clustering on raw vectors (NOT on UMAP projections).
Produces cluster assignments for each space + composite.
"""
import os, sys, json
import numpy as np
import pyarrow.parquet as pq
from hdbscan import HDBSCAN

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

PARQUET_PATH = "ecosystem_graph/frontier_ecosystem.parquet"
OUTPUT_DIR = "ecosystem_graph/clusters"


def load_data():
    table = pq.read_table(PARQUET_PATH)
    ids = table.column("project_id").to_pylist()
    names = table.column("project_name").to_pylist()
    archetypes = table.column("primary_archetype").to_pylist()
    product = np.array([v.as_py() for v in table.column("product_vector")], dtype=np.float32)
    technical = np.array([v.as_py() for v in table.column("technical_vector")], dtype=np.float32)
    market = np.array([v.as_py() for v in table.column("market_vector")], dtype=np.float32)
    return ids, names, archetypes, product, technical, market


import umap

def run_hdbscan(vectors, space_name, min_cluster_size=10, min_samples=3):
    print(f"\n  Running UMAP reduction + HDBSCAN on {space_name} space ({vectors.shape})...")
    reducer = umap.UMAP(n_neighbors=15, min_dist=0.0, n_components=5, random_state=42)
    reduced_vectors = reducer.fit_transform(vectors)

    clusterer = HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric='euclidean',
        cluster_selection_method='eom'
    )
    labels = clusterer.fit_predict(reduced_vectors)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = (labels == -1).sum()
    print(f"    Clusters: {n_clusters}")
    print(f"    Noise points: {n_noise} ({n_noise/len(labels)*100:.1f}%)")
    return labels, clusterer


def main():
    print("=" * 60)
    print("HDBSCAN CLUSTERING (on raw vectors)")
    print("=" * 60)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    ids, names, archetypes, product, technical, market = load_data()

    all_results = {}
    for space_name, vectors in [("product", product), ("technical", technical), ("market", market)]:
        labels, clusterer = run_hdbscan(vectors, space_name)

        assignments = []
        for i, pid in enumerate(ids):
            assignments.append({
                "project_id": pid,
                "project_name": names[i],
                "archetype": archetypes[i],
                "cluster": int(labels[i]),
                "outlier_score": float(clusterer.outlier_scores_[i]) if hasattr(clusterer, 'outlier_scores_') else 0.0
            })
        all_results[space_name] = assignments

        out_path = os.path.join(OUTPUT_DIR, f"{space_name}_clusters.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(assignments, f, indent=2, ensure_ascii=False)

        # Cluster summary
        cluster_map = {}
        for a in assignments:
            cl = a["cluster"]
            if cl not in cluster_map:
                cluster_map[cl] = []
            cluster_map[cl].append(a["archetype"])

        print(f"    Top clusters:")
        for cl_id in sorted(cluster_map.keys(), key=lambda x: -len(cluster_map[x]))[:5]:
            members = cluster_map[cl_id]
            from collections import Counter
            top_arch = Counter(members).most_common(3)
            label = "NOISE" if cl_id == -1 else f"Cluster {cl_id}"
            archs = ", ".join(f"{a}({c})" for a, c in top_arch)
            print(f"      {label}: {len(members)} projects — {archs}")

    # Save combined
    combined_path = os.path.join(OUTPUT_DIR, "all_clusters.json")
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print("DONE")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

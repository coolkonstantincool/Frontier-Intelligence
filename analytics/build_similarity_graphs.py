"""
Build k-NN similarity graphs for each vector space.
Output: 3 independent neighbor graphs + 1 composite graph.
Analytics on RAW vectors, NOT on UMAP projections.
"""
import os
import sys
import json
import numpy as np
import pyarrow.parquet as pq
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

PARQUET_PATH = "ecosystem_graph/frontier_ecosystem.parquet"
OUTPUT_DIR = "ecosystem_graph/graphs"
K = 20  # top-k neighbors


def load_vectors_from_parquet():
    table = pq.read_table(PARQUET_PATH)
    ids = table.column("project_id").to_pylist()
    names = table.column("project_name").to_pylist()
    archetypes = table.column("primary_archetype").to_pylist()

    product = np.array([v.as_py() for v in table.column("product_vector")], dtype=np.float32)
    technical = np.array([v.as_py() for v in table.column("technical_vector")], dtype=np.float32)
    market = np.array([v.as_py() for v in table.column("market_vector")], dtype=np.float32)

    return ids, names, archetypes, product, technical, market


def build_knn_graph(ids, names, archetypes, vectors, space_name, k=K):
    """Build k-NN graph using cosine similarity on raw vectors."""
    print(f"  Computing cosine similarity matrix for {space_name}...")
    sim_matrix = cosine_similarity(vectors)

    G = nx.DiGraph()
    for i, pid in enumerate(ids):
        G.add_node(pid, name=names[i], archetype=archetypes[i])

    edges = []
    for i in range(len(ids)):
        # Get top-k neighbors (exclude self)
        sims = sim_matrix[i].copy()
        sims[i] = -1  # exclude self
        top_indices = np.argsort(sims)[-k:][::-1]

        for j in top_indices:
            weight = float(sims[j])
            if weight > 0:
                G.add_edge(ids[i], ids[j], weight=weight)
                edges.append({
                    "source": ids[i],
                    "target": ids[j],
                    "similarity": round(weight, 6)
                })

    return G, edges, sim_matrix


def build_composite_graph(ids, names, archetypes, product_sim, technical_sim, market_sim,
                          w_product=0.5, w_technical=0.3, w_market=0.2, k=K):
    """Composite similarity = weighted sum of per-space cosine similarities."""
    print(f"  Computing composite similarity (weights: {w_product}/{w_technical}/{w_market})...")
    composite_sim = w_product * product_sim + w_technical * technical_sim + w_market * market_sim

    G = nx.DiGraph()
    for i, pid in enumerate(ids):
        G.add_node(pid, name=names[i], archetype=archetypes[i])

    edges = []
    for i in range(len(ids)):
        sims = composite_sim[i].copy()
        sims[i] = -1
        top_indices = np.argsort(sims)[-k:][::-1]

        for j in top_indices:
            weight = float(sims[j])
            if weight > 0:
                G.add_edge(ids[i], ids[j], weight=weight)
                edges.append({
                    "source": ids[i],
                    "target": ids[j],
                    "similarity": round(weight, 6)
                })

    return G, edges


def main():
    print("=" * 60)
    print("SIMILARITY GRAPH BUILDER")
    print("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    ids, names, archetypes, product, technical, market = load_vectors_from_parquet()
    print(f"Loaded {len(ids)} projects.\n")

    # Build per-space graphs
    results = {}
    for space_name, vectors in [("product", product), ("technical", technical), ("market", market)]:
        G, edges, sim_matrix = build_knn_graph(ids, names, archetypes, vectors, space_name)
        results[space_name] = {"graph": G, "edges": edges, "sim_matrix": sim_matrix}

        # Save edges
        edge_path = os.path.join(OUTPUT_DIR, f"{space_name}_neighbors.json")
        with open(edge_path, "w", encoding="utf-8") as f:
            json.dump(edges, f, ensure_ascii=False)
        print(f"  {space_name}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges -> {edge_path}")

    # Build composite graph
    G_comp, comp_edges = build_composite_graph(
        ids, names, archetypes,
        results["product"]["sim_matrix"],
        results["technical"]["sim_matrix"],
        results["market"]["sim_matrix"]
    )
    comp_path = os.path.join(OUTPUT_DIR, "composite_neighbors.json")
    with open(comp_path, "w", encoding="utf-8") as f:
        json.dump(comp_edges, f, ensure_ascii=False)
    print(f"  composite: {G_comp.number_of_nodes()} nodes, {G_comp.number_of_edges()} edges -> {comp_path}")

    # Save sim matrices as .npy for downstream analytics
    for space_name in ["product", "technical", "market"]:
        np.save(os.path.join(OUTPUT_DIR, f"{space_name}_sim_matrix.npy"), results[space_name]["sim_matrix"])
    print(f"\nSimilarity matrices saved as .npy files.")

    print(f"\n{'=' * 60}")
    print("DONE")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

"""
Topology Diagnostics — The most important analytics module.
Detects: semantic collapse, ontology leakage, bridge nodes,
space divergence, density asymmetry, primitive convergence.
"""
import os, sys, json
import numpy as np
import pyarrow.parquet as pq
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

PARQUET_PATH = "ecosystem_graph/frontier_ecosystem.parquet"
GRAPHS_DIR = "ecosystem_graph/graphs"
OUTPUT_DIR = "ecosystem_graph/diagnostics"


def load_data():
    table = pq.read_table(PARQUET_PATH)
    ids = table.column("project_id").to_pylist()
    names = table.column("project_name").to_pylist()
    archetypes = table.column("primary_archetype").to_pylist()
    countries = table.column("country").to_pylist()
    categories = table.column("category").to_pylist()
    domains = [json.loads(d) for d in table.column("ecosystem_domains").to_pylist()]
    product = np.array([v.as_py() for v in table.column("product_vector")], dtype=np.float32)
    technical = np.array([v.as_py() for v in table.column("technical_vector")], dtype=np.float32)
    market = np.array([v.as_py() for v in table.column("market_vector")], dtype=np.float32)
    return ids, names, archetypes, countries, categories, domains, product, technical, market


def detect_semantic_collapse(sim_matrix, ids, archetypes, space_name, threshold=0.92):
    """Detect clusters where too many projects are near-identical."""
    print(f"\n  [{space_name}] Semantic collapse detection (threshold={threshold})...")
    collapse_pairs = []
    for i in range(len(ids)):
        for j in range(i+1, len(ids)):
            if sim_matrix[i][j] > threshold:
                collapse_pairs.append({
                    "a": ids[i], "b": ids[j],
                    "similarity": round(float(sim_matrix[i][j]), 4),
                    "archetype_a": archetypes[i],
                    "archetype_b": archetypes[j],
                    "same_archetype": archetypes[i] == archetypes[j]
                })

    # Group by archetype
    arch_collapse = Counter()
    for p in collapse_pairs:
        if p["same_archetype"]:
            arch_collapse[p["archetype_a"]] += 1

    print(f"    High-similarity pairs (>{threshold}): {len(collapse_pairs)}")
    if arch_collapse:
        print(f"    Archetypes with most collapse:")
        for arch, count in arch_collapse.most_common(5):
            print(f"      {arch}: {count} near-duplicate pairs")

    return collapse_pairs


def detect_country_leakage(sim_matrix, countries, space_name, k=15):
    """Check if country clusters appear in product/technical space (contamination)."""
    print(f"\n  [{space_name}] Country leakage detection...")

    country_neighbor_purity = {}
    for i in range(len(countries)):
        if not countries[i]:
            continue
        sims = sim_matrix[i].copy()
        sims[i] = -1
        top_k = np.argsort(sims)[-k:]
        neighbor_countries = [countries[j] for j in top_k if countries[j]]
        if neighbor_countries:
            same_country = sum(1 for c in neighbor_countries if c == countries[i])
            purity = same_country / len(neighbor_countries)
            country = countries[i]
            if country not in country_neighbor_purity:
                country_neighbor_purity[country] = []
            country_neighbor_purity[country].append(purity)

    # Average purity per country
    avg_purity = {}
    for country, purities in country_neighbor_purity.items():
        if len(purities) >= 5:  # Need enough samples
            avg_purity[country] = round(np.mean(purities), 4)

    # Flag countries with suspiciously high purity (leakage)
    flagged = {c: p for c, p in avg_purity.items() if p > 0.4}
    if flagged:
        print(f"    WARNING: Country gravity detected in {space_name}:")
        for c, p in sorted(flagged.items(), key=lambda x: -x[1])[:5]:
            print(f"      {c}: {p:.1%} neighbor purity")
    else:
        print(f"    OK: No country leakage detected")

    return avg_purity


def detect_bridge_nodes(product_sim, technical_sim, market_sim, ids, names, archetypes, k=15):
    """
    Find bridge projects: high similarity in one space, low in others.
    These are often the most innovative projects.
    """
    print(f"\n  Bridge node detection...")

    bridges = []
    for i in range(len(ids)):
        # Get top-k neighbors in each space
        p_top = set(np.argsort(product_sim[i])[-k:])
        t_top = set(np.argsort(technical_sim[i])[-k:])
        m_top = set(np.argsort(market_sim[i])[-k:])

        # Measure overlap between neighbor sets
        pt_overlap = len(p_top & t_top) / k
        pm_overlap = len(p_top & m_top) / k
        tm_overlap = len(t_top & m_top) / k
        avg_overlap = (pt_overlap + pm_overlap + tm_overlap) / 3

        # Low overlap = bridge node (different neighbors in different spaces)
        if avg_overlap < 0.15:
            bridges.append({
                "project_id": ids[i],
                "project_name": names[i],
                "archetype": archetypes[i],
                "product_tech_overlap": round(pt_overlap, 3),
                "product_market_overlap": round(pm_overlap, 3),
                "tech_market_overlap": round(tm_overlap, 3),
                "avg_overlap": round(avg_overlap, 3)
            })

    bridges.sort(key=lambda x: x["avg_overlap"])
    print(f"    Bridge nodes found: {len(bridges)}")
    for b in bridges[:10]:
        print(f"      {b['project_name']} ({b['archetype']}) — overlap: {b['avg_overlap']:.3f}")

    return bridges


def compute_space_divergence(product_sim, technical_sim, market_sim, ids, names, archetypes, k=15):
    """
    Find projects where neighbors differ drastically between spaces.
    'same architecture, different market' or 'same market, different primitives'
    """
    print(f"\n  Space divergence analysis...")

    divergences = []
    for i in range(len(ids)):
        p_top = set(np.argsort(product_sim[i])[-k:])
        t_top = set(np.argsort(technical_sim[i])[-k:])
        m_top = set(np.argsort(market_sim[i])[-k:])

        # Projects in tech neighbors but NOT in product neighbors
        tech_not_product = t_top - p_top
        product_not_tech = p_top - t_top
        market_not_product = m_top - p_top

        divergences.append({
            "project_id": ids[i],
            "project_name": names[i],
            "archetype": archetypes[i],
            "same_tech_diff_product": len(tech_not_product),
            "same_product_diff_tech": len(product_not_tech),
            "same_market_diff_product": len(market_not_product),
        })

    # Sort by highest divergence
    divergences.sort(key=lambda x: -(x["same_tech_diff_product"] + x["same_product_diff_tech"]))

    print(f"    Top 10 most divergent projects:")
    for d in divergences[:10]:
        print(f"      {d['project_name']}: tech≠product={d['same_tech_diff_product']}, product≠tech={d['same_product_diff_tech']}")

    return divergences


def compute_density_metrics(sim_matrix, ids, archetypes, space_name, k=15):
    """Compute semantic density and neighbor entropy per project."""
    print(f"\n  [{space_name}] Density & entropy metrics...")

    metrics = []
    for i in range(len(ids)):
        sims = sim_matrix[i].copy()
        sims[i] = -1
        top_k_sims = np.sort(sims)[-k:]

        # Semantic density: mean similarity to k nearest neighbors
        density = float(np.mean(top_k_sims))

        # Neighbor entropy: how diverse are the archetypes of neighbors
        top_k_idx = np.argsort(sims)[-k:]
        neighbor_archs = [archetypes[j] for j in top_k_idx]
        arch_counts = Counter(neighbor_archs)
        total = sum(arch_counts.values())
        entropy = -sum((c/total) * np.log2(c/total) for c in arch_counts.values() if c > 0)

        metrics.append({
            "project_id": ids[i],
            "density": round(density, 4),
            "neighbor_entropy": round(entropy, 4),
            "dominant_neighbor_archetype": arch_counts.most_common(1)[0][0] if arch_counts else "",
        })

    # Summary stats
    densities = [m["density"] for m in metrics]
    entropies = [m["neighbor_entropy"] for m in metrics]
    print(f"    Density: mean={np.mean(densities):.4f}, std={np.std(densities):.4f}")
    print(f"    Entropy: mean={np.mean(entropies):.4f}, std={np.std(entropies):.4f}")

    return metrics


def main():
    print("=" * 60)
    print("TOPOLOGY DIAGNOSTICS ENGINE")
    print("=" * 60)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    ids, names, archetypes, countries, categories, domains, product, technical, market = load_data()
    print(f"Loaded {len(ids)} projects.\n")

    # Compute similarity matrices (or load from cache)
    print("[1/5] Computing similarity matrices...")
    sims = {}
    for space_name, vectors in [("product", product), ("technical", technical), ("market", market)]:
        cache_path = os.path.join(GRAPHS_DIR, f"{space_name}_sim_matrix.npy")
        if os.path.exists(cache_path):
            sims[space_name] = np.load(cache_path)
            print(f"  Loaded cached {space_name} sim matrix")
        else:
            sims[space_name] = cosine_similarity(vectors)
            print(f"  Computed {space_name} sim matrix")

    report = {}

    # [2] Semantic collapse
    print("\n[2/5] Semantic Collapse Detection...")
    for space in ["product", "technical", "market"]:
        collapse = detect_semantic_collapse(sims[space], ids, archetypes, space)
        report[f"{space}_collapse_pairs"] = len(collapse)

    # [3] Country leakage
    print("\n[3/5] Country Leakage Detection...")
    for space in ["product", "technical"]:
        leakage = detect_country_leakage(sims[space], countries, space)
        report[f"{space}_country_leakage"] = leakage

    # [4] Bridge nodes
    print("\n[4/5] Bridge Node & Space Divergence Analysis...")
    bridges = detect_bridge_nodes(sims["product"], sims["technical"], sims["market"], ids, names, archetypes)
    with open(os.path.join(OUTPUT_DIR, "bridge_nodes.json"), "w", encoding="utf-8") as f:
        json.dump(bridges, f, indent=2, ensure_ascii=False)

    divergences = compute_space_divergence(sims["product"], sims["technical"], sims["market"], ids, names, archetypes)
    with open(os.path.join(OUTPUT_DIR, "space_divergence.json"), "w", encoding="utf-8") as f:
        json.dump(divergences[:100], f, indent=2, ensure_ascii=False)

    # [5] Density & entropy
    print("\n[5/5] Density & Entropy Metrics...")
    all_density = {}
    for space in ["product", "technical", "market"]:
        metrics = compute_density_metrics(sims[space], ids, archetypes, space)
        all_density[space] = metrics

    with open(os.path.join(OUTPUT_DIR, "density_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(all_density, f, indent=2, ensure_ascii=False)

    # Summary report
    report["bridge_nodes_count"] = len(bridges)
    report["total_projects"] = len(ids)
    with open(os.path.join(OUTPUT_DIR, "topology_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print("TOPOLOGY DIAGNOSTICS COMPLETE")
    print(f"  Bridge nodes: {len(bridges)}")
    print(f"  All outputs in: {OUTPUT_DIR}/")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

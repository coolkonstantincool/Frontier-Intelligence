"""
Frontier Judge — Ecosystem Context Builder

Reads topology data (clusters, outlier scores, neighbors, archetypes)
and produces a human-readable ecosystem_context.json for each project.

The judge model never sees raw embeddings or cluster IDs.
It sees calibrated, natural-language context.

Usage:
    python judge/build_context.py --videos-dir videos/ --clusters-dir ecosystem_graph/clusters/
"""

import os, json, argparse
from collections import Counter, defaultdict


def load_clusters(clusters_dir: str) -> dict:
    """Load cluster assignments for all spaces."""
    spaces = {}
    for space in ['product', 'technical', 'market']:
        path = os.path.join(clusters_dir, f"{space}_clusters.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            spaces[space] = {item["project_id"]: item for item in data}
    return spaces


def load_all_ontologies(videos_dir: str) -> dict:
    """Load ontology_intelligence.json for all projects."""
    ontologies = {}
    for d in sorted(os.listdir(videos_dir)):
        path = os.path.join(videos_dir, d, "ontology_intelligence.json")
        if os.path.isdir(os.path.join(videos_dir, d)) and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    o = json.load(f)
                if isinstance(o, list):
                    o = o[0] if o else {}
                ontologies[d] = o
            except:
                ontologies[d] = {}
    return ontologies


def compute_category_formation_rates(ontologies: dict) -> dict:
    """Compute unique archetypes per project ratio for each domain."""
    domain_archetypes = defaultdict(set)
    domain_counts = defaultdict(int)
    for pid, o in ontologies.items():
        archetype = o.get("primary_archetype", "")
        domains = o.get("ecosystem_domains", []) or []
        for dom in domains:
            domain_counts[dom] += 1
            if archetype:
                domain_archetypes[dom].add(archetype)
    rates = {}
    for dom in domain_counts:
        rates[dom] = round(len(domain_archetypes[dom]) / max(domain_counts[dom], 1), 2)
    return rates


def classify_saturation(cluster_size: int, outlier_score: float) -> str:
    """Human-readable saturation level."""
    if cluster_size == -1 or cluster_size == 0:
        return "outlier — no cluster assigned"
    if outlier_score > 0.7:
        return "frontier — structurally isolated from known clusters"
    if cluster_size >= 50:
        return "highly saturated"
    if cluster_size >= 20:
        return "moderately saturated"
    if cluster_size >= 10:
        return "lightly saturated"
    return "sparse — small or emerging cluster"


def build_context_for_project(
    project_id: str,
    spaces: dict,
    ontologies: dict,
    archetype_counts: Counter,
    cfr: dict,
    cluster_archetypes: dict,
) -> dict:
    """Build the ecosystem_context.json for a single project."""

    onto = ontologies.get(project_id, {})
    archetype = onto.get("primary_archetype", "UNKNOWN")
    domains = onto.get("ecosystem_domains", []) or []

    # Product space data
    prod = spaces.get("product", {}).get(project_id, {})
    cluster_id = prod.get("cluster", -1)
    outlier_score = prod.get("outlier_score", 0)

    # Cluster size and nearby archetypes
    cluster_size = 0
    nearby_archetypes = []
    if cluster_id != -1 and cluster_id in cluster_archetypes:
        ca = cluster_archetypes[cluster_id]
        cluster_size = sum(ca.values())
        nearby_archetypes = [a for a, _ in ca.most_common(5) if a != archetype][:4]

    # Saturation classification
    saturation = classify_saturation(cluster_size, outlier_score)

    # Archetype frequency
    arch_count = archetype_counts.get(archetype, 0)

    # Novelty position
    if outlier_score > 0.7:
        novelty_position = "high — structurally unique in the ecosystem"
    elif outlier_score > 0.4:
        novelty_position = "moderate — some structural differentiation"
    elif outlier_score > 0.2:
        novelty_position = "low-moderate — within a recognized cluster"
    else:
        novelty_position = "low — deep inside a saturated cluster"

    # Cross-space behavior
    tech = spaces.get("technical", {}).get(project_id, {})
    mkt = spaces.get("market", {}).get(project_id, {})
    tech_outlier = tech.get("cluster", 0) == -1
    mkt_outlier = mkt.get("cluster", 0) == -1

    # Category formation rates for this project's domains
    domain_cfrs = {d: cfr.get(d, 0) for d in domains if d in cfr}

    # Ecosystem notes (human-readable calibration)
    notes = []
    if cluster_size >= 50:
        notes.append(f"This project is in a large cluster of {cluster_size} structurally similar submissions.")
    if arch_count >= 10:
        notes.append(f"The archetype '{archetype}' appears in {arch_count} other projects. Claims of uniqueness require strong evidence.")
    if arch_count <= 2:
        notes.append(f"The archetype '{archetype}' is rare or unique in this hackathon ({arch_count} total).")
    if outlier_score > 0.7:
        notes.append("This project occupies an unusual position in the topology — structurally distant from known clusters.")
    if any(v < 0.5 for v in domain_cfrs.values()):
        saturated_doms = [d for d, v in domain_cfrs.items() if v < 0.5]
        notes.append(f"The domain(s) {saturated_doms} have low category formation rates, indicating design-space exhaustion.")
    if tech_outlier and not mkt_outlier:
        notes.append("This project has no clear technical peers, suggesting novel or unusual architecture.")
    if mkt_outlier and not tech_outlier:
        notes.append("This project has no clear market peers, suggesting an unusual target audience.")

    # Detect potential semantic camouflage
    camouflage_risk = outlier_score < 0.15 and cluster_size >= 30

    context = {
        "cluster_size": cluster_size,
        "cluster_type": saturation,
        "nearest_archetypes": nearby_archetypes,
        "novelty_position": novelty_position,
        "structural_originality_score": round(outlier_score, 3),
        "archetype_frequency": arch_count,
        "category_formation_rates": domain_cfrs,
        "cross_space": {
            "technical_outlier": tech_outlier,
            "market_outlier": mkt_outlier,
        },
        "semantic_camouflage_risk": camouflage_risk,
        "ecosystem_notes": notes,
    }
    return context


def main():
    parser = argparse.ArgumentParser(description="Build ecosystem context for each project")
    parser.add_argument("--videos-dir", default="videos", help="Path to videos directory")
    parser.add_argument("--clusters-dir", default="ecosystem_graph/clusters", help="Path to clusters directory")
    args = parser.parse_args()

    print("Loading cluster data...")
    spaces = load_clusters(args.clusters_dir)

    print("Loading ontologies...")
    ontologies = load_all_ontologies(args.videos_dir)

    print("Computing category formation rates...")
    cfr = compute_category_formation_rates(ontologies)

    # Pre-compute archetype counts
    archetype_counts = Counter()
    for o in ontologies.values():
        a = o.get("primary_archetype", "")
        if a:
            archetype_counts[a] += 1

    # Pre-compute cluster archetype distributions
    cluster_archetypes = defaultdict(Counter)
    prod_space = spaces.get("product", {})
    for pid, info in prod_space.items():
        cl = info.get("cluster", -1)
        if cl != -1:
            a = ontologies.get(pid, {}).get("primary_archetype", "UNKNOWN")
            cluster_archetypes[cl][a] += 1

    # Build context for each project
    dirs = sorted([d for d in os.listdir(args.videos_dir)
                   if os.path.isdir(os.path.join(args.videos_dir, d))])

    built = 0
    for d in dirs:
        ctx = build_context_for_project(d, spaces, ontologies, archetype_counts, cfr, cluster_archetypes)
        out_path = os.path.join(args.videos_dir, d, "ecosystem_context.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(ctx, f, indent=2, ensure_ascii=False)
        built += 1

    print(f"Built ecosystem context for {built} projects.")


if __name__ == "__main__":
    main()

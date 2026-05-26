# Frontier Ecosystem Intelligence Dataset

> **A map of the ecosystem's unconscious.**  
> *A massive, open-source structural intelligence dataset decoding the collective cognition of 2,870 Solana builders.*

## Overview

The Frontier Ecosystem Intelligence Dataset is not a list of startups. It is a **live semantic topology**. 

Built from raw hackathon submissions, 4,141 demo videos, and unstructured GitHub data, this dataset transforms chaotic human intent into a queryable, 768-dimensional mathematical space. We processed thousands of hours of video transcripts and forced state-of-the-art LLMs to extract rigid ontologies—mapping every project across three distinct semantic axes: **Product**, **Technical**, and **Market**.

This is a **public good** for the Web3 ecosystem. It empowers funds, protocol designers, ecosystem leads, and researchers to move beyond qualitative narratives and analyze innovation as a structural, quantifiable science.

---

## What's Inside

The dataset is engineered for maximum portability and analytical power, combining relational metadata with high-performance vector formats.

### 1. The Relational Core (`frontier_ecosystem.db` - SQLite)
The ultimate source of truth, containing:
*   **Raw Intelligence:** Full text transcripts extracted from 4,141 demo videos (what founders *actually* said, not just their marketing copy).
*   **Structured Ontology:** AI-extracted classifications for all 2,870 projects, including Archetype, Behavioral Pattern, and Technical Primitives.
*   **Link Health Data:** Validation status for websites, repos, and videos (a leading indicator of project mortality).
*   **Topological Metadata:** Pre-computed UMAP coordinates, cluster assignments, and outlier scores across all semantic spaces.

### 2. The Vector Space (`embeddings.parquet`)
768-dimensional embeddings for every project. Because innovation isn't flat, we embed each project three times:
*   **Product Space Vector:** What the project IS.
*   **Technical Space Vector:** How the project is BUILT.
*   **Market Space Vector:** Who the project is FOR.

### 3. The Relationship Graph (`precomputed_neighbors.parquet`)
*O(1)* graph relationships mapping the top 15 nearest semantic neighbors for each project across all spaces. Perfect for instant network analysis without running FAISS locally.

### 4. The Macro Regions (`cluster_metadata.parquet`)
Detailed metadata on the 60+ macro-level semantic regions, including saturation scores, dominant archetypes, and semantic entropy.

---

## Why This Exists (The Problem It Solves)

Current ecosystem analysis relies on vibes, Twitter narratives, and manual review. This dataset solves three massive systemic problems:

1.  **Semantic Camouflage:** Founders often use novel buzzwords (e.g., "AI Coordination Layer") to describe commoditized ideas (e.g., a prediction market). Vector embeddings ignore the buzzwords and map the *actual* structure.
2.  **The Monoculture Blindspot:** We identified 15,188 technical collapse pairs vs. only 145 product collapse pairs. The ecosystem builds diverse products on dangerously identical infrastructure. Without this dataset, that systemic fragility is invisible.
3.  **The Attention Misallocation:** The dataset reveals critical gaps—like the ecosystem building autonomous agents 29x faster than the identity infrastructure needed to govern them.

---

## Core Use Cases

### 📈 Capital Allocation & VC Intelligence
*   **Saturation Detection:** Identify which product categories are mathematical monocultures (e.g., AI Trading Copilots) and which are blue-ocean anomalies.
*   **Bridge Node Identification:** Find projects that connect radically different clusters (e.g., bridging DeFi and physical logistics). Bridge nodes often represent category-defining innovations.
*   **False Novelty Filtering:** Mathematically prove if a pitch is truly unique or structurally identical to 50 other projects.

### 🏗️ Ecosystem & Protocol Strategy
*   **Infrastructure Dependency Mapping:** Identify critical single points of failure. (e.g., 58% of the ecosystem relies on a single verification primitive).
*   **Whitespace Discovery:** Find areas where the ecosystem is drastically under-investing (e.g., Moderation, Public Goods, Governance).
*   **Geographic Specialization:** Analyze how different regions build differently (e.g., Pakistan builds utility; the US builds speculative optimization).

### 🧠 Founder Research
*   **Competitive Neighborhood Analysis:** Founders can query their exact semantic coordinates to see who is building adjacent to them, across product, tech, and market spaces.
*   **Narrative Arbitrage:** Identify emerging archetypes that lack dedicated infrastructure.

---

## Quick Start Examples

The dataset is designed to be instantly usable with Pandas, DuckDB, or pure Python.

### Example 1: Finding High-Novelty "Frontier" Projects (Python/SQLite)
Find projects that defy classification (high outlier score) but actually have working products.

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('frontier_ecosystem.db')
query = """
SELECT p.id, i.primary_archetype, p.outlier_score_product
FROM projects p
JOIN intelligence i ON p.id = i.project_id
WHERE p.outlier_score_product > 0.8 
ORDER BY p.outlier_score_product DESC
LIMIT 10;
"""
df = pd.read_sql_query(query, conn)
print(df)
```

### Example 2: Analyzing the Monoculture (DuckDB/Parquet)
Instantly query the precomputed neighbors to find highly clustered sectors.

```python
import duckdb

# Find projects with the most identical technical neighbors
query = """
SELECT source_id, COUNT(*) as highly_similar_neighbors
FROM read_parquet('precomputed_neighbors.parquet')
WHERE space = 'technical' AND similarity_score > 0.95
GROUP BY source_id
ORDER BY highly_similar_neighbors DESC
LIMIT 5;
"""
duckdb.query(query).show()
```

### Example 3: Extracting Behavioral Assumptions
Analyze the core behavioral patterns the ecosystem assumes users will take.

```python
import sqlite3
from collections import Counter

conn = sqlite3.connect('frontier_ecosystem.db')
cursor = conn.cursor()
cursor.execute("SELECT behavioral_pattern FROM intelligence WHERE behavioral_pattern IS NOT NULL")
patterns = [row[0] for row in cursor.fetchall()]

print(Counter(patterns).most_common(5))
# Output reveals massive bias toward "PROACTIVE_MONITORING_AND_ALERTING"
```

---

## Contributing & License

This dataset is an open-source public good. We encourage researchers to build upon it, map new dimensions, and use it to better understand how decentralized ecosystems organize themselves.

*(Include your specific License details here, e.g., MIT, CC-BY)*

Open source at [Frontier-Intelligence](https://github.com/coolkonstantincool/Frontier-Intelligence).

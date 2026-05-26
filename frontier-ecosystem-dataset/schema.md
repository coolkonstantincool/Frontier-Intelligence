# Ecosystem Intelligence Data Schema

## 1. SQLite Database: `frontier_ecosystem.db`

The human-readable core database containing parsed AI intelligence and metadata.

### `projects`
Raw metadata for all startups.
- `project_id` (TEXT PRIMARY KEY)
- `name` (TEXT)
- `description` (TEXT)
- `category` (TEXT)
- `country` (TEXT)
- `website_url` (TEXT)
- `repo_url` (TEXT)
- `pitch_video_url` (TEXT)
- `demo_video_url` (TEXT)

### `intelligence`
Structured intelligence extracted from multi-modal analysis.
- `project_id` (TEXT PRIMARY KEY)
- `what_is_built` (TEXT)
- `tags` (TEXT) — JSON array
- `key_strengths` (TEXT) — JSON array
- `key_weaknesses` (TEXT) — JSON array
- `product_summary` (TEXT)
- `technical_summary` (TEXT)
- `market_summary` (TEXT)

### `ontology`
Normalized taxonomic assignments for clustering.
- `project_id` (TEXT PRIMARY KEY)
- `primary_archetype` (TEXT)
- `behavioral_pattern` (TEXT)
- `primitives` (TEXT) — JSON array of infrastructure dependencies

### `judging`
Quantitative and qualitative evaluation scores.
- `project_id` (TEXT PRIMARY KEY)
- `overall_score` (REAL)
- `final_verdict` (TEXT)
- `raw_scores` (TEXT) — JSON object containing dimensional scores

### `topology`
Precomputed layout metrics and insights.
- `project_id` (TEXT PRIMARY KEY)
- `cluster_id` (INTEGER)
- `x_2d`, `y_2d` (REAL) — UMAP composite coordinates
- `is_bridge` (BOOLEAN)
- `bridge_overlap` (REAL) — Degree of intersection between semantic clusters
- `outlier_score` (REAL) — Topological isolation score
- `is_hero` (BOOLEAN) — Central node in cluster

### `transcripts`
Full video transcript chunks.
- `project_id` (TEXT)
- `video_type` (TEXT)
- `transcript_text` (TEXT)

### `links_validation`
Uptime verification of source links.
- `project_id` (TEXT PRIMARY KEY)
- `website_alive` (BOOLEAN)
- `repo_alive` (BOOLEAN)
- `video_alive` (BOOLEAN)
- `dead_links` (TEXT) — JSON array containing dead link types and URLs

---

## 2. Parquet: `embeddings.parquet`

The raw, uncompressed 768-dimensional embeddings for advanced ML usage.

| Column | Type | Description |
|---|---|---|
| `project_id` | string | Unique project identifier |
| `product_vector` | list<float32> | 768-dim user behavior and interaction vector |
| `technical_vector` | list<float32> | 768-dim architecture and primitives vector |
| `market_vector` | list<float32> | 768-dim commercial positioning vector |
| `product_norm` | float32 | L2 Norm |
| `technical_norm` | float32 | L2 Norm |
| `market_norm` | float32 | L2 Norm |

---

## 3. Parquet: `precomputed_neighbors.parquet`

O(1) lookup table for the ecosystem graph. Top 15 nearest neighbors precalculated for every node in every semantic space using FAISS L2/IP.

| Column | Type | Description |
|---|---|---|
| `project_id` | string | Source project |
| `neighbor_id` | string | Target project |
| `space` | string | Semantic space ('product', 'technical', 'market') |
| `similarity` | float32 | Cosine similarity / Inner Product score |
| `rank` | int32 | Rank of the neighbor (1 to 15) |

---

## 4. Parquet: `cluster_metadata.parquet`

Macro-level semantic regions and their saturation properties.

| Column | Type | Description |
|---|---|---|
| `cluster_id` | int32 | Unique region ID |
| `space` | string | Semantic Space where cluster was formed |
| `cluster_name` | string | AI-generated categorical label |
| `cluster_size` | int32 | Total projects within region |
| `dominant_archetypes`| string | JSON string of highest-density archetypes |
| `saturation_score` | float32 | Degree of competition in this region |
| `novelty_density` | float32 | Concentration of outliers inside the cluster |

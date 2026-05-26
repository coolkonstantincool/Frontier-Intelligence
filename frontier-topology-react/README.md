# Frontier Topology: Ecosystem Intelligence Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Status: Experimental](https://img.shields.io/badge/Status-Experimental-indigo.svg)]()

Frontier Topology is an institutional-grade visual intelligence engine designed for rendering large-scale semantic ecosystems. Originally developed to analyze the Frontier Hackathon dataset, this project is now open-sourced as a Public Good to help researchers, DAOs, and venture funds visualize complex, unstructured project landscapes.

By combining **LLM Embeddings**, **UMAP Dimensionality Reduction**, and **WebGL Hardware Acceleration**, Frontier Topology transforms thousands of text-based project pitches into a navigable, cognitive operating system.

---

## 🌌 The Problem It Solves

Traditional dashboards fail when scaling to thousands of early-stage projects. Lists hide relationships. Tags are too rigid. Human review becomes inconsistent.

Frontier Topology solves this by treating an ecosystem not as a database, but as a **semantic spatial topology**:
1.  **AI Comprehension**: We use LLMs to extract deep semantic vectors from project functionality, technical architectures, and business models.
2.  **Spatial Projection**: We project these high-dimensional vectors down to 2D space using UMAP.
3.  **Semantic Clustering**: We mathematically identify clusters of innovation, surfacing macro-narratives (e.g., "DeFi Primitives", "ZK Infrastructure") autonomously.
4.  **Hardware-Accelerated UI**: We render the resulting topology smoothly using Sigma.js (WebGL), enveloped in a premium Glass Design System.

## ✨ Features

- **Decoupled Architecture**: Easily pass your own `dataset.json` containing `points` (projects), `hulls` (semantic regions), and `edges` (similarity metrics).
- **WebGL Rendering**: Effortlessly handles thousands of nodes at 60 FPS using [Sigma.js](https://www.sigmajs.org/) and [Graphology](https://graphology.github.io/).
- **Autonomous Label Collision Engine**: Macro-cluster labels dynamically fade, scale, and avoid collision as you zoom deep into the ecosystem.
- **Glass Design System**: A meticulously crafted, institutional UI emphasizing clarity, depth, and cognitive control.
- **Zero-Config Deployment**: Works out of the box with Vite and TailwindCSS v4.

---

## 🚀 Quickstart

1. **Clone the repository:**
   ```bash
   cd Frontier-Intelligence/frontier-topology-react
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Run the development server:**
   ```bash
   npm run dev
   ```

You should instantly see the interactive topology map running at `http://localhost:5173`. 

*Note: This repository includes a snapshot of the Renaissance Ecosystem dataset in `public/dataset.json` for immediate visualization.*

---

## 🛠️ How to "Hack" This for Your Own Use Case

The real magic of Frontier Topology is that it's entirely data-driven. The map doesn't care if you're plotting Web3 startups, AI research papers, molecular structures, or GitHub repositories.

**Step 1: Generate Vectors**
Take your unstructured text data (descriptions, tweets, code) and pass them through an embedding model (like `text-embedding-3-small` or local `bge-m3`).

**Step 2: Reduce & Cluster**
Run your vectors through UMAP to get `(x, y)` coordinates, and run HDBSCAN to find clusters. (We recommend Python for this: `pip install umap-learn hdbscan`).

**Step 3: Calculate Hulls & Edges**
For each cluster, calculate the Convex Hull or use simple bounding boxes for `hulls`. For `edges`, use KNN to link the closest projects based on cosine similarity.

**Step 4: Swap `dataset.json`**
Output your data to `public/dataset.json` in the exact format below, and the React app will automatically render your custom semantic universe.

```json
{
  "space": "product",
  "count": 2869,
  "points": [
    {
      "project_id": "0003_SolGuard",
      "project_name": "SolGuard",
      "archetype": "Wallet Security Scanner",
      "country": "China",
      "category": "AI Platforms / Agents",
      "x": 3.7531,
      "y": 11.4550,
      "cluster": 35,
      "outlier_score": 0.0161,
      "is_bridge": false,
      "bridge_overlap": 1.0,
      "has_logo": true
    }
  ],
  "hulls": [
    {
      "cluster_id": 35,
      "label": "Wallet Security Scanner",
      "centroid": [3.7137, 11.4288],
      "hull": [
        [3.2209, 11.4132],
        [3.4292, 11.1098],
        [3.4984, 11.0968]
      ],
      "size": 54
    }
  ]
}
```

### 🧠 Data Dictionary

**Top-Level Properties:**
* `space`: The mathematical or conceptual space being mapped (e.g., "product", "technology").
* `count`: Total number of data points.

**`points` Array (The Projects):**
* `x` & `y`: Pre-computed UMAP coordinates representing the semantic location of the project.
* `cluster`: The HDBSCAN cluster integer ID this project belongs to (-1 means noise/unclustered).
* `outlier_score`: Float [0, 1] representing how anomalous the point is within its cluster.
* `is_bridge`: Boolean flag. True if the point connects two separate semantic clusters.
* `bridge_overlap`: Float [0, 1] representing the strength of the bridge.
* `archetype`, `category`, `country`: Metadata fields used for filtering and tooltip rendering.

**`hulls` Array (The Clusters):**
* `cluster_id`: Corresponds to the `cluster` integer in the `points` array.
* `label`: The AI-generated macro-narrative or topic for this cluster.
* `centroid`: The mathematical center `[x, y]` of the cluster.
* `hull`: An array of `[x, y]` coordinates forming the bounding polygon (Convex Hull) of the cluster.
* `size`: Total number of points in this cluster.

## 🏗️ Production Deployment

Since this is a standard Vite React App, deployment is instantaneous:

```bash
# Build the production bundle
npm run build

# Preview locally
npm run preview
```

Deploy the `dist/` folder to Vercel, Netlify, Cloudflare Pages, or GitHub Pages. No backend required—the entire engine runs client-side using WebGL.

## 🤝 Contributing to the Public Good

We built this as a public good for the ecosystem. If you are a researcher building custom embedding models, a data scientist tweaking UMAP parameters, or a developer extending the UI, we welcome your Pull Requests. 

**Let's build the ultimate cognitive operating system for ecosystem intelligence.**

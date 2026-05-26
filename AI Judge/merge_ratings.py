"""
Frontier Judge — Merge Ratings into Database & Cross-Model Comparison

Loads score files from any model into the SQLite database.
Generates comparison reports when multiple models have judged the same projects.

Usage:
    python judge/merge_ratings.py --model gemini-flash --videos-dir videos/ --db frontier-ecosystem/frontier_ecosystem.db
    python judge/merge_ratings.py --compare --db frontier-ecosystem/frontier_ecosystem.db
"""

import os, sys, json, sqlite3, argparse
from collections import defaultdict
import numpy as np


DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS model_ratings (
    project_id TEXT,
    model_name TEXT,
    model_version TEXT,
    timestamp TEXT,
    functionality_score INTEGER,
    functionality_justification TEXT,
    impact_score INTEGER,
    impact_justification TEXT,
    novelty_score INTEGER,
    novelty_justification TEXT,
    ux_score INTEGER,
    ux_justification TEXT,
    business_score INTEGER,
    business_justification TEXT,
    overall_score REAL,
    adjusted_score REAL,
    confidence REAL,
    key_strengths TEXT,
    key_weaknesses TEXT,
    category_saturation TEXT,
    differentiation_quality TEXT,
    semantic_camouflage_flag BOOLEAN,
    final_verdict TEXT,
    PRIMARY KEY (project_id, model_name)
);
"""


def init_db(db_path: str):
    """Create the model_ratings table if it doesn't exist."""
    conn = sqlite3.connect(db_path)
    conn.execute(DB_SCHEMA)
    conn.commit()
    conn.close()


def insert_rating(conn: sqlite3.Connection, score: dict):
    """Insert or replace a single rating."""
    scores = score.get("scores", {})
    eco = score.get("ecosystem_positioning", {})

    conn.execute("""
        INSERT OR REPLACE INTO model_ratings
        (project_id, model_name, model_version, timestamp,
         functionality_score, functionality_justification,
         impact_score, impact_justification,
         novelty_score, novelty_justification,
         ux_score, ux_justification,
         business_score, business_justification,
         overall_score, adjusted_score, confidence,
         key_strengths, key_weaknesses,
         category_saturation, differentiation_quality,
         semantic_camouflage_flag, final_verdict)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        score.get("project_id", ""),
        score.get("model", ""),
        score.get("model_version", ""),
        score.get("timestamp", ""),
        scores.get("functionality", {}).get("score", 0),
        scores.get("functionality", {}).get("justification", ""),
        scores.get("impact", {}).get("score", 0),
        scores.get("impact", {}).get("justification", ""),
        scores.get("novelty", {}).get("score", 0),
        scores.get("novelty", {}).get("justification", ""),
        scores.get("ux", {}).get("score", 0),
        scores.get("ux", {}).get("justification", ""),
        scores.get("business", {}).get("score", 0),
        scores.get("business", {}).get("justification", ""),
        score.get("overall_score", 0),
        score.get("adjusted_score", 0),
        score.get("confidence", 0),
        json.dumps(score.get("key_strengths", []), ensure_ascii=False),
        json.dumps(score.get("key_weaknesses", []), ensure_ascii=False),
        eco.get("category_saturation", ""),
        eco.get("differentiation_quality", ""),
        score.get("semantic_camouflage_flag", False),
        score.get("final_verdict", ""),
    ))


def merge_model(model_name: str, videos_dir: str, db_path: str):
    """Load all score files for a model into the database."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)

    dirs = sorted([d for d in os.listdir(videos_dir)
                   if os.path.isdir(os.path.join(videos_dir, d))])

    loaded = 0
    for d in dirs:
        score_path = os.path.join(videos_dir, d, f"score_{model_name}.json")
        if not os.path.exists(score_path):
            continue
        try:
            with open(score_path, "r", encoding="utf-8") as f:
                score = json.load(f)
            # Ensure project_id is set
            if "project_id" not in score:
                score["project_id"] = d
            insert_rating(conn, score)
            loaded += 1
        except Exception as e:
            print(f"  ERROR loading {d}: {e}")

    conn.commit()
    conn.close()
    print(f"Loaded {loaded} ratings from model '{model_name}' into {db_path}")


def compare_models(db_path: str):
    """Generate cross-model comparison report."""
    conn = sqlite3.connect(db_path)

    # Get all models
    models = [r[0] for r in conn.execute("SELECT DISTINCT model_name FROM model_ratings").fetchall()]
    print(f"\nModels in database: {models}")

    if len(models) < 2:
        print("Need at least 2 models for comparison.")
        conn.close()
        return

    # Per-model stats
    print("\n" + "=" * 60)
    print("PER-MODEL STATISTICS")
    print("=" * 60)

    for model in models:
        rows = conn.execute("""
            SELECT overall_score, adjusted_score, confidence,
                   functionality_score, impact_score, novelty_score, ux_score, business_score
            FROM model_ratings WHERE model_name = ?
        """, (model,)).fetchall()

        if not rows:
            continue

        overall = [r[0] for r in rows]
        adjusted = [r[1] for r in rows]
        confidence = [r[2] for r in rows]
        func = [r[3] for r in rows]
        impact = [r[4] for r in rows]
        novelty = [r[5] for r in rows]
        ux = [r[6] for r in rows]
        biz = [r[7] for r in rows]

        print(f"\n  {model} ({len(rows)} projects)")
        print(f"    Overall:      mean={np.mean(overall):.2f}, std={np.std(overall):.2f}")
        print(f"    Adjusted:     mean={np.mean(adjusted):.2f}, std={np.std(adjusted):.2f}")
        print(f"    Confidence:   mean={np.mean(confidence):.2f}")
        print(f"    Functionality: mean={np.mean(func):.2f}")
        print(f"    Impact:       mean={np.mean(impact):.2f}")
        print(f"    Novelty:      mean={np.mean(novelty):.2f}")
        print(f"    UX:           mean={np.mean(ux):.2f}")
        print(f"    Business:     mean={np.mean(biz):.2f}")

    # Cross-model correlation (for projects scored by multiple models)
    if len(models) >= 2:
        print("\n" + "=" * 60)
        print("CROSS-MODEL CORRELATION")
        print("=" * 60)

        for i in range(len(models)):
            for j in range(i + 1, len(models)):
                m1, m2 = models[i], models[j]
                rows = conn.execute("""
                    SELECT a.overall_score, b.overall_score
                    FROM model_ratings a
                    JOIN model_ratings b ON a.project_id = b.project_id
                    WHERE a.model_name = ? AND b.model_name = ?
                """, (m1, m2)).fetchall()

                if len(rows) < 5:
                    print(f"  {m1} vs {m2}: insufficient overlap ({len(rows)} projects)")
                    continue

                scores_a = [r[0] for r in rows]
                scores_b = [r[1] for r in rows]
                corr = np.corrcoef(scores_a, scores_b)[0, 1]
                mean_diff = np.mean(np.array(scores_a) - np.array(scores_b))

                print(f"  {m1} vs {m2}:")
                print(f"    Projects in common: {len(rows)}")
                print(f"    Pearson correlation: {corr:.3f}")
                print(f"    Mean score difference: {mean_diff:+.2f} ({m1} {'higher' if mean_diff > 0 else 'lower'})")

                # Biggest disagreements
                diffs = [(abs(r[0] - r[1]), r[0], r[1]) for r in rows]
                diffs.sort(reverse=True)
                print(f"    Max disagreement: {diffs[0][0]:.1f} ({m1}={diffs[0][1]}, {m2}={diffs[0][2]})")

    # Consensus top projects
    print("\n" + "=" * 60)
    print("CONSENSUS TOP 20 (averaged across all models)")
    print("=" * 60)

    rows = conn.execute("""
        SELECT project_id, AVG(adjusted_score) as avg_score, COUNT(*) as model_count
        FROM model_ratings
        GROUP BY project_id
        HAVING model_count >= 1
        ORDER BY avg_score DESC
        LIMIT 20
    """).fetchall()

    for i, (pid, avg, cnt) in enumerate(rows):
        print(f"  {i+1:>3}. {pid:<50} avg={avg:.2f} (models={cnt})")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Merge ratings into DB or compare models")
    parser.add_argument("--model", default=None, help="Model name to merge")
    parser.add_argument("--videos-dir", default="videos", help="Path to videos directory")
    parser.add_argument("--db", default="frontier-ecosystem/frontier_ecosystem.db", help="Database path")
    parser.add_argument("--compare", action="store_true", help="Compare all models in the database")
    args = parser.parse_args()

    if args.compare:
        compare_models(args.db)
    elif args.model:
        merge_model(args.model, args.videos_dir, args.db)
    else:
        print("Specify --model to merge, or --compare to compare models.")


if __name__ == "__main__":
    main()

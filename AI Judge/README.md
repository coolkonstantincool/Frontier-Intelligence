# Frontier AI Judge — Multi-Model Hackathon Evaluation System

> **A topology-aware, model-agnostic judging pipeline for evaluating 2,870 Solana Frontier hackathon projects.**
> 
> Designed so any LLM — from Gemini Flash to Claude to GPT — can serve as a judge using the same methodology, the same evidence, and the same rubric. Ratings from different models are stored independently and can be compared, averaged, or ensembled.

---

## Architecture

The system is split into three independent layers. Each layer does one thing well.

```
┌─────────────────────────────────────────────────────┐
│                   Layer 1: EVIDENCE                  │
│         (Intelligence Extraction — already done)     │
│                                                      │
│  intelligence.json + enriched_intelligence.json      │
│  + ontology_intelligence.json + transcripts          │
│                                                      │
│  → Structured facts about what was built             │
├─────────────────────────────────────────────────────┤
│                  Layer 2: CONTEXT                     │
│          (Ecosystem Context Engine)                   │
│                                                      │
│  build_context.py reads topology data and produces   │
│  a human-readable ecosystem_context.json per project │
│                                                      │
│  → "This project sits in a saturated zone with       │
│     61 similar submissions. Differentiation claims   │
│     should require strong evidence."                 │
├─────────────────────────────────────────────────────┤
│                  Layer 3: JUDGE                       │
│           (Model-Agnostic Scoring)                   │
│                                                      │
│  run_judge.py sends evidence + context to any LLM    │
│  and receives standardized rubric scores             │
│                                                      │
│  → score_gemini_flash.json per project               │
│  → score_claude_opus.json per project                │
│  → score_gpt4o.json per project                      │
└─────────────────────────────────────────────────────┘
```

### Key Design Principle

The judge model **never sees raw embeddings, UMAP coordinates, or cluster IDs**. It receives human-readable ecosystem context that informs interpretation without replacing the official rubric.

Topology influences judgment. It does not become judgment.

---

## File Structure

```
judge/
├── README.md                  ← This file
├── prompts.py                 ← System + user prompts (the judging methodology)
├── schemas.py                 ← Output JSON schema + validation
├── build_context.py           ← Builds ecosystem_context.json per project
├── build_project_intel.py     ← Assembles project_intelligence.json per project
├── run_judge.py               ← Main CLI — runs any model against any project set
├── merge_ratings.py           ← Loads model ratings into SQLite + comparison reports
└── config.py                  ← Model configurations, API keys, rate limits
```

### Per-Project Output

After judging, each project directory gets:

```
videos/{project_id}/
├── intelligence.json              ← (existing) Raw extraction
├── enriched_intelligence.json     ← (existing) Deeper extraction
├── ontology_intelligence.json     ← (existing) Ontology classification
├── embeddings.json                ← (existing) Vector embeddings
├── ecosystem_context.json         ← (NEW) Human-readable topology context
├── project_intelligence.json      ← (NEW) Assembled evidence packet
├── score_gemini_flash.json        ← (NEW) Gemini Flash ratings
├── score_claude_opus.json         ← (NEW) Claude Opus ratings (future)
└── score_gpt4o.json               ← (NEW) GPT-4o ratings (future)
```

---

## Scoring Methodology

### Official Rubric (5 Criteria)

| Criterion | Weight | What It Measures |
|---|---|---|
| **Functionality** | Strongest | Working implementation, completeness, technical execution, demo evidence |
| **Potential Impact** | High | Problem importance, ecosystem usefulness, adoption potential |
| **Novelty** | High | Originality, structural differentiation, non-trivial innovation |
| **UX** | Medium | Usability, onboarding, interface quality, user flow |
| **Business Viability** | Medium | User demand, monetization, sustainability |

### Scoring Scale

| Score | Meaning |
|---|---|
| 9–10 | Exceptional — best-in-class execution and insight |
| 7–8 | Strong — clearly above average, well-executed |
| 5–6 | Average — functional but unremarkable |
| 3–4 | Weak — significant gaps in execution or concept |
| 0–2 | Incomplete — missing implementation or unsupported claims |

### How Ecosystem Context Influences Scoring

The ecosystem context is injected as calibration intelligence, not as a scoring axis.

**Novelty scoring is calibrated against:**
- Category saturation (how many similar projects exist)
- Category formation rate (how exhausted the design space is)
- Structural originality score (outlier score from topology)
- Cross-domain vocabulary signals

**Example influence:**
- A prediction market (category formation rate 0.44, 96 similar projects) claiming "first-of-its-kind" must provide very strong differentiation evidence to score above 5 on Novelty.
- A DePIN project (category formation rate 1.0, likely unique) gets baseline novelty credit for occupying unexplored territory.

**What ecosystem context does NOT do:**
- It does not override functionality scores.
- It does not penalize projects for being in popular categories if execution is exceptional.
- It does not reward projects for being outliers if implementation is weak.

### Confidence Scoring

Each judgment includes a confidence score (0.0–1.0) based on evidence quality:

| Evidence Quality | Confidence |
|---|---|
| Clear demo + detailed transcript + repo | 0.9–1.0 |
| Decent demo + some transcript | 0.7–0.8 |
| Vague demo or missing transcript | 0.5–0.6 |
| No demo or very poor evidence | 0.3–0.4 |

**Adjusted score formula:**

```
adjusted_score = overall_score × (0.7 + 0.3 × confidence)
```

This means:
- High-confidence projects keep 100% of their score
- Low-confidence projects are penalized by up to 30%
- Bullshit-heavy submissions with no evidence get structurally deflated

---

## How to Run

### Step 1: Build Ecosystem Context (one-time)

```bash
python judge/build_context.py --videos-dir videos/ --clusters-dir ecosystem_graph/clusters/
```

Generates `ecosystem_context.json` for every project.

### Step 2: Build Project Intelligence Packets (one-time)

```bash
python judge/build_project_intel.py --videos-dir videos/
```

Assembles `project_intelligence.json` from existing intelligence files.

### Step 3: Run a Judge Model

```bash
python judge/run_judge.py \
  --model gemini-flash \
  --videos-dir videos/ \
  --batch-size 10 \
  --start 0 \
  --end 100
```

This sends each project's evidence + context to the specified model and saves `score_{model_name}.json`.

### Step 4: Merge Ratings into Database

```bash
python judge/merge_ratings.py \
  --model gemini-flash \
  --videos-dir videos/ \
  --db frontier-ecosystem/frontier_ecosystem.db
```

Loads all ratings from a specific model into the SQLite database.

---

## Adding a New Judge Model

1. Add model configuration to `judge/config.py`:

```python
MODELS = {
    "gemini-flash": {
        "provider": "google",
        "model_id": "gemini-2.0-flash",
        "rpm": 60,
        "description": "Fast, cost-efficient baseline judge"
    },
    "claude-opus": {
        "provider": "anthropic",
        "model_id": "claude-opus-4",
        "rpm": 30,
        "description": "Deep reasoning, high-quality analysis"
    }
}
```

2. Run the judge:

```bash
python judge/run_judge.py --model claude-opus --videos-dir videos/
```

3. Merge ratings:

```bash
python judge/merge_ratings.py --model claude-opus --videos-dir videos/ --db frontier-ecosystem/frontier_ecosystem.db
```

The system handles everything else — same prompts, same rubric, same output schema, different model.

---

## Output Schema

Every `score_{model}.json` follows this exact structure:

```json
{
  "model": "gemini-flash",
  "model_version": "gemini-2.0-flash",
  "timestamp": "2025-05-25T12:00:00Z",
  "project_id": "0042_ProjectName",
  "project_name": "ProjectName",
  "track": "AI",

  "scores": {
    "functionality": { "score": 7, "justification": "..." },
    "impact": { "score": 6, "justification": "..." },
    "novelty": { "score": 4, "justification": "..." },
    "ux": { "score": 5, "justification": "..." },
    "business": { "score": 5, "justification": "..." }
  },

  "overall_score": 5.4,
  "adjusted_score": 5.13,
  "confidence": 0.81,

  "key_strengths": ["...", "..."],
  "key_weaknesses": ["...", "..."],

  "ecosystem_positioning": {
    "category_saturation": "high",
    "differentiation_quality": "low — structurally similar to 14 other AI trading copilots",
    "structural_notes": "Project uses standard ONCHAIN_VERIFICATION + ORACLE_CONSENSUS stack"
  },

  "semantic_camouflage_flag": false,
  "evidence_used": ["demo transcript", "pitch transcript", "ontology data"],
  "final_verdict": "Functional but undifferentiated trading assistant in a highly saturated category."
}
```

---

## Database Schema for Ratings

```sql
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
```

---

## Multi-Model Comparison

Once multiple models have judged the same projects:

```bash
python judge/merge_ratings.py --compare --db frontier-ecosystem/frontier_ecosystem.db
```

Produces a comparison report showing:
- Score correlation between models
- Projects with highest disagreement
- Systematic biases (e.g., "Model X rates novelty 1.2 points higher on average")
- Consensus top-50 per track

---

## Philosophy

This system is built on a simple premise:

> **A judge should evaluate what was built, not what was promised.**

Every design decision flows from this:
- Evidence-based scoring (no hallucinated features)
- Confidence penalties (no reward for vague pitches)
- Ecosystem calibration (no reward for semantic camouflage)
- Functionality as the strongest criterion (building > talking)
- Model-agnostic architecture (the methodology is the product, not the model)

The system is a public good. The methodology is open. The rubric is fixed. Only the model changes.

Open source at [Frontier-Intelligence](https://github.com/coolkonstantincool/Frontier-Intelligence).

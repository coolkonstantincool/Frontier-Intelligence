"""
Frontier Judge — Project Intelligence Assembler

Assembles all existing intelligence files into a single project_intelligence.json
that the judge model receives as evidence.

Usage:
    python judge/build_project_intel.py --videos-dir videos/
"""

import os, json, argparse


def load_json_safe(path: str) -> dict:
    """Load JSON file, return empty dict on failure."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data[0] if data else {}
        return data
    except:
        return {}


def load_transcript(path: str) -> str:
    """Load text file, return empty string on failure."""
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except:
        return ""


def build_intel_for_project(project_dir: str, project_id: str) -> dict:
    """Assemble the project_intelligence packet from existing files."""

    intel = load_json_safe(os.path.join(project_dir, "intelligence.json"))
    enriched = load_json_safe(os.path.join(project_dir, "enriched_intelligence.json"))
    ontology = load_json_safe(os.path.join(project_dir, "ontology_intelligence.json"))

    # Load all transcript files
    transcripts = []
    for f in sorted(os.listdir(project_dir)):
        if f.endswith(".txt"):
            content = load_transcript(os.path.join(project_dir, f))
            if len(content) > 50:
                label = "pitch" if "pitch" in f.lower() else "demo" if "demo" in f.lower() else "transcript"
                transcripts.append({"type": label, "content": content[:3000]})  # Cap at 3k chars

    # Detect what evidence exists
    files = os.listdir(project_dir)
    has_mp4 = any(f.endswith(".mp4") for f in files)
    has_repo = bool(intel.get("repo_url") or intel.get("github_url"))
    has_website = bool(intel.get("website_url") or intel.get("demo_url"))

    # Extract project name from ID
    parts = project_id.split("_", 1)
    project_name = parts[1] if len(parts) > 1 else project_id

    # Detect track from ontology domains
    domains = ontology.get("ecosystem_domains", []) or []
    track = "General"
    track_priority = {"AI": 3, "DEFI": 2, "INFRASTRUCTURE": 2, "CONSUMER": 1, "GAMING": 1}
    for d in domains:
        if d in track_priority and track_priority.get(d, 0) > track_priority.get(track, 0):
            track = d

    packet = {
        "project_id": project_id,
        "project_name": project_name,
        "track": track,

        # From intelligence.json
        "description": intel.get("description", intel.get("project_description", "")),
        "what_is_actually_built": intel.get("what_is_actually_built", ""),
        "core_problem": intel.get("core_problem", intel.get("problem_statement", "")),
        "core_mechanism": intel.get("core_mechanism", intel.get("solution_approach", "")),

        # From ontology
        "product_archetype": ontology.get("primary_archetype", ""),
        "behavioral_pattern": str(ontology.get("behavioral_pattern", "")),
        "technical_primitives": ontology.get("technical_primitives", []) or [],
        "target_users": ontology.get("target_users", []) or [],
        "ecosystem_domains": domains,

        # From enriched
        "solana_primitives_used": enriched.get("solana_primitives", []) or [],
        "competitive_landscape": enriched.get("competitive_landscape", ""),
        "technical_architecture": enriched.get("technical_architecture", ""),

        # Evidence signals
        "video_present": has_mp4,
        "repo_present": has_repo,
        "website_present": has_website,
        "transcript_count": len(transcripts),

        # Transcript evidence (the actual words of the founders)
        "transcript_evidence": transcripts,

        # Execution signals
        "execution_signals": {
            "demo_completeness": enriched.get("demo_completeness", "unknown"),
            "technical_depth": enriched.get("technical_depth", "unknown"),
            "feature_completeness": enriched.get("feature_completeness", "unknown"),
        },

        "risks_or_missing_pieces": enriched.get("risks", []) or [],
    }

    return packet


def main():
    parser = argparse.ArgumentParser(description="Build project intelligence packets")
    parser.add_argument("--videos-dir", default="videos", help="Path to videos directory")
    args = parser.parse_args()

    dirs = sorted([d for d in os.listdir(args.videos_dir)
                   if os.path.isdir(os.path.join(args.videos_dir, d))])

    built = 0
    for d in dirs:
        project_dir = os.path.join(args.videos_dir, d)
        packet = build_intel_for_project(project_dir, d)
        out_path = os.path.join(project_dir, "project_intelligence.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(packet, f, indent=2, ensure_ascii=False)
        built += 1

    print(f"Built project intelligence for {built} projects.")


if __name__ == "__main__":
    main()

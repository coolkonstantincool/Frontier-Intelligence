"""
Frontier Judge — Output Schema & Validation

Validates that judge output conforms to the standard schema.
Ensures cross-model comparability.
"""

import json

REQUIRED_FIELDS = {
    "project_name": str,
    "track": str,
    "scores": dict,
    "overall_score": (int, float),
    "confidence": (int, float),
    "key_strengths": list,
    "key_weaknesses": list,
    "ecosystem_positioning": dict,
    "semantic_camouflage_flag": bool,
    "evidence_used": list,
    "final_verdict": str,
}

REQUIRED_SCORE_FIELDS = ["functionality", "impact", "novelty", "ux", "business"]


def validate_score(score_json: dict) -> tuple[bool, list[str]]:
    """Validate a judge output against the schema. Returns (is_valid, errors)."""
    errors = []

    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in score_json:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(score_json[field], expected_type):
            errors.append(f"Field '{field}' has wrong type: expected {expected_type}, got {type(score_json[field])}")

    if "scores" in score_json:
        for sf in REQUIRED_SCORE_FIELDS:
            if sf not in score_json["scores"]:
                errors.append(f"Missing score field: scores.{sf}")
            elif not isinstance(score_json["scores"][sf], dict):
                errors.append(f"Score field scores.{sf} must be a dict with 'score' and 'justification'")
            else:
                entry = score_json["scores"][sf]
                if "score" not in entry:
                    errors.append(f"Missing 'score' in scores.{sf}")
                elif not isinstance(entry["score"], (int, float)):
                    errors.append(f"scores.{sf}.score must be numeric")
                elif not (0 <= entry["score"] <= 10):
                    errors.append(f"scores.{sf}.score={entry['score']} out of range [0, 10]")
                if "justification" not in entry:
                    errors.append(f"Missing 'justification' in scores.{sf}")

    if "confidence" in score_json:
        if not (0 <= score_json["confidence"] <= 1):
            errors.append(f"confidence={score_json['confidence']} out of range [0, 1]")

    if "overall_score" in score_json:
        if not (0 <= score_json["overall_score"] <= 10):
            errors.append(f"overall_score={score_json['overall_score']} out of range [0, 10]")

    return len(errors) == 0, errors


def compute_adjusted_score(overall_score: float, confidence: float) -> float:
    """Apply confidence penalty: adjusted = overall * (0.7 + 0.3 * confidence)"""
    return round(overall_score * (0.7 + 0.3 * confidence), 2)


def enrich_output(score_json: dict, model_name: str, model_version: str,
                  project_id: str, timestamp: str) -> dict:
    """Add metadata fields to the judge output for storage."""
    score_json["model"] = model_name
    score_json["model_version"] = model_version
    score_json["project_id"] = project_id
    score_json["timestamp"] = timestamp
    score_json["adjusted_score"] = compute_adjusted_score(
        score_json.get("overall_score", 0),
        score_json.get("confidence", 0.5)
    )
    return score_json


def parse_judge_response(raw_text: str) -> dict:
    """Extract JSON from model response, handling markdown fences."""
    text = raw_text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (fences)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    return json.loads(text)

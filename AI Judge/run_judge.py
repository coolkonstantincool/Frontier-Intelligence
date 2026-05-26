"""
Frontier Judge — Main Judge Runner

Sends project evidence + ecosystem context to any configured LLM model
and saves standardized score files.

Usage:
    python judge/run_judge.py --model gemini-flash --videos-dir videos/ --start 0 --end 100
    python judge/run_judge.py --model gemini-flash --videos-dir videos/ --project 0042_ProjectName
"""

import os, sys, json, time, argparse
from datetime import datetime, timezone
import concurrent.futures

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from schemas import validate_score, enrich_output, parse_judge_response, compute_adjusted_score
from config import MODELS, TRACKS


def get_track_context(track: str) -> dict:
    """Get track-specific evaluation context."""
    # Normalize track name
    track_upper = track.upper().replace(" ", "_")
    for key in TRACKS:
        if key.upper() == track_upper:
            return TRACKS[key]
    return TRACKS["default"]


def load_project_data(project_dir: str) -> tuple[dict, dict]:
    """Load project intelligence and ecosystem context."""
    intel_path = os.path.join(project_dir, "project_intelligence.json")
    ctx_path = os.path.join(project_dir, "ecosystem_context.json")

    intel = {}
    if os.path.exists(intel_path):
        with open(intel_path, "r", encoding="utf-8") as f:
            intel = json.load(f)

    ctx = {}
    if os.path.exists(ctx_path):
        with open(ctx_path, "r", encoding="utf-8") as f:
            ctx = json.load(f)

    return intel, ctx


def call_google(model_id: str, system_prompt: str, user_prompt: str,
                max_tokens: int, temperature: float) -> str:
    """Call Google Gemini via Vertex AI."""
    from google import genai
    from google.genai import types

    PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "your-gcp-project-id")
    LOCATION = os.environ.get("GCP_LOCATION", "us-central1")

    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    response = client.models.generate_content(
        model=model_id,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=max_tokens,
            temperature=temperature,
            response_mime_type="application/json",
            safety_settings=[
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE,
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE,
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE,
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE,
                ),
            ],
        ),
    )
    return response.text


def call_anthropic(model_id: str, system_prompt: str, user_prompt: str,
                   max_tokens: int, temperature: float) -> str:
    """Call Anthropic Claude API."""
    import anthropic
    client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var

    response = client.messages.create(
        model=model_id,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    return response.content[0].text


def call_openai(model_id: str, system_prompt: str, user_prompt: str,
                max_tokens: int, temperature: float) -> str:
    """Call OpenAI API."""
    from openai import OpenAI
    client = OpenAI()  # Uses OPENAI_API_KEY env var

    response = client.chat.completions.create(
        model=model_id,
        max_tokens=max_tokens,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content


def call_model(provider: str, model_id: str, system_prompt: str, user_prompt: str,
               max_tokens: int, temperature: float) -> str:
    """Route to the correct provider."""
    if provider == "google":
        return call_google(model_id, system_prompt, user_prompt, max_tokens, temperature)
    elif provider == "anthropic":
        return call_anthropic(model_id, system_prompt, user_prompt, max_tokens, temperature)
    elif provider == "openai":
        return call_openai(model_id, system_prompt, user_prompt, max_tokens, temperature)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def judge_project(project_dir: str, project_id: str, model_name: str,
                  model_config: dict) -> dict | None:
    """Judge a single project. Returns the score dict or None on failure."""

    intel, ctx = load_project_data(project_dir)
    if not intel:
        print(f"  SKIP {project_id}: no project_intelligence.json")
        return None

    # Get track context
    track = intel.get("track", "General")
    track_ctx = get_track_context(track)

    # Build the user prompt
    # Combine intel + track context into the ecosystem context section
    combined_context = json.dumps(ctx, indent=2, ensure_ascii=False) if ctx else "{}"
    combined_intel = json.dumps(intel, indent=2, ensure_ascii=False)

    # Add track context to ecosystem context
    full_context = combined_context
    if track_ctx:
        full_context += "\n\n# Track Context\n" + json.dumps(track_ctx, indent=2, ensure_ascii=False)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        project_intelligence=combined_intel,
        ecosystem_context=full_context,
    )

    # Call the model with retries
    max_retries = 3
    for attempt in range(max_retries):
        try:
            raw = call_model(
                provider=model_config["provider"],
                model_id=model_config["model_id"],
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_tokens=model_config["max_tokens"],
                temperature=model_config["temperature"],
            )
            score = parse_judge_response(raw)
            break # Success, exit retry loop
        except json.JSONDecodeError as e:
            print(f"  WARN {project_id}: Failed to parse JSON (attempt {attempt+1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                # Save raw response for debugging on final failure
                err_path = os.path.join(project_dir, f"score_{model_name}_error.txt")
                with open(err_path, "w", encoding="utf-8") as f:
                    f.write(raw)
                return None
            time.sleep(2)
        except Exception as e:
            print(f"  WARN {project_id}: API call failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return None
            time.sleep(5)

    # Validate
    is_valid, errors = validate_score(score)
    if not is_valid:
        print(f"  WARN {project_id}: Validation errors: {errors}")
        # Still save — partial data is better than no data

    # Enrich with metadata
    timestamp = datetime.now(timezone.utc).isoformat()
    score = enrich_output(score, model_name, model_config["model_id"], project_id, timestamp)

    return score


def main():
    parser = argparse.ArgumentParser(description="Run AI judge on hackathon projects")
    parser.add_argument("--model", required=True, help="Model name from config (e.g. gemini-flash)")
    parser.add_argument("--videos-dir", default="videos", help="Path to videos directory")
    parser.add_argument("--start", type=int, default=0, help="Start index (inclusive)")
    parser.add_argument("--end", type=int, default=None, help="End index (exclusive)")
    parser.add_argument("--project", default=None, help="Judge a single project by ID")
    parser.add_argument("--skip-existing", action="store_true", help="Skip projects already scored by this model")
    parser.add_argument("--workers", type=int, default=5, help="Number of concurrent API calls")
    args = parser.parse_args()

    if args.model not in MODELS:
        print(f"Unknown model: {args.model}. Available: {list(MODELS.keys())}")
        sys.exit(1)

    model_config = MODELS[args.model]
    model_name = args.model
    rpm = model_config["rpm"]
    delay = 60.0 / rpm  # seconds between calls

    print(f"Judge Model: {model_name} ({model_config['model_id']})")
    print(f"Rate limit: {rpm} RPM ({delay:.1f}s between calls)")
    print(f"Description: {model_config['description']}")
    print()

    # Get project list
    if args.project:
        dirs = [args.project]
    else:
        dirs = sorted([d for d in os.listdir(args.videos_dir)
                       if os.path.isdir(os.path.join(args.videos_dir, d))])
        end = args.end if args.end else len(dirs)
        dirs = dirs[args.start:end]

    print(f"Projects to judge: {len(dirs)}")
    print()

    scored = 0
    skipped = 0
    failed = 0
    
    # Filter directories to process
    to_process = []
    for d in dirs:
        project_dir = os.path.join(args.videos_dir, d)
        score_path = os.path.join(project_dir, f"score_{model_name}.json")
        if args.skip_existing and os.path.exists(score_path):
            skipped += 1
        else:
            to_process.append((project_dir, d))
            
    print(f"Skipped {skipped} already judged. Remaining to process: {len(to_process)}")
    print(f"Starting with {args.workers} workers...")
    
    def process_project(item):
        project_dir, d = item
        score_path = os.path.join(project_dir, f"score_{model_name}.json")
        score = judge_project(project_dir, d, model_name, model_config)
        if score:
            with open(score_path, "w", encoding="utf-8") as f:
                json.dump(score, f, indent=2, ensure_ascii=False)
            return (d, True, score)
        return (d, False, None)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_project, item): item for item in to_process}
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            d, success, score = future.result()
            print(f"[{i+1}/{len(to_process)}] Finished {d}")
            if success:
                overall = score.get("overall_score", 0)
                adjusted = score.get("adjusted_score", 0)
                conf = score.get("confidence", 0)
                print(f"  -> score={overall}, adjusted={adjusted}, confidence={conf}")
                scored += 1
            else:
                failed += 1

    print()
    print(f"Done. Scored: {scored}, Skipped: {skipped}, Failed: {failed}")


if __name__ == "__main__":
    main()

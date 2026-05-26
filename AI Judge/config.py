"""
Frontier Judge — Model Configuration

Add new judge models here. The pipeline uses the same prompts and rubric for all models.
Only the API call changes.
"""

MODELS = {
    "gemini-flash": {
        "provider": "google",
        "model_id": "gemini-2.5-flash",
        "rpm": 60,
        "max_tokens": 4096,
        "temperature": 0.1,
        "description": "Fast, cost-efficient baseline judge. Good for initial sweep."
    },
    "gemini-pro": {
        "provider": "google",
        "model_id": "gemini-2.5-pro",
        "rpm": 30,
        "max_tokens": 8192,
        "temperature": 0.1,
        "description": "Stronger reasoning, higher quality analysis."
    },
    "claude-opus": {
        "provider": "anthropic",
        "model_id": "claude-opus-4",
        "rpm": 20,
        "max_tokens": 8192,
        "temperature": 0.1,
        "description": "Deep reasoning, nuanced evaluation."
    },
    "gpt4o": {
        "provider": "openai",
        "model_id": "gpt-4o",
        "rpm": 30,
        "max_tokens": 4096,
        "temperature": 0.1,
        "description": "Strong general-purpose judge."
    },
}

# Track definitions for track-specific context
TRACKS = {
    "AI": {
        "track_name": "AI",
        "track_patterns": [
            "Many projects use agent wrappers around existing LLM APIs.",
            "Infrastructure-level AI innovation is rare — most submissions are application-layer.",
            "A large portion focuses on trading automation and portfolio management.",
            "Agent orchestration and multi-agent coordination represent emerging subcategories."
        ],
        "evaluation_focus": [
            "Working agent behavior with demonstrable autonomy",
            "Clear user value beyond 'AI does X for you'",
            "Non-trivial implementation — not just API wrapper",
            "Evidence of actual on-chain interaction, not just off-chain LLM calls"
        ]
    },
    "DeFi": {
        "track_name": "DeFi",
        "track_patterns": [
            "Lending, AMM, and yield aggregation are heavily saturated subcategories.",
            "Many projects reimplement existing DeFi primitives with minor variations.",
            "Cross-chain and intent-based architectures are emerging differentiators.",
            "RWA tokenization is a growing but increasingly crowded niche."
        ],
        "evaluation_focus": [
            "Novel mechanism design or meaningful parameter innovation",
            "Working smart contracts with on-chain evidence",
            "Risk management and security considerations",
            "Clear differentiation from existing DeFi protocols"
        ]
    },
    "Consumer": {
        "track_name": "Consumer",
        "track_patterns": [
            "Gaming, social, and content platforms are common but rarely deeply implemented.",
            "Many projects have ambitious scope but limited functional demos.",
            "Real-world utility projects (payments, identity) tend to be more grounded.",
            "UX quality varies dramatically — this is where it matters most."
        ],
        "evaluation_focus": [
            "Polished user experience with clear onboarding",
            "Demonstrated user flow, not just landing pages",
            "Realistic scope relative to hackathon timeline",
            "Evidence of real user need, not hypothetical demand"
        ]
    },
    "Infrastructure": {
        "track_name": "Infrastructure",
        "track_patterns": [
            "Dev tooling and SDK projects are common but often incomplete.",
            "Many infrastructure projects lack clear end-user demonstration.",
            "ZK and privacy infrastructure is technically ambitious but often conceptual.",
            "Developer experience and documentation quality are strong differentiators."
        ],
        "evaluation_focus": [
            "Working developer-facing tooling with clear documentation",
            "Performance benchmarks or technical evidence",
            "Clear ecosystem value — who uses this and why",
            "Integration with existing Solana developer workflows"
        ]
    },
    "default": {
        "track_name": "General",
        "track_patterns": [
            "Cross-category projects should be evaluated on execution quality first.",
            "Novel category combinations may indicate genuine innovation or scope confusion."
        ],
        "evaluation_focus": [
            "Working implementation",
            "Clear problem definition",
            "Evidence-supported functionality claims"
        ]
    }
}

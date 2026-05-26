# Frontier Ecosystem Statistical Intelligence Export

> Canonical statistical appendix for the Solana Frontier Hackathon dataset.
> *Total Projects Analyzed: 2870*

This document provides a purely structural, quantitative mapping of the ecosystem. It is designed to serve as the baseline calibration layer for analytical models and AI judges.

---

## 1. Geographic Intelligence

The topological diversity of the ecosystem is not uniformly distributed. Emerging ecosystems actively explore the design space (high Frontier Index, high Originality Density), while mature ecosystems optimize around existing saturated categories.

* **Frontier Index**: Unique Archetypes / Total Projects. Closer to 1.0 indicates pure exploration.
* **Originality Density**: % of projects with an outlier score > 0.7 (structurally distant from known clusters).
* **NDS (Narrative Dependency Score)**: % of projects building in the top 10 most saturated archetypes.
* **Spec/Util Ratio**: Weighted ratio of utility-focused domains (Payments, DePIN) to speculative domains (Trading, Yield). >1.0 indicates utility dominance.

### Top Countries by Originality (Min. 10 projects)
| Country            |   Projects |   Frontier_Index |   Originality_Density |   SpecUtil_Ratio |   NDS |
|:-------------------|-----------:|-----------------:|----------------------:|-----------------:|------:|
| Singapore          |         28 |            1.000 |                 0.429 |            1.110 | 0.143 |
| Nepal              |         51 |            0.980 |                 0.392 |            2.899 | 0.039 |
| Australia          |         35 |            0.971 |                 0.343 |            1.905 | 0.114 |
| Malaysia           |         53 |            0.925 |                 0.340 |            1.649 | 0.189 |
| France             |         32 |            0.969 |                 0.312 |            1.578 | 0.125 |
| Brazil             |        145 |            0.931 |                 0.303 |            2.422 | 0.110 |
| Germany            |         82 |            0.976 |                 0.280 |            2.173 | 0.061 |
| Japan              |         36 |            1.000 |                 0.278 |            1.500 | 0.083 |
| Thailand           |         33 |            1.000 |                 0.273 |            2.080 | 0.030 |
| Ireland {Republic} |         54 |            0.981 |                 0.259 |            2.288 | 0.093 |

![Country Speculation vs Utilization](charts/country_spec_util.png)

---

## 2. Archetype & Category Formation

The distribution of archetypes follows an extreme heavy-tailed distribution, departing from classical power laws observed in mature systems. 

* **Zipf Exponent (α)**: {-coeffs[0]:.3f}
* **Singletons**: {len(arch_stats[arch_stats['Projects'] == 1])} archetypes have exactly 1 project.
* **Category Concentration (HHI)**: {calculate_hhi(df['archetype']):.2f} (Extremely unconcentrated)

![Archetype Zipf Distribution](charts/zipf_distribution.png)

### Top 15 Most Saturated Archetypes
| archetype                       |   Projects |   Countries |   Mean_Outlier |   Mean_Cluster_Size |
|:--------------------------------|-----------:|------------:|---------------:|--------------------:|
| UNKNOWN                         |        101 |          38 |           0.31 |               83.79 |
| ONCHAIN_PREDICTION_MARKET       |         73 |          25 |           0.24 |              135.88 |
| AI_TRADING_COPILOT              |         60 |          23 |           0.22 |               29.43 |
| RWA_TOKENIZATION_PLATFORM       |         28 |          16 |           0.21 |              108.00 |
| WALLET_SECURITY_SCANNER         |         27 |          14 |           0.19 |               52.00 |
|                                 |         26 |          17 |           0.52 |               73.12 |
| AI_AGENT_MARKETPLACE            |         25 |          17 |           0.34 |               19.84 |
| PREDICTION_MARKET               |         23 |          15 |           0.32 |              140.22 |
| ZK_VERIFICATION_LAYER           |         12 |           7 |           0.29 |                6.33 |
| CRYPTO_PAYMENT_GATEWAY          |         11 |           5 |           0.36 |                8.64 |
| AI_AGENT_ORCHESTRATION_PLATFORM |         10 |           9 |           0.29 |               15.70 |
| AI_AGENT_SECURITY_LAYER         |          8 |           6 |           0.37 |               25.75 |
| AI_AGENT_PAYMENT_GATEWAY        |          7 |           5 |           0.22 |               41.00 |
| BASE_BUILDING_PVP_GAME          |          6 |           5 |           0.00 |              167.00 |
| AI_AGENT_COMPETITION_PLATFORM   |          5 |           5 |           0.22 |               10.40 |

---

## 3. Infrastructure Dependency

The product diversity of the ecosystem relies on a remarkably narrow infrastructure base.

* **Global ONCHAIN_VERIFICATION Dependency**: {df['primitives'].apply(lambda x: 'ONCHAIN_VERIFICATION' in x).mean() * 100:.1f}%

### Dependency by Country (Top 10)
| Country        |   Projects |   Infra_Dependency |
|:---------------|-----------:|-------------------:|
| Argentina      |         14 |              0.929 |
| France         |         32 |              0.875 |
| Korea South    |         31 |              0.839 |
| Vietnam        |         12 |              0.833 |
| Turkey         |         67 |              0.791 |
| Georgia        |         54 |              0.778 |
| Mexico         |         12 |              0.750 |
| Nepal          |         51 |              0.725 |
| Australia      |         35 |              0.714 |
| United Kingdom |        102 |              0.706 |

---

## 4. The Agent Economy (AI Saturation)

Autonomous agents represent a parallel economic system. AI is not evenly distributed globally.

### Highest AI Saturation (Min. 10 projects)
| Country     |   Projects |   AI_Saturation |   Originality_Density |
|:------------|-----------:|----------------:|----------------------:|
| Vietnam     |         12 |           0.750 |                 0.167 |
| Hong Kong   |         33 |           0.606 |                 0.091 |
| China       |         95 |           0.600 |                 0.211 |
| Argentina   |         14 |           0.571 |                 0.214 |
| Turkey      |         67 |           0.567 |                 0.254 |
| Japan       |         36 |           0.556 |                 0.278 |
| Singapore   |         28 |           0.536 |                 0.429 |
| Korea South |         31 |           0.516 |                 0.161 |
| Netherlands |         33 |           0.515 |                 0.242 |
| Malaysia    |         53 |           0.509 |                 0.340 |

---
*Exported at {pd.Timestamp.now('UTC').isoformat()}*
*Data source: project_intelligence.json, ecosystem_context.json*

#Competitor_Comparison_Agent.py

import json
import sys
from pathlib import Path
from typing import List, Dict
from phi.agent import Agent
from phi.llm.ollama import Ollama


# Handle imports for both direct execution and module import
try:
    from .schemas import CompetitorProfile, TrendSignals, ComparisonRequest, ComparisonResult
    from .security import verify_hmac, role_allowed, audit_log, validate_json_payload, sanitize_text, SecurityError
    from .config import get_config, get_ollama_config
except ImportError:
    # Add current directory to path for direct execution
    sys.path.insert(0, str(Path(__file__).parent))
    from schemas import CompetitorProfile, TrendSignals, ComparisonRequest, ComparisonResult
    from security import verify_hmac, role_allowed, audit_log, validate_json_payload, sanitize_text, SecurityError
    from config import get_config, get_ollama_config

# Get configuration
config = get_config()
ollama_config = get_ollama_config()

DATA_IN = Path(__file__).resolve().parents[1] / config.data.inbound_path
DATA_OUT = Path(__file__).resolve().parents[1] / config.data.outbound_path
DATA_OUT.mkdir(parents=True, exist_ok=True)

# ---- LLM (local) - Direct Ollama client using configuration
import requests
import json

def call_ollama_llm(prompt: str) -> str:
    """Direct call to Ollama API using configuration"""
    try:
        url = f"{ollama_config.base_url}/api/generate"
        data = {
            "model": ollama_config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": ollama_config.temperature,
                "top_p": ollama_config.top_p,
                "max_tokens": ollama_config.max_tokens
            }
        }
        
        # Use configured timeout
        response = requests.post(url, json=data, timeout=ollama_config.timeout)
        if response.status_code == 200:
            result = response.json()
            return result.get('response', '').strip()
        else:
            print(f"Ollama API error: {response.status_code}")
            return ""
    except requests.exceptions.Timeout:
        print(f"Ollama request timed out after {ollama_config.timeout}s - model may be loading for first time")
        return ""
    except Exception as e:
        print(f"Ollama call failed: {e}")
        return ""

# Keep the old phidata Agent for compatibility but don't use it for LLM calls
llm = Ollama(
    model=ollama_config.model,
    base_url=ollama_config.base_url,
    temperature=ollama_config.temperature
)

agent4 = None  # We'll use direct Ollama calls instead

system_prompt = f"""You are {config.agent.name} v{config.agent.version}: Competitor Comparison & Security.
- Use provided competitor profiles, KPIs, pricing, and features.
- Compute a composite score per competitor based on weights.
- Justify ranking briefly.
- Output concise, decision-ready insights.
- Environment: {config.agent.environment}
"""

def _load_json_file(p: Path) -> dict:
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def gather_inputs() -> Dict:
    """Load latest files dropped by Agents 1–3.
    Also supports fallback for Trend Analyzer output from Agent 3 written to outbound as trend_chart_plan.json.
    """
    data = {}
    # Primary inbound files
    for fname in ["competitors.json", "trends.json", "comparison_request.json"]:
        fp = DATA_IN / fname
        if fp.exists():
            data[fname] = _load_json_file(fp)

    # Fallback: if trends.json missing, look for trend chart plan in outbound
    if "trends.json" not in data:
        fallback_plan = DATA_OUT / "trend_chart_plan.json"
        if fallback_plan.exists():
            data["trend_chart_plan.json"] = _load_json_file(fallback_plan)

    return data

def compute_scores(profiles: List[CompetitorProfile], req: ComparisonRequest) -> ComparisonResult:
    # Simple baseline: normalize availability of features, sum weighted KPIs, lower price => higher score
    scores: Dict[str, float] = {}
    for prof in profiles:
        # KPIs
        kpi_score = 0.0
        for k in req.primary_kpis:
            v = prof.kpis.get(k, 0.0)
            kpi_score += v
        # Features
        feat_score = 0.0
        for f, w in req.feature_weights.items():
            feat_score += (1.0 if prof.features.get(f, False) else 0.0) * w
        # Price (assume lower total monthly avg is better)
        price_avg = 0.0
        if prof.pricing:
            price_avg = sum(prof.pricing.values()) / max(len(prof.pricing), 1)
        # Normalize price into a benefit: lower price => higher value
        price_term = 1.0 / (1.0 + price_avg)

        composite = (req.kpi_weight * kpi_score) + (req.feature_weight * feat_score) + (req.price_weight * price_term)
        scores[prof.name] = float(composite)

    ranking = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)
    return ComparisonResult(scores=scores, ranking=ranking, notes="Baseline composite scoring.")

def run_compare(requester_role: str = "agent4") -> Path:
    """Enhanced secure competitor comparison with RBAC and audit logging"""
    from datetime import datetime
    
    # Security checks
    if not role_allowed(requester_role, "compare"):
        audit_log("unauthorized_comparison_attempt", requester_role)
        raise SecurityError(f"Role {requester_role} not authorized to perform comparison")
    
    audit_log("comparison_started", requester_role, {"timestamp": datetime.utcnow().isoformat()})
    
    try:
        data = gather_inputs()
        
        # Validate input data integrity
        for filename, content in data.items():
            if not validate_json_payload(json.dumps(content)):
                audit_log("invalid_input_data", requester_role, {"filename": filename})
                raise SecurityError(f"Invalid data format in {filename}")
        
        # Basic validation with enhanced security
        comps = []
        for comp_data in data.get("competitors.json", []):
            try:
                # Sanitize competitor data
                sanitized_comp = {
                    "name": sanitize_text(comp_data.get("name", "")),
                    "website": sanitize_text(comp_data.get("website", "")),
                    "kpis": comp_data.get("kpis", {}),
                    "pricing": comp_data.get("pricing", {}),
                    "features": comp_data.get("features", {})
                }
                comps.append(CompetitorProfile(**sanitized_comp))
            except Exception as e:
                audit_log("competitor_data_error", requester_role, {"error": str(e), "data": comp_data})
                print(f"Warning: Skipping invalid competitor data: {e}")
        
        trends = None
        if "trends.json" in data:
            try:
                trends_data = data["trends.json"]
                # Sanitize trends data
                sanitized_trends = {
                    "topics": [sanitize_text(topic) for topic in trends_data.get("topics", [])],
                    "sentiment_score": trends_data.get("sentiment_score"),
                    "growth_keywords": [sanitize_text(kw) for kw in trends_data.get("growth_keywords", [])],
                    "regions": [sanitize_text(region) for region in trends_data.get("regions", [])]
                }
                trends = TrendSignals(**sanitized_trends)
            except Exception as e:
                audit_log("trends_data_error", requester_role, {"error": str(e)})
                print(f"Warning: Invalid trends data: {e}")
        # Fallback: build a minimal TrendSignals from trend_chart_plan.json
        elif "trend_chart_plan.json" in data:
            try:
                plan = data["trend_chart_plan.json"] or {}
                charts = plan.get("charts", []) if isinstance(plan, dict) else []
                topics: List[str] = []
                # Extract company names or labels from first chart series
                if charts and isinstance(charts[0], dict):
                    series_list = charts[0].get("series", [])
                    if series_list and isinstance(series_list[0], dict):
                        data_points = series_list[0].get("data", [])
                        # data_points expected like [["Company A", 123], ...] or list of pairs
                        for dp in data_points:
                            try:
                                name = dp[0]
                                if isinstance(name, str):
                                    topics.append(sanitize_text(name))
                            except Exception:
                                continue
                sanitized_trends = {
                    "topics": topics[:10],
                    "sentiment_score": None,
                    "growth_keywords": [],
                    "regions": [],
                }
                trends = TrendSignals(**sanitized_trends)
                audit_log("trend_fallback_used", requester_role, {"source": "trend_chart_plan.json", "topics_count": len(topics)})
            except Exception as e:
                audit_log("trend_fallback_error", requester_role, {"error": str(e)})
                print(f"Warning: Trend fallback failed: {e}")
        
        req_data = data.get("comparison_request.json", {
            "market": "default",
            "primary_kpis": ["MAU", "NPS"],
            "feature_weights": {"feature_x": 0.5, "feature_y": 0.5},
            "price_weight": 0.2, "kpi_weight": 0.5, "feature_weight": 0.3,
        })
        
        # Sanitize request data
        sanitized_req = {
            "market": sanitize_text(req_data.get("market", "default")),
            "primary_kpis": [sanitize_text(kpi) for kpi in req_data.get("primary_kpis", [])],
            "feature_weights": req_data.get("feature_weights", {}),
            "price_weight": req_data.get("price_weight", 0.2),
            "kpi_weight": req_data.get("kpi_weight", 0.5),
            "feature_weight": req_data.get("feature_weight", 0.3)
        }
        req = ComparisonRequest(**sanitized_req)

        if not comps:
            audit_log("no_valid_competitors", requester_role)
            raise SecurityError("No valid competitor data found")

        result = compute_scores(comps, req)
        
        # Ask LLM for a short executive summary (uses phidata+Ollama)
        prompt = f"""Market: {req.market}
        Trends: {trends.dict() if trends else {}}
        Scores: {result.scores}
        Ranking: {result.ranking}
        Provide an executive summary (<=150 words) focusing on why the top 2 rank highest and risks to watch."""
        
        summary = "LLM analysis unavailable - using baseline scoring only."
        try:
            llm_response = call_ollama_llm(prompt)
            if llm_response:
                summary = sanitize_text(llm_response)
                audit_log("llm_summary_generated", requester_role, {"summary_length": len(summary)})
            else:
                audit_log("llm_response_empty", requester_role)
        except Exception as e:
            audit_log("llm_error", requester_role, {"error": str(e)})
            print(f"LLM call failed: {e}")
        
        # Prepare secure output
        out = {
            "comparison": result.dict(),
            "executive_summary": summary,
            "request": req.dict(),
            "metadata": {
                "generated_by": requester_role,
                "timestamp": datetime.utcnow().isoformat(),
                "competitors_analyzed": len(comps),
                "security_validated": True
            }
        }
        
        out_path = DATA_OUT / "competitor_comparison_result.json"
        out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        
        audit_log("comparison_completed", requester_role, {
            "output_file": str(out_path),
            "competitors_count": len(comps),
            "ranking": result.ranking
        })
        
        print(f"Secure comparison completed for {requester_role}")
        print(f"Analyzed {len(comps)} competitors")
        print(f"Results: {result.ranking}")
        
        return out_path
        
    except Exception as e:
        audit_log("comparison_error", requester_role, {"error": str(e)})
        raise

if __name__ == "__main__":
    run_compare()


def run_compare_from_payload(
    competitors: List[Dict],
    trends: Dict = None,
    request: Dict = None,
    requester_role: str = "agent4",
) -> Dict:
    """Run comparison using in-memory payloads instead of reading/writing files.
    Returns the output dict that would normally be written to outbound JSON.
    """
    from datetime import datetime

    # Security check consistent with file-based flow
    if not role_allowed(requester_role, "compare"):
        audit_log("unauthorized_comparison_attempt", requester_role)
        raise SecurityError(f"Role {requester_role} not authorized to perform comparison")

    audit_log("comparison_started", requester_role, {"mode": "payload", "timestamp": datetime.utcnow().isoformat()})

    try:
        # Competitors
        comps: List[CompetitorProfile] = []
        for comp_data in competitors or []:
            try:
                sanitized_comp = {
                    "name": sanitize_text(comp_data.get("name", "")),
                    "website": sanitize_text(comp_data.get("website", "")),
                    "kpis": comp_data.get("kpis", {}),
                    "pricing": comp_data.get("pricing", {}),
                    "features": comp_data.get("features", {}),
                }
                comps.append(CompetitorProfile(**sanitized_comp))
            except Exception as e:
                audit_log("competitor_data_error", requester_role, {"error": str(e), "data": comp_data})

        # Trends (optional)
        trend_signals: TrendSignals = None
        if trends:
            try:
                sanitized_trends = {
                    "topics": [sanitize_text(t) for t in trends.get("topics", [])],
                    "sentiment_score": trends.get("sentiment_score"),
                    "growth_keywords": [sanitize_text(k) for k in trends.get("growth_keywords", [])],
                    "regions": [sanitize_text(r) for r in trends.get("regions", [])],
                }
                trend_signals = TrendSignals(**sanitized_trends)
            except Exception as e:
                audit_log("trends_data_error", requester_role, {"error": str(e)})

        # Request
        req_input = request or {}
        sanitized_req = {
            "market": sanitize_text(req_input.get("market", "default")),
            "primary_kpis": [sanitize_text(kpi) for kpi in req_input.get("primary_kpis", [])],
            "feature_weights": req_input.get("feature_weights", {}),
            "price_weight": req_input.get("price_weight", 0.2),
            "kpi_weight": req_input.get("kpi_weight", 0.5),
            "feature_weight": req_input.get("feature_weight", 0.3),
        }
        req = ComparisonRequest(**sanitized_req)

        if not comps:
            audit_log("no_valid_competitors", requester_role)
            raise SecurityError("No valid competitor data found")

        # Score
        result = compute_scores(comps, req)

        # Summary via Ollama
        prompt = f"""Market: {req.market}
        Trends: {trend_signals.dict() if trend_signals else {}}
        Scores: {result.scores}
        Ranking: {result.ranking}
        Provide an executive summary (<=150 words) focusing on why the top 2 rank highest and risks to watch."""

        summary = "LLM analysis unavailable - using baseline scoring only."
        try:
            llm_response = call_ollama_llm(prompt)
            if llm_response:
                summary = sanitize_text(llm_response)
                audit_log("llm_summary_generated", requester_role, {"summary_length": len(summary), "mode": "payload"})
            else:
                audit_log("llm_response_empty", requester_role)
        except Exception as e:
            audit_log("llm_error", requester_role, {"error": str(e)})

        out = {
            "comparison": result.dict(),
            "executive_summary": summary,
            "request": req.dict(),
            "metadata": {
                "generated_by": requester_role,
                "timestamp": datetime.utcnow().isoformat(),
                "competitors_analyzed": len(comps),
                "security_validated": True,
                "mode": "payload",
            },
        }

        audit_log("comparison_completed", requester_role, {"mode": "payload", "competitors_count": len(comps), "ranking": result.ranking})
        return out

    except Exception as e:
        audit_log("comparison_error", requester_role, {"error": str(e), "mode": "payload"})
        raise

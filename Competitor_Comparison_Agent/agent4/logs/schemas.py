#schemas.py

from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class CompetitorProfile(BaseModel):
    name: str
    website: Optional[str] = None
    description: Optional[str] = None
    kpis: Dict[str, float] = Field(default_factory=dict)  # e.g., MAU, DAU, churn, NPS
    pricing: Dict[str, float] = Field(default_factory=dict)  # plan->price
    features: Dict[str, bool] = Field(default_factory=dict)  # feature->available?

class TrendSignals(BaseModel):
    topics: List[str] = []
    sentiment_score: Optional[float] = None   # -1..1
    growth_keywords: List[str] = []
    regions: List[str] = []

class ComparisonRequest(BaseModel):
    market: str
    primary_kpis: List[str]
    feature_weights: Dict[str, float]  # feature -> weight 0..1
    price_weight: float = 0.2          # 0..1
    kpi_weight: float = 0.5
    feature_weight: float = 0.3

class ComparisonResult(BaseModel):
    scores: Dict[str, float]          # competitor -> composite score
    ranking: List[str]
    notes: str = ""

"""
YouTube Expert - World-class YouTube channel management system

A comprehensive suite of AI-powered skills for maintaining, optimizing,
and analyzing YouTube channels. Designed to be run by agents.

Skills:
  - diagnostics: Channel health check & issue detection
  - performance: Deep video performance analysis
  - shorts_strategy: Shorts vs long-form optimization
  - thumbnail_optimizer: Title/thumbnail A/B test recommendations
  - upload_scheduler: Optimal upload timing analysis
  - seo_optimizer: Title, description, tags optimization
  - audience_analyzer: Viewer retention & demographics
  - revenue_optimizer: Monetization strategy
  - growth_projector: Trend forecasting & projections
  - competitor_analyzer: Competitive landscape analysis
  - content_planner: Content calendar recommendations
  - trend_detector: Trending topics in your niche
"""

__version__ = "1.0.0"
__author__ = "YouTube Expert System"

from .core import YouTubeExpert
from .skills import (
    DiagnosticsSkill,
    PerformanceSkill,
    ShortsStrategySkill,
    ThumbnailOptimizerSkill,
    UploadSchedulerSkill,
    SEOOptimizerSkill,
    AudienceAnalyzerSkill,
    RevenueOptimizerSkill,
    GrowthProjectorSkill,
    CompetitorAnalyzerSkill,
    ContentPlannerSkill,
    TrendDetectorSkill,
)

__all__ = [
    "YouTubeExpert",
    "DiagnosticsSkill",
    "PerformanceSkill",
    "ShortsStrategySkill",
    "ThumbnailOptimizerSkill",
    "UploadSchedulerSkill",
    "SEOOptimizerSkill",
    "AudienceAnalyzerSkill",
    "RevenueOptimizerSkill",
    "GrowthProjectorSkill",
    "CompetitorAnalyzerSkill",
    "ContentPlannerSkill",
    "TrendDetectorSkill",
]

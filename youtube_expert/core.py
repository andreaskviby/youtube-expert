"""
Core YouTube Expert engine - orchestrates all skills
"""

from __future__ import annotations

import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class ChannelData:
    """Container for all channel data sources"""

    videos_df: Optional[pd.DataFrame] = None
    daily_totals_df: Optional[pd.DataFrame] = None
    daily_videos_df: Optional[pd.DataFrame] = None
    channel_info: Dict[str, Any] = field(default_factory=dict)

    # Computed metrics
    total_views: int = 0
    total_watch_hours: float = 0.0
    total_subscribers: int = 0
    video_count: int = 0
    shorts_count: int = 0
    longform_count: int = 0

    def __post_init__(self):
        if self.videos_df is not None:
            self._compute_metrics()

    def _compute_metrics(self):
        df = self.videos_df

        # Skip total row if present (handles both Swedish and English column names)
        if 'Innehåll' in df.columns:
            df = df[df['Innehåll'].notna() & (df['Innehåll'] != 'Totalt')]
        elif 'video_id' in df.columns:
            df = df[df['video_id'].notna() & (df['video_id'] != 'Totalt')]

        self.video_count = len(df)

        # Handle both Swedish and English column names
        views_col = 'views' if 'views' in df.columns else 'Visningar'
        hours_col = 'watch_hours' if 'watch_hours' in df.columns else 'Visningstid (timmar)'
        subs_col = 'subscribers_gained' if 'subscribers_gained' in df.columns else 'Prenumeranter'
        duration_col = 'duration_seconds' if 'duration_seconds' in df.columns else 'Längd'

        self.total_views = int(df[views_col].sum()) if views_col in df.columns else 0

        if hours_col in df.columns:
            self.total_watch_hours = float(df[hours_col].sum())

        if subs_col in df.columns:
            self.total_subscribers = int(df[subs_col].sum())

        # Classify shorts vs longform (Shorts are <= 60 seconds)
        if duration_col in df.columns:
            self.shorts_count = len(df[df[duration_col] <= 60])
            self.longform_count = len(df[df[duration_col] > 60])


class DataLoader:
    """Loads and normalizes YouTube analytics data from CSV files"""

    COLUMN_MAP = {
        # Swedish to English mapping
        'Innehåll': 'video_id',
        'Videotitel': 'title',
        'Publiceringstid för video': 'published_at',
        'Längd': 'duration_seconds',
        'Visningar': 'views',
        'Visningstid (timmar)': 'watch_hours',
        'Prenumeranter': 'subscribers_gained',
        'Exponeringar': 'impressions',
        'Klickfrekvens för exponeringar (%)': 'ctr_percent',
        'Datum': 'date',
    }

    @classmethod
    def load_from_directory(cls, directory: str | Path) -> ChannelData:
        """Load all CSV files from a directory"""
        directory = Path(directory)
        data = ChannelData()

        # Table data (main video metrics)
        table_path = directory / "Table data.csv"
        if table_path.exists():
            data.videos_df = cls._load_and_normalize(table_path)

        # Daily totals
        totals_path = directory / "Totals.csv"
        if totals_path.exists():
            data.daily_totals_df = cls._load_and_normalize(totals_path)

        # Daily per-video data
        chart_path = directory / "Chart data.csv"
        if chart_path.exists():
            data.daily_videos_df = cls._load_and_normalize(chart_path)

        # Recompute metrics with loaded data
        if data.videos_df is not None:
            data._compute_metrics()

        return data

    @classmethod
    def _load_and_normalize(cls, path: Path) -> pd.DataFrame:
        """Load CSV and normalize column names"""
        df = pd.read_csv(path)

        # Rename columns using mapping
        rename_map = {k: v for k, v in cls.COLUMN_MAP.items() if k in df.columns}
        df = df.rename(columns=rename_map)

        # Parse dates
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')

        if 'published_at' in df.columns:
            df['published_at'] = pd.to_datetime(df['published_at'], format='mixed', errors='coerce')

        # Add computed columns
        if 'duration_seconds' in df.columns:
            df['is_short'] = df['duration_seconds'] <= 60
            df['content_type'] = df['is_short'].map({True: 'SHORT', False: 'LONGFORM'})
            df['duration_minutes'] = df['duration_seconds'] / 60

        if 'views' in df.columns and 'watch_hours' in df.columns:
            # Average view duration in minutes
            df['avg_view_duration'] = (df['watch_hours'] * 60) / df['views'].replace(0, 1)

            # Retention estimate (avg view / total duration)
            if 'duration_seconds' in df.columns:
                df['retention_estimate'] = (df['avg_view_duration'] * 60) / df['duration_seconds'].replace(0, 1)
                df['retention_estimate'] = df['retention_estimate'].clip(0, 1) * 100

        return df


class YouTubeExpert:
    """
    Main orchestrator for YouTube Expert skills

    Usage:
        expert = YouTubeExpert("/path/to/data")

        # Run individual skills
        diag = expert.run_skill("diagnostics")
        perf = expert.run_skill("performance")

        # Run all skills
        full_report = expert.run_all_skills()

        # Get skill directly
        skill = expert.get_skill("shorts_strategy")
        result = skill.analyze(expert.data)
    """

    def __init__(self, data_directory: str | Path = None):
        self.data_directory = Path(data_directory) if data_directory else None
        self.data: Optional[ChannelData] = None
        self._skills: Dict[str, Any] = {}

        if self.data_directory:
            self.load_data()

        self._register_skills()

    def load_data(self, directory: str | Path = None):
        """Load channel data from CSV files"""
        if directory:
            self.data_directory = Path(directory)

        if not self.data_directory:
            raise ValueError("No data directory specified")

        self.data = DataLoader.load_from_directory(self.data_directory)
        return self.data

    def _register_skills(self):
        """Register all available skills"""
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

        self._skills = {
            'diagnostics': DiagnosticsSkill(),
            'performance': PerformanceSkill(),
            'shorts_strategy': ShortsStrategySkill(),
            'thumbnail_optimizer': ThumbnailOptimizerSkill(),
            'upload_scheduler': UploadSchedulerSkill(),
            'seo_optimizer': SEOOptimizerSkill(),
            'audience_analyzer': AudienceAnalyzerSkill(),
            'revenue_optimizer': RevenueOptimizerSkill(),
            'growth_projector': GrowthProjectorSkill(),
            'competitor_analyzer': CompetitorAnalyzerSkill(),
            'content_planner': ContentPlannerSkill(),
            'trend_detector': TrendDetectorSkill(),
        }

    def get_skill(self, name: str):
        """Get a specific skill by name"""
        if name not in self._skills:
            raise ValueError(f"Unknown skill: {name}. Available: {list(self._skills.keys())}")
        return self._skills[name]

    def run_skill(self, name: str, **kwargs) -> Dict[str, Any]:
        """Run a specific skill and return results"""
        skill = self.get_skill(name)
        return skill.analyze(self.data, **kwargs)

    def run_all_skills(self) -> Dict[str, Any]:
        """Run all skills and return comprehensive report"""
        results = {}
        for name, skill in self._skills.items():
            try:
                results[name] = skill.analyze(self.data)
            except Exception as e:
                results[name] = {"error": str(e)}

        return {
            "timestamp": datetime.now().isoformat(),
            "channel_summary": {
                "video_count": self.data.video_count,
                "total_views": self.data.total_views,
                "total_watch_hours": round(self.data.total_watch_hours, 1),
                "shorts_count": self.data.shorts_count,
                "longform_count": self.data.longform_count,
            },
            "skills": results,
        }

    def list_skills(self) -> List[Dict[str, str]]:
        """List all available skills with descriptions"""
        return [
            {
                "name": name,
                "description": skill.__doc__ or "No description",
            }
            for name, skill in self._skills.items()
        ]

    def get_quick_summary(self) -> str:
        """Get a quick text summary of channel status"""
        if not self.data or self.data.videos_df is None:
            return "No data loaded"

        df = self.data.videos_df

        # Filter out total row
        if 'video_id' in df.columns:
            df = df[df['video_id'].notna() & (df['video_id'] != 'Totalt')]

        lines = [
            "=" * 60,
            "YOUTUBE CHANNEL QUICK SUMMARY",
            "=" * 60,
            f"Total Videos: {self.data.video_count}",
            f"  - Shorts (≤60s): {self.data.shorts_count}",
            f"  - Long-form (>60s): {self.data.longform_count}",
            "",
            f"Total Views: {self.data.total_views:,}",
            f"Total Watch Hours: {self.data.total_watch_hours:,.1f}",
            "",
        ]

        # Top 5 videos
        if 'views' in df.columns:
            top5 = df.nlargest(5, 'views')[['title', 'views', 'content_type']]
            lines.append("Top 5 Videos by Views:")
            for _, row in top5.iterrows():
                lines.append(f"  [{row['content_type']}] {row['views']:,} - {row['title'][:50]}")

        return "\n".join(lines)

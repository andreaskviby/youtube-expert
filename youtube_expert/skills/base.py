"""
Base skill class for YouTube Expert
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core import ChannelData


class BaseSkill(ABC):
    """
    Base class for all YouTube Expert skills

    Each skill:
    - Analyzes specific aspects of channel data
    - Returns structured results with metrics, insights, and recommendations
    - Generates a human-readable digest
    - Can be run independently by agents
    """

    name: str = "base"
    description: str = "Base skill"

    @abstractmethod
    def analyze(self, data: ChannelData, **kwargs) -> Dict[str, Any]:
        """
        Analyze channel data and return results

        Returns:
            Dict with keys:
            - metrics: Quantitative measurements
            - insights: Key findings
            - recommendations: Actionable suggestions
            - severity: OK | WATCH | WARNING | CRITICAL
            - digest: Human-readable summary string
        """
        pass

    def _severity_from_score(self, score: float) -> str:
        """Convert a 0-100 score to severity level"""
        if score >= 80:
            return "OK"
        elif score >= 60:
            return "WATCH"
        elif score >= 40:
            return "WARNING"
        else:
            return "CRITICAL"

    def _format_number(self, n: float) -> str:
        """Format large numbers with K/M suffix"""
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        elif n >= 1_000:
            return f"{n/1_000:.1f}K"
        else:
            return f"{n:.0f}"

    def _format_percent(self, value: float, decimals: int = 1) -> str:
        """Format percentage"""
        return f"{value:.{decimals}f}%"

    def _calculate_percentile(self, values: list, value: float) -> float:
        """Calculate what percentile a value is in a list"""
        if not values:
            return 50.0
        below = sum(1 for v in values if v < value)
        return (below / len(values)) * 100

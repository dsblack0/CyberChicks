"""
AI Analysis Package for SnapAlert

This package provides automated productivity analysis using Ollama's Mistral model.
It includes:
- ProductivityAnalyzer: Core analysis engine
- AIAnalysisScheduler: Scheduling and orchestration
- System prompts for consistent analysis
"""

from .analyzer import ProductivityAnalyzer, create_default_config
from .scheduler import (
    AIAnalysisScheduler,
    get_scheduler,
    init_scheduler,
    start_scheduler,
    stop_scheduler,
)

__version__ = "1.0.0"
__all__ = [
    "ProductivityAnalyzer",
    "AIAnalysisScheduler",
    "create_default_config",
    "get_scheduler",
    "init_scheduler",
    "start_scheduler",
    "stop_scheduler",
]

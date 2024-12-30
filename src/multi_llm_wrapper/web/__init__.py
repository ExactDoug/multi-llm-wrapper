"""
Multi-LLM Web Interface

This module provides a web interface for the Multi-LLM Wrapper, allowing real-time
streaming of responses from multiple language models simultaneously.

Key Components:
- FastAPI application for serving the web interface
- Server-Sent Events (SSE) for real-time streaming
- Responsive UI that works on desktop and mobile devices
- Markdown rendering for formatted responses
- Expandable/collapsible windows for detailed viewing

Usage:
    from multi_llm_wrapper.web import run
    run.main()
"""

from . import app
from . import run

__all__ = ['app', 'run']
from typing import Dict, Any, List, AsyncGenerator
import json
from ..analyzer.query_analyzer import QueryAnalyzer
from .knowledge_aggregator import KnowledgeAggregator
from ..fetcher.brave_client import BraveSearchClient

class BraveKnowledgeAggregator:
    """
    Bridges between LLMService and the specialized search engine knowledge components.
    Maintains streaming compatibility while leveraging advanced processing capabilities.
    """
    
    def __init__(self, brave_client: BraveSearchClient):
        self.query_analyzer = QueryAnalyzer()
        self.knowledge_aggregator = KnowledgeAggregator()
        self.brave_client = brave_client

    async def process_query(self, query: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a query through the specialized search engine knowledge pipeline.
        Returns a streaming response compatible with LLMService expectations.
        """
        try:
            # 1. Analyze query
            analysis = await self.query_analyzer.analyze_query(query)
            search_query = analysis.search_string

            # 2. Execute search
            results = await self.brave_client.search(search_query)

            # 3. Process results through aggregator
            aggregated = await self.knowledge_aggregator.process_parallel(
                query=search_query,
                sources=["brave_search"],
                raw_results=results
            )

            # 4. Stream formatted response
            # First send title
            yield {"type": "title", "title": "Brave Search"}

            # Format and stream content
            formatted_response = []
            formatted_response.append("### Search Results\n")

            # Add analyzed query insights if available
            if analysis.insights:
                formatted_response.append("#### Query Analysis")
                formatted_response.append(f"{analysis.insights}\n")

            # Add aggregated results
            for i, result in enumerate(aggregated.results, 1):
                formatted_response.append(f"{i}. **{result.title}**")
                formatted_response.append(f"   URL: {result.url}")
                formatted_response.append(f"   {result.description}")
                if result.additional_context:
                    formatted_response.append(f"   Additional Context: {result.additional_context}")
                formatted_response.append("")  # Empty line between results

            # Add synthesis if available
            if aggregated.synthesis:
                formatted_response.append("### Knowledge Synthesis")
                formatted_response.append(f"{aggregated.synthesis}\n")

            content = "\n".join(formatted_response)
            yield {"type": "content", "content": content}

            # Signal completion
            yield {"type": "done"}

        except Exception as e:
            yield {"type": "error", "message": str(e)}
from typing import AsyncGenerator, Dict, List, Optional, Union

from ..analyzer.query_analyzer import QueryAnalyzer
from ..fetcher.brave_client import BraveSearchClient
from .knowledge_synthesizer import KnowledgeSynthesizer


class BraveKnowledgeAggregator:
    def __init__(
        self,
        brave_client: BraveSearchClient,
        query_analyzer: Optional[QueryAnalyzer] = None,
        knowledge_synthesizer: Optional[KnowledgeSynthesizer] = None,
    ):
        self.brave_client = brave_client
        self.query_analyzer = query_analyzer or QueryAnalyzer()
        self.knowledge_synthesizer = knowledge_synthesizer or KnowledgeSynthesizer()

    async def process_query(
        self, query: str
    ) -> AsyncGenerator[Dict[str, Union[str, bool]], None]:
        """Process a query and yield results."""
        try:
            # Get query analysis first
            query_analysis = await self.query_analyzer.analyze_query(query)

            # Get search results
            search_results = []
            try:
                # Get search results using async iterator
                search_iterator = self.brave_client.search(query)  # Remove await since search() returns an iterator
                async for result in search_iterator:
                    search_results.append(result)
                    # Yield content after each result
                    formatted_response = {
                        "type": "content",
                        "title": f"Processing query: {query}",
                        "content": (
                            f"Query analysis: {query_analysis}\n\n"
                            f"Search results:\n{self._format_results(search_results)}"
                        )
                    }
                    yield formatted_response

                if not search_results:
                    yield {"type": "error", "error": "No search results found"}
                    return

                # After all results, add knowledge synthesis
                knowledge = await self.knowledge_synthesizer.synthesize(search_results)
                formatted_response = {
                    "type": "content",
                    "title": f"Processing query: {query}",
                    "content": (
                        f"Query analysis: {query_analysis}\n\n"
                        f"Search results:\n{self._format_results(search_results)}\n\n"
                        f"Knowledge synthesis: {knowledge}"
                    )
                }
                yield formatted_response

            except Exception as e:
                # If we got any results before the error, yield them
                if search_results:
                    formatted_response = {
                        "type": "content",
                        "title": f"Processing query: {query}",
                        "content": (
                            f"Query analysis: {query_analysis}\n\n"
                            f"Partial search results:\n{self._format_results(search_results)}"
                        )
                    }
                    yield formatted_response
                # Then yield the error
                yield {"type": "error", "error": str(e)}
                return

        except Exception as e:
            # If error occurs before getting any results
            yield {"type": "error", "error": str(e)}
            return

    def _format_results(self, results: List[Dict[str, str]]) -> str:
        """Format search results into a readable string."""
        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(
                f"{i}. {result['title']}\n"
                f"   URL: {result['url']}\n"
                f"   {result['description']}\n"
            )
        return "\n".join(formatted)
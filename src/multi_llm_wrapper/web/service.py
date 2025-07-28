from typing import AsyncGenerator, Dict, Any, Optional
import os
from datetime import datetime, timedelta
import json
from ..wrapper import LLMWrapper

class LLMService:
    def __init__(self):
        self.wrapper = LLMWrapper()
        self.responses = {}  # session_id -> {query, timestamp, responses}
        self.last_cleanup = datetime.now()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        if hasattr(self.wrapper, 'brave_search'):
            await self.wrapper.brave_search.close()
        
    def add_response(self, session_id: str, llm_index: int, response: str, query: str = None):
        """Add a response for a specific LLM in a session."""
        if session_id not in self.responses:
            self.responses[session_id] = {
                'timestamp': datetime.now(),
                'query': query,
                'responses': {}
            }
        self.responses[session_id]['responses'][llm_index] = response
        self._cleanup()
        
    def get_responses(self, session_id: str) -> dict:
        """Get all responses for a session."""
        if session_id in self.responses:
            return self.responses[session_id]
        return {'responses': {}, 'query': None}
    
    def _cleanup(self):
        """Remove old sessions (older than 1 hour)."""
        current_time = datetime.now()
        if (current_time - self.last_cleanup).seconds < 3600:  # Only cleanup every hour
            return
            
        self.responses = {
            sid: data for sid, data in self.responses.items()
            if current_time - data['timestamp'] < timedelta(hours=1)
        }
        self.last_cleanup = current_time
        
    async def stream_llm_response(self, llm_index: int, query: str, session_id: str) -> AsyncGenerator[str, None]:
        """Stream responses from a specific LLM."""
        complete_response = []  # Accumulate complete response
        try:
            # Map indices to specific models
            models = [
                "claude-3-opus-20240229",    # 0: Claude 3 Opus
                "claude-3-sonnet-20240229",  # 1: Claude 3 Sonnet
                "gpt-4",                     # 2: GPT-4
                "gpt-3.5-turbo",            # 3: GPT-3.5 Turbo
                "groq/mistral-saba-24b",       # 4: Groq Mistral
                "groq/llama3-8b-8192",           # 5: Groq LLaMA 3
                "sonar",              # 6: Perplexity Sonar
                "sonar-pro",              # 7: Perplexity Sonar Pro
                "gemini-1.5-flash",         # 8: Google Gemini 1.5 Flash
                "brave_search",              # 9: Brave Search
                "groq_proxy/llama2-70b-8192" # 10: Groq Proxy Llama2
            ]
            
            # Validate index and get model
            if not (0 <= llm_index < len(models)):
                raise ValueError(f"Invalid LLM index: {llm_index}. Must be between 0 and {len(models)-1}")
                
            model = models[llm_index]
            # Handle Brave Search using specialized knowledge aggregator
            if model == "brave_search":
                if not self.wrapper.brave_search:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Brave Search not configured. Please set BRAVE_SEARCH_API_KEY in .env'})}\n\n"
                    return

                try:
                    # Use BraveKnowledgeAggregator for enhanced processing
                    from brave_search_aggregator.synthesizer.brave_knowledge_aggregator import BraveKnowledgeAggregator
                    from brave_search_aggregator.utils.config import Config

                    # Get API key from environment or wrapper config
                    # The wrapper.brave_search uses a different client class that stores API key in config.api_key
                    api_key = os.getenv("BRAVE_API_KEY", "")
                    if not api_key and hasattr(self.wrapper.brave_search, 'config'):
                        api_key = self.wrapper.brave_search.config.api_key
                    
                    if not api_key:
                        yield f"data: {json.dumps({'type': 'error', 'message': 'Brave Search API key not found in environment or configuration'})}\n\n"
                        return

                    # Create configuration
                    config = Config(
                        brave_api_key=api_key,
                        max_results_per_query=20,
                        timeout_seconds=30,
                        rate_limit=20,
                        enable_streaming=True
                    )

                    # Create aggregator with client and config
                    aggregator = BraveKnowledgeAggregator(
                        brave_client=self.wrapper.brave_search,
                        config=config
                    )
                    
                    try:
                        # Process query with proper async iteration
                        async for result in aggregator.process_query(query):
                            # Process the result
                            if result['type'] == 'content':
                                # Transform rich format to standard model format while preserving metadata
                                transformed_content = {
                                    'type': 'content',
                                    'status': 'success',
                                    'content': result.get('content', ''),
                                    'model_metadata': {
                                        'model': 'brave_search',
                                        'source': result.get('source', 'brave_search'),
                                        'confidence': result.get('confidence', 1.0),
                                        'title': result.get('title'),
                                        'query_analysis': result.get('query_analysis'),
                                        'knowledge_synthesis': result.get('knowledge_synthesis')
                                    }
                                }
                                # Accumulate complete response while preserving structure
                                if result.get('content'):
                                    complete_response.append(result['content'])
                                yield f"data: {json.dumps(transformed_content)}\n\n"
                            elif result['type'] == 'error':
                                # Enhanced error format standardization
                                error_content = {
                                    'type': 'error',
                                    'status': 'error',
                                    'message': result.get('error') or result.get('message', 'Unknown error'),
                                    'code': result.get('code', 'BRAVE_SEARCH_ERROR'),
                                    'model_metadata': {
                                        'model': 'brave_search',
                                        'phase': result.get('phase', 'unknown'),
                                        'recoverable': result.get('recoverable', False)
                                    }
                                }
                                yield f"data: {json.dumps(error_content)}\n\n"
                    except Exception as iteration_error:
                        # Handle any unexpected errors during iteration
                        error_content = {
                            'type': 'error',
                            'status': 'error',
                            'message': f"Error during result iteration: {str(iteration_error)}",
                            'code': 'BRAVE_SEARCH_ITERATION_ERROR',
                            'model_metadata': {
                                'model': 'brave_search',
                                'phase': 'iteration',
                                'recoverable': False,
                                'error_type': iteration_error.__class__.__name__
                            }
                        }
                        yield f"data: {json.dumps(error_content)}\n\n"
                except Exception as e:
                    # Enhanced error handling with standardized format and metadata
                    error_content = {
                        'type': 'error',
                        'status': 'error',
                        'message': str(e),
                        'code': 'BRAVE_SEARCH_INTERNAL_ERROR',
                        'model_metadata': {
                            'model': 'brave_search',
                            'phase': 'aggregation',
                            'recoverable': False,
                            'error_type': e.__class__.__name__
                        }
                    }
                    yield f"data: {json.dumps(error_content)}\n\n"
                finally:
                    # Ensure resources are properly cleaned up
                    if hasattr(aggregator, 'close'):
                        await aggregator.close()
            else:
                # Handle regular models with standard approach
                # Get the stream generator for LLM responses
                stream = await self.wrapper.query(query, model=model, stream=True)
            
                # Stream responses
                async for chunk in stream:
                    if isinstance(chunk, dict):
                        if chunk['status'] == 'error':
                            yield f"data: {json.dumps({'type': 'error', 'message': chunk['error']})}\n\n"
                            break
                        elif chunk['status'] == 'success' and chunk.get('content'):
                            content = chunk['content']
                            complete_response.append(content)
                            yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
            
            # Store complete response and send completion messages
            if complete_response:
                self.add_response(session_id, llm_index, ''.join(complete_response), query)
                yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            
    async def stream_synthesis(self, session_id: str) -> AsyncGenerator[str, None]:
        """Stream the synthesis of all LLM responses using Groq LLaMA 3."""
        try:
            stored_responses = self.get_responses(session_id)
            if not stored_responses:
                raise ValueError("No responses found for synthesis")

            original_query = stored_responses.get('query', 'No query available')

            # Build up the synthesis prompt by merging your analysis methodology & formatting rules
            # synthesis_prompt = f"""Original User Query:
            # {original_query}
            
            synthesis_prompt = f"""Please analyze & compare the data from the following knowledge sources::
                        
            """

            # Add all collected model responses, labeled by index/model name
            model_names = [            "SOURCE 1",
                "SOURCE 2",
                "SOURCE 3",
                "SOURCE 4",
                "SOURCE 5",
                "SOURCE 6",
                "SOURCE 7",
                "SOURCE 8",
                "SOURCE 9",
                "SOURCE 10"
            ]
            for idx, response in sorted(stored_responses['responses'].items()): # Removed the key lambda
                try:
                    model_index = int(idx)  # Try converting to int; handle exceptions if it fails
                    model_name = model_names[model_index] if model_index < len(model_names) else f"Model {idx}"
                except ValueError:
                    model_name = f"Knowledge Source: {idx}" # Handle non-integer keys
                synthesis_prompt += f"=== {model_name} Response ===\n{response}\n\n"

            # Now include the specific formatting and content instructions
            synthesis_prompt += """
            ## For your analysis, ensure that your response:
            1. **Merges all unanimous responses** into a single answer (and clearly state this was unanimous).
            2. Is written as if from a single **subject matter expert** with broader knowledge than any single LLM.
            3. **Preserves all unique and nuanced details, and displays them as such** (as possibly unique or conflicting information).
            4. If there are conflicts, **present them clearly** as such, rather than omitting them.
            5. Be as **concise as possible, while fully complying** with all requirements above.
            6. Use/retain **markdown** as appropriate.
            7. Retain **links/references to sources**, especially URLs from search results, so the user can verify.
            8. Be as concise as possible, while still providing a clearly human-readable response. Full sentences are not required.
            9. Do not provide verbose output to the user such as "now I will", or "based on all the knowledge sources", or "here is the prompt you can paste", etc.
            10. ABSOLUTELY ALWAYS APPEND at the end of the response, a `Request for clarification` section that adheres to the `truth-serum-iterative-clarification-process`. NO MATTER WHAT, YOU MUST ALWAYS INCLUDE THIS SECTION, even if you think the information is clear. This is critical for the iterative clarification process.
            
            # truth-serum-iterative-clarification-process

                1. Analyze each of the data/knowledge reports/findings/details provided from each knowledge source.

                2. Identify each distinct set of data/knowledge reports/findings/details by cryptic but consistent names or designations (call these "knowledge sources," assign a usable but not human-meaningful label).

                3. Compare information across the knowledge sources and classify items into:
                - a) Clearly overt unanimous agreements.
                - b) Possibly unanimous information (potentially ambiguous due to lack of explicitness).
                - c) Clearly ambiguous, vague, or non-specific information.
                - d) Clearly overt disagreements/discrepancies with explicit conflicts.
                - e) Potentially unique information found in only 1-2 sources (may be either a valuable insight or an anomaly).

                4. **Provide a concise, detailed bullet-point list** for each of these classifications.

                5. **Draft a user prompt/request** (for clarification) that could be pasted into each knowledge source, requesting them to:
                - Clarify all areas not classified as clear, overt, unanimous agreements.
                - List for each unclear/conflicting/ambiguous item: what was unclear/conflicting, and include supporting URLs/references cited by each source.
                - Request sources to double-check their previous answers and manually check each cited URL/source (and use web search for any URLs they cannot fetch, recursively, to reconstruct as much information as possible from search snippets).
                - Instruct sources to consider the recency and reputation of URLs/sources; prioritize current, reputable information.
                - If unable to fetch a page, recommend using web search scoped to that URL to gather snippets recursively and reconstruct content.
                - Require a full bibliography at the end of their response: full URLs, brief titles, and relevance/explanation for each source.
                (create only 1 clarification request prompt to be used by all knowledge sources)

                6. When new clarifications are received, repeat steps 3-5 recursively until all discrepancies are resolved.
            
            end-of-truth-serum-iterative-clarification-process
            """

            # Execute the query to the Groq LLaMA 3 model as a stream
            stream = await self.wrapper.query(
                synthesis_prompt,
                model="groq/llama3-8b-8192",
                stream=True
            )

            async for chunk in stream:
                if isinstance(chunk, dict):
                    if chunk.get('status') == 'error':
                        yield f"data: {json.dumps({'type': 'error', 'message': chunk.get('error')})}\n\n"
                        break
                    elif chunk.get('status') == 'success' and chunk.get('content'):
                        yield f"data: {json.dumps({'type': 'content', 'content': chunk['content']})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
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
                "groq/mixtral-8x7b-32768",       # 4: Groq Mixtral
                "groq/llama3-8b-8192",           # 5: Groq LLaMA 3
                "sonar-small",              # 6: Perplexity Sonar Small
                "sonar-large",              # 7: Perplexity Sonar Large
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
            # Get stored responses for the session
            stored_responses = self.get_responses(session_id)
            if not stored_responses:
                raise ValueError("No responses found for synthesis")
                
            # Create synthesis prompt with original query
            original_query = stored_responses.get('query', 'No query available')
            synthesis_prompt = f"Original User Query:\n{original_query}\n\nAnalyze and synthesize the following AI responses to this query:\n\n"
            
            model_names = [
                "Claude 3 Opus",
                "Claude 3 Sonnet",
                "GPT-4",
                "GPT-3.5 Turbo",
                "Groq Mixtral",
                "Groq LLaMA 3",
                "Perplexity Sonar Small",
                "Perplexity Sonar Large",
                "Google Gemini Pro",
                "Brave Search Results"
            ]
            
            for idx, response in sorted(stored_responses['responses'].items()):
                model_name = model_names[int(idx)] if int(idx) < len(model_names) else f"Model {idx}"
                synthesis_prompt += f"=== {model_name} Response ===\n{response}\n\n"
            
            synthesis_prompt += "\nProvide a comprehensive yet concise synthesis that:\n"
            synthesis_prompt += "1. Merges all responses into a single response that directly addresses the user's original query\n"
            synthesis_prompt += "2. Presents the response as though from a single SME (subject matter expert) with access to a broader and more nuanced knowledgebase than any 1 LLM would have\n"
            synthesis_prompt += "3. Treats Brave Search results as factual context to verify and enhance LLM responses\n"
            synthesis_prompt += "4. Uses search results to validate claims made by LLMs where possible\n"
            synthesis_prompt += "5. Preserves all unique (or possibly unique) details, including more nuanced details\n"
            synthesis_prompt += "6. For more-nuanced or minority details, presents them as such, in order to not give overconfidence in a detail that is seemingly less common, though potentially could still be highly-beneficial\n"
            synthesis_prompt += "7. If the request/prompt is for research, coding or development: Identifies key agreements and disagreements\n"
            synthesis_prompt += "8. If there are conflicting responses (discrepancies), rather than omitting these, present these details accordingly in a clear intuitive way\n"
            synthesis_prompt += "9. Is as concise as possible, while still being incredibly useful and high-value, and adhering to the above requirements\n"
            synthesis_prompt += "10. Uses/preserves markdown as/when appropriate\n"
            synthesis_prompt += "11. Preserves links and/or references to various sources, especially URLs from search results, so the user is able to go verify the answers themselves\n"
            synthesis_prompt += "12. Attempt to respond to the user in such a way that would be appropriate based on their request (while utilizing the additional information from the other LLMs and search results in an appropriate way)\n"
            synthesis_prompt += "13. Respect the user's requested answer format. If they say 'be brief' or 'be concise', give them a brief/concise response while still utilizing all the aggregated knowledge sources to the extent possible\n"
            synthesis_prompt += "14. If any LLMs diverge from the requested format, you are not obligated to represent them in their entirety. Although we want you to incorporate and consider the information they add, we don't want this to cause the user to no longer receive the type of response they are requesting (in terms of the format of the response)\n"
            
            # Get the stream generator
            stream = await self.wrapper.query(
                synthesis_prompt,
                model="groq/llama3-8b-8192",
                stream=True
            )
            
            # Stream synthesis
            async for chunk in stream:
                if isinstance(chunk, dict):
                    if chunk['status'] == 'error':
                        yield f"data: {json.dumps({'type': 'error', 'message': chunk['error']})}\n\n"
                        break
                    elif chunk['status'] == 'success' and chunk.get('content'):
                        yield f"data: {json.dumps({'type': 'content', 'content': chunk['content']})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
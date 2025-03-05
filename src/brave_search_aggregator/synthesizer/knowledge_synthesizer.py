"""
Knowledge synthesis and response generation using MoE-style routing and SLERP-based merging.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np
from enum import Enum

class SynthesisMode(Enum):
    """Supported synthesis modes."""
    RESEARCH = "research"
    CODING = "coding"
    ANALYSIS = "analysis"
    CREATIVE = "creative"

@dataclass
class SynthesisResult:
    """Result of knowledge synthesis."""
    content: str
    confidence_score: float
    sources: List[str]
    mode: SynthesisMode
    coherence_score: Optional[float] = None
    consistency_score: Optional[float] = None
    
    def get(self, key, default=None):
        """Make SynthesisResult act like a dictionary."""
        if key == 'type':
            return 'content'
        elif key == 'content':
            return self.content
        elif key == 'confidence':
            return self.confidence_score
        elif key == 'sources':
            return self.sources
        elif key == 'mode':
            return self.mode.value if self.mode else None
        elif key == 'coherence_score':
            return self.coherence_score
        elif key == 'consistency_score':
            return self.consistency_score
        return default
        
    def __getitem__(self, key):
        """Allow dictionary-style access."""
        result = self.get(key)
        if result is None:
            raise KeyError(f"Key '{key}' not found in SynthesisResult")
        return result

@dataclass
class ModelRoute:
    """Model routing decision."""
    selected_models: List[str]
    routing_confidence: float
    synthesis_mode: SynthesisMode

class KnowledgeSynthesizer:
    """
    Synthesizes search results into coherent responses using MoE routing,
    task vector operations, and SLERP-based merging.
    """
    
    def __init__(self):
        """Initialize the knowledge synthesizer."""
        self.mode_model_weights = {
            SynthesisMode.RESEARCH: {
                "perplexity": 0.8,
                "brave_search": 0.7,
                "gemini": 0.6
            },
            SynthesisMode.CODING: {
                "chatgpt": 0.8,
                "gemini": 0.7,
                "perplexity": 0.6
            },
            SynthesisMode.ANALYSIS: {
                "gemini": 0.8,
                "chatgpt": 0.7,
                "perplexity": 0.6
            },
            SynthesisMode.CREATIVE: {
                "chatgpt": 0.8,
                "gemini": 0.7,
                "poe": 0.6
            }
        }

    async def route_query(self, query: str, synthesis_mode: str) -> ModelRoute:
        """
        Route query to appropriate models using MoE-style routing.
        
        Args:
            query: The user's query
            synthesis_mode: Desired synthesis mode
            
        Returns:
            ModelRoute containing selected models and confidence
        """
        try:
            mode = SynthesisMode(synthesis_mode)
        except ValueError:
            mode = SynthesisMode.RESEARCH  # Default to research mode
            
        # Get model weights for the selected mode
        weights = self.mode_model_weights[mode]
        
        # Select models above confidence threshold (0.6)
        selected_models = [
            model for model, weight in weights.items()
            if weight >= 0.6
        ]
        
        # Calculate overall routing confidence
        routing_confidence = np.mean([
            weight for model, weight in weights.items()
            if model in selected_models
        ])
        
        return ModelRoute(
            selected_models=selected_models,
            routing_confidence=routing_confidence,
            synthesis_mode=mode
        )

    async def combine_knowledge(
        self,
        responses: List[Dict[str, str]],
        operation: str = "task_vector_merge"
    ) -> Dict[str, float]:
        """
        Combine knowledge using task vector operations.
        
        Args:
            responses: List of model responses
            operation: Type of vector operation to perform
            
        Returns:
            Combined knowledge with coherence score
        """
        # TODO: Implement actual vector operations
        # Safely extract content from responses that could be search results
        extracted_contents = []
        for resp in responses:
            if "content" in resp:
                extracted_contents.append(resp["content"])
            elif "description" in resp:
                # Handle search results (which have description but no content)
                extracted_contents.append(f"{resp.get('title', '')}: {resp.get('description', '')}")
            elif isinstance(resp, dict):
                # Try to extract something useful from the dict
                values = [str(v) for k, v in resp.items() if isinstance(v, (str, int, float))]
                if values:
                    extracted_contents.append(". ".join(values))
        
        # If no content could be extracted, use a placeholder
        if not extracted_contents:
            extracted_contents = ["No content available"]
            
        # Combine the extracted content
        combined_content = "\n\n".join(extracted_contents)
        
        return {
            "content": combined_content,
            "coherence_score": 0.7  # Placeholder
        }

    async def merge_responses(
        self,
        responses: List[Dict[str, str]],
        interpolation_factor: float = 0.5
    ) -> Dict[str, float]:
        """
        Merge responses using SLERP-based interpolation.
        
        Args:
            responses: List of responses to merge
            interpolation_factor: SLERP interpolation factor
            
        Returns:
            Merged response with consistency score
        """
        # TODO: Implement actual SLERP merging
        # Safely extract content from responses that could be search results
        extracted_contents = []
        for resp in responses:
            if "content" in resp:
                extracted_contents.append(resp["content"])
            elif "description" in resp:
                # Handle search results (which have description but no content)
                title = resp.get('title', 'No title')
                desc = resp.get('description', 'No description')
                url = resp.get('url', '')
                extracted_contents.append(f"**{title}**\n{desc}" + (f"\n[{url}]({url})" if url else ""))
            elif isinstance(resp, dict):
                # Try to extract something useful from the dict
                values = [str(v) for k, v in resp.items() if isinstance(v, (str, int, float))]
                if values:
                    extracted_contents.append(". ".join(values))
        
        # If no content could be extracted, use a placeholder
        if not extracted_contents:
            extracted_contents = ["No content available"]
            
        # Merge the extracted content
        merged_content = "\n\n".join(extracted_contents)
        
        return {
            "content": merged_content,
            "consistency_score": 0.8  # Placeholder
        }

    async def synthesize(
        self,
        query_or_responses,
        responses = None,
        synthesis_mode: str = "research"
    ) -> SynthesisResult:
        """
        Synthesize responses into coherent output.
        
        This method is overloaded to handle both:
        1. synthesize(query, responses, synthesis_mode)
        2. synthesize(responses) - where no query or mode is specified
        
        Args:
            query_or_responses: Either the original user query or a list of responses
            responses: List of model responses (or None if first arg is responses)
            synthesis_mode: Desired synthesis mode
            
        Returns:
            SynthesisResult containing combined knowledge
        """
        # Handle overloaded signatures
        if responses is None:
            # First argument is actually responses
            responses = query_or_responses
            query = "Unknown query"  # Default value when not provided
        else:
            # Normal case: query and responses provided
            query = query_or_responses
            
        # Continue with the regular synthesis
        # Route query to appropriate models
        route = await self.route_query(query, synthesis_mode)
        
        # Filter responses to only use selected models
        if route.selected_models:
            filtered_responses = [
                resp for resp in responses
                if resp.get("model") in route.selected_models
            ]
            if not filtered_responses:  # If no matches, use all responses
                filtered_responses = responses
        else:
            filtered_responses = responses
        
        # Combine knowledge using task vectors
        combined = await self.combine_knowledge(filtered_responses)
        
        # Merge responses using SLERP
        merged = await self.merge_responses(filtered_responses)
        
        # When response list is empty, create simple result
        if not filtered_responses:
            if isinstance(query, str) and len(query) > 0:
                content = f"No results found for: {query}"
            else:
                content = "No results available"
            return SynthesisResult(
                content=content,
                confidence_score=0.5,
                sources=[],
                mode=route.synthesis_mode,
                coherence_score=0.5,
                consistency_score=0.5
            )
            
        return SynthesisResult(
            content=merged["content"],
            confidence_score=route.routing_confidence,
            sources=[resp.get("model", "unknown") for resp in filtered_responses],
            mode=route.synthesis_mode,
            coherence_score=combined["coherence_score"],
            consistency_score=merged["consistency_score"]
        )
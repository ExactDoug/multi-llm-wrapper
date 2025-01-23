"""Tests for BraveKnowledgeAggregator model interface pattern."""
import pytest
import pytest_asyncio
import json
import asyncio
from src.multi_llm_wrapper.web.service import LLMService
from src.brave_search_aggregator.synthesizer.brave_knowledge_aggregator import BraveKnowledgeAggregator

pytestmark = pytest.mark.asyncio(scope="module")

@pytest_asyncio.fixture(scope="module")
async def service():
    """Create a shared LLMService instance for the test module."""
    async with LLMService() as service:
        yield service

@pytest.mark.asyncio
async def test_brave_search_format_transformation(service):
    """Test format transformation of BraveKnowledgeAggregator responses."""
    
    # Create a generator to simulate streaming responses
    async def mock_stream():
        responses = [
            {'type': 'content', 'content': 'Test content', 'source': 'test_source', 'confidence': 0.9},
            {'type': 'error', 'message': 'Test error', 'code': 'TEST_ERROR'}
        ]
        for response in responses:
            yield response

    # Test content transformation
    async for chunk in service.stream_llm_response(9, "test query", "test_session"):
        data = json.loads(chunk.replace('data: ', ''))
        
        if data['type'] == 'content':
            # Verify standard model format
            assert 'type' in data
            assert 'content' in data
            assert 'status' in data
            assert data['status'] == 'success'
            
            # Verify model metadata
            assert 'model_metadata' in data
            assert data['model_metadata']['model'] == 'brave_search'
            assert 'source' in data['model_metadata']
            assert 'confidence' in data['model_metadata']
        
        elif data['type'] == 'error':
            # Verify standardized error format
            assert 'status' in data
            assert data['status'] == 'error'
            assert 'message' in data
            assert 'code' in data

@pytest.mark.asyncio
async def test_synthesis_integration(service):
    """Test BraveKnowledgeAggregator integration with synthesis."""
    session_id = "test_synthesis_session"
    
    try:
        # First, get Brave Search response
        async for chunk in service.stream_llm_response(9, "quantum computing", session_id):
            data = json.loads(chunk.replace('data: ', ''))
            if data['type'] == 'done':
                break
        
        # Then test synthesis
        async for chunk in service.stream_synthesis(session_id):
            data = json.loads(chunk.replace('data: ', ''))
            
            if data['type'] == 'content':
                assert data.get('content')  # Verify synthesis produces content
            elif data['type'] == 'error':
                assert False, f"Synthesis error: {data['message']}"  # Fail if synthesis errors
            elif data['type'] == 'done':
                break
    except asyncio.CancelledError:
        # Handle task cancellation gracefully
        pass

@pytest.mark.asyncio
async def test_streaming_verification(service):
    """Test streaming behavior of transformed responses."""
    received_chunks = []
    
    try:
        async for chunk in service.stream_llm_response(9, "test streaming", "test_session"):
            data = json.loads(chunk.replace('data: ', ''))
            received_chunks.append(data)
            
            # Verify chunk format
            if data['type'] == 'content':
                assert data['status'] == 'success'
                assert 'content' in data
            elif data['type'] == 'error':
                assert data['status'] == 'error'
                assert 'message' in data
            elif data['type'] == 'done':
                break
        
        # Verify streaming sequence
        assert len(received_chunks) > 0
        assert received_chunks[-1]['type'] == 'done'
    except asyncio.CancelledError:
        # Handle task cancellation gracefully
        pass

@pytest.mark.asyncio
async def test_error_handling(service):
    """Test standardized error handling in model interface."""
    try:
        # Test with invalid query
        async for chunk in service.stream_llm_response(9, "", "test_session"):
            data = json.loads(chunk.replace('data: ', ''))
            if data['type'] == 'error':
                assert data['status'] == 'error'
                assert 'message' in data
                assert 'code' in data
                break
    except asyncio.CancelledError:
        # Handle task cancellation gracefully
        pass
import pytest
from unittest.mock import AsyncMock, MagicMock
from brave_search_aggregator.synthesizer.brave_knowledge_aggregator import BraveKnowledgeAggregator
from brave_search_aggregator.fetcher.brave_client import BraveSearchClient

@pytest.fixture
def mock_brave_client():
    client = AsyncMock(spec=BraveSearchClient)
    client.search.return_value = [
        {
            'title': 'Test Result 1',
            'url': 'https://example.com/1',
            'description': 'Description 1'
        },
        {
            'title': 'Test Result 2',
            'url': 'https://example.com/2',
            'description': 'Description 2'
        }
    ]
    return client

@pytest.fixture
def aggregator(mock_brave_client):
    return BraveKnowledgeAggregator(mock_brave_client)

@pytest.mark.asyncio
async def test_process_query_success(aggregator):
    """Test successful query processing with proper response format."""
    results = []
    async for result in aggregator.process_query("test query"):
        results.append(result)

    # Verify response structure
    assert len(results) >= 3  # Title, content, and done messages
    assert results[0]['type'] == 'title'
    assert results[0]['title'] == 'Brave Search'
    assert results[-1]['type'] == 'done'

    # Verify content format
    content_results = [r for r in results if r['type'] == 'content']
    assert len(content_results) > 0
    content = content_results[0]['content']
    assert '### Search Results' in content
    assert 'Test Result 1' in content
    assert 'Test Result 2' in content

@pytest.mark.asyncio
async def test_process_query_with_error(aggregator, mock_brave_client):
    """Test error handling in query processing."""
    mock_brave_client.search.side_effect = Exception("API Error")
    
    results = []
    async for result in aggregator.process_query("test query"):
        results.append(result)

    assert len(results) == 1
    assert results[0]['type'] == 'error'
    assert 'API Error' in results[0]['message']

@pytest.mark.asyncio
async def test_query_analysis_integration(aggregator):
    """Test that query analysis insights are included in response."""
    results = []
    async for result in aggregator.process_query("complex technical query"):
        results.append(result)

    content_results = [r for r in results if r['type'] == 'content']
    assert len(content_results) > 0
    content = content_results[0]['content']
    assert '#### Query Analysis' in content

@pytest.mark.asyncio
async def test_knowledge_synthesis_integration(aggregator):
    """Test that knowledge synthesis is included when available."""
    results = []
    async for result in aggregator.process_query("synthesis test query"):
        results.append(result)

    content_results = [r for r in results if r['type'] == 'content']
    assert len(content_results) > 0
    content = content_results[0]['content']
    assert '### Knowledge Synthesis' in content

@pytest.mark.asyncio
async def test_streaming_response_format(aggregator):
    """Test that streaming response follows LLMService format."""
    results = []
    async for result in aggregator.process_query("test query"):
        results.append(result)

    # Verify all results follow expected format
    for result in results:
        assert 'type' in result
        assert result['type'] in ['title', 'content', 'error', 'done']
        if result['type'] == 'content':
            assert isinstance(result['content'], str)
        elif result['type'] == 'error':
            assert isinstance(result['message'], str)
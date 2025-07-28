# Graceful API Key Error Handling Implementation Plan

## Overview

This document outlines a minimal, elegant solution to handle missing API keys gracefully in the Multi-LLM Wrapper project. Currently, the application crashes completely when API keys are missing. This plan transforms that hard failure into graceful degradation with clear user feedback.

## Problem Statement

### Current Behavior
1. **Hard Crash**: Missing API keys cause the entire server to fail during startup
2. **Poor User Experience**: Users see "connection refused" with no indication of the problem
3. **No Partial Functionality**: Even if only one provider's API key is missing, nothing works
4. **Unclear Error Messages**: Python tracebacks in console provide no actionable guidance

### Root Cause
The `WrapperConfig` class in `config.py` validates API keys during initialization and raises a `ValueError` if the default provider's key is missing. This prevents the entire service from starting.

## Solution Philosophy

The Multi-LLM Wrapper should embody its own design principle: work with whatever providers are available. This solution allows the service to start and function with available providers while clearly communicating which providers are unavailable and why.

## Implementation Plan

### Phase 1: Service-Level Error Handling

**File**: `src/multi_llm_wrapper/web/app.py`

**Changes**:
1. Wrap `LLMService` initialization in try/except
2. Store initialization error for status reporting
3. Allow server to start even if LLM service fails

```python
# Line ~31, replace:
llm_service = LLMService()

# With:
llm_service = None
startup_error = None

try:
    llm_service = LLMService()
except ValueError as e:
    startup_error = str(e)
    logger.warning(f"LLM Service initialization failed: {startup_error}")
    # Server continues without LLM service
```

**Rationale**: This catches the error at the appropriate architectural level - the web service layer, not the core configuration layer. The server can still serve the UI and report status.

### Phase 2: Status Reporting API

**File**: `src/multi_llm_wrapper/web/app.py`

**Addition**: New endpoint after existing endpoints (~line 50)

```python
@app.get("/api/status")
async def get_status():
    """Report service availability status"""
    return {
        "llm_service_available": llm_service is not None,
        "error": startup_error,
        "message": "LLM service not configured. Please set API keys in .env file." if startup_error else "Ready"
    }
```

**Rationale**: Provides a clean API for the frontend to check service status without attempting LLM operations.

### Phase 3: Web UI Status Integration

**File**: `src/multi_llm_wrapper/static/index.html`

**Addition 1**: Status check on page load (in existing script section)

```javascript
// Add after DOMContentLoaded event listener setup
async function checkServiceStatus() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();
        
        if (!status.llm_service_available) {
            showConfigWarning(status.message);
        }
    } catch (error) {
        console.error('Failed to check service status:', error);
    }
}

function showConfigWarning(message) {
    // Create warning element if it doesn't exist
    let warning = document.getElementById('config-warning');
    if (!warning) {
        warning = document.createElement('div');
        warning.id = 'config-warning';
        warning.className = 'config-warning';
        warning.innerHTML = `
            <span class="warning-icon">⚠️</span>
            <span class="warning-text">${message}</span>
            <button class="warning-close" onclick="this.parentElement.style.display='none'">×</button>
        `;
        document.body.insertBefore(warning, document.body.firstChild);
    }
}

// Call on page load
checkServiceStatus();
```

**Addition 2**: CSS for warning banner (in existing style section)

```css
.config-warning {
    background-color: #fff3cd;
    border: 1px solid #ffeaa7;
    color: #856404;
    padding: 12px 20px;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 14px;
}

.warning-icon {
    font-size: 18px;
}

.warning-close {
    margin-left: auto;
    background: none;
    border: none;
    font-size: 20px;
    cursor: pointer;
    color: #856404;
    padding: 0 5px;
}

.warning-close:hover {
    color: #533f03;
}
```

**Rationale**: Non-intrusive banner that informs without blocking functionality. Dismissible to not annoy users who understand the issue.

### Phase 4: Streaming Endpoint Protection

**File**: `src/multi_llm_wrapper/web/app.py`

**Modification**: Update streaming endpoints to check service availability

```python
@app.get("/stream/{llm_index}")
async def stream_endpoint(
    llm_index: int,
    query: str,
    session_id: str = Query(None)
):
    """Endpoint for streaming LLM responses."""
    # Add service availability check
    if not llm_service:
        return StreamingResponse(
            error_generator(
                f"LLM service is not available. {startup_error or 'Please configure API keys in .env file.'}"
            ),
            media_type="text/event-stream"
        )
    
    # Generate session ID if not provided
    if not session_id:
        session_id = str(uuid4())
    
    return StreamingResponse(
        llm_service.stream_llm_response(llm_index, query, session_id),
        media_type="text/event-stream"
    )

# Add helper function for error streaming
async def error_generator(message: str):
    """Generate error message in streaming format"""
    yield f"data: {json.dumps({'type': 'error', 'message': message, 'code': 'SERVICE_UNAVAILABLE'})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"
```

**Modification**: Apply same pattern to synthesis endpoint

```python
@app.get("/synthesize/{session_id}")
async def synthesize_endpoint(session_id: str):
    """Endpoint for synthesizing responses."""
    if not llm_service:
        return StreamingResponse(
            error_generator("LLM service is not available. Please configure API keys."),
            media_type="text/event-stream"
        )
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")
        
    return StreamingResponse(
        llm_service.stream_synthesis(session_id),
        media_type="text/event-stream"
    )
```

**Rationale**: Provides graceful errors through the existing streaming interface instead of crashes or 500 errors.

## User Experience Flow

### Before Implementation
1. User starts services via desktop script
2. Server crashes with Python traceback
3. Browser shows "This site can't be reached"
4. User must check console logs to understand issue

### After Implementation
1. User starts services via desktop script
2. Server starts successfully (warning logged to console)
3. Web UI loads normally with yellow warning banner
4. Banner explains: "⚠️ LLM service not configured. Please set API keys in .env file."
5. If user tries to query LLMs, they get clear error message
6. Once .env is configured, user can restart and everything works

## Benefits

1. **No Breaking Changes**: All existing functionality preserved
2. **Progressive Enhancement**: Service degrades gracefully
3. **Clear Communication**: Users understand exactly what's wrong
4. **Minimal Code Changes**: ~50 lines across 2 files
5. **Better Developer Experience**: Can explore UI without API keys

## Configuration Guide for Users

After implementing this plan, users will see clear guidance to:

1. Copy `.env.example` to `.env`
2. Add their API keys:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   OPENAI_API_KEY=sk-...
   GROQ_API_KEY=gsk_...
   ```
3. Restart the services

## Testing Plan

1. **Missing API Keys**: Verify server starts and shows warning
2. **With API Keys**: Verify normal operation
3. **Partial Keys**: Test with some providers configured
4. **Error Messages**: Verify clear, actionable error text
5. **UI Behavior**: Test warning banner display/dismiss

## Future Enhancements

This minimal plan solves the immediate problem. Possible future enhancements:
- Per-provider status indicators in UI
- Dynamic provider enable/disable
- API key configuration UI (security considerations)
- Automatic .env file creation from template

## Implementation Priority

This should be implemented as soon as possible because:
1. It's a critical usability issue for new users
2. The changes are minimal and low-risk
3. It improves the development experience
4. It aligns with the project's philosophy of flexibility

---

*Document created: December 26, 2024*  
*Author: Multi-LLM Wrapper Development Team*

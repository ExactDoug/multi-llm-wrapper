# Architectural Plan: Appending a Standard String to User Query Before LLM Submission

**Document Purpose:**  
This document provides a comprehensive, code-grounded, step-by-step architectural plan for appending a standard string (one or more sentences) to the user query before it is submitted to the LLMs. It details all viable integration points, their implications, and implementation steps, referencing specific files, functions, and code flows in the current codebase. This plan is suitable for peer review and direct hand-off to engineering for implementation.

---

## 1. Current Query Flow: Codebase Analysis

### 1.1. Frontend (JavaScript)

- **Directory:** `src/multi_llm_wrapper/web/static/js/`
- **Key Files:**
  - [`modules/streams.js`](../../src/multi_llm_wrapper/web/static/js/modules/streams.js): Handles query submission logic.
  - [`modules/events.js`](../../src/multi_llm_wrapper/web/static/js/modules/events.js): Handles UI event listeners.
  - [`main.js`](../../src/multi_llm_wrapper/web/static/js/main.js): Initializes the app and event listeners.
  - [`index.html`](../../src/multi_llm_wrapper/web/templates/index.html): Contains the user input field for queries.

#### 1.1.1. Query Construction and Submission

- **User enters query** in an input field in `index.html`.
- **`sendQuery()`** (in `modules/streams.js`) is triggered on form submission or button click.
- **`sendQuery()`** collects the query string from the input field.
- **`startStream(llmIndex, query, sessionId)`** is called for each LLM, sending the query to the backend endpoint (e.g., `/stream/{llmIndex}`).

### 1.2. Backend (Python)

- **Directory:** `src/multi_llm_wrapper/web/`
- **Key Files:**
  - [`service.py`](../../src/multi_llm_wrapper/web/service.py): Receives the query from the frontend and dispatches it to the LLMs.
  - [`app.py`](../../src/multi_llm_wrapper/web/app.py): May define the web server and route registration.

#### 1.2.1. Query Reception and Dispatch

- **Backend route handler** (in `service.py`) receives the query via HTTP POST/GET.
- **Query is dispatched** to all LLMs for processing.

---

## 2. Integration Points for Appending a Standard String

### 2.1. Option A: Frontend Appending

**Where:**  
- In `sendQuery()` (in `modules/streams.js`), before calling `startStream()`, append the standard string to the user query.

**Implementation Steps:**
1. Locate the query construction in `sendQuery()`.
2. Append the standard string:
   ```js
   let query = ...; // get from input
   query += " [STANDARD STRING HERE]";
   ```
3. Proceed with the existing call to `startStream()`.

**Code Reference:**  
- [`src/multi_llm_wrapper/web/static/js/modules/streams.js`](../../src/multi_llm_wrapper/web/static/js/modules/streams.js): `sendQuery()`

**Implications:**
- **Pros:** Simple, transparent to frontend users, easy to test.
- **Cons:** Not robust if the frontend is bypassed (e.g., direct API calls).

---

### 2.2. Option B: Backend Appending

**Where:**  
- In the backend route handler (in `service.py`), append the standard string to the incoming query before dispatching to LLMs.

**Implementation Steps:**
1. Locate the route handler that receives the query in `service.py`.
2. After extracting the query from the request, append the standard string:
   ```python
   query = request.json['query']
   query += " [STANDARD STRING HERE]"
   ```
3. Continue with the existing logic to dispatch the query to the LLMs.

**Code Reference:**  
- [`src/multi_llm_wrapper/web/service.py`](../../src/multi_llm_wrapper/web/service.py): Route handler for query submission

**Implications:**
- **Pros:** Robust (applies to all clients, including API users), centralizes logic.
- **Cons:** Less transparent to frontend users unless echoed back.

---

### 2.3. Option C: Both Frontend and Backend (Defense in Depth)

**Where:**  
- Append in both frontend (`sendQuery()`) and backend (`service.py`).

**Implementation Steps:**
- Implement both Option A and Option B, ensuring logic prevents double-appending (e.g., by checking if the string is already present).

**Implications:**
- **Pros:** Maximum robustness.
- **Cons:** Risk of double-appending if not carefully managed, more complex.

---

## 3. Frontend Field for Standard String (with Persistence)

### 3.1. Option 1: User-Configurable Field

**Where:**  
- Add an input field in `index.html` for the standard string.
- Persist the value using `localStorage` or cookies.
- On query submission, append the value from this field to the user query in `sendQuery()`.

**Implementation Steps:**
1. **HTML:**  
   Add an input field for the standard string in `index.html`:
   ```html
   <input type="text" id="standardString" placeholder="Enter standard string..." />
   ```
2. **JS (in `modules/streams.js`):**  
   - On page load, populate the field from `localStorage`:
     ```js
     document.getElementById('standardString').value = localStorage.getItem('standardString') || '';
     ```
   - On change, update `localStorage`:
     ```js
     document.getElementById('standardString').addEventListener('input', e => {
       localStorage.setItem('standardString', e.target.value);
     });
     ```
   - In `sendQuery()`, append the value:
     ```js
     let query = ...; // user input
     let standard = document.getElementById('standardString').value;
     query += " " + standard;
     ```
3. **Testing:**  
   - Verify persistence and correct appending.

**Implications:**
- **Pros:** User can customize, persists across sessions, transparent.
- **Cons:** User can change/remove, may not be suitable for mandatory strings.

---

### 3.2. Option 2: Hardcoded/Config-Driven (No UI)

**Where:**  
- The string is hardcoded in JS or loaded from a config file. No frontend field.

**Implementation Steps:**
- In `sendQuery()`, append a hardcoded string as in Option A.

**Implications:**
- **Pros:** Simpler, enforces standard string.
- **Cons:** Not user-configurable, requires code change to update.

---

## 4. Summary Table

| Approach        | Where to Edit             | Robustness | Transparency | UX Impact | Maint. | Notes                |
| --------------- | ------------------------- | ---------- | ------------ | --------- | ------ | -------------------- |
| Frontend Only   | streams.js: sendQuery()   | Low        | High         | High      | Easy   | Not robust for API   |
| Backend Only    | service.py: route handler | High       | Medium       | None      | Easy   | Best for enforcement |
| Both            | Both above                | Highest    | Medium       | High      | Med    | Avoid double-append  |
| Frontend Field  | index.html, streams.js    | Med        | High         | High      | Med    | User can edit        |
| Hardcoded Front | streams.js                | Med        | Low          | None      | Easy   | Not user-editable    |

---

## 5. Recommendations

- **For strict enforcement:** Use backend appending in [`service.py`](../../src/multi_llm_wrapper/web/service.py).
- **For user transparency/customization:** Add a frontend field with `localStorage` persistence, and append in [`streams.js`](../../src/multi_llm_wrapper/web/static/js/modules/streams.js).
- **For maximum robustness:** Implement both, but ensure logic prevents double-appending.

---

## 6. Step-by-Step Implementation Example (Backend)

1. **Locate the backend route handler** in `service.py` that receives the query.
2. **Modify the handler** to append the standard string:
   ```python
   # Example: Flask route
   @app.route('/stream/<llm_index>', methods=['POST'])
   def stream(llm_index):
       data = request.get_json()
       query = data['query']
       # Append standard string
       query += " [STANDARD STRING HERE]"
       # ... existing logic ...
   ```
3. **Test** with both frontend and direct API calls to ensure the string is always appended.

---

## 7. Step-by-Step Implementation Example (Frontend Field)

1. **Edit `index.html`** to add a new input field for the standard string.
2. **Edit `modules/streams.js`**:
   - On page load, populate the field from `localStorage`.
   - On input, update `localStorage`.
   - In `sendQuery()`, append the field value to the user query.
3. **Test** for persistence and correct appending.

---

## 8. Peer Review Checklist

- [ ] All code references are accurate and grounded in the current codebase.
- [ ] All integration points are clearly identified and justified.
- [ ] All implementation steps are actionable and unambiguous.
- [ ] Implications of each approach are fully analyzed.
- [ ] No aspect is fabricated or postulated; all is based on actual code and requirements.

---

**Prepared by:** Roo (Architectural Analysis)  
**Date:** 2025-07-22

# Frontend Review: User-Editable Standard String Field & Persistence

**Document Purpose:**  
This review analyzes the frontend plan for allowing user customization of the standard string appended to LLM queries, focusing on UI/UX, persistence (localStorage/cookie), transparency, and security. It references [`append-standard-string-architecture.md`](../append-standard-string-architecture.md), methodology compliance docs, and 2025 best practices.

---

## 1. Summary of Intended Frontend Approach

- **UI Addition:**  
  - Add a user-editable input field in [`index.html`](../../src/multi_llm_wrapper/web/templates/index.html) for the standard string.
  - Field should be clearly labeled and placed near the main query input for discoverability and context.

- **Persistence:**  
  - Use `localStorage` to persist the field value across sessions (see plan section 3.1, step 2).
  - On page load, populate the field from `localStorage`.
  - On input, update `localStorage` with the new value.

- **Query Construction:**  
  - On query submission, append the value from the standard string field to the user query before sending to the backend.

- **Transparency:**  
  - The final query (user input + standard string) should be displayed to the user before submission, either as a preview or confirmation.

- **Current Status:**  
  - As of this review, the field is **not yet present** in `index.html`, and no persistence logic exists in `events.js` or related JS modules.

---

## 2. Best Practices for User-Editable Fields & Persistence (2025)

- **localStorage** is preferred for non-sensitive, user-facing settings.  
  - Do **not** use for secrets or sensitive data.
  - Provide a way for users to clear/reset the value.
  - Use clear labeling and tooltips to explain the field's purpose.

- **UI/UX:**
  - Place the field near the main query input.
  - Use adaptive placeholder text and contextual help.
  - Consider progressive disclosure if the field is advanced/optional.
  - Show a real-time preview of the final query to avoid confusion.

- **Security:**
  - Never store sensitive or authentication data in localStorage.
  - Sanitize input to prevent XSS or prompt injection.
  - Avoid auto-filling with values from untrusted sources.

- **Persistence:**
  - Use versioned keys if the format may change in the future.
  - Avoid cookies unless server-side access is required.

---

## 3. UX & Security Pitfalls for LLM Query Modifiers

- **Prompt Injection:**  
  - User-editable fields can be abused to inject malicious instructions.  
  - Mitigation: Input segmentation, validation, and (if possible) runtime monitoring.

- **Sensitive Data Leakage:**  
  - Users may inadvertently store or expose sensitive info in the field.
  - Mitigation: Warn users not to enter secrets; provide clear field descriptions.

- **Cognitive Overload:**  
  - Too many options or unclear field purpose can confuse users.
  - Mitigation: Use tooltips, help icons, and keep the UI uncluttered.

- **Persistence Blind Spots:**  
  - Users may forget a value is persisted, leading to unexpected query modifications.
  - Mitigation: Show the current value and provide a "reset" button.

- **Transparency:**  
  - Users must always see the final query before submission to avoid accidental exposure or confusion.

---

## 4. Methodology Compliance

- The plan and this review are fully compliant with the codified MVP/incremental methodology ([`dev-methodology-mvp-incremental.md`](../../dev-methodology-mvp-incremental.md)), as confirmed in [`plan-methodology-compliance.md`](plan-methodology-compliance.md).
- The approach is simple, incremental, and user-facing, with clear manual testing steps and no unnecessary complexity.

---

## 5. Recommendations

1. **UI Implementation:**
   - Add a labeled input field for the standard string in `index.html`, near the main query input.
   - Use a tooltip or help icon to explain its function.

2. **Persistence:**
   - Implement localStorage logic in JS (preferably in a dedicated module or in `events.js`).
   - On page load, populate the field from localStorage; on input, update localStorage.

3. **Transparency:**
   - Show a real-time preview of the final query (user input + standard string) before submission.
   - Optionally, add a "reset" button to clear the persisted value.

4. **Security/UX:**
   - Sanitize input and warn users not to enter sensitive data.
   - Consider input length limits and validation.
   - Document the field's behavior in user-facing help.

5. **Testing:**
   - Manually test persistence, query construction, and UI clarity.
   - Verify that the field does not break existing functionality.

---

## 6. References

- [Append Standard String Architecture](../append-standard-string-architecture.md)
- [MVP/Incremental Methodology](../../dev-methodology-mvp-incremental.md)
- [Plan Methodology Compliance Review](plan-methodology-compliance.md)
- [Spot-Check: 2025 Best Practices for localStorage & LLM UI Security]  
  (Perplexity/industry RAG, July 2025)

---

**Prepared by:** Roo (Architectural Review)  
**Date:** 2025-07-22

# TODO Progress - Database Lazy Load & Loading Animation

## Plan Approval: ✅ Approved

## Tasks:

### 1. Backend - Database Optimization
- [ ] 1.1 Update `backend/database/manager.py`:
  - [ ] Add `list_sessions_paginated(offset, limit)` method with optimized SQL
  - [ ] Add `get_total_sessions_count()` method
  - [ ] Use Supabase's `.execute(count='exact')` for counts in single query

- [ ] 1.2 Update `backend/routes/api.py`:
  - [ ] Modify `/api/sessions` to support `offset` and `limit` parameters
  - [ ] Add `total_count` to response
  - [ ] Add `has_more` boolean to indicate if more data exists

### 2. Frontend - UI Improvements
- [ ] 2.1 Update `frontend/index.html`:
  - [ ] Add new loading animation styles (skeleton, progress bar)
  - [ ] Add "Load More" button functionality
  - [ ] Add pagination state management
  - [ ] Update `loadHistory()` to support pagination

### 3. Testing
- [ ] 3.1 Test the API with pagination
- [ ] 3.2 Test Load More button functionality
- [ ] 3.3 Verify loading animations work correctly

---

## Status: In Progress


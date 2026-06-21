# Frontend Development TODO

## Gaps Identified in `/src` Review

### Critical Missing Components

#### 1. API Layer (`api/` - 6 files) ✅ COMPLETED
**Status: COMPLETE - 100%**

- ✅ Create API client with fetch
  - ✅ Base API configuration with interceptors
  - ✅ Error handling middleware (ApiException)
  - ✅ Authentication token management
- ✅ Institution API endpoints (`institutions.ts`)
  - ✅ `GET /institutions` - List with filters
  - ✅ `GET /institutions/:slug` - Get by slug
  - ✅ `POST /institutions` - Create (admin)
  - ✅ `PUT /institutions/:id` - Update (admin)
  - ✅ `DELETE /institutions/:id` - Delete (admin)
  - ✅ Contacts & Requirements endpoints
  - ✅ Featured & Popular endpoints
- ✅ Search API endpoints (`search.ts`)
  - ✅ `GET /search?q=` - Basic search
  - ✅ `GET /search/fuzzy?q=` - Fuzzy search
  - ✅ `GET /search/autocomplete?q=` - Autocomplete
  - ✅ `GET /search/personalized` - Personalized search
  - ✅ `GET /search/did-you-mean?q=` - Spell suggestions
  - ✅ Popular searches endpoint
  - ✅ Suggestions for you endpoint
- ✅ Analytics tracking endpoints
  - ✅ `POST /analytics/track/search` - Track search
  - ✅ `POST /analytics/track/search-click` - Track clicks
- ✅ Auth API endpoints (`auth.ts`)
  - ✅ `POST /auth/login` - Login
  - ✅ `POST /auth/register` - Register
  - ✅ `POST /auth/refresh` - Refresh token
  - ✅ `GET /auth/me` - Get current user
  - ✅ Password reset & change
  - ✅ Profile update & avatar upload
- ✅ Locations API (`locations.ts`)
  - ✅ Divisions, Districts, Upazilas endpoints

#### 2. Custom Hooks (`hooks/` - 7 files) ✅ COMPLETED
**Status: COMPLETE - 100%**

- ✅ `useDebounce.ts` - Debounce hook for search input
- ✅ `useLocalStorage.ts` - localStorage with React state sync
- ✅ `useRecentlyViewed.ts` - Manage recently viewed institutions
- ✅ `useCompare.ts` - Manage comparison list (localStorage)
- ✅ `useSearch.ts` - Search with debounce, caching, analytics
- ✅ `useInstitution.ts` - Fetch single institution with tracking
- ✅ `useInstitutions.ts` - Fetch institutions list with filters

#### 3. State Management (`stores/` - 5 files) ✅ COMPLETED
**Status: COMPLETE - 100%**

Zustand with persist middleware for localStorage:

- ✅ `authStore.ts` - Authentication state
  - ✅ User data with persistence
  - ✅ Login/logout actions
  - ✅ Token management
- ✅ `searchStore.ts` - Search state
  - ✅ Current query, filters, results
  - ✅ Pagination state
  - ✅ Search history (20 items, persisted)
  - ✅ Loading/error states
- ✅ `compareStore.ts` - Comparison state
  - ✅ Selected institutions (max 3)
  - ✅ Add/remove/clear actions
  - ✅ Persistence to localStorage
- ✅ `uiStore.ts` - UI state
  - ✅ Sidebar open/closed
  - ✅ Modal states
  - ✅ Global loading state
  - ✅ Toast notifications
  - ✅ Keyboard shortcuts help

#### 4. TypeScript Types (`types/` - 0 items)
**Status: EMPTY - High Priority**

- [ ] `institution.ts` - Institution interfaces
  - [ ] Institution
  - [ ] InstitutionType
  - [ ] InstitutionContact
  - [ ] InstitutionRequirement
- [ ] `location.ts` - Location interfaces
  - [ ] Division
  - [ ] District
  - [ ] Upazila
- [ ] `search.ts` - Search types
  - [ ] SearchFilters
  - [ ] SearchResult
  - [ ] AutocompleteSuggestion
  - [ ] FuzzySearchResult
- [ ] `user.ts` - User types
  - [ ] User
  - [ ] UserRole
  - [ ] AuthResponse
- [ ] `api.ts` - API types
  - [ ] ApiResponse<T>
  - [ ] ApiError
  - [ ] PaginationParams
  - [ ] PaginatedResponse<T>
- [ ] `analytics.ts` - Analytics types
  - [ ] SearchEvent
  - [ ] PageViewEvent
  - [ ] ClickEvent

### Empty Component Subdirectories

#### 4. Common Components (`components/common/` - 4 files) ✅ COMPLETED
**Status: COMPLETE - Core Components Done**

- ✅ `Button.tsx` - Reusable button with variants (primary, secondary, outline, ghost, danger)
- ✅ `Input.tsx` - Form input with label, error states, icons
- ✅ `Card.tsx` - Card with Header, Title, Description, Content, Footer subcomponents
- ✅ `Modal.tsx` - Modal/dialog with backdrop, escape key handling

**Remaining (lower priority):**
- [ ] `Select.tsx` - Dropdown select component
- [ ] `Loading.tsx` - Loading spinner/skeleton
- [ ] `ErrorBoundary.tsx` - Error boundary for graceful failures
- [ ] `EmptyState.tsx` - Empty state illustration component
- [ ] `Badge.tsx` - Badge/pill component for tags
- [ ] `Avatar.tsx` - User avatar component

#### 5. Institution Components (`components/institutions/` - 2 files) ✅ COMPLETED
**Status: CORE COMPLETE - Additional features pending**

Core components done:
- ✅ `InstitutionCard.tsx` - Institution list card with CompareButton integration
- ✅ `InstitutionDetail.tsx` - Full institution detail view with contact info

Additional features (lower priority):
- [ ] `InstitutionMap.tsx` - Location map component
- [ ] `InstitutionContact.tsx` - Extended contact info display

#### 6. Search Components (`components/search/` - 2 files) ✅ CORE COMPLETE
**Status: CORE COMPLETE - Additional features pending**

Core components done:
- ✅ `SearchBar.tsx` - Main search with autocomplete, keyboard navigation
- ✅ `SearchFilters.tsx` - Filter panel with type/location filters

Additional features (lower priority):
- [ ] `SearchResultsList.tsx` - Results list/grid wrapper
- [ ] `DidYouMean.tsx` - Spell correction suggestions display
- [ ] `SearchPagination.tsx` - Pagination controls
- [ ] `SearchSorting.tsx` - Sort dropdown
- [ ] `NoResults.tsx` - No results state with suggestions

#### 7. UI Components (`components/ui/` - 0 items)
**Status: EMPTY - Consider using shadcn/ui**

Options:
1. Install shadcn/ui components:
   - [ ] Button
   - [ ] Input
   - [ ] Select
   - [ ] Dialog
   - [ ] Dropdown Menu
   - [ ] Tabs
   - [ ] Accordion
   - [ ] Tooltip
   - [ ] Toast
   - [ ] Skeleton

2. Or build custom UI kit in this folder

---

## Implementation Priority

### Phase 1: Foundation (Blocks everything else) ✅ COMPLETED
1. ✅ `types/` - Define all TypeScript interfaces
2. ✅ `api/` - Create API client and endpoint wrappers
3. ✅ `hooks/` - Core data fetching hooks

### Phase 2: Core Components ✅ COMPLETED
4. ✅ `components/common/` - Button, Input, Card, Modal components
5. 🚧 `components/search/` - Search-specific components (next phase)
6. ✅ `stores/` - Zustand stores (auth, search, compare, ui)

### Phase 3: Feature Components ✅ COMPLETED
7. ✅ `components/search/` - SearchBar (with autocomplete), SearchFilters
8. ✅ `components/institutions/` - InstitutionCard, InstitutionDetail
9. 🚧 Integration with existing components (can be done incrementally)

---

## Current Gaps Impact

### ✅ RESOLVED - Phase 1, 2 & 3 Complete
**What's NOW available:**
- ✅ Type safety across the frontend (`types/`)
- ✅ API communication layer (`api/` with interceptors)
- ✅ Custom hooks for common patterns (`hooks/`)
- ✅ State management (`stores/` - 4 Zustand stores with persist)
- ✅ Reusable UI component library (`components/common/` - Button, Input, Card, Modal)
- ✅ Search components (`components/search/` - SearchBar with autocomplete, SearchFilters)
- ✅ Institution components (`components/institutions/` - InstitutionCard, InstitutionDetail)
- ✅ Full TypeScript definitions for all entities

### 🚧 REMAINING - Phase 3 Extras (Lower Priority)
**Still needed:**
- Additional institution features (map, courses, reviews)
- Additional search features (DidYouMean, pagination, sorting)

**Files ready for refactoring with new types/hooks/stores/components:**
- `HeroSection.tsx` - Can now use `SearchBar` component, `useSearch` hook
- `SearchResults.tsx` - Can use `InstitutionCard` component
- `CompareButton.tsx` - Can use `useCompareStore` instead of localStorage directly
- `RecentlyViewed.tsx` - Can use `InstitutionCard` component
- `Dashboard.tsx` - Can use new API layer, types
- All admin components - Can use API types, stores

---

## Quick Wins

1. **Install shadcn/ui** - Gets UI components quickly
2. **Create types first** - Unblocks all other work
3. **Build API layer** - Centralizes all backend communication
4. **Extract hooks** - DRY up data fetching code

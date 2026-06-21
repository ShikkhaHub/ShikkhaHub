# Frontend Structure

## Directory Organization

```
src/
├── api/                    # API client and endpoints
│   └── client.ts
├── components/
│   ├── ui/                 # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   └── ...
│   ├── common/             # Shared components
│   │   ├── SEO.tsx
│   │   ├── Loading.tsx
│   │   ├── ErrorBoundary.tsx
│   │   └── Skeleton.tsx
│   ├── institutions/       # Institution-specific
│   │   ├── InstitutionCard.tsx
│   │   ├── InstitutionList.tsx
│   │   └── CompareWidget.tsx
│   ├── admin/              # Admin components
│   │   ├── StatsCard.tsx
│   │   ├── Chart.tsx
│   │   └── DataTable.tsx
│   └── search/             # Search components
│       ├── SearchBar.tsx
│       ├── FilterPanel.tsx
│       └── ResultsList.tsx
├── hooks/                  # Custom React hooks
│   ├── useAuth.ts
│   ├── useSearch.ts
│   └── useRecentlyViewed.ts
├── lib/                    # Utilities (existing)
│   ├── utils.ts
│   ├── api.ts
│   └── recentlyViewed.ts
├── pages/                  # Route pages (existing)
│   ├── Dashboard.tsx
│   ├── InstitutionDetail.tsx
│   └── admin/
│       └── AdminDashboard.tsx
├── stores/                 # State management
│   └── useAuthStore.ts
├── types/                  # TypeScript types
│   └── index.ts
└── App.tsx                 # Main app component
```

## Component Guidelines

### UI Components (`components/ui/`)
- Reusable, generic components
- From shadcn/ui or custom
- No business logic
- Props-driven

### Feature Components (`components/{institutions,admin,search}/`)
- Domain-specific components
- Can use hooks and stores
- Can call API functions

### Common Components (`components/common/`)
- Shared across features
- SEO, Loading, Error handling

## Import Conventions

```typescript
// UI components
import { Button, Card } from '@/components/ui';

// Feature components
import { InstitutionCard } from '@/components/institutions';
import { StatsCard } from '@/components/admin';

// Hooks
import { useAuth } from '@/hooks/useAuth';

// Utils
import { cn } from '@/lib/utils';
```

## Adding New Components

1. Choose appropriate folder based on purpose
2. Create component file with `.tsx` extension
3. Add TypeScript interfaces
4. Export from index file
5. Add to appropriate page

## Migration Notes

Components are gradually being moved to the new structure:
- Existing components in `src/components/` root will be migrated
- New components should follow the new structure
- Backward compatibility maintained during migration

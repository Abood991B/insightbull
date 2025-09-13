# Project Structure Documentation

## Overview
This is a React + TypeScript frontend application for stock market sentiment analysis and insights. The project is structured following a feature-based architecture for better scalability and maintainability.

## Directory Structure

```
FYP2 Dashboard/
├── src/                      # Source code
│   ├── features/            # Feature-based modules
│   │   ├── dashboard/       # Main dashboard feature
│   │   │   ├── components/  # Dashboard-specific components
│   │   │   ├── pages/       # Dashboard pages (Index, About, NotFound)
│   │   │   └── index.ts     # Feature exports
│   │   ├── analysis/        # Stock analysis features
│   │   │   ├── components/  # Analysis-specific components
│   │   │   ├── pages/       # Analysis pages (StockAnalysis, SentimentVsPrice, etc.)
│   │   │   └── index.ts     # Feature exports
│   │   ├── admin/           # Admin panel features
│   │   │   ├── components/  # Admin-specific components
│   │   │   ├── pages/       # Admin pages (Dashboard, ApiConfig, etc.)
│   │   │   └── index.ts     # Feature exports
│   │   └── auth/            # Authentication features (future)
│   │       ├── components/  # Auth-specific components
│   │       ├── pages/       # Auth pages
│   │       └── index.ts     # Feature exports
│   ├── shared/              # Shared resources across features
│   │   ├── components/      
│   │   │   ├── ui/         # Base UI components (shadcn/ui)
│   │   │   └── layouts/    # Layout components (AdminLayout, UserLayout)
│   │   ├── hooks/          # Custom React hooks
│   │   ├── utils/          # Utility functions
│   │   └── types/          # Shared TypeScript types
│   ├── api/                # API layer (ready for backend integration)
│   │   ├── services/       # API service classes
│   │   ├── hooks/          # React Query hooks for API calls
│   │   └── types/          # API-specific types
│   ├── config/             # Application configuration
│   │   └── constants.ts    # App constants and config
│   ├── styles/             # Global styles
│   │   ├── index.css       # Main styles
│   │   └── App.css         # App-specific styles
│   ├── App.tsx             # Main application component
│   ├── main.tsx            # Application entry point
│   └── vite-env.d.ts       # Vite type definitions
├── backend/                # Future backend code
├── shared/                 # Shared between frontend & backend
│   └── types/             # Shared type definitions
├── docs/                   # Documentation
├── public/                 # Static assets
└── [config files]          # Configuration files (vite, tsconfig, etc.)
```

## Architecture Principles

### 1. Feature-Based Organization
- Each major feature has its own directory under `src/features/`
- Features are self-contained with their own components, pages, and exports
- This makes the codebase more modular and easier to maintain

### 2. Shared Resources
- Common components, hooks, and utilities are in `src/shared/`
- UI components from shadcn/ui are centralized in `src/shared/components/ui/`
- Layout components are separated in `src/shared/components/layouts/`

### 3. API Layer
- Prepared for backend integration with `src/api/`
- Base service class for consistent API calls
- Type definitions for API responses
- Ready for React Query hooks

### 4. Configuration Management
- Centralized configuration in `src/config/`
- Environment variables support
- Feature flags for easy feature toggling

### 5. Type Safety
- Shared types in `src/shared/types/`
- API types in `src/api/types/`
- Future shared types between frontend and backend in root `shared/types/`

## Import Aliases
The project uses the `@/` alias for imports, which maps to the `src/` directory:
- `@/features/...` - Feature modules
- `@/shared/...` - Shared resources
- `@/api/...` - API layer
- `@/config/...` - Configuration

## Adding New Features

To add a new feature:
1. Create a new directory under `src/features/[feature-name]/`
2. Add subdirectories for `components/` and `pages/`
3. Create an `index.ts` file to export the feature's public API
4. Import and use in `App.tsx`

## Backend Integration

When ready to add the backend:
1. Implement backend code in the `backend/` directory
2. Share types between frontend and backend using `shared/types/`
3. Update API services in `src/api/services/`
4. Create React Query hooks in `src/api/hooks/`

## Best Practices

1. **Keep features isolated** - Avoid cross-feature dependencies
2. **Use barrel exports** - Export through index.ts files
3. **Centralize shared code** - Put reusable code in shared/
4. **Type everything** - Leverage TypeScript for type safety
5. **Follow naming conventions** - Use PascalCase for components, camelCase for utilities

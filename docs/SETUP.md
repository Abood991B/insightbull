# Setup Instructions

## Prerequisites
- Node.js (v18 or higher)
- npm or yarn package manager

## Installation

1. **Install Node.js**
   - Download from [nodejs.org](https://nodejs.org/)
   - Or use nvm (Node Version Manager) for easier version management

2. **Install Dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Run Development Server**
   ```bash
   npm run dev
   # or
   yarn dev
   ```
   The application will be available at `http://localhost:8080`

## Environment Variables

Create a `.env` file in the root directory:

```env
# API Configuration
VITE_API_BASE_URL=http://localhost:3000/api

# Feature Flags (optional)
VITE_ENABLE_ADMIN=true
VITE_ENABLE_ANALYTICS=true
```

## Build for Production

```bash
npm run build
# or
yarn build
```

The production build will be in the `dist/` directory.

## Project Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run build:dev` - Build for development
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Troubleshooting

### Port Already in Use
If port 8080 is already in use, you can change it in `vite.config.ts`:
```typescript
server: {
  port: 3001, // Change to your preferred port
}
```

### Module Resolution Issues
If you encounter import errors after reorganization:
1. Clear node_modules: `rm -rf node_modules`
2. Clear package lock: `rm package-lock.json`
3. Reinstall: `npm install`

### TypeScript Errors
Run `npm run lint` to check for TypeScript errors and fix them accordingly.

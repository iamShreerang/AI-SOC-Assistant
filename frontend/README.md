# AI SOC Assistant - Frontend

> Modern React-based Security Operations Center dashboard with real-time monitoring, alert management, and ML analytics.

## Tech Stack

- **React 19** - UI Library
- **TypeScript** - Type Safety
- **Tailwind CSS** - Styling
- **Recharts** - Data Visualization
- **Axios** - HTTP Client
- **Zustand** - State Management
- **React Router** - Routing
- **Vite** - Build Tool

## Features

### Authentication
- ✅ Login with JWT
- ✅ User Registration
- ✅ Password Reset
- ✅ Role-based Access Control
- ✅ Protected Routes

### Dashboard
- ✅ Real-time Statistics
- ✅ System Health Monitoring
- ✅ Interactive Charts
- ✅ Alert Severity Distribution
- ✅ Event Timeline

### Real-Time Monitoring
- ✅ Live Event Stream
- ✅ Auto-refresh (5s intervals)
- ✅ Event Filtering
- ✅ Severity Indicators

### Alert Management
- ✅ Alert Table with Sorting
- ✅ Status Updates (Open → Acknowledged → Resolved)
- ✅ Severity Filtering
- ✅ Alert Details View

### Incident Management
- ✅ Incident Tracking
- ✅ AI-Generated Summaries
- ✅ Alert Correlation
- ✅ Status Workflow

### ML Analytics
- ✅ Anomaly Detection Results
- ✅ Threat Classification
- ✅ Confidence Scores
- ✅ Model Accuracy Metrics

### Log Explorer
- ✅ Advanced Search
- ✅ Severity Filtering
- ✅ Raw Log Viewing
- ✅ Export to CSV

### Settings
- ✅ Profile Management
- ✅ Notification Preferences
- ✅ Auto-refresh Configuration

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── charts/         # Chart components
│   │   ├── dashboard/      # Dashboard-specific components
│   │   ├── layout/         # Layout components (Sidebar, TopNav)
│   │   └── ui/             # Reusable UI components
│   ├── hooks/              # Custom React hooks
│   ├── pages/              # Page components
│   │   ├── auth/           # Authentication pages
│   │   ├── Dashboard.tsx
│   │   ├── Monitoring.tsx
│   │   ├── Alerts.tsx
│   │   ├── Incidents.tsx
│   │   ├── MLAnalytics.tsx
│   │   ├── LogExplorer.tsx
│   │   └── Settings.tsx
│   ├── services/           # API service layer
│   ├── store/              # Zustand stores
│   ├── types/              # TypeScript type definitions
│   ├── utils/              # Helper functions
│   ├── App.tsx             # Main app component
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles
├── index.html
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

## Getting Started

### Prerequisites

- Node.js 20+
- npm or yarn

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Update .env with your backend API URL
# VITE_API_BASE_URL=http://localhost:8000
```

### Development

```bash
# Start development server
npm run dev

# The app will open at http://localhost:3000
```

### Build

```bash
# Type check
npm run type-check

# Build for production
npm run build

# Preview production build
npm run preview
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000` |

## Component Overview

### UI Components

- **Button** - Primary, secondary, danger, ghost variants
- **Card** - Container for dashboard sections
- **Input** - Form input with error handling
- **Badge** - Status and severity indicators
- **Spinner** - Loading states
- **Alert** - Notification messages

### Charts

- **DonutChart** - Severity distribution
- **BarChart** - Log counts by type
- **LineChart** - Time series data
- **AreaChart** - Trend visualization

### Layout

- **MainLayout** - App wrapper with sidebar and topnav
- **Sidebar** - Navigation menu
- **TopNav** - Search, notifications, user menu

## State Management

### Stores (Zustand)

- **authStore** - User authentication state
- **notificationStore** - In-app notifications
- **settingsStore** - User preferences
- **uiStore** - UI state (sidebar, modals)

## API Integration

All API calls are centralized in `src/services/api.ts`:

```typescript
// Example usage
import { apiService } from '@/services/api';

const alerts = await apiService.getAlerts({ severity: 'critical' });
const summary = await apiService.getDashboardSummary();
```

## Custom Hooks

- **useFetch** - Data fetching with loading/error states
- **usePolling** - Auto-refresh data at intervals
- **useDebounce** - Debounce input values

## Styling

### Tailwind Configuration

Custom color palette for cybersecurity theme:

- `soc-bg-*` - Background colors
- `soc-accent-*` - Accent colors (cyan, blue, purple)
- `soc-text-*` - Text colors
- `severity-*` - Severity-based colors (critical, high, medium, low)

### Custom Classes

- `.cyber-gradient` - Gradient background
- `.cyber-border` - Animated border
- `.glow-text` - Text shadow effect
- `.scrollbar-thin` - Custom scrollbar

## Accessibility

- WCAG 2.2 AA Compliant
- Semantic HTML
- ARIA labels
- Keyboard navigation
- High contrast colors
- Focus indicators

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Performance

- Code splitting with React.lazy
- Memoization with useMemo/useCallback
- Optimized re-renders
- Virtual scrolling for large lists
- Image optimization

## Testing

```bash
# Run type checks
npm run type-check

# Lint code
npm run lint
```

## Deployment

### Build Output

```bash
npm run build
# Output: dist/
```

### Serve Static Files

Deploy the `dist/` folder to any static hosting service:

- Vercel
- Netlify
- AWS S3 + CloudFront
- Nginx

## Backend Integration

Ensure the backend API is running at the URL specified in `.env`:

```bash
# Backend should be running at
http://localhost:8000

# API endpoints used:
/auth/login
/auth/register
/alerts
/incidents
/logs
/stats/summary
```

## Troubleshooting

### CORS Issues

If you encounter CORS errors, ensure the backend has CORS enabled for your frontend URL.

### Authentication Errors

Check that tokens are being stored correctly in localStorage and the Authorization header is set.

### Build Errors

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Contributing

1. Create feature branch from `frontend` branch
2. Follow naming convention: `feature/frontend/<feature-name>`
3. Ensure type safety (no TypeScript errors)
4. Test all routes and features
5. Submit PR with detailed description

## License

AGPL-3.0 - See [LICENSE](../LICENSE)

## Support

For issues or questions, please open an issue on GitHub.

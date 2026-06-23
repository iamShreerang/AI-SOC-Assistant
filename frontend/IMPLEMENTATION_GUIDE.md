# AI SOC Assistant - Frontend Implementation Guide

## 🎯 Project Overview

A production-ready SOC (Security Operations Center) Dashboard built with React 19, TypeScript, Tailwind CSS, and Recharts. Features a cybersecurity-focused dark theme with real-time monitoring capabilities.

## 📁 Complete Project Structure

```
frontend/
├── public/
│   └── vite.svg
├── src/
│   ├── assets/              # Static assets (images, fonts)
│   ├── components/
│   │   ├── ui/             # Reusable UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Select.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Table.tsx
│   │   │   ├── Tabs.tsx
│   │   │   ├── Alert.tsx
│   │   │   ├── Spinner.tsx
│   │   │   └── index.ts
│   │   ├── layout/         # Layout components
│   │   │   ├── Sidebar.tsx
│   │   │   ├── TopNav.tsx
│   │   │   ├── MainLayout.tsx
│   │   │   └── index.ts
│   │   ├── dashboard/      # Dashboard-specific components
│   │   │   ├── StatCard.tsx
│   │   │   ├── SystemHealth.tsx
│   │   │   ├── RecentAlerts.tsx
│   │   │   ├── ThreatMap.tsx
│   │   │   └── index.ts
│   │   └── charts/         # Chart components
│   │       ├── AreaChart.tsx
│   │       ├── BarChart.tsx
│   │       ├── PieChart.tsx
│   │       ├── LineChart.tsx
│   │       └── index.ts
│   ├── pages/              # Page components
│   │   ├── auth/
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   └── ForgotPassword.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Monitoring.tsx
│   │   ├── Alerts.tsx
│   │   ├── AlertDetail.tsx
│   │   ├── Incidents.tsx
│   │   ├── IncidentDetail.tsx
│   │   ├── MLAnalytics.tsx
│   │   ├── LogExplorer.tsx
│   │   ├── Settings.tsx
│   │   └── NotFound.tsx
│   ├── services/           # API services
│   │   └── api.ts
│   ├── hooks/              # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useAlerts.ts
│   │   ├── useIncidents.ts
│   │   ├── useLogs.ts
│   │   ├── useStats.ts
│   │   └── useWebSocket.ts
│   ├── store/              # State management
│   │   └── index.ts
│   ├── types/              # TypeScript types
│   │   └── index.ts
│   ├── utils/              # Utility functions
│   │   └── helpers.ts
│   ├── App.tsx             # Main App component
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles
├── .env.example            # Environment variables template
├── .gitignore
├── index.html              # HTML template
├── package.json            # Dependencies
├── postcss.config.js       # PostCSS configuration
├── tailwind.config.js      # Tailwind CSS configuration
├── tsconfig.json           # TypeScript configuration
├── tsconfig.node.json      # TypeScript for Vite
├── vite.config.ts          # Vite configuration
└── README.md               # Project documentation
```

## 🚀 Quick Start

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

### Build

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## 🎨 Design System

### Color Palette

#### Background Colors
- Primary: `#0a0e17`
- Secondary: `#111827`
- Tertiary: `#1f2937`
- Elevated: `#374151`

#### Accent Colors
- Cyan (Primary): `#06b6d4`
- Blue: `#3b82f6`
- Purple: `#8b5cf6`
- Red: `#ef4444`
- Orange: `#f97316`
- Green: `#10b981`
- Yellow: `#f59e0b`

#### Severity Colors
- Critical: `#dc2626`
- High: `#ea580c`
- Medium: `#f59e0b`
- Low: `#10b981`
- Info: `#3b82f6`

### Typography
- Font Family: Inter (sans-serif), JetBrains Mono (monospace)
- Sizes: text-xs to text-4xl

### Spacing
- Uses Tailwind's default spacing scale (0.25rem increments)

## 📦 Core Components

### UI Components

#### Button
```tsx
<Button variant="primary" size="md" onClick={handleClick}>
  Click Me
</Button>
```

Variants: `primary` | `secondary` | `danger` | `ghost` | `outline`
Sizes: `sm` | `md` | `lg`

#### Card
```tsx
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>Content</CardContent>
  <CardFooter>Footer</CardFooter>
</Card>
```

#### Input
```tsx
<Input
  label="Username"
  placeholder="Enter username"
  error="Invalid username"
  onChange={handleChange}
/>
```

#### Badge
```tsx
<Badge variant="severity" severity="critical">
  Critical
</Badge>
<Badge variant="status" status="open">
  Open
</Badge>
```

## 🔌 API Integration

### Configuration

Create `.env` file:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### Usage

```tsx
import { apiService } from '@/services/api';

// Get alerts
const alerts = await apiService.getAlerts({ 
  severity: 'high', 
  limit: 10 
});

// Create incident
const incident = await apiService.createIncident({
  title: 'Security Breach',
  alert_ids: [1, 2, 3]
});
```

## 📊 State Management

Uses Zustand for global state:

```tsx
import { useAuthStore } from '@/store';

const { user, setAuth, clearAuth } = useAuthStore();
```

Available stores:
- `useAuthStore` - Authentication state
- `useNotificationStore` - Notifications
- `useSettingsStore` - User settings
- `useUIStore` - UI state (sidebar, modals)

## 🔐 Authentication Flow

1. User enters credentials
2. POST to `/auth/login`
3. Receive JWT tokens
4. Store in localStorage and Zustand
5. Add to Authorization header
6. Auto-refresh on 401 errors

## 📱 Pages

### Dashboard
- Summary statistics cards
- Real-time charts
- System health indicators
- Recent activity feed

### Monitoring
- Live event stream
- Auto-refresh toggle
- Severity filters
- Search functionality

### Alerts
- Sortable table
- Status filters
- Bulk actions
- Detail modal

### Incidents
- Incident list
- AI-generated summaries
- Status management
- Alert associations

### ML Analytics
- Anomaly detection results
- Confidence scores
- Model metrics
- Prediction history

### Log Explorer
- Full-text search
- Advanced filters
- Log details
- Export functionality

### Settings
- Profile management
- Notification preferences
- Theme settings
- Auto-refresh configuration

## 🎯 Key Features

### Accessibility (WCAG 2.2 AA Compliant)
- Keyboard navigation
- Screen reader support
- High contrast colors
- Focus indicators
- ARIA labels

### Responsive Design
- Desktop-first approach
- Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)
- Collapsible sidebar on mobile

### Real-time Updates
- WebSocket support ready
- Auto-refresh intervals
- Live event streaming
- Toast notifications

### Performance
- Code splitting
- Lazy loading
- Memoization
- Virtual scrolling for large lists

## 🛠️ Development Guidelines

### Component Structure
```tsx
import { FC } from 'react';
import { cn } from '@/utils/helpers';

interface ComponentProps {
  // Props definition
}

export const Component: FC<ComponentProps> = ({ ...props }) => {
  return (
    <div>
      {/* Component JSX */}
    </div>
  );
};
```

### TypeScript Best Practices
- Use strict mode
- Define interfaces for all props
- Avoid `any` type
- Use type inference where possible

### Styling Guidelines
- Use Tailwind utility classes
- Create custom classes in `index.css` for reusable patterns
- Follow mobile-first approach
- Use design tokens from `tailwind.config.js`

## 🧪 Testing

### Unit Tests
```bash
npm run test
```

### Type Checking
```bash
npm run type-check
```

### Linting
```bash
npm run lint
```

## 📚 Dependencies

### Core
- React 18.3.1
- TypeScript 5.3.3
- Vite 5.1.0

### UI
- Tailwind CSS 3.4.1
- Lucide React (icons)
- Recharts 2.12.0

### State & Data
- Zustand 4.5.0
- Axios 1.6.7
- date-fns 3.3.1

### Routing
- React Router DOM 6.22.0

## 🔄 Integration with Backend

The frontend is designed to work seamlessly with the FastAPI backend:

**Base URL**: `http://localhost:8000`

### Endpoints Used
- `POST /auth/login` - Authentication
- `GET /alerts` - Fetch alerts
- `GET /incidents` - Fetch incidents
- `GET /logs` - Fetch logs
- `GET /stats/summary` - Dashboard statistics
- `GET /stats/activity` - Recent activity
- `GET /stats/trends` - Alert trends

### Authentication
- JWT tokens stored in localStorage
- Auto-refresh mechanism
- Protected routes with redirect

## 🎨 Theme Customization

Edit `tailwind.config.js` to customize:
- Colors
- Spacing
- Typography
- Animations
- Shadows

## 📖 Next Steps

1. Complete remaining UI components (Modal, Select, Table, etc.)
2. Implement all page components
3. Add custom hooks for data fetching
4. Implement WebSocket for real-time updates
5. Add comprehensive error handling
6. Implement data export functionality
7. Add unit and integration tests
8. Optimize bundle size
9. Add PWA support
10. Implement advanced analytics visualizations

## 🤝 Contributing

1. Follow the component structure
2. Use TypeScript strictly
3. Follow accessibility guidelines
4. Write meaningful commit messages
5. Test before committing

## 📝 Notes

- Dark theme is default and recommended
- All times are displayed in user's local timezone
- API responses are cached for 30 seconds
- Auto-refresh can be disabled in settings
- Export functionality supports CSV and JSON formats

---

**Status**: Foundation Complete ✅
**Next**: Implement remaining components and pages

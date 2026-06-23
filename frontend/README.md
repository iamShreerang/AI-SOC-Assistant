# AI SOC Assistant - Frontend

> Modern React 19 + TypeScript SOC Dashboard with real-time security monitoring

## 🚀 Features

- **Modern Tech Stack**: React 19, TypeScript, Tailwind CSS, Recharts
- **Authentication**: JWT-based auth with automatic token refresh
- **Real-time Dashboard**: Live statistics and security event monitoring
- **Dark Cybersecurity Theme**: Professional SOC appearance with blue/cyan accents
- **Responsive Design**: Desktop-first with mobile support
- **Accessibility**: WCAG 2.2 AA compliant
- **State Management**: Zustand for global state
- **API Integration**: Axios with interceptors for FastAPI backend

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # Reusable UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Spinner.tsx
│   │   │   └── Alert.tsx
│   │   ├── layout/          # Layout components
│   │   │   ├── Sidebar.tsx
│   │   │   ├── TopNav.tsx
│   │   │   └── MainLayout.tsx
│   │   └── dashboard/       # Dashboard components
│   │       ├── StatCard.tsx
│   │       └── SystemHealth.tsx
│   ├── pages/               # Page components
│   │   ├── auth/
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   └── ForgotPassword.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Monitoring.tsx
│   │   ├── Alerts.tsx
│   │   ├── Incidents.tsx
│   │   ├── MLAnalytics.tsx
│   │   ├── LogExplorer.tsx
│   │   └── Settings.tsx
│   ├── services/            # API services
│   │   └── api.ts
│   ├── store/               # State management
│   │   └── index.ts
│   ├── types/               # TypeScript types
│   │   └── index.ts
│   ├── utils/               # Utility functions
│   │   └── helpers.ts
│   ├── App.tsx              # Main app with routing
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles
├── public/
├── index.html
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── vite.config.ts
└── README.md
```

## 🛠️ Installation

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

### Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Edit .env with your API URL
# VITE_API_BASE_URL=http://localhost:8000

# Start development server
npm run dev
```

The app will open at `http://localhost:3000`

## 📦 Available Scripts

```bash
# Development
npm run dev          # Start dev server with hot reload

# Build
npm run build        # Build for production
npm run preview      # Preview production build

# Code Quality
npm run lint         # Run ESLint
npm run type-check   # TypeScript type checking
```

## 🎨 Design System

### Color Palette

#### Backgrounds
- Primary: `#0a0e17`
- Secondary: `#111827`
- Tertiary: `#1f2937`

#### Accent Colors
- Cyan: `#06b6d4`
- Blue: `#3b82f6`
- Purple: `#8b5cf6`

#### Severity Colors
- Critical: `#dc2626`
- High: `#ea580c`
- Medium: `#f59e0b`
- Low: `#10b981`

### Typography

- Font Family: Inter (sans-serif)
- Sizes: xs (0.75rem) to 4xl (2.25rem)

### Components

#### Button
```tsx
<Button variant="primary" size="md" onClick={handleClick}>
  Click Me
</Button>
```
Variants: `primary | secondary | danger | ghost | outline`

#### Card
```tsx
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>Content</CardContent>
</Card>
```

#### Badge
```tsx
<Badge variant="severity" severity="critical">Critical</Badge>
<Badge variant="status" status="open">Open</Badge>
```

## 🔌 API Integration

### Configuration

The app uses environment variables for API configuration:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### Authentication Flow

1. User logs in via `/auth/login`
2. JWT tokens stored in localStorage and Zustand
3. Tokens automatically added to API requests
4. Auto-refresh on 401 errors
5. Redirect to login on authentication failure

### API Service

```tsx
import { apiService } from '@/services/api';

// Get dashboard stats
const stats = await apiService.getDashboardSummary();

// Get alerts with filters
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

## 📊 Pages

### Dashboard (`/dashboard`)
- Real-time statistics cards
- Alert severity distribution (Pie chart)
- Alert status overview (Bar chart)
- Events timeline (Line chart)
- System health indicators
- Recent alerts feed

### Monitoring (`/monitoring`)
- Live security event stream
- Auto-refresh functionality
- Event filtering and search

### Alerts (`/alerts`)
- Sortable alert table
- Status filters
- Bulk actions
- Alert detail view

### Incidents (`/incidents`)
- Incident management
- AI-generated summaries
- Alert associations
- Status tracking

### ML Analytics (`/ml-analytics`)
- Anomaly detection results
- Prediction confidence scores
- Model performance metrics

### Log Explorer (`/logs`)
- Full-text search
- Advanced filters
- Log details
- Export functionality

### Settings (`/settings`)
- Profile management
- Notification preferences
- Theme settings
- Auto-refresh configuration

## 🔐 Authentication

### Demo Credentials

**Analyst Account:**
- Username: `analyst`
- Password: `analyst123`

**Admin Account:**
- Username: `admin`
- Password: `admin123`

### Protected Routes

All routes except `/login`, `/register`, and `/forgot-password` require authentication.

## 🎯 State Management

### Zustand Stores

```tsx
import { useAuthStore, useNotificationStore, useUIStore } from '@/store';

// Auth
const { user, setAuth, clearAuth } = useAuthStore();

// Notifications
const { notifications, addNotification } = useNotificationStore();

// UI State
const { sidebarOpen, toggleSidebar } = useUIStore();
```

## 🧪 Testing

```bash
# Run tests (when configured)
npm run test

# Type checking
npm run type-check
```

## 🚀 Deployment

### Build for Production

```bash
npm run build
```

Output will be in the `dist/` directory.

### Environment Variables

Set these in your production environment:

```env
VITE_API_BASE_URL=https://api.your-domain.com
```

### Deploy to Static Hosting

The built files can be deployed to:
- Vercel
- Netlify
- AWS S3 + CloudFront
- Any static file server

## 🎨 Customization

### Theme Colors

Edit `tailwind.config.js` to customize colors:

```js
colors: {
  'soc-accent': {
    cyan: '#06b6d4',  // Change this
  }
}
```

### API Base URL

Update `.env`:

```env
VITE_API_BASE_URL=http://your-api-url
```

## 📝 Development Guidelines

### Component Structure

```tsx
import { FC } from 'react';

interface ComponentProps {
  title: string;
}

export const Component: FC<ComponentProps> = ({ title }) => {
  return <div>{title}</div>;
};
```

### TypeScript

- Use strict mode
- Define interfaces for all props
- Avoid `any` type
- Leverage type inference

### Styling

- Use Tailwind utility classes
- Follow mobile-first approach
- Use design tokens from config
- Maintain consistent spacing

## 🔧 Troubleshooting

### Cannot connect to API

Check:
1. Backend is running on `http://localhost:8000`
2. `.env` file has correct `VITE_API_BASE_URL`
3. CORS is configured on backend

### Build errors

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
```

### TypeScript errors

```bash
# Run type check
npm run type-check
```

## 📚 Resources

- [React Documentation](https://react.dev)
- [TypeScript](https://www.typescriptlang.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Recharts](https://recharts.org/)
- [Vite](https://vitejs.dev/)

## 🤝 Contributing

1. Follow the component structure
2. Use TypeScript strictly
3. Follow accessibility guidelines
4. Test before committing

## 📄 License

GNU Affero General Public License v3.0

## 👥 Team

- **Shreerang Kolhe** - Backend + Integration
- **Aryan Dandge** - Frontend
- **Sayog Shendre** - AI/ML
- **Ayush Dandge** - Big Data Pipeline
- **Sumiran Bagul** - Database

---

**Status**: ✅ Foundation Complete
**Version**: 1.0.0

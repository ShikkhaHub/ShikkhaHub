# ShikkhaHub Mobile App

Cross-platform mobile application for discovering and exploring educational institutions across Bangladesh.

## Features

- **Institution Search**: Find institutions by name, type, division, or district
- **Saved Institutions**: Bookmark institutions for later reference
- **Institution Reviews**: Read and submit reviews and ratings
- **User Profiles**: Manage account settings and preferences
- **AI Assistant**: Get instant answers about institutions
- **Location-based Search**: Find nearby institutions (future feature)
- **Offline Support**: Access saved institutions offline (future feature)

## Tech Stack

- **React Native 0.74** - Cross-platform mobile development
- **Expo 51** - Development platform and build service
- **TypeScript** - Type-safe development
- **React Navigation** - Navigation and routing
- **Zustand** - State management
- **Axios** - HTTP client
- **Tailwind CSS** (via NativeWind) - Styling (future)

## Project Structure

```
mobile/
├── app/                    # Expo configuration
├── screens/               # Screen components
│   ├── auth/             # Authentication screens
│   ├── HomeScreen.tsx    # Home tab
│   ├── SearchScreen.tsx  # Search tab
│   ├── SavedScreen.tsx   # Saved institutions
│   └── ProfileScreen.tsx # User profile
├── components/           # Reusable components (future)
├── hooks/               # Custom hooks
│   └── useStore.ts      # Zustand state management
├── services/            # API services
│   └── api.ts          # API client
├── utils/               # Utility functions (future)
├── assets/             # Images, fonts, icons
├── config/             # Configuration files
├── App.tsx             # Root component
├── app.json            # Expo configuration
├── package.json        # Dependencies
└── tsconfig.json       # TypeScript configuration
```

## Getting Started

### Prerequisites

- Node.js 18+
- pnpm (or npm/yarn)
- Expo CLI (`npm install -g expo-cli`)
- iOS Simulator or Android Emulator (optional)

### Installation

```bash
cd mobile
pnpm install
```

### Development

Start the development server:

```bash
pnpm start
```

Then choose your platform:
- **iOS Simulator**: Press `i`
- **Android Emulator**: Press `a`
- **Web**: Press `w`
- **Scan QR Code**: Use Expo Go app on your phone

### Building

#### iOS Build

```bash
pnpm build:ios
```

#### Android Build

```bash
pnpm build:android
```

#### Both Platforms

```bash
pnpm build:all
```

### Deployment

#### App Store (iOS)

```bash
pnpm submit:ios
```

#### Google Play (Android)

```bash
pnpm submit:android
```

## API Integration

The app communicates with the backend API at:

```
https://api.shikkhahub.edu.bd/api/v1
```

Set this via environment variable:

```bash
VITE_API_URL=https://api.shikkhahub.edu.bd/api/v1
```

## State Management

Using Zustand for simple, scalable state management:

- **useAuthStore**: User authentication and profile
- **useSearchStore**: Search state and results
- **useSavedStore**: Saved institutions
- **useUIStore**: UI preferences (dark mode, etc.)

Example usage:

```typescript
import { useAuthStore } from '@hooks/useStore';

function LoginComponent() {
  const { login, isLoading, error } = useAuthStore();
  
  const handleLogin = async (email: string, password: string) => {
    await login(email, password);
  };
}
```

## API Endpoints

### Authentication

- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `POST /auth/logout` - User logout

### Institutions

- `GET /institutions/search` - Search institutions
- `GET /institutions/:id` - Get institution details
- `GET /institutions/nearby` - Find nearby institutions
- `GET /divisions/:division/institutions` - Get institutions by division

### User

- `GET /users/profile` - Get user profile
- `PATCH /users/profile` - Update user profile
- `GET /users/saved-institutions` - Get saved institutions
- `POST /users/saved-institutions/:id` - Save institution
- `DELETE /users/saved-institutions/:id` - Remove saved institution

### Reviews

- `GET /institutions/:id/reviews` - Get institution reviews
- `POST /institutions/:id/reviews` - Submit review

## Testing

Run tests:

```bash
pnpm test
```

Watch mode:

```bash
pnpm test:watch
```

## Troubleshooting

### Build Issues

Clear cache and rebuild:

```bash
pnpm expo start --clear
```

### Metro Bundler Issues

Reset bundler:

```bash
pnpm expo start --clear --reset-cache
```

### Dependency Issues

Reinstall dependencies:

```bash
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

## Environment Variables

Create `.env.local` file:

```env
EXPO_PUBLIC_API_URL=https://api.shikkhahub.edu.bd/api/v1
EXPO_PUBLIC_ENVIRONMENT=development
```

## Performance Tips

1. Use `React.memo()` for expensive components
2. Implement list virtualization for long lists
3. Lazy load images with `expo-image`
4. Profile with Expo Profiler

## Contributing

1. Create feature branch: `git checkout -b feature/name`
2. Commit changes: `git commit -m 'Add feature'`
3. Push to branch: `git push origin feature/name`
4. Open Pull Request

## Roadmap

- [ ] Location-based search
- [ ] Offline support
- [ ] Real-time notifications
- [ ] Chat feature
- [ ] Video profiles
- [ ] Advanced filters
- [ ] Maps integration
- [ ] Social sharing

## Support

For issues and questions:
- GitHub Issues: [ShikkhaHub Issues]
- Email: support@shikkhahub.edu.bd
- Discord: [ShikkhaHub Community]

## License

MIT

## Team

- Mobile Lead: [Your Name]
- Contributors: [Contributors]

---

**Last Updated**: 2024
**Version**: 1.0.0

# ShikkhaHub Mobile App - React Native with Expo

## Overview

The ShikkhaHub mobile app is a React Native application built with Expo, providing a seamless cross-platform experience for iOS and Android users. The app allows users to search, discover, and interact with educational institutions across Bangladesh.

## Project Structure

```
mobile/
├── app/
│   └── index.tsx                 # Main app entry point with navigation
├── screens/
│   ├── HomeScreen.tsx            # Homepage with suggestions and divisions
│   ├── SearchScreen.tsx          # Advanced search with filters
│   ├── InstitutionDetailsScreen/ # Full institution details with reviews
│   ├── SavedScreen.tsx           # Saved/bookmarked institutions
│   ├── ProfileScreen.tsx         # User profile and settings
│   ├── LoginScreen.tsx           # Authentication login
│   └── RegisterScreen.tsx        # User registration
├── hooks/
│   └── useAuthStore.ts           # Zustand auth state management
├── services/
│   └── api.ts                    # API client with axios
├── config/
│   └── constants.ts              # App constants and config
├── utils/
│   └── helpers.ts                # Utility functions
├── assets/
│   ├── images/                   # App icons and images
│   └── fonts/                    # Custom fonts
├── app.json                      # Expo configuration
├── package.json                  # Dependencies
└── tsconfig.json                 # TypeScript configuration
```

## Key Features

### Authentication
- Email/password registration and login
- JWT token-based authentication
- Persistent token storage with AsyncStorage
- Auto-login on app launch if token exists

### Home Screen
- Personalized greeting
- Quick search button
- Popular institutions carousel
- Browse by division/district
- Quick action links (AI Assistant, FAQs, etc.)

### Search Screen
- Full-text search across institution names and descriptions
- Filter by division and institution type
- Auto-complete suggestions
- Result sorting and pagination
- Responsive to user input with debouncing

### Institution Details
- Complete institution information
- Photos and logos
- Contact information (phone, email, website)
- Ratings and reviews
- Write and read reviews
- Save to wishlist
- Share institution

### Saved Screen
- View all saved institutions
- Quick access to favorite institutions
- Remove from saved list
- Sort and filter saved items

### Profile Screen
- User information display
- Edit profile (optional)
- Notification preferences
- Account settings
- Help and support links
- Terms and privacy policy
- Logout functionality

## State Management

Using **Zustand** for global state management:

```typescript
// useAuthStore.ts
- user: UserProfile
- token: string | null
- isAuthenticated: boolean
- isInitialized: boolean
- login(email, password)
- register(email, password, name)
- logout()
- updateProfile(data)
```

## API Integration

The app uses **axios** with the following features:
- Request/response interceptors for token management
- Automatic error handling and user-friendly messages
- Support for pagination and filtering
- Timeout handling (30s default)

## Building and Deployment

### Prerequisites
```bash
npm install -g expo-cli
npm install -g eas-cli
```

### Local Development
```bash
cd mobile
pnpm install
pnpm start

# Run on specific platform
pnpm start:ios
pnpm start:android
```

### Build for Production
```bash
# Build APK/IPA
pnpm build:ios
pnpm build:android

# Submit to app stores
pnpm submit:ios
pnpm submit:android
```

## Environment Configuration

The app reads API base URL from `app.json`:
```json
{
  "extra": {
    "apiUrl": "https://api.shikkhahub.edu.bd/api/v1",
    "eas": {
      "projectId": "your-project-id"
    }
  }
}
```

## Styling

- **Color Scheme**: Uses consistent Tailwind-inspired colors
- **Font**: Inter (primary), with fallback system fonts
- **Responsive**: Flexbox-based layouts that work on all screen sizes

## Performance Optimizations

1. **Code Splitting**: Each screen is a separate component
2. **Image Caching**: Network images are cached by React Native
3. **Lazy Loading**: Reviews and content loaded on demand
4. **Memoization**: Components memoized to prevent unnecessary re-renders

## Testing

```bash
# Run tests
pnpm test

# Watch mode
pnpm test:watch
```

## Known Limitations

1. TextInput inside ScrollView can be tricky - review form uses placeholder text
2. Geolocation requires additional permissions setup
3. Video playback not yet implemented
4. Offline mode not available (could be added with Redux Persist)

## Future Enhancements

1. **Push Notifications**: Implement Expo Notifications for alerts
2. **Offline Mode**: Add Redux Persist for offline browsing
3. **Maps Integration**: Show institution locations on map
4. **Video Tutorials**: Embedded institution video tours
5. **AR Features**: Augmented reality institution previews
6. **Accessibility**: Enhanced VoiceOver and TalkBack support
7. **Dark Mode**: Native dark mode toggle

## Security Considerations

1. **Tokens**: Stored securely in AsyncStorage (encrypted on iOS)
2. **HTTPS**: All API calls use HTTPS
3. **Input Validation**: All user inputs validated before API calls
4. **Error Handling**: Sensitive errors not exposed to users

## Troubleshooting

### Common Issues

**App won't start**
```bash
pnpm install
npx expo start --clear
```

**API connection errors**
- Check `app.json` `apiUrl` configuration
- Ensure backend is running and accessible
- Check network connectivity

**Build fails**
```bash
pnpm expo prebuild --clean
pnpm build:ios  # or build:android
```

## Support

For issues or questions, contact: support@shikkhahub.edu.bd

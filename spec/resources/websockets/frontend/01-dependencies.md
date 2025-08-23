# Frontend Dependencies for Socket.IO Integration

## Primary Dependencies

### Socket.IO Client

```bash
cd frontend
npm install socket.io-client@^4.7.0
```

**Why this version:**
- TypeScript support out of the box
- Compatible with Socket.IO server v4.x
- Stable API with good documentation
- Automatic reconnection handling

### TypeScript Types (if needed)

```bash
npm install --save-dev @types/socket.io-client
```

**Note**: `socket.io-client@^4.7.0` includes TypeScript definitions, so separate `@types` package may not be needed.

## Optional Performance Dependencies

### Better Connection Management

```bash
npm install ws@^8.14.0  # WebSocket implementation
```

### Development Dependencies

```bash
npm install --save-dev @types/ws
```

## Package.json Changes

Add to your `package.json`:

```json
{
  "dependencies": {
    "socket.io-client": "^4.7.0",
    "ws": "^8.14.0"
  },
  "devDependencies": {
    "@types/ws": "^8.5.0"
  }
}
```

## Version Compatibility

### Next.js Compatibility
- **Next.js 15**: ✅ Fully compatible
- **Next.js 14**: ✅ Compatible
- **React 19**: ✅ Compatible
- **React Server Components**: ⚠️ Client-side only (use 'use client')

### Browser Support
- **Modern browsers**: Full WebSocket support
- **Fallback**: Automatic polling for older browsers
- **Mobile**: Full support on iOS Safari, Android Chrome

### Node.js Compatibility
- **Minimum**: Node.js 16+
- **Recommended**: Node.js 18+
- **Tested**: Node.js 20+

## Installation Verification

Test the installation:

```typescript
// Test file: test-socket-install.ts
import { io, Socket } from 'socket.io-client';

console.log('Socket.IO client loaded successfully');

// Test type definitions
const socket: Socket = io('http://localhost:8103');
socket.on('connect', () => {
  console.log('Connection test passed');
});
```

Run the test:
```bash
npx tsx test-socket-install.ts
```

## Bundle Size Impact

Expected bundle size increase:
- **socket.io-client**: ~45KB gzipped
- **ws**: ~15KB gzipped (if used)
- **Total impact**: ~60KB gzipped

### Bundle Optimization

For production builds, Socket.IO client tree-shakes well:

```typescript
// Import only what you need
import { io } from 'socket.io-client';

// Avoid importing the entire package
// ❌ import * as SocketIO from 'socket.io-client';
// ✅ import { io, Socket } from 'socket.io-client';
```

## Environment-Specific Installation

### Development
```bash
npm install socket.io-client ws
npm install --save-dev @types/ws
```

### Production
Only runtime dependencies are needed:
```json
{
  "dependencies": {
    "socket.io-client": "^4.7.0"
  }
}
```

### Docker Installation
In `frontend/Dockerfile`:

```dockerfile
# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# For production builds
RUN npm install --only=production
```

## Troubleshooting

### Common Installation Issues

1. **Peer Dependency Warnings**
   ```bash
   npm install --legacy-peer-deps
   ```

2. **TypeScript Errors**
   ```bash
   # Ensure TypeScript version compatibility
   npm install typescript@^5.0.0
   ```

3. **Build Errors with Next.js**
   ```bash
   # Clear Next.js cache
   rm -rf .next
   npm run build
   ```

### Version Conflicts

If you encounter version conflicts:

```bash
# Check dependency tree
npm ls socket.io-client

# Force resolution in package.json
{
  "overrides": {
    "socket.io-client": "^4.7.0"
  }
}
```

## Development vs Production

### Development Features
- Hot Module Replacement support
- Debug logging enabled
- Source maps included

### Production Optimizations
- Tree shaking
- Minification
- Connection pooling
- Automatic compression

## Security Considerations

### Package Auditing
```bash
# Audit dependencies for vulnerabilities
npm audit

# Fix vulnerabilities
npm audit fix
```

### Content Security Policy

Update your CSP headers to allow WebSocket connections:

```typescript
// next.config.js
const nextConfig = {
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: "connect-src 'self' ws://localhost:8103 wss://yourdomain.com"
          }
        ]
      }
    ]
  }
}
```

This ensures Socket.IO client is properly installed and configured for the Next.js environment.
Purpose: Define screens, wireframes, and flows.

Key Pages:

Login / Signup (SSO ready – Entra ID / Google Workspace).

Dashboard (per role: business, partner, admin, reviewer).

Ad Upload (drag/drop, metadata form, live AI scan preview).

Review Queue (AI score, flagged reason, approve/reject).

Kiosk Management (menu builder + ad playlist editor).

Category Subscription (business subscribes to promotion types).

User & Role Management (CRUD + audit logs).

## Flutter Digital Signage UI Specifications

### Screen Architecture (5-Screen System)

#### 1. Setup & Registration Screen
**Purpose**: Device onboarding and secure backend communication

**Key Features**:
- QR code scanning interface with camera preview
- Manual input form with validation
- Network connectivity indicators
- Real-time registration status
- Bilingual support (Arabic RTL/English LTR)

**UI Components**:
- Full-screen camera viewfinder with QR overlay
- Floating action buttons for manual entry
- Progress indicators for registration steps
- Error handling with retry mechanisms
- Responsive design for tablets/kiosks

**Accessibility**:
- Large touch targets (minimum 44dp)
- High contrast mode support
- Screen reader compatibility
- Voice guidance for setup process

#### 2. Main Display Screen
**Purpose**: Full-screen content rendering with dynamic layouts

**Key Features**:
- Multi-zone content display using Stack layout
- Hardware-accelerated video playback
- Smooth content transitions
- Dynamic text overlay rendering
- Real-time content scheduling

**UI Components**:
- Full-screen content containers
- Overlay positioning system
- Transition animations between content
- Loading states with progress indicators
- Emergency exit gestures (admin access)

**Performance**:
- 60 FPS animation performance
- Memory management for large media files
- Background content preloading
- Battery optimization for extended playback

#### 3. Interactive & Game Screen
**Purpose**: User engagement through NFC/Bluetooth interactions

**Key Features**:
- NFC proximity detection with visual feedback
- Bluetooth beacon scanning interface
- Gamified experience with rewards
- Touch-optimized game controls
- Privacy-compliant data collection

**UI Components**:
- Interactive game overlays
- Progress bars and score displays
- QR code generation for rewards
- Haptic feedback integration
- Session timeout handling

**Privacy & Security**:
- Anonymous user identification
- Consent management interface
- Data retention controls
- GDPR-compliant tracking

#### 4. Status & Diagnostics Screen
**Purpose**: Administrative interface for device management

**Key Features**:
- Real-time system health monitoring
- Network diagnostics dashboard
- Content synchronization status
- Remote management controls
- Admin authentication methods

**UI Components**:
- System metrics dashboard
- Network connectivity tests
- Storage utilization graphs
- Temperature monitoring display
- Admin action buttons

**Security**:
- PIN-based authentication
- Biometric verification support
- Time-based access controls
- Audit trail logging

#### 5. Error & Offline Mode Screen
**Purpose**: Graceful degradation during connectivity issues

**Key Features**:
- Offline content playback
- Network reconnection monitoring
- Error classification system
- Recovery action suggestions
- Emergency contact display

**UI Components**:
- Error message displays with icons
- Network status indicators
- Recovery action buttons
- Cached content playlist
- Contact information cards

**Resilience**:
- Automatic error recovery
- Graceful service degradation
- User-friendly troubleshooting
- Emergency override options

### Cross-Screen Design System

#### Material Design 3 Implementation
- Dynamic color theming
- Consistent component library
- Accessibility-first design
- Multi-device optimization

#### Responsive Design Principles
- Breakpoint-based layouts (Mobile/Tablet/TV)
- Aspect ratio preservation
- Touch target optimization
- Orientation handling

#### Performance Optimizations
- Lazy loading for content
- Image optimization pipeline
- Memory management strategies
- Battery conservation modes

Include accessibility (WCAG 2.1 AA).
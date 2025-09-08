# Launch Video & Standby Screen Implementation

This implementation adds launch video and standby screen functionality to the Adara Digital Signage app.

## Features Implemented

### 1. Launch Video Screen (`launch_video_screen.dart`)
- **Purpose**: Plays a video when the app starts up
- **Features**:
  - Fullscreen video playback
  - Skip button (appears after 3 seconds)
  - Progress indicator
  - Fallback to logo screen if video fails to load
  - Auto-complete when video finishes
  - Smooth fade animations

### 2. Standby Screen (`standby_screen.dart`)
- **Purpose**: Displays when there's no content to play
- **Features**:
  - Beautiful background image or gradient fallback
  - Animated logo with breathing effect
  - Real-time clock display
  - Device and organization information
  - Touch-to-wake functionality
  - Responsive design for different screen sizes

### 3. Enhanced Main Display (`main_display_screen.dart`)
- **Updated**: Now uses `StandbyScreen` when no content is available
- **Integration**: Seamlessly transitions between content and standby mode

### 4. App Wrapper (`main_launch.dart`)
- **Purpose**: Manages app flow from launch video to main application
- **Features**:
  - Handles launch video playback
  - Initializes app state
  - Manages screen transitions
  - Error handling

## Required Assets

Add these files to `assets/images/`:

1. **`launch_video.mp4`** - Video to play on app startup
2. **`standby_screen.jpg`** - Background image for standby screen
3. **`logo.png`** - App logo (already exists)

## Usage

### Basic Implementation
```dart
// To use launch video screen directly
LaunchVideoScreen(
  onVideoComplete: () {
    // Navigate to next screen
  },
  onSkip: () {
    // Handle skip action
  },
)

// To use standby screen
StandbyScreen(
  deviceName: 'Display-001',
  organizationName: 'Your Organization',
  showClock: true,
  showLogo: true,
  onWakeUp: () {
    // Handle wake up action
  },
)
```

### Integration with Existing App

1. **Replace main.dart** with `main_launch.dart` content
2. **Update pubspec.yaml** to include new assets
3. **Add video assets** to the assets/images folder

### Demo Application

Run the demo to test functionality:
```bash
# Run the demo app
flutter run lib/demo_video_standby.dart
```

## Configuration Options

### Launch Video Screen
- `onVideoComplete`: Callback when video finishes
- `onSkip`: Callback when user skips video

### Standby Screen
- `deviceName`: Name of the device to display
- `organizationName`: Organization name to display
- `showClock`: Whether to show the real-time clock
- `showLogo`: Whether to show the app logo
- `onWakeUp`: Callback when user touches the screen

## Technical Details

### Video Playback
- Uses `video_player` package
- Supports both asset and network videos
- Handles initialization errors gracefully
- Automatically manages video controller lifecycle

### Animations
- Smooth fade transitions
- Breathing animation for logo
- Slide-in effects for text
- Progress indicators

### Responsive Design
- Adapts to different screen orientations
- Scales content based on screen size
- Optimized for landscape displays

### Error Handling
- Graceful fallback if video fails to load
- Default graphics if images are missing
- Network connectivity awareness

## File Structure

```
lib/
├── screens/
│   ├── launch_video_screen.dart    # Launch video functionality
│   ├── standby_screen.dart         # Standby screen with clock
│   └── main_display_screen.dart    # Updated main display
├── main_launch.dart                # App wrapper with video integration
├── demo_video_standby.dart         # Demo application
└── main.dart                       # Original main file (backup)

assets/
└── images/
    ├── launch_video.mp4           # Launch video (add this)
    ├── standby_screen.jpg         # Standby background (add this)
    └── logo.png                   # App logo (existing)
```

## Next Steps

1. **Add your assets**: Place the launch video and standby image in the assets folder
2. **Test the functionality**: Use the demo app to verify everything works
3. **Customize appearance**: Modify colors, animations, and layout as needed
4. **Integration**: Replace the main app entry point with the new implementation

## Dependencies

The implementation uses these packages (already in pubspec.yaml):
- `video_player`: For video playback
- `flutter/services`: For fullscreen mode
- `provider`: For state management (if using app state)

## Notes

- Videos should be optimized for the target device resolution
- Consider video file size for app bundle size
- Test on actual hardware for performance validation
- Ensure assets are properly included in pubspec.yaml

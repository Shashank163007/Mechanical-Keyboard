# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| Latest  | ✅ Yes             |

## Important Note About Keyboard Hooks

This application uses **`pynput`** to create a global keyboard listener. This is required for its core functionality (playing sounds on keystrokes). The app:

- ❌ Does **NOT** suppress or intercept keyboard input
- ❌ Does **NOT** log, record, or store keystrokes
- ❌ Does **NOT** transmit any data over the network
- ✅ Only reads key events to trigger audio playback

The keyboard listener can be paused at any time from within the app or the system tray menu.

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

1. **Do NOT** open a public issue for security vulnerabilities
2. Open a private security advisory on the repository, or contact the maintainer directly
3. Provide a clear description of the vulnerability and steps to reproduce it

We will respond as quickly as possible and work to fix the issue.

## Best Practices for Users

- Download this project only from the official GitHub repository
- Verify the source code if you have security concerns — it's fully open source
- Keep Python and dependencies updated to their latest versions
- Use the system tray pause feature when you don't need the keyboard listener active

# Contributing to Mechanical Keyboard Audio Simulator

First off, thank you for considering contributing! 🎉 Every contribution helps make this project better.

## How Can I Contribute?

### 🐛 Reporting Bugs

1. **Check existing issues** to see if it's already reported
2. Open a new issue with:
   - A clear, descriptive title
   - Steps to reproduce the bug
   - What you expected vs. what actually happened
   - Your Python version and Windows version

### 💡 Suggesting Features

Open an issue with the **"Feature Request"** label and describe:
- What you'd like to see
- Why it would be useful
- Any ideas for how it could work

### 🔊 Adding Soundpacks

New soundpacks are one of the best ways to contribute! Here's how:

1. Create a folder: `sounds/<Brand Name>/<Model Name>/`
2. Add audio files (`.wav`, `.mp3`, or `.ogg`)
3. Supported naming:
   - Per-key: `a.wav`, `b.wav`, etc.
   - Stabilizers: `space.wav`, `enter.wav`, `backspace.wav`, `shift.wav`
   - Default: `default.wav`
   - Multi-sample: `1.wav`, `2.wav`, `key1.wav`, `key2.wav`
4. **Important:** Only contribute sounds that you own or have permission to distribute. Include a `LICENSE` file in the soundpack directory if the audio has separate license terms.

### 🛠️ Submitting Code Changes

1. **Fork** the repository
2. **Clone** your fork:
   ```bash
   git clone https://github.com/Shashank163007/Mechanical-Keyboard.git
   cd Mechanical-Keyboard
   ```
3. **Create a branch** for your change:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make your changes** — keep them focused and minimal
5. **Test your changes** by running the app and verifying everything works
6. **Commit** with a clear message:
   ```bash
   git commit -m "Add: brief description of change"
   ```
7. **Push** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
8. Open a **Pull Request** against the `main` branch

## Code Guidelines

- Keep code clean and readable
- Add comments for complex logic
- Follow the existing code style (PEP 8 for Python)
- Don't add unnecessary dependencies
- Test your changes on Windows before submitting

## Commit Message Format

Use clear, concise commit messages:

```
Add: description     (new feature)
Fix: description     (bug fix)
Update: description  (improvement to existing feature)
Docs: description    (documentation changes)
Refactor: description (code restructuring)
```

## Code of Conduct

By participating in this project, you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Questions?

Open an issue with the **"Question"** label — happy to help!

---

Thank you for making Mechanical Keyboard Audio Simulator better! ⌨️✨

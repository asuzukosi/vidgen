# CLI Migration to Textual

## Overview

The VidGen project has been successfully migrated from a traditional command-line script to a modern Terminal User Interface (TUI) using the [Textual](https://github.com/Textualize/textual) framework.

## What Changed

### Removed
- ❌ `script.py` - Old argparse-based command-line script

### Added
- ✅ `cli/` - New CLI package with Textual UI
- ✅ `vidgen.py` - New main entry point
- ✅ `cli/README.md` - CLI-specific documentation
- ✅ `QUICKSTART.md` - Quick start guide

## New Structure

```
cli/
├── __init__.py              # Package initialization
├── README.md                # CLI documentation
├── app.py                   # Main Textual application
├── utils.py                 # Utility functions (migrated from script.py)
├── screens/                 # Application screens
│   ├── __init__.py
│   ├── main_screen.py       # Main interface with PDF selection
│   ├── progress_screen.py   # Progress tracking screen
│   └── file_browser.py      # Interactive PDF file browser
└── widgets/                 # Custom widgets
    ├── __init__.py
    └── log_viewer.py        # Real-time log viewer
```

## Key Features

### 1. **Interactive File Browser**
- Visual directory tree navigation
- Filters to show only PDF files
- Keyboard and mouse navigation

### 2. **Main Screen**
- PDF file selection (browse or manual entry)
- Output path configuration
- Video style selector (4 options)
- Test phase buttons (Phases 1-4)
- Generate full video button
- Real-time activity log

### 3. **Progress Screen**
- Progress bar for long-running tasks
- Phase-by-phase updates
- Real-time log viewer
- Cancel button (placeholder for future implementation)

### 4. **Background Processing**
- Non-blocking video generation
- Asynchronous workers for tests and generation
- UI remains responsive during long operations

### 5. **Beautiful UI**
- Modern terminal interface with colors and borders
- Split-pane layout (config + logs)
- Dark/light mode toggle
- Professional styling

## Migration Guide

### For Users

**Old Way:**
```bash
python script.py document.pdf --style slideshow --test-parser
```

**New Way:**
```bash
python vidgen.py
# Then use the interactive UI
```

### For Developers

All core functionality from `script.py` has been moved to `cli/utils.py`:

```python
# Old
from script import test_phase1, generate_full_video

# New
from cli.utils import test_phase1, generate_full_video
```

## Updated Dependencies

Added to `requirements.txt`:
```
textual>=0.85.0
textual-dev
```

Removed:
```
argparse  # Built-in to Python, was redundant
```

## Installation

```bash
# Install new dependencies
pip install -r requirements.txt

# Run the application
python vidgen.py
```

## Keyboard Shortcuts

- `q` - Quit application
- `d` - Toggle dark/light mode
- `Tab` - Navigate between UI elements
- `Enter` - Activate buttons
- Arrow keys - Navigate in file browser

## Technical Details

### Textual App Architecture

**VidGenApp** (Main Application)
- Manages screens and navigation
- Handles global keybindings
- Coordinates between screens

**MainScreen** (Primary Interface)
- Left panel: Configuration and controls
- Right panel: Activity log
- Handles user input and validation
- Spawns background workers

**ProgressScreen** (Progress Tracking)
- Shows during long operations
- Updates progress bar
- Displays phase-specific logs

**FileBrowserScreen** (PDF Selection)
- Custom DirectoryTree filtering
- PDF file highlighting
- Dismissible with result

### Background Workers

The app uses Textual's worker system for async operations:

```python
self.app.run_worker(
    self._generate_video_worker(pdf_path, style, output_path),
    name="generate_video"
)
```

This keeps the UI responsive during:
- Video generation (can take 5-15 minutes)
- Test phases (1-5 minutes each)
- File operations

### Logging Integration

The CLI integrates with the existing centralized logging system:
- All logs go to `temp/vidgen.log`
- Real-time display in the activity log widget
- Colored output for different log levels

## Benefits of the New CLI

1. **Better User Experience**
   - Visual feedback
   - No need to remember command-line flags
   - Interactive file selection
   - Real-time progress updates

2. **More Discoverable**
   - All options visible at once
   - Test phases clearly labeled
   - Immediate feedback

3. **Modern & Professional**
   - Beautiful terminal UI
   - Consistent with modern TUI applications
   - Dark/light mode support

4. **Easier to Extend**
   - Modular screen architecture
   - Easy to add new screens/features
   - Custom widgets for reusable components

5. **Better Error Handling**
   - Visual error messages
   - Validation before submission
   - Clear status updates

## Future Enhancements

Planned features for the TUI:

- [ ] Real-time progress bars for each phase
- [ ] Configuration editor screen
- [ ] Video preview/playback
- [ ] Batch processing interface
- [ ] Template management
- [ ] Help screen with keyboard shortcuts
- [ ] Settings/preferences screen
- [ ] Notification system
- [ ] Video history/recent files
- [ ] Export/import project settings

## Development

### Running with Dev Console

```bash
# Terminal 1: Start dev console
textual console

# Terminal 2: Run app
python vidgen.py
```

The dev console shows:
- Widget hierarchy
- CSS inspection
- Log messages
- Events

### Hot Reload

```bash
textual run --dev cli/app.py:VidGenApp
```

Changes to CSS and some code will auto-reload.

### Testing

The TUI can be tested programmatically:

```python
from textual.pilot import Pilot
from cli.app import VidGenApp

async def test_app():
    app = VidGenApp()
    async with app.run_test() as pilot:
        # Simulate user interactions
        await pilot.click("#browse-btn")
        # ...
```

## Backward Compatibility

The core functionality remains unchanged:
- Same configuration files (`config.yaml`, `.env`)
- Same output structure
- Same intermediate files in `temp/`
- Same video styles
- All core modules unchanged

Only the interface has changed from CLI to TUI.

## Documentation Updates

Updated files:
- `README.md` - Main readme with TUI usage
- `cli/README.md` - New CLI-specific docs
- `QUICKSTART.md` - New quick start guide
- `requirements.txt` - Added Textual

## Support

For issues with the new TUI:
1. Check `cli/README.md` for detailed documentation
2. Review `temp/vidgen.log` for errors
3. Ensure Textual is properly installed: `pip install --upgrade textual`
4. Try the dev console for debugging

## Credits

Built with [Textual](https://github.com/Textualize/textual) by Textualize.io
- Modern, feature-rich TUI framework
- Excellent documentation
- Active community
- Regular updates

---

**The migration is complete and the new CLI is ready to use! 🎉**


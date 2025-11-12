# VidGen CLI Demo

## Screenshots & Features

### Main Screen

```
┌─────────────────────────────────────────────────────────────────────┐
│ VidGen - PDF to Video Generator                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────┐  ┌───────────────────────────────────────┐ │
│  │ 📄 PDF to Video     │  │ 📋 Activity Log                       │ │
│  │ Generator           │  │                                       │ │
│  │                     │  │ 🚀 VidGen CLI Started                │ │
│  │ PDF File:           │  │ Welcome to PDF to Video Generator!   │ │
│  │ ┌─────────────────┐ │  │ Select a PDF file to get started.   │ │
│  │ │ Path or browse  │ │  │                                       │ │
│  │ └─────────────────┘ │  │                                       │ │
│  │ [ Browse Files ]    │  │                                       │ │
│  │                     │  │                                       │ │
│  │ Output Path:        │  │                                       │ │
│  │ ┌─────────────────┐ │  │                                       │ │
│  │ │ output/video.mp4│ │  │                                       │ │
│  │ └─────────────────┘ │  │                                       │ │
│  │                     │  │                                       │ │
│  │ Video Style:        │  │                                       │ │
│  │ ┌─────────────────┐ │  │                                       │ │
│  │ │ Slideshow      ▼│ │  │                                       │ │
│  │ └─────────────────┘ │  │                                       │ │
│  │                     │  │                                       │ │
│  │ 🧪 Test Phases      │  │                                       │ │
│  │ [ Test Phase 1 ]    │  │                                       │ │
│  │ [ Test Phase 2 ]    │  │                                       │ │
│  │ [ Test Phase 3 ]    │  │                                       │ │
│  │ [ Test Phase 4 ]    │  │                                       │ │
│  │                     │  │                                       │ │
│  │ 🎬 Generate Video   │  │                                       │ │
│  │ [ Generate Full ]   │  │                                       │ │
│  │                     │  │                                       │ │
│  │ ┌─────────────────┐ │  │                                       │ │
│  │ │ Status: Ready   │ │  │                                       │ │
│  │ └─────────────────┘ │  │                                       │ │
│  └─────────────────────┘  └───────────────────────────────────────┘ │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│ q Quit  d Dark Mode                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Usage Flow

### 1. Select PDF File

Two options:
- **Browse**: Click "Browse Files" → Navigate → Select
- **Manual**: Type/paste path directly

### 2. Configure Options

- Set output path (optional)
- Choose video style from dropdown

### 3. Test or Generate

**Option A: Test Individual Phases**
- Click test buttons to verify each step
- View results in activity log

**Option B: Generate Full Video**
- Click "Generate Full Video"
- Monitor progress in real-time
- Get notification when complete

## Features

### Interactive Elements

- ✨ **Buttons** - Click or press Enter to activate
- 📝 **Input Fields** - Type text directly
- 📋 **Dropdowns** - Select from multiple options
- 🌲 **File Browser** - Navigate directory tree
- 📊 **Logs** - Scrollable, colorized output

### Keyboard Navigation

| Key | Action |
|-----|--------|
| `q` | Quit application |
| `d` | Toggle dark/light mode |
| `Tab` | Next element |
| `Shift+Tab` | Previous element |
| `Enter` | Activate button/confirm |
| `Esc` | Cancel/go back |
| `↑↓` | Navigate lists |
| `PgUp/PgDn` | Scroll logs |

### Visual Feedback

- ✅ Success messages in green
- ❌ Error messages in red
- ⚡ Processing indicators
- 📊 Progress updates
- 🎨 Syntax-highlighted logs

## Example Sessions

### Testing Phase 1

```
📋 Activity Log
═══════════════════════════════════════════════════
Starting PHASE1 test
PDF: /Users/john/documents/report.pdf
═══════════════════════════════════════════════════

=== Phase 1: PDF Text Extraction Test ===
============================================================
PDF Title: Annual Report 2024
Total Pages: 45
Sections Found: 12
============================================================

Section 1: Executive Summary
Level: 1
Content Length: 1,247 characters
Preview: This report presents the findings from our...

Section 2: Introduction
Level: 1
Content Length: 892 characters
Preview: The purpose of this document is to...

✓ Phase 1 Test Completed Successfully!
```

### Generating Video

```
📋 Activity Log
═══════════════════════════════════════════════════
Starting full video generation
PDF: /Users/john/documents/report.pdf
Style: combined
═══════════════════════════════════════════════════

Running full content pipeline (Phases 1-4)...

--- Phase 1: PDF Parsing ---
✓ Parsed 45 pages

--- Phase 2: Image Extraction & Labeling ---
✓ Extracted and labeled 12 images

--- Phase 3: Content Analysis & Segmentation ---
✓ Created outline with 8 segments

--- Phase 4: Script Generation & Voiceover ---
✓ Generated scripts
✓ Generated voiceovers

--- Generating COMBINED Video ---

===============================================================
✓✓✓ VIDEO GENERATION COMPLETE! ✓✓✓
===============================================================
Output: output/report_combined.mp4
===============================================================

🎉 SUCCESS! Your explainer video is ready!
```

## Color Scheme

The UI uses semantic colors:

- **Primary** (Cyan): Borders, highlights
- **Accent** (Magenta): Section titles, emphasis
- **Success** (Green): Completion messages, status box
- **Error** (Red): Error messages, cancel button
- **Warning** (Yellow): Warnings, test phases

## Accessibility

- **Keyboard-only navigation** supported
- **Screen reader friendly** (via terminal)
- **High contrast mode** available
- **Consistent tab order**
- **Clear focus indicators**

## Performance

- **Non-blocking operations** - UI stays responsive
- **Background workers** - Long tasks don't freeze UI
- **Efficient rendering** - Only updates changed widgets
- **Lazy loading** - File browser loads on-demand

## Error Handling

```
📋 Activity Log
════════════════════════════════════════════
Error: PDF file not found: /path/to/missing.pdf
════════════════════════════════════════════

Status: ❌ PDF file not found: /path/to/missing.pdf
```

Clear, actionable error messages appear in:
1. Activity log (detailed)
2. Status box (summary)
3. Color-coded for visibility

## Development Mode

Run with dev console for debugging:

```bash
# Terminal 1
textual console

# Terminal 2
python vidgen.py
```

Dev console shows:
- Widget hierarchy and structure
- CSS styles and computed values
- Log messages and events
- Performance metrics
- DOM tree

## Customization

The UI can be customized via CSS in each screen's `CSS` attribute:

```python
class MainScreen(Screen):
    CSS = """
    MainScreen {
        background: $surface;
    }
    
    #main-container {
        height: 100%;
        padding: 1;
    }
    
    Button {
        margin-right: 1;
    }
    """
```

## Advantages Over Old CLI

| Feature | Old CLI | New TUI |
|---------|---------|---------|
| File selection | Manual typing | Interactive browser |
| Configuration | Command flags | Visual forms |
| Progress | Text output | Real-time log |
| Errors | Plain text | Color-coded |
| Discoverability | Help command | Visual layout |
| Feedback | After completion | Real-time |
| User-friendly | Command-line savvy | Anyone |

## Technical Stack

- **Textual 0.85+** - TUI framework
- **Rich** - Terminal formatting (included with Textual)
- **Python 3.8+** - Runtime

## Browser Compatibility

Works in any terminal that supports:
- ANSI colors (most modern terminals)
- Mouse input (optional, keyboard works too)
- UTF-8 characters

Tested on:
- ✅ iTerm2 (macOS)
- ✅ Terminal.app (macOS)
- ✅ Windows Terminal (Windows)
- ✅ GNOME Terminal (Linux)
- ✅ Konsole (Linux)
- ✅ tmux/screen (with proper TERM)

---

**Try it now: `python vidgen.py`** 🚀


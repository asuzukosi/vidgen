# VidGen CLI - Terminal User Interface

A beautiful, interactive terminal application for generating professional explainer videos from PDF documents.

## Features

- 🎨 **Modern TUI**: Built with [Textual](https://github.com/Textualize/textual) for a beautiful terminal experience
- 📄 **PDF Selection**: Interactive file browser for easy PDF selection
- 🧪 **Test Phases**: Run individual test phases to verify each step of the pipeline
- 🎬 **Multiple Styles**: Generate videos in different styles (slideshow, animated, AI-generated, combined)
- 📋 **Real-time Logs**: Monitor progress with live log viewer
- ⚡ **Background Processing**: Non-blocking video generation with progress tracking

## Getting Started

### Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Running the Application

Run the interactive TUI:

```bash
python vidgen.py
```

Or directly:

```bash
python -m cli.app
```

## Usage

### Main Screen

The main screen provides:

1. **PDF Selection**
   - Enter path manually or use the Browse button
   - File browser filters to show only PDF files

2. **Output Configuration**
   - Specify custom output path (optional)
   - Default: `output/<pdf_name>_<style>.mp4`

3. **Video Style Selection**
   - Slideshow: Classic slide-based presentation
   - Animated: Dynamic transitions and effects
   - AI Generated: Full AI-generated visuals
   - Combined: AI-selected mix of all styles

4. **Test Phases**
   - Test Phase 1: PDF parsing and text extraction
   - Test Phase 2: Image extraction and AI labeling
   - Test Phase 3: Content analysis and segmentation
   - Test Phase 4: Script generation and voiceover

5. **Generate Video**
   - Run the complete pipeline to generate your video

### Keyboard Shortcuts

- `q` - Quit application
- `d` - Toggle dark mode
- `h` - Show help (coming soon)

### Activity Log

The right panel shows real-time logs:
- Status updates
- Progress information
- Error messages
- Success notifications

## Architecture

```
cli/
├── __init__.py          # Package initialization
├── app.py               # Main Textual application
├── utils.py             # Helper functions (phases 1-4, video generation)
├── screens/             # Application screens
│   ├── __init__.py
│   ├── main_screen.py   # Main interface
│   ├── progress_screen.py  # Progress tracking
│   └── file_browser.py  # PDF file browser
└── widgets/             # Custom widgets
    ├── __init__.py
    └── log_viewer.py    # Log display widget
```

## Configuration

The CLI uses the same `config.yaml` and `.env` files as the rest of the application:

- **config.yaml**: Video generation settings, segment duration, etc.
- **.env**: API keys (OpenAI, ElevenLabs, Unsplash, Pexels)

## Development

### Running in Development Mode

```bash
# With textual dev console
textual console

# In another terminal
python vidgen.py
```

This will show the Textual dev console with debugging information.

### Hot Reload

```bash
textual run --dev cli/app.py:VidGenApp
```

## Features in Detail

### Phase Testing

Test individual phases before running the full pipeline:

1. **Phase 1**: Verify PDF can be parsed correctly
2. **Phase 2**: Check image extraction and AI labeling
3. **Phase 3**: Review content segmentation and outline
4. **Phase 4**: Test script generation and voiceover

### Background Processing

Long-running tasks (video generation, tests) run in background workers:
- UI remains responsive
- Progress updates in real-time
- Can be cancelled (coming soon)

### File Browser

Specialized directory tree:
- Shows only directories and PDF files
- Navigate with keyboard or mouse
- Select and confirm with buttons

## Troubleshooting

### API Key Issues

If you see errors about missing API keys:
1. Copy `.env.example` to `.env`
2. Add your API keys
3. Restart the application

### Import Errors

Make sure you're running from the project root:
```bash
cd /path/to/vidgen
python vidgen.py
```

### Textual Issues

Update to the latest version:
```bash
pip install --upgrade textual textual-dev
```

## Future Enhancements

- [ ] Progress bars for each phase
- [ ] Configuration editor screen
- [ ] Video preview
- [ ] Batch processing
- [ ] Template management
- [ ] Export/import settings
- [ ] Help screen with keyboard shortcuts
- [ ] Video player integration

## Support

For issues and questions:
- Check the main README.md
- Review logs in `temp/vidgen.log`
- Check the Textual documentation: https://textual.textualize.io/


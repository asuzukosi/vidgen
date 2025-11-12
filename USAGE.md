# VidGen Usage Guide

## Two Ways to Use VidGen

VidGen provides two interfaces:

1. **Interactive TUI** - Beautiful terminal interface (recommended for interactive use)
2. **Command Line** - Traditional CLI (recommended for automation/scripting)

---

## 🎨 Interactive Terminal UI

### Launch

```bash
python vidgen.py
```

### Features

- **Visual PDF Browser**: Navigate and select files visually
- **Configuration Panel**: Set all options in one place
- **Test Phases**: Click buttons to test individual phases
- **Real-time Logs**: Watch progress as it happens
- **Status Updates**: Clear feedback on what's happening

### Workflow

1. **Select PDF**
   - Click "Browse Files" button
   - Navigate through directories
   - Select your PDF file
   - Or type/paste path directly

2. **Configure Settings**
   - Set output path (optional)
   - Choose video style from dropdown
   - All options visible at once

3. **Test or Generate**
   - **Test buttons**: Verify each phase works
   - **Generate button**: Create full video
   - Monitor in activity log

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit application |
| `d` | Toggle dark/light mode |
| `Tab` | Navigate between elements |
| `Enter` | Activate button |
| `↑↓` | Navigate in browser |

### When to Use TUI

- ✅ Interactive video creation
- ✅ Testing and debugging
- ✅ Learning the tool
- ✅ One-off video generation
- ✅ Visual feedback preferred

---

## 💻 Command Line Interface

### Basic Usage

```bash
python script.py <pdf_file> [options]
```

### Generate Videos

```bash
# Combined style (recommended)
python script.py document.pdf --style combined

# Specific output path
python script.py document.pdf --style slideshow -o output/my_video.mp4

# Different styles
python script.py document.pdf --style animated
python script.py document.pdf --style ai_generated
```

### Test Individual Phases

```bash
# Phase 1: PDF parsing
python script.py document.pdf --test-parser

# Phase 2: Image extraction and labeling
python script.py document.pdf --test-images

# Phase 3: Content analysis
python script.py document.pdf --test-content

# Phase 4: Script generation and voiceover
python script.py document.pdf --test-script
```

### Command Line Options

```
positional arguments:
  pdf                   Path to the PDF file

optional arguments:
  -h, --help            Show help message
  -o, --output PATH     Output video file path
  -s, --style STYLE     Video style (slideshow/animated/ai_generated/combined)
  --test-parser         Test Phase 1: PDF parsing
  --test-images         Test Phase 2: Image extraction
  --test-content        Test Phase 3: Content analysis
  --test-script         Test Phase 4: Script generation
  --config PATH         Path to configuration file
```

### Examples

**Generate combined style video:**
```bash
python script.py research_paper.pdf --style combined -o research_video.mp4
```

**Test all phases sequentially:**
```bash
python script.py report.pdf --test-parser
python script.py report.pdf --test-images
python script.py report.pdf --test-content
python script.py report.pdf --test-script
```

**Generate with custom config:**
```bash
python script.py document.pdf --config my_config.yaml --style animated
```

### When to Use CLI

- ✅ Automation and scripting
- ✅ Batch processing
- ✅ CI/CD pipelines
- ✅ Remote/headless servers
- ✅ Integration with other tools

---

## 📊 Comparison

| Feature | TUI (`vidgen.py`) | CLI (`script.py`) |
|---------|-------------------|-------------------|
| **Interface** | Visual, interactive | Text-based commands |
| **Learning Curve** | Easy, self-explanatory | Requires learning flags |
| **Feedback** | Real-time, visual | Text output, logs |
| **File Selection** | Browse visually | Type path manually |
| **Best For** | Interactive use | Automation, scripting |
| **Progress** | Live updates | Log messages |
| **Errors** | Color-coded, clear | Text messages |

---

## 🎬 Video Styles

Both interfaces support the same four video styles:

### Combined (Recommended)
```bash
# TUI: Select "Combined" from dropdown
# CLI:
python script.py document.pdf --style combined
```
AI analyzes content and intelligently chooses the best style for each segment.

### Slideshow
```bash
python script.py document.pdf --style slideshow
```
Classic presentation style with text overlays and image displays.

### Animated
```bash
python script.py document.pdf --style animated
```
Motion graphics with dynamic effects, transitions, and animations.

### AI Generated
```bash
python script.py document.pdf --style ai_generated
```
Custom DALL-E images generated specifically for your content.

---

## 📂 Output Structure

Both interfaces produce the same output:

```
output/
└── <pdf_name>_<style>.mp4    # Your finished video

temp/
├── video_outline.json         # Video structure
├── video_script.json          # Generated scripts
├── script_with_audio.json     # Scripts with audio
├── full_voiceover.mp3         # Complete audio track
├── images/                    # Extracted PDF images
├── stock_images/              # Downloaded stock images
└── audio/                     # Individual segment audio
```

---

## 🔧 Configuration

Both interfaces use the same configuration files:

### config.yaml
Edit to customize:
- Video resolution and FPS
- Segment duration
- Animation effects
- Stock image preferences
- Output settings

### .env
Set your API keys:
```bash
OPENAI_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here
UNSPLASH_ACCESS_KEY=your_key_here
PEXELS_API_KEY=your_key_here
```

---

## 🚀 Quick Start Examples

### Interactive Session (TUI)

```bash
# Launch the app
python vidgen.py

# In the UI:
# 1. Click "Browse Files"
# 2. Navigate to your PDF
# 3. Select "Combined" style
# 4. Click "Generate Full Video"
# 5. Watch progress in real-time
```

### Automated Pipeline (CLI)

```bash
# Test pipeline
python script.py document.pdf --test-parser
python script.py document.pdf --test-images
python script.py document.pdf --test-content
python script.py document.pdf --test-script

# Generate video
python script.py document.pdf --style combined -o output/final.mp4
```

### Batch Processing (CLI)

```bash
#!/bin/bash
# Process multiple PDFs
for pdf in pdfs/*.pdf; do
    python script.py "$pdf" --style combined
done
```

---

## 💡 Tips

1. **Start with Tests**: Run test phases before full generation
2. **Use Combined Style**: Generally produces best results
3. **Check Logs**: Review `temp/vidgen.log` for details
4. **Reuse Data**: Regenerating reuses intermediate files (faster)
5. **TUI for Learning**: Use interactive mode to understand the process
6. **CLI for Production**: Use command line for automated workflows

---

## 🆘 Troubleshooting

### TUI Not Working

```bash
# Update Textual
pip install --upgrade textual

# Check terminal compatibility
echo $TERM
```

### CLI Errors

```bash
# Check if script is executable
chmod +x script.py

# Run with python explicitly
python script.py document.pdf --help
```

### Both Interfaces

```bash
# Check API keys
cat .env

# Check configuration
cat config.yaml

# Review detailed logs
tail -f temp/vidgen.log
```

---

## 📚 More Information

- **[README.md](README.md)** - Project overview
- **[cli/README.md](cli/README.md)** - TUI documentation
- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide
- **[config.yaml](config.yaml)** - Configuration reference

---

**Choose the interface that works best for your workflow!** 🎬


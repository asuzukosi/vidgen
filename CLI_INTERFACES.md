# VidGen - Dual Interface System

VidGen now provides **two complementary interfaces** for maximum flexibility:

## 🎨 Interactive TUI (`vidgen.py`)

### Launch
```bash
python vidgen.py
```

### Best For
- Interactive video creation
- Learning the tool
- Visual feedback
- Testing individual phases
- One-off video generation

### Features
- Visual PDF file browser
- Real-time activity log
- Click buttons to test phases
- Progress monitoring
- Dark/light mode toggle

### Key Benefits
- No command-line flags to remember
- Visual feedback at every step
- Browse files interactively
- See all options at once
- Modern, beautiful interface

---

## 💻 Command Line (`script.py`)

### Launch
```bash
python script.py document.pdf [options]
```

### Best For
- Automation and scripting
- Batch processing
- CI/CD pipelines
- Remote/headless servers
- Integration with other tools

### Features
- Traditional CLI with argparse
- All functionality via flags
- Scriptable and automatable
- Works in any environment
- Perfect for cron jobs

### Key Benefits
- Easy to script
- Works without display
- Can be automated
- Standard CLI conventions
- Pipe-friendly output

---

## Quick Comparison

| Feature | TUI (`vidgen.py`) | CLI (`script.py`) |
|---------|-------------------|-------------------|
| **Launch** | `python vidgen.py` | `python script.py file.pdf` |
| **File Selection** | Visual browser | Command argument |
| **Progress** | Real-time UI | Log messages |
| **Automation** | Manual only | Fully scriptable |
| **Learning Curve** | Intuitive | Requires docs |
| **Best Use** | Interactive | Automation |

---

## Examples

### Interactive TUI Workflow

```bash
# Launch the app
python vidgen.py

# Then in the UI:
# 1. Click "Browse Files"
# 2. Select your PDF
# 3. Choose style
# 4. Click "Generate Full Video"
# 5. Watch progress in real-time
```

### Command Line Workflow

```bash
# Test phases
python script.py document.pdf --test-parser
python script.py document.pdf --test-images
python script.py document.pdf --test-content
python script.py document.pdf --test-script

# Generate video
python script.py document.pdf --style combined -o output.mp4
```

### Automation Example

```bash
#!/bin/bash
# Batch process all PDFs in a directory

for pdf in pdfs/*.pdf; do
    echo "Processing $pdf..."
    python script.py "$pdf" --style combined
done
```

---

## CLI Options

```
usage: script.py [-h] [-o OUTPUT] [-s STYLE] [--test-parser] 
                 [--test-images] [--test-content] [--test-script]
                 [--config CONFIG] pdf

positional arguments:
  pdf                   path to the pdf file

optional arguments:
  -h, --help            show this help message and exit
  -o, --output OUTPUT   output video file path
  -s, --style STYLE     video style (slideshow, animated, ai_generated, combined)
  --test-parser         test pdf parsing only (phase 1)
  --test-images         test image extraction and labeling (phase 2)
  --test-content        test content analysis and segmentation (phase 3)
  --test-script         test script generation and voiceover (phase 4)
  --config CONFIG       path to configuration file
```

---

## Both Interfaces Share

✅ Same configuration files (`config.yaml`, `.env`)  
✅ Same output structure  
✅ Same video styles  
✅ Same intermediate files  
✅ Same core functionality  
✅ Same API integrations  

---

## When to Use Which

### Use TUI When:
- You're creating videos interactively
- You want visual feedback
- You're learning the tool
- You prefer clicking over typing
- You want to see logs in real-time

### Use CLI When:
- You're automating workflows
- You're batch processing files
- You're running on a server
- You're integrating with scripts
- You're using CI/CD pipelines

---

## Getting Started

### Installation
```bash
pip install -r requirements.txt
```

### Try the TUI
```bash
python vidgen.py
```

### Try the CLI
```bash
python script.py --help
python script.py your-document.pdf --style combined
```

---

**Both interfaces are fully supported and maintained!**  
Choose the one that fits your workflow best. 🚀


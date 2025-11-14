# PDF to Video Generator

A powerful tool to convert PDF documents into professional explainer videos with multiple visual styles.

## Project Status

**🎉 ALL PHASES COMPLETE! Full System Ready ✅**

The complete PDF-to-Video system is fully functional! You can now convert any PDF into professional explainer videos with three distinct visual styles.

### ✅ All Features Implemented
- ✅ **Phase 1:** PDF text extraction with intelligent structure detection
- ✅ **Phase 2:** Image extraction from PDFs with AI-powered labeling (GPT-4 Vision)
- ✅ **Phase 3:** Content analysis, video segmentation, and stock image integration
- ✅ **Phase 4:** Natural script generation and professional voiceover (ElevenLabs/gTTS)
- ✅ **Phase 5:** Slideshow video generator with text overlays and transitions
- ✅ **Phase 6:** Animated motion graphics with dynamic effects
- ✅ **Phase 7:** AI-generated visuals using DALL-E for custom images
- ✅ **Phase 8:** Complete CLI pipeline integration with style selection
- ✅ **BONUS:** Combined style that uses AI to intelligently mix all styles per segment

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp env.example .env
```

4. Edit `.env` and add your API keys:
   - `OPENAI_API_KEY` - For content analysis and script generation
   - `ELEVENLABS_API_KEY` - For high-quality voiceover
   - `UNSPLASH_ACCESS_KEY` - For stock images (optional)
   - `PEXELS_API_KEY` - For stock images (optional)

## Usage

### 🎨 Interactive Terminal UI (Recommended)

Launch the beautiful, interactive terminal application:

```bash
python vidgen.py
```

The TUI provides:
- 📁 Interactive PDF file browser
- 🎬 Multiple video style selection
- 🧪 Individual phase testing
- 📋 Real-time activity log
- ⚡ Background processing

**Features:**
- Browse and select PDF files visually
- Configure output settings interactively
- Run individual test phases with a button click
- Monitor progress in real-time
- Beautiful, modern interface built with [Textual](https://github.com/Textualize/textual)

**Keyboard Shortcuts:**
- `q` - Quit application
- `d` - Toggle dark mode

See [cli/README.md](cli/README.md) for detailed CLI documentation.

### 💻 Command Line Interface

For automation and scripting, use the traditional CLI:

```bash
# Test individual phases
python script.py document.pdf --test-parser
python script.py document.pdf --test-images
python script.py document.pdf --test-content
python script.py document.pdf --test-script

# Generate videos with different styles
python script.py document.pdf --style combined -o output.mp4
python script.py document.pdf --style slideshow
python script.py document.pdf --style animated
python script.py document.pdf --style ai_generated
```

### 🎬 Video Generation

**Using the TUI:**
1. Launch `python vidgen.py`
2. Select your PDF file
3. Choose video style (slideshow, animated, ai_generated, or combined)
4. Click "Generate Full Video"
5. Monitor progress in real-time

**Using the CLI:**
```bash
python script.py document.pdf --style combined -o output/my_video.mp4
```

**Video Styles:**
- **Combined** (RECOMMENDED): AI intelligently mixes all styles per segment
- **Slideshow**: Presentation-style with text overlays
- **Animated**: Motion graphics with dynamic effects
- **AI Generated**: Custom DALL-E images for each segment

**Default output:** Videos are saved to `output/<pdf_name>_<style>.mp4`

### 📦 What You Get:
- 🎥 **Complete MP4 video** ready to share
- 📄 Structured PDF content (`temp/video_outline.json`)
- 🖼️ Extracted and labeled images (`temp/images/`)
- 📝 Complete video script (`temp/video_script.txt`)
- 🎙️ Professional voiceover audio (`temp/full_voiceover.mp3`)
- 📊 Detailed metadata for every step

## Configuration

Edit `config.yaml` to customize:

- **Video settings**: Resolution, FPS, default style
- **Content settings**: Target segments, segment duration
- **Voiceover settings**: Provider, voice ID, model
- **Image settings**: Stock image preferences
- **Style-specific settings**: Transitions, animations, effects
- **Output settings**: Directories, codecs

## Project Structure

```
vidgen/
├── core/                    # Core pipeline modules
│   ├── pdf_parser.py       # PDF text extraction ✓
│   ├── config_loader.py    # Configuration management ✓
│   ├── image_extractor.py  # Image extraction (Phase 2)
│   ├── image_labeler.py    # AI image labeling (Phase 2)
│   ├── content_analyzer.py # Content segmentation (Phase 3)
│   ├── script_generator.py # Script generation (Phase 4)
│   └── voiceover_generator.py # Audio generation (Phase 4)
│
├── cli/                     # Terminal User Interface ✓
│   ├── app.py              # Main Textual application
│   ├── utils.py            # Core utility functions
│   ├── screens/            # Application screens
│   │   ├── main_screen.py  # Main interface
│   │   ├── progress_screen.py # Progress tracking
│   │   └── file_browser.py # PDF file browser
│   └── widgets/            # Custom UI widgets
│       └── log_viewer.py   # Log display widget
│
├── styles/                  # Video style generators
│   ├── slideshow.py        # Slideshow style (Phase 5)
│   ├── animated.py         # Animated style (Phase 6)
│   ├── ai_generated.py     # AI visuals style (Phase 7)
│   └── combined.py         # Combined style (BONUS)
│
├── output/                  # Generated videos
├── temp/                    # Temporary files
├── vidgen.py               # TUI entry point ✓
├── script.py               # CLI entry point ✓
├── test_stage1_parsing.py  # Test Stage 1 independently
├── test_stage2_images.py   # Test Stage 2 independently
├── test_stage3_content.py  # Test Stage 3 independently
├── test_stage4_script.py   # Test Stage 4 independently
├── test_stage5_video.py    # Test Stage 5 (all styles)
├── TEST_STAGES_README.md   # Stage testing documentation
├── config.yaml             # Configuration file ✓
├── requirements.txt        # Python dependencies ✓
└── README.md              # This file ✓
```

## Tech Stack

### Paid APIs
- **OpenAI API (GPT-4)** - Content analysis, script generation, image labeling
- **ElevenLabs API** - Professional text-to-speech voiceover
- **Unsplash API** - High-quality stock images (free tier)
- **Pexels API** - Additional stock images (free tier)

### Open-Source Libraries
- **Textual** - Modern terminal user interface framework
- **pdfplumber** - PDF text extraction
- **PyMuPDF** - Advanced PDF processing
- **pdf2image** - PDF image extraction
- **moviepy** - Video composition and rendering
- **Pillow** - Image manipulation
- **gTTS** - Free text-to-speech fallback
- **python-dotenv** - Environment variable management
- **PyYAML** - Configuration management

## Development Progress

### Phase 1: Project Setup & PDF Text Extraction ✅
- [x] Create project structure
- [x] Set up requirements.txt and configuration system
- [x] Implement PDF text extraction with pdfplumber
- [x] Intelligent section detection with heading hierarchy
- [x] Create CLI framework
- [x] Metadata extraction (title, pages, structure)

### Phase 2: Image Extraction & AI Labeling ✅
- [x] Extract images from PDFs with PyMuPDF
- [x] Filter out small icons and decorations
- [x] Implement OpenAI Vision API integration (GPT-4 Vision)
- [x] Auto-label extracted images with descriptions
- [x] Store comprehensive image metadata
- [x] Extract text context from PDF pages

### Phase 3: Content Analysis & Segmentation ✅
- [x] AI-powered content analysis with GPT-4
- [x] Intelligent video segmentation (5-10 segments per video)
- [x] Semantic image-to-segment matching
- [x] Stock image integration (Unsplash & Pexels APIs)
- [x] Generate structured video outline
- [x] Visual keyword extraction

### Phase 4: Script Generation & Voiceover ✅
- [x] Natural language script generation
- [x] Conversational narration for each segment
- [x] ElevenLabs integration for premium voiceover
- [x] gTTS fallback for free alternative
- [x] Individual and combined audio file generation
- [x] Audio timing and duration metadata
- [x] Export scripts as JSON and plain text

### Phase 5: Slideshow Video Generator ✅
- [x] Video composition with moviepy
- [x] Slide templates with gradient backgrounds
- [x] Text overlay synchronization with voiceover
- [x] Image display (PDF + stock images)
- [x] Smooth crossfade transitions between segments
- [x] Professional title and end cards

### Phase 6: Animated Motion Graphics ✅
- [x] Animated text (fade in, slide effects)
- [x] Shape animations (underlines, accents)
- [x] Camera movements (zoom, pan on background)
- [x] Ken Burns effect on images
- [x] Staggered animations for visual interest
- [x] Dynamic composition with multiple layers

### Phase 7: AI-Generated Visuals ✅
- [x] DALL-E integration for custom image generation
- [x] Intelligent prompt engineering from content
- [x] Ken Burns effect on generated images
- [x] Text overlays with AI-generated backgrounds
- [x] Unique visuals created for each segment

### Phase 8: CLI & Pipeline Integration ✅
- [x] Complete end-to-end pipeline orchestration
- [x] Style selection system (4 styles)
- [x] Progress tracking and logging
- [x] Error handling and recovery
- [x] Automatic intermediate file caching
- [x] Beautiful Terminal UI with Textual
- [x] Interactive PDF file browser
- [x] Real-time log viewer
- [x] Background task processing

## Testing the System

### Prerequisites for Testing
1. Install dependencies: `pip install -r requirements.txt`
2. Set up your `.env` file with API keys:
   - `OPENAI_API_KEY` (required for Phases 2-4)
   - `ELEVENLABS_API_KEY` (optional, will fallback to gTTS)
   - `UNSPLASH_ACCESS_KEY` (optional, for stock images)

### 🧪 Test Each Stage Independently (NEW!)

**Comprehensive stage testing scripts** let you test and evaluate each stage independently with full control:

```bash
# Stage 1: PDF Parsing
python test_stage1_parsing.py document.pdf

# Stage 2: Image Extraction & AI Labeling
python test_stage2_images.py document.pdf [--use-cached]

# Stage 3: Content Analysis & Segmentation
python test_stage3_content.py document.pdf [--use-cached] [--skip-stock]

# Stage 4: Script Generation & Voiceover
python test_stage4_script.py document.pdf [--use-cached] [--provider elevenlabs|gtts]

# Stage 5: Video Generation (all styles)
python test_stage5_video.py document.pdf --style slideshow|animated|ai_generated|combined
```

**Features:**
- 📋 Detailed explanations of each stage's approach at the top of each file
- 🔄 Option to use cached results from previous stages (`--use-cached`)
- 📊 Comprehensive console output showing results and statistics
- 💾 Saves intermediate files for inspection and next stage
- 🎬 Test all video styles independently (Stage 5)

**See [TEST_STAGES_README.md](TEST_STAGES_README.md) for complete documentation!**

### Test Each Phase (Quick Tests)

**Using the TUI:**
```bash
python vidgen.py
```
1. Select a PDF file using the Browse button or enter path manually
2. Click the respective test button
3. Monitor results in the real-time activity log panel

**Using the CLI:**
```bash
python script.py sample.pdf --test-parser      # Phase 1: PDF parsing
python script.py sample.pdf --test-images      # Phase 2: Image extraction
python script.py sample.pdf --test-content     # Phase 3: Content analysis
python script.py sample.pdf --test-script      # Phase 4: Script & voiceover
```

### Output Files

After running the tests, check the `temp/` directory:
```
temp/
├── video_outline.json          # Video structure
├── video_script.json           # Generated scripts
├── video_script.txt            # Readable script
├── script_with_audio.json      # Script + audio metadata
├── full_voiceover.mp3          # Complete audio track
├── images/                     # Extracted PDF images
│   └── images_metadata_labeled.json
├── stock_images/               # Downloaded stock images
└── audio/                      # Individual segment audio files
    ├── segment_01_Introduction.mp3
    ├── segment_02_...
    └── ...
```

## Contributing

This project is being built phase-by-phase. Each phase builds upon the previous one, creating a complete end-to-end pipeline.

## License

MIT License

## Documentation

📚 **Detailed guides and documentation:**

- **[README.md](README.md)** - This file - quick start guide and overview

- **[TEST_STAGES_README.md](TEST_STAGES_README.md)** - 🧪 **NEW!** Complete guide to testing each stage independently with full control

- **[COMBINED_STYLE.md](.claude_docs/COMBINED_STYLE.md)** - Complete guide to the AI-powered combined style (RECOMMENDED!)

- **[TUTORIAL.md](.claude_docs/TUTORIAL.md)** - Comprehensive step-by-step tutorial explaining how each phase was built, key concepts, implementation details, and best practices

- **[SETUP_GUIDE.md](.claude_docs/SETUP_GUIDE.md)** - Detailed setup instructions with API key guides and troubleshooting

- **[COMPLETE.md](.claude_docs/COMPLETE.md)** - Complete system overview, all features, usage examples

- **[LOGGER_USAGE.md](.claude_docs/LOGGER_USAGE.md)** - How to use the centralized logging system

**Additional documentation:**
- **[PROGRESS.md](.claude_docs/PROGRESS.md)** - Project status and development progress
- **[SUMMARY.md](.claude_docs/SUMMARY.md)** - Implementation summary and statistics
- **[BONUS_FEATURE.md](.claude_docs/BONUS_FEATURE.md)** - Details about the combined style feature

### Learning Resources

The tutorial walks through:
- **Phase 1:** PDF parsing and structure detection techniques
- **Phase 2:** Image extraction and AI vision integration  
- **Phase 3:** Content analysis and semantic matching algorithms
- **Phase 4:** Script generation and text-to-speech integration
- **Phases 5-8:** Video generation (coming soon)

---

## Support

For issues, questions, or contributions, please refer to the project documentation.

**Note**: This is an active development project. Phases 1-4 are complete. Video generation (Phases 5-7) and final integration (Phase 8) are in progress.


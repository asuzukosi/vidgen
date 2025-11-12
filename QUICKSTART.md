# VidGen Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs all required packages including the new Textual UI framework.

### Step 2: Configure API Keys

Copy the example environment file:

```bash
cp env.example .env
```

Edit `.env` and add your API keys:

```bash
# Required for content analysis, script generation, and image labeling
OPENAI_API_KEY=your_openai_api_key_here

# Optional: For high-quality voiceover (will fallback to gTTS if not provided)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Optional: For stock images
UNSPLASH_ACCESS_KEY=your_unsplash_key_here
PEXELS_API_KEY=your_pexels_key_here
```

### Step 3: Launch the Application

```bash
python vidgen.py
```

## 🎨 Using the Terminal UI

### Main Interface

When you launch VidGen, you'll see:

**Left Panel - Configuration:**
- PDF file selection (browse or enter path)
- Output path (optional)
- Video style selector
- Test phase buttons
- Generate video button

**Right Panel - Activity Log:**
- Real-time progress updates
- Status messages
- Error notifications

### Selecting a PDF

**Option 1: Browse**
1. Click the "Browse Files" button
2. Navigate through directories
3. Select your PDF file
4. Click "Select"

**Option 2: Manual Entry**
- Type or paste the PDF file path directly into the input field

### Testing Individual Phases

Before generating a full video, test each phase:

1. **Phase 1 - Parser**: Test PDF text extraction
2. **Phase 2 - Images**: Test image extraction and AI labeling
3. **Phase 3 - Content**: Test content analysis and segmentation
4. **Phase 4 - Script**: Test script generation and voiceover

Results appear in the activity log in real-time.

### Generating a Video

1. Select your PDF file
2. Choose a video style:
   - **Combined** (Recommended): AI mixes all styles intelligently
   - **Slideshow**: Presentation with text overlays
   - **Animated**: Motion graphics with effects
   - **AI Generated**: DALL-E generated visuals
3. Optionally set output path
4. Click "Generate Full Video"
5. Monitor progress in the log viewer

### Keyboard Shortcuts

- `q` - Quit application
- `d` - Toggle dark/light mode
- `Tab` - Navigate between elements
- `Enter` - Activate buttons

## 📦 Output Files

After generation, you'll find:

**Main Output:**
- `output/<pdf_name>_<style>.mp4` - Your finished video

**Intermediate Files in `temp/`:**
- `video_outline.json` - Video structure
- `video_script.json` - Generated scripts
- `script_with_audio.json` - Scripts with audio metadata
- `full_voiceover.mp3` - Complete audio track
- `images/` - Extracted PDF images with labels
- `stock_images/` - Downloaded stock images
- `audio/` - Individual segment audio files

## 🛠️ Troubleshooting

### "OpenAI API key not found"
Make sure your `.env` file exists and contains `OPENAI_API_KEY=...`

### "PDF file not found"
- Check the file path is correct
- Use absolute paths if relative paths don't work
- Make sure the file exists and is readable

### UI looks broken
Update Textual to the latest version:
```bash
pip install --upgrade textual
```

### Video generation fails
1. Check all required API keys are set
2. Review the activity log for specific errors
3. Check `temp/vidgen.log` for detailed logs
4. Ensure sufficient disk space in `output/` and `temp/`

## 💡 Tips

1. **Test First**: Run test phases before full generation
2. **Reuse Data**: If you regenerate with the same PDF, intermediate files are reused
3. **Check Logs**: The activity log shows detailed progress
4. **Try Styles**: Experiment with different video styles
5. **Combined Style**: For best results, use the "Combined" style

## 📚 Learn More

- **[README.md](README.md)** - Complete project overview
- **[cli/README.md](cli/README.md)** - Detailed CLI documentation
- **[config.yaml](config.yaml)** - Configuration options

## 🎉 Example Workflow

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp env.example .env
# Edit .env with your API keys

# 3. Launch
python vidgen.py

# 4. In the UI:
#    - Browse and select your PDF
#    - Choose "Combined" style
#    - Click "Generate Full Video"
#    - Watch the magic happen! ✨

# 5. Find your video in output/
```

## ⚡ Advanced Usage

### Development Mode

Run with Textual dev console for debugging:

```bash
# Terminal 1
textual console

# Terminal 2
python vidgen.py
```

### Custom Configuration

Edit `config.yaml` to customize:
- Video resolution and FPS
- Segment duration
- Voiceover settings
- Animation effects
- Stock image preferences

## 🆘 Need Help?

1. Check the activity log in the UI
2. Review `temp/vidgen.log` for detailed logs
3. Consult the documentation in the repo
4. Verify all dependencies are installed

---

**Happy video generation! 🎬**


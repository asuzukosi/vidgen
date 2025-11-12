"""
Main Screen - Primary interface for VidGen
"""

import os
from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Button, Input, Select, Static, Label,
    DirectoryTree, RichLog, Checkbox
)
from textual.reactive import reactive
from textual import on


class MainScreen(Screen):
    """Main screen for PDF to Video generation."""
    
    CSS = """
    MainScreen {
        background: $surface;
    }
    
    #main-container {
        height: 100%;
        padding: 1;
    }
    
    #left-panel {
        width: 40%;
        border: solid $primary;
        padding: 1;
    }
    
    #right-panel {
        width: 60%;
        border: solid $accent;
        padding: 1;
        margin-left: 1;
    }
    
    .section-title {
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .input-group {
        margin-bottom: 1;
    }
    
    .button-group {
        margin-top: 1;
        height: auto;
    }
    
    Button {
        margin-right: 1;
        margin-bottom: 1;
    }
    
    #status-box {
        border: solid $success;
        padding: 1;
        margin-top: 1;
        height: auto;
    }
    
    #log-viewer {
        height: 100%;
        border: solid $primary;
    }
    
    Input {
        margin-bottom: 1;
    }
    
    Select {
        margin-bottom: 1;
    }
    """
    
    selected_pdf = reactive("")
    current_style = reactive("slideshow")
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        
        with Container(id="main-container"):
            with Horizontal():
                # Left panel - Configuration
                with Vertical(id="left-panel"):
                    yield Static("📄 PDF to Video Generator", classes="section-title")
                    
                    # PDF Selection
                    with Vertical(classes="input-group"):
                        yield Label("PDF File:")
                        yield Input(
                            placeholder="Path to PDF file or browse...",
                            id="pdf-input"
                        )
                        yield Button("Browse Files", id="browse-btn", variant="primary")
                    
                    # Output Path
                    with Vertical(classes="input-group"):
                        yield Label("Output Path (optional):")
                        yield Input(
                            placeholder="output/video.mp4",
                            id="output-input"
                        )
                    
                    # Video Style
                    with Vertical(classes="input-group"):
                        yield Label("Video Style:")
                        yield Select(
                            [
                                ("Slideshow", "slideshow"),
                                ("Animated", "animated"),
                                ("AI Generated", "ai_generated"),
                                ("Combined (AI-Mixed)", "combined")
                            ],
                            value="slideshow",
                            id="style-select"
                        )
                    
                    # Test Options
                    yield Static("🧪 Test Phases", classes="section-title")
                    with Vertical(classes="button-group"):
                        yield Button("Test Phase 1: Parser", id="test-phase1", variant="default")
                        yield Button("Test Phase 2: Images", id="test-phase2", variant="default")
                        yield Button("Test Phase 3: Content", id="test-phase3", variant="default")
                        yield Button("Test Phase 4: Script", id="test-phase4", variant="default")
                    
                    # Generate Button
                    yield Static("🎬 Generate Video", classes="section-title")
                    yield Button("Generate Full Video", id="generate-btn", variant="success")
                    
                    # Status Box
                    with Container(id="status-box"):
                        yield Static("Ready", id="status-text")
                
                # Right panel - Logs
                with Vertical(id="right-panel"):
                    yield Static("📋 Activity Log", classes="section-title")
                    yield RichLog(id="log-viewer", wrap=True, highlight=True, markup=True)
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the screen."""
        log_viewer = self.query_one("#log-viewer", RichLog)
        log_viewer.write("🚀 VidGen CLI Started")
        log_viewer.write("Welcome to the PDF to Video Generator!")
        log_viewer.write("Select a PDF file to get started.\n")
    
    @on(Button.Pressed, "#browse-btn")
    def show_file_browser(self) -> None:
        """Show file browser for PDF selection."""
        self.app.push_screen("file_browser")
    
    @on(Button.Pressed, "#test-phase1")
    def test_phase1(self) -> None:
        """Run Phase 1 test."""
        self.run_test("phase1")
    
    @on(Button.Pressed, "#test-phase2")
    def test_phase2(self) -> None:
        """Run Phase 2 test."""
        self.run_test("phase2")
    
    @on(Button.Pressed, "#test-phase3")
    def test_phase3(self) -> None:
        """Run Phase 3 test."""
        self.run_test("phase3")
    
    @on(Button.Pressed, "#test-phase4")
    def test_phase4(self) -> None:
        """Run Phase 4 test."""
        self.run_test("phase4")
    
    @on(Button.Pressed, "#generate-btn")
    def generate_video(self) -> None:
        """Generate full video."""
        pdf_input = self.query_one("#pdf-input", Input)
        output_input = self.query_one("#output-input", Input)
        style_select = self.query_one("#style-select", Select)
        
        pdf_path = pdf_input.value.strip()
        output_path = output_input.value.strip() or None
        style = str(style_select.value)
        
        if not pdf_path:
            self.update_status("❌ Please select a PDF file", "error")
            self.log("Error: No PDF file selected", "red")
            return
        
        if not os.path.exists(pdf_path):
            self.update_status(f"❌ PDF file not found: {pdf_path}", "error")
            self.log(f"Error: PDF file not found: {pdf_path}", "red")
            return
        
        self.update_status(f"🎬 Generating {style} video...", "working")
        self.log(f"\n{'='*60}", "cyan")
        self.log(f"Starting full video generation", "cyan")
        self.log(f"PDF: {pdf_path}", "cyan")
        self.log(f"Style: {style}", "cyan")
        self.log(f"{'='*60}\n", "cyan")
        
        # Switch to progress screen
        self.app.push_screen(
            "progress",
            callback=lambda result: self.on_generation_complete(result)
        )
        
        # Start generation in background
        self.app.run_worker(
            self._generate_video_worker(pdf_path, style, output_path),
            name="generate_video"
        )
    
    async def _generate_video_worker(self, pdf_path: str, style: str, output_path: str):
        """Worker to generate video in background."""
        from core.config_loader import get_config
        from cli.utils import generate_full_video
        
        config = get_config()
        config.ensure_directories()
        
        # Determine output path
        if not output_path:
            output_dir = config.get('output.directory', 'output')
            pdf_name = Path(pdf_path).stem
            output_path = os.path.join(output_dir, f"{pdf_name}_{style}.mp4")
        
        success = generate_full_video(pdf_path, style, output_path, config)
        
        return {
            'success': success,
            'output_path': output_path,
            'style': style
        }
    
    def on_generation_complete(self, result: dict) -> None:
        """Handle completion of video generation."""
        if result['success']:
            self.update_status("✅ Video generation complete!", "success")
            self.log(f"\n🎉 SUCCESS! Video ready at: {result['output_path']}", "green bold")
        else:
            self.update_status("❌ Video generation failed", "error")
            self.log("\n❌ Video generation failed. Check logs for details.", "red bold")
    
    def run_test(self, phase: str) -> None:
        """Run a test phase."""
        pdf_input = self.query_one("#pdf-input", Input)
        pdf_path = pdf_input.value.strip()
        
        if not pdf_path:
            self.update_status("❌ Please select a PDF file", "error")
            self.log("Error: No PDF file selected", "red")
            return
        
        if not os.path.exists(pdf_path):
            self.update_status(f"❌ PDF file not found: {pdf_path}", "error")
            self.log(f"Error: PDF file not found: {pdf_path}", "red")
            return
        
        self.update_status(f"🧪 Running {phase.upper()} test...", "working")
        self.log(f"\n{'='*60}", "yellow")
        self.log(f"Starting {phase.upper()} test", "yellow")
        self.log(f"PDF: {pdf_path}", "yellow")
        self.log(f"{'='*60}\n", "yellow")
        
        # Run test in background
        self.app.run_worker(
            self._run_test_worker(pdf_path, phase),
            name=f"test_{phase}"
        )
    
    async def _run_test_worker(self, pdf_path: str, phase: str):
        """Worker to run test in background."""
        from core.config_loader import get_config
        from cli.utils import test_phase1, test_phase2, test_phase3, test_phase4
        
        config = get_config()
        config.ensure_directories()
        
        if phase == "phase1":
            success = test_phase1(pdf_path)
        elif phase == "phase2":
            success = test_phase2(pdf_path, config)
        elif phase == "phase3":
            success = test_phase3(pdf_path, config)
        elif phase == "phase4":
            success = test_phase4(pdf_path, config)
        else:
            success = False
        
        return {'success': success, 'phase': phase}
    
    def update_status(self, message: str, status_type: str = "info") -> None:
        """Update the status text."""
        status_text = self.query_one("#status-text", Static)
        status_text.update(message)
    
    def log(self, message: str, style: str = "") -> None:
        """Add a log message."""
        log_viewer = self.query_one("#log-viewer", RichLog)
        if style:
            log_viewer.write(f"[{style}]{message}[/{style}]")
        else:
            log_viewer.write(message)


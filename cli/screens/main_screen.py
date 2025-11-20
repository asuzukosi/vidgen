"""
main screen - primary interface for vidgen
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
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
    """main screen for pdf to video generation."""
    
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
    
    def compose(self) -> ComposeResult:
        """create child widgets."""
        yield Header()
        
        with Container(id="main-container"):
            with Horizontal():
                # Left panel - Configuration
                with Vertical(id="left-panel"):
                    yield Static("PDF to Video Generator", classes="section-title")
                    
                    # PDF Selection
                    with Vertical(classes="input-group"):
                        yield Label("PDF File:")
                        yield Input(
                            placeholder="Path to PDF file or browse...",
                            id="pdf-input"
                        )
                        yield Button("Browse Files", id="browse-btn", variant="primary")
                    
                    # output path
                    with Vertical(classes="input-group"):
                        yield Label("Output Path (optional):")
                        yield Input(
                            placeholder="output/video.mp4",
                            id="output-input"
                        )
                    
                    # operations
                    yield Static("operations", classes="section-title")
                    with Vertical(classes="button-group"):
                        yield Button("Parse Document", id="parse-doc", variant="default")
                        yield Button("Extract Images", id="extract-images", variant="default")
                        yield Button("Analyze Content", id="analyze-content", variant="default")
                        yield Button("Generate Script", id="generate-script", variant="default")
                    
                    # Generate Button
                    yield Static("Generate Video", classes="section-title")
                    yield Button("Generate Full Video", id="generate-btn", variant="success")
                    
                    # Status Box
                    with Container(id="status-box"):
                        yield Static("Ready", id="status-text")
                
                # Right panel - Logs
                with Vertical(id="right-panel"):
                    yield Static("Activity Log", classes="section-title")
                    yield RichLog(id="log-viewer", wrap=True, highlight=True, markup=True)
        
        yield Footer()
    
    def on_mount(self) -> None:
        """initialize the screen."""
        log_viewer = self.query_one("#log-viewer", RichLog)
        log_viewer.write("VidGen CLI Started")
        log_viewer.write("Welcome to the PDF to Video Generator!")
        log_viewer.write("Select a PDF file to get started.\n")
    
    @on(Button.Pressed, "#browse-btn")
    def show_file_browser(self) -> None:
        """show file browser for pdf selection."""
        self.app.push_screen("file_browser")
    
    @on(Button.Pressed, "#parse-doc")
    def parse_document(self) -> None:
        """parse document operation."""
        self.run_operation("parse_document")
    
    @on(Button.Pressed, "#extract-images")
    def extract_images(self) -> None:
        """extract images operation."""
        self.run_operation("extract_images")
    
    @on(Button.Pressed, "#analyze-content")
    def analyze_content(self) -> None:
        """analyze content operation."""
        self.run_operation("analyze_content")
    
    @on(Button.Pressed, "#generate-script")
    def generate_script(self) -> None:
        """generate script operation."""
        self.run_operation("generate_script")
    
    @on(Button.Pressed, "#generate-btn")
    def generate_video(self) -> None:
        """generate full video."""
        pdf_input = self.query_one("#pdf-input", Input)
        output_input = self.query_one("#output-input", Input)
        
        pdf_path = pdf_input.value.strip()
        output_path = output_input.value.strip() or None
        
        if not pdf_path:
            self.update_status("Please select a PDF file", "error")
            self.log("Error: No PDF file selected", "red")
            return
        
        if not os.path.exists(pdf_path):
            self.update_status(f"PDF file not found: {pdf_path}", "error")
            self.log(f"Error: PDF file not found: {pdf_path}", "red")
            return
        
        self.update_status("Generating video...", "working")
        self.log(f"\n{'='*60}", "cyan")
        self.log(f"Starting full video generation", "cyan")
        self.log(f"PDF: {pdf_path}", "cyan")
        self.log(f"{'='*60}\n", "cyan")
        
        # Switch to progress screen
        self.app.push_screen(
            "progress",
            callback=lambda result: self.on_generation_complete(result)
        )
        
        # Start generation in background
        self.app.run_worker(
            self._generate_video_worker(pdf_path, output_path),
            name="generate_video"
        )
    
    async def _generate_video_worker(self, pdf_path: str, output_path: Optional[str]) -> Dict[str, Any]:
        """worker to generate video in background."""
        from utils.config_loader import get_config
        from cli.utils import generate_full_video
        
        config = get_config()
        config.ensure_directories()
        
        # Determine output path
        if not output_path:
            output_dir = config.get('output.directory', 'output')
            pdf_name = Path(pdf_path).stem
            output_path = os.path.join(output_dir, f"{pdf_name}_slideshow.mp4")
        
        pipeline_data = generate_full_video(pdf_path, output_path, config)
        
        return {
            'success': pipeline_data.status == "completed" and pipeline_data.video_path is not None,
            'output_path': pipeline_data.video_path or output_path,
            'pipeline_id': pipeline_data.id
        }
    
    def on_generation_complete(self, result: Dict[str, Any]) -> None:
        """handle completion of video generation."""
        if result.get('success'):
            self.update_status("Video generation complete!", "success")
            self.log(f"\nSUCCESS! Video ready at: {result.get('output_path', 'unknown')}", "green bold")
            self.log(f"Pipeline ID: {result.get('pipeline_id', 'unknown')}", "green")
        else:
            self.update_status("Video generation failed", "error")
            self.log("\nVideo generation failed. Check logs for details.", "red bold")
    
    def run_operation(self, operation: str) -> None:
        """run an operation."""
        pdf_input = self.query_one("#pdf-input", Input)
        pdf_path = pdf_input.value.strip()
        
        if not pdf_path:
            self.update_status("Please select a PDF file", "error")
            self.log("Error: No PDF file selected", "red")
            return
        
        if not os.path.exists(pdf_path):
            self.update_status(f"PDF file not found: {pdf_path}", "error")
            self.log(f"Error: PDF file not found: {pdf_path}", "red")
            return
        
        operation_names = {
            "parse_document": "Parse Document",
            "extract_images": "Extract Images",
            "analyze_content": "Analyze Content",
            "generate_script": "Generate Script"
        }
        
        operation_name = operation_names.get(operation, operation)
        self.update_status(f"Running {operation_name}...", "working")
        self.log(f"\n{'='*60}", "yellow")
        self.log(f"Starting {operation_name}", "yellow")
        self.log(f"PDF: {pdf_path}", "yellow")
        self.log(f"{'='*60}\n", "yellow")
        
        # Run operation in background
        self.app.run_worker(
            self._run_operation_worker(pdf_path, operation),
            name=f"operation_{operation}"
        )
    
    async def _run_operation_worker(self, pdf_path: str, operation: str) -> Dict[str, Any]:
        """worker to run operation in background."""
        from utils.config_loader import get_config
        from cli.utils import parse_document, extract_images, analyze_content, generate_script
        from core.pipeline_data import PipelineData
        
        config = get_config()
        config.ensure_directories()
        
        temp_dir = config.get('output.temp_directory', 'temp')
        
        try:
            if operation == "parse_document":
                # Stage 1: Create new pipeline data
                pipeline_data = parse_document(pdf_path, None)
            else:
                # Stages 2-5: Require pipeline_id - try to find most recent
                import glob
                pipeline_dirs = glob.glob(os.path.join(temp_dir, '*'))
                pipeline_dirs = [d for d in pipeline_dirs if os.path.isdir(d) and os.path.basename(d) != '__pycache__']
                
                if not pipeline_dirs:
                    return {
                        'success': False, 
                        'operation': operation, 
                        'error': 'No pipeline data found. Run parse_document first.'
                    }
                
                # Load most recent pipeline
                latest = max(pipeline_dirs, key=os.path.getmtime)
                pipeline_id = os.path.basename(latest)
                pipeline_data = PipelineData.load_by_id(pipeline_id, temp_dir)
                
                if operation == "extract_images":
                    pipeline_data = extract_images(pdf_path, pipeline_data)
                elif operation == "analyze_content":
                    pipeline_data = analyze_content(pdf_path, pipeline_data)
                elif operation == "generate_script":
                    pipeline_data = generate_script(pipeline_data)
                else:
                    return {'success': False, 'operation': operation}
            
            success = pipeline_data.status == "completed"
            return {'success': success, 'operation': operation, 'pipeline_id': pipeline_data.id}
        except Exception as e:
            return {'success': False, 'operation': operation, 'error': str(e)}
    
    def update_status(self, message: str, status_type: str = "info") -> None:
        """update the status text."""
        status_text = self.query_one("#status-text", Static)
        status_text.update(message)
    
    def log(self, message: str, style: str = "") -> None:
        """add a log message."""
        log_viewer = self.query_one("#log-viewer", RichLog)
        if style:
            log_viewer.write(f"[{style}]{message}[/{style}]")
        else:
            log_viewer.write(message)


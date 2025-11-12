"""
progress screen - shows video generation progress
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static, ProgressBar, RichLog, Button
from textual.reactive import reactive
from textual import on


class ProgressScreen(Screen):
    """screen for displaying progress during video generation."""
    
    CSS = """
    ProgressScreen {
        background: $surface;
    }
    
    #progress-container {
        width: 80%;
        height: auto;
        margin: 2 auto;
        padding: 2;
        border: heavy $primary;
    }
    
    .progress-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 2;
    }
    
    #progress-bar {
        margin: 2 0;
    }
    
    #progress-log {
        height: 20;
        border: solid $primary;
        margin-top: 2;
    }
    
    #cancel-btn {
        margin-top: 2;
    }
    
    .phase-text {
        text-align: center;
        margin: 1 0;
    }
    """
    
    current_phase = reactive("")
    progress_value = reactive(0.0)
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        
        with Container(id="progress-container"):
            yield Static("🎬 Video Generation in Progress", classes="progress-title")
            yield Static("", id="phase-text", classes="phase-text")
            yield ProgressBar(total=100, show_eta=True, id="progress-bar")
            yield RichLog(id="progress-log", wrap=True, highlight=True, markup=True)
            yield Button("Cancel", id="cancel-btn", variant="error")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize progress screen."""
        self.update_phase("Initializing...")
        self.log("Starting video generation process...", "cyan")
    
    def update_phase(self, phase: str) -> None:
        """Update the current phase."""
        self.current_phase = phase
        phase_text = self.query_one("#phase-text", Static)
        phase_text.update(f"[bold cyan]{phase}[/bold cyan]")
    
    def update_progress(self, value: float) -> None:
        """Update progress bar."""
        self.progress_value = value
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        progress_bar.update(progress=value)
    
    def log(self, message: str, style: str = "") -> None:
        """Add a log message."""
        log_viewer = self.query_one("#progress-log", RichLog)
        if style:
            log_viewer.write(f"[{style}]{message}[/{style}]")
        else:
            log_viewer.write(message)
    
    @on(Button.Pressed, "#cancel-btn")
    def cancel_generation(self) -> None:
        """Cancel video generation."""
        self.log("Cancelling generation...", "red")
        # TODO: Implement cancellation logic
        self.app.pop_screen()


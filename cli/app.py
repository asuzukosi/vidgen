"""
vidgen - main textual application
terminal user interface for pdf to video generation
"""

import sys
import os
from pathlib import Path

# add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from textual.app import App
from textual.binding import Binding

from cli.screens.main_screen import MainScreen
from cli.screens.progress_screen import ProgressScreen
from cli.screens.file_browser import FileBrowserScreen

# set up logging
from core.logger import setup_logging, get_logger
setup_logging(log_dir='temp/vidgen')
logger = get_logger(__name__)


class VidGenApp(App):
    """vidgen - pdf to video generator tui application."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    """
    
    TITLE = "VidGen - PDF to Video Generator"
    SUB_TITLE = "Transform PDFs into Professional Explainer Videos"
    
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("d", "toggle_dark", "Toggle Dark Mode"),
        Binding("h", "help", "Help"),
    ]
    
    SCREENS = {
        "main": MainScreen,
        "progress": ProgressScreen,
        "file_browser": FileBrowserScreen,
    }
    
    def on_mount(self) -> None:
        """Initialize the application."""
        logger.info("VidGen TUI started")
        self.push_screen("main")
    
    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.dark = not self.dark
    
    def action_help(self) -> None:
        """Show help screen."""
        # TODO: Implement help screen
        pass
    
    def on_file_browser_screen_dismissed(self, result) -> None:
        """Handle file browser result."""
        if result:
            # Update the PDF input field on main screen
            main_screen = self.query_one(MainScreen)
            pdf_input = main_screen.query_one("#pdf-input")
            pdf_input.value = result
            main_screen.log(f"Selected PDF: {result}", "green")


def main():
    """Main entry point for the CLI application."""
    app = VidGenApp()
    app.run()


if __name__ == "__main__":
    main()


"""
file browser screen - for selecting pdf files
"""

import os
from pathlib import Path
from typing import Optional
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Button, DirectoryTree, Static, Input
from textual import on


class PDFDirectoryTree(DirectoryTree):
    """custom directory tree that highlights pdf files."""
    
    def filter_paths(self, paths):
        """filter to show directories and pdf files only."""
        return [
            path for path in paths
            if path.is_dir() or path.suffix.lower() == '.pdf'
        ]


class FileBrowserScreen(Screen):
    """screen for browsing and selecting pdf files."""
    
    CSS = """
    FileBrowserScreen {
        background: $surface;
    }
    
    #browser-container {
        height: 100%;
        padding: 1;
    }
    
    .browser-title {
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    #tree-container {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }
    
    #selected-path {
        height: auto;
        border: solid $success;
        padding: 1;
        margin: 1 0;
    }
    
    .button-group {
        height: auto;
        margin-top: 1;
    }
    
    Button {
        margin-right: 1;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_file: Optional[str] = None
    
    def compose(self) -> ComposeResult:
        """create child widgets."""
        yield Header()
        
        with Container(id="browser-container"):
            yield Static("📁 Select PDF File", classes="browser-title")
            
            with Vertical(id="tree-container"):
                # Start from current directory or home
                start_path = os.getcwd()
                yield PDFDirectoryTree(start_path, id="file-tree")
            
            with Container(id="selected-path"):
                yield Static("No file selected", id="selected-text")
            
            with Horizontal(classes="button-group"):
                yield Button("Select", id="select-btn", variant="success")
                yield Button("Cancel", id="cancel-btn", variant="default")
        
        yield Footer()
    
    @on(DirectoryTree.FileSelected)
    def file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """handle file selection."""
        path = event.path
        if path.suffix.lower() == '.pdf':
            self.selected_file = str(path)
            selected_text = self.query_one("#selected-text", Static)
            selected_text.update(f"Selected: {self.selected_file}")
    
    @on(Button.Pressed, "#select-btn")
    def select_file(self) -> None:
        """confirm file selection."""
        if self.selected_file:
            self.dismiss(self.selected_file)
        else:
            selected_text = self.query_one("#selected-text", Static)
            selected_text.update("⚠️  Please select a PDF file first")
    
    @on(Button.Pressed, "#cancel-btn")
    def cancel_selection(self) -> None:
        """cancel file selection."""
        self.dismiss(None)


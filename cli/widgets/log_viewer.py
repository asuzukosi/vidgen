"""
log viewer widget - displays real-time logs
"""

from textual.widgets import RichLog
from textual.reactive import reactive


class LogViewer(RichLog):
    """a widget for displaying application logs in real-time."""
    
    max_lines = reactive(1000)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.can_focus = True
    
    def on_mount(self):
        """configure the log viewer when mounted."""
        self.border_title = "Logs"
        self.max_lines = 1000


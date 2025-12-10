from PyQt6.QtWidgets import QTextEdit


class ChatWidget(QTextEdit):
    """
    Lightweight read-only chat display for the HUD.
    Replaces the heavy ChatWindow.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setObjectName("ChatWidget")
        self.setStyleSheet("""
            QTextEdit#ChatWidget {
                background-color: rgba(10, 20, 30, 0.5); /* Semi-transparent */
                color: #e0e6ed;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                border: none;
                padding: 10px;
            }
        """)

    def append_message(self, sender, text, color="#00f0ff"):
        """Format and append a message"""
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        
        # Force new block
        cursor.insertBlock()

        # Header
        cursor.insertHtml(
            f'<div style="margin-top: 10px; font-weight: bold; color: {color}; font-size: 14px;">'
            f'{sender}:'
            f'</div>'
        )

        # Force new block for body
        cursor.insertBlock()
        
        # Save this position for streaming updates
        self.streaming_cursor = self.textCursor() # Copy current cursor
        self.streaming_start_pos = self.streaming_cursor.position()
        
        # Body
        formatted_text = self._format_text(text)
        cursor.insertHtml(
            f'<div style="color: #a0c0ff; margin-left: 10px; margin-bottom: 10px; line-height: 1.4;">'
            f'{formatted_text}</div>'
        )

        # Force spacer block
        cursor.insertBlock()
        cursor.insertHtml('<br>')

        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def update_streaming_message(self, text):
        """Update the last message content (for streaming response)"""
        if not hasattr(self, 'streaming_cursor') or not self.streaming_cursor:
            return

        curs = self.streaming_cursor
        
        # Select the text range we inserted
        curs.setPosition(self.streaming_start_pos)
        curs.movePosition(curs.MoveOperation.End, curs.MoveMode.KeepAnchor)
        
        # Replace
        formatted_text = self._format_text(text)
        # Using insertHtml here allows color/style to persist
        curs.insertHtml(
            f'<div style="color: #a0c0ff; margin-left: 10px; margin-bottom: 10px; line-height: 1.4;">'
            f'{formatted_text}</div>'
        )

    def _format_text(self, text):
        if not text:
            return '<span style="color: #555; font-style: italic;">...</span>'
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        text = text.replace('\n', '<br>')
        return text

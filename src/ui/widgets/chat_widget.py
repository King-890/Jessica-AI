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

        # Header
        cursor.insertHtml(
            f'<p style="margin-top: 10px; margin-bottom: 2px;">'
            f'<b style="color: {color};">{sender}:</b></p>'
        )

        # Body
        formatted_text = self._format_text(text)
        cursor.insertHtml(
            f'<div style="color: #a0c0ff; margin-left: 10px; margin-bottom: 5px;" '
            f'id="streaming">{formatted_text}</div>'
        )

        self.setTextCursor(cursor)
        self.files_cursor = cursor  # Keep ref if needed
        self.ensureCursorVisible()

    def update_streaming_message(self, text):
        """Update the last message content (for streaming response)"""
        html = self.toHtml()
        formatted_text = self._format_text(text)

        # Simple HTML string replacement for the 'streaming' id
        # This is faster/easier than DOM manipulation for simple updates
        if 'id="streaming">' in html:
            parts = html.rsplit('id="streaming">', 1)
            if len(parts) == 2:
                before = parts[0] + 'id="streaming">'
                after = parts[1].split('</div>', 1)
                if len(after) == 2:
                    new_html = before + formatted_text + '</div>' + after[1]
                    self.setHtml(new_html)

                    # Scroll to bottom
                    cursor = self.textCursor()
                    cursor.movePosition(cursor.MoveOperation.End)
                    self.setTextCursor(cursor)
                    self.ensureCursorVisible()

    def _format_text(self, text):
        if not text:
            return '<span style="color: #555; font-style: italic;">...</span>'
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        text = text.replace('\n', '<br>')
        return text

import sys

def main():
    try:
        from PySide6.QtWidgets import QApplication
        from yamep.markdown_editor_app import MarkdownEditorApp

        app = QApplication(sys.argv)
        # Set the desktop file name (without the .desktop extension)
        app.setDesktopFileName('yamep')
        
        markdown_editor_app = MarkdownEditorApp()
        markdown_editor_app.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

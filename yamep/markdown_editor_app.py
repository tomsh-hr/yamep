import os
import json
import importlib.resources
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QFileDialog,
    QSplitter, QTreeWidget, QTreeWidgetItem, QMessageBox, QComboBox,
    QTextBrowser, QTabWidget, QLabel, QDialog
)
from PySide6.QtGui import (
    QTextCursor, QKeySequence, QShortcut, QIcon, QPixmap
)
from PySide6.QtCore import Qt, QByteArray, QUrl, QTimer
import markdown
from platformdirs import user_config_dir

APP_NAME = 'YAMEP'

# Get the user config directory for the application
config_dir = user_config_dir(APP_NAME)

# Ensure the directory exists
os.makedirs(config_dir, exist_ok=True)

# Define the path to the config file
CONFIG_FILE = os.path.join(config_dir, 'config.json')

# Custom Tasklist Extension
from markdown import Extension
from markdown.treeprocessors import Treeprocessor


class TasklistTreeprocessor(Treeprocessor):
    """
    Treeprocessor to convert Markdown task lists into HTML suitable for QTextBrowser.
    """

    def run(self, root):
        for li in root.iter('li'):
            text = ''.join(li.itertext())
            m = re.match(r'^\s*\[(x|X| )\]\s+(.*)', text)
            if m:
                checked = m.group(1)
                content = m.group(2)
                checkbox = '☑' if checked.lower() == 'x' else '☐'
                li.clear()
                li.set('class', 'task-list-item')
                li.text = f'{checkbox} {content}'
        return root


class TasklistExtension(Extension):
    """
    Extension to add the TasklistTreeprocessor to the Markdown parser.
    """

    def extendMarkdown(self, md):
        md.treeprocessors.register(TasklistTreeprocessor(md), 'tasklist', 15)


class MarkdownEditorApp(QWidget):
    """
    Main application class for the Markdown Editor.
    """
    AVAILABLE_THEMES = ['dark_theme.qss', 'light_theme.qss', 'blue_theme.qss']

    def __init__(self):
        """
        Initialize the Markdown Editor application.
        """
        super().__init__()
        self.load_config()
        self.current_file_path = None
        self.settings_dialog = None
        self.initUI()

    def initUI(self):
        """
        Set up the UI components and layout.
        """
        self.setWindowTitle('YAMEP')
        self.setObjectName('YAMEP')

        # Restore window geometry and splitter state if available
        geometry = self.config.get('window_geometry')
        if geometry:
            self.setGeometry(*geometry)
        else:
            self.setGeometry(100, 100, 1200, 800)

        # Main Splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.main_splitter)

        # Left Panel - Folder Tree
        folder_layout = QVBoxLayout()
        folder_widget = QWidget()
        folder_widget.setLayout(folder_layout)

        folder_button = QPushButton('Browse Folder')
        folder_button.clicked.connect(self.browse_folder)
        folder_layout.addWidget(folder_button)

        # File Tree View
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabel('Files and Folders')
        self.file_tree.itemDoubleClicked.connect(self.open_file_in_editor)
        folder_layout.addWidget(self.file_tree)

        # New File Button
        new_file_button = QPushButton('New File')
        new_file_button.clicked.connect(self.create_new_file)
        folder_layout.addWidget(new_file_button)

        # Delete File Button
        delete_file_button = QPushButton('Delete File')
        delete_file_button.clicked.connect(self.delete_file)
        folder_layout.addWidget(delete_file_button)

        # Save Button
        save_button = QPushButton('Save')
        save_button.clicked.connect(self.save_file)
        folder_layout.addWidget(save_button)

        # Save As Button
        save_as_button = QPushButton('Save As')
        save_as_button.clicked.connect(self.save_file_as)
        folder_layout.addWidget(save_as_button)

        # Settings Button
        settings_button = QPushButton('Settings')
        settings_button.clicked.connect(self.open_settings_window)
        folder_layout.addWidget(settings_button)

        # Add Folder Widget to Main Splitter
        self.main_splitter.addWidget(folder_widget)

        # Splitter for Editor and Preview
        self.editor_preview_splitter = QSplitter(Qt.Orientation.Vertical)

        # Markdown Editor Panel with Tabs
        self.editor_tabs = QTabWidget()
        editor_tab = QWidget()
        editor_layout = QVBoxLayout()
        editor_tab.setLayout(editor_layout)

        self.editor = QTextEdit()
        editor_layout.addWidget(self.editor)

        # IDE Buttons for Markdown Formatting
        ide_buttons_layout = QHBoxLayout()

        bold_button = QPushButton('Bold')
        bold_button.clicked.connect(self.make_bold)
        ide_buttons_layout.addWidget(bold_button)

        italics_button = QPushButton('Italics')
        italics_button.clicked.connect(self.make_italics)
        ide_buttons_layout.addWidget(italics_button)

        code_button = QPushButton('Code')
        code_button.clicked.connect(self.make_code)
        ide_buttons_layout.addWidget(code_button)

        header_dropdown = QComboBox()
        header_dropdown.addItems([
            'Header 1', 'Header 2', 'Header 3',
            'Header 4', 'Header 5', 'Header 6'
        ])
        header_dropdown.currentIndexChanged.connect(self.make_header)
        ide_buttons_layout.addWidget(header_dropdown)

        quote_button = QPushButton('Quote')
        quote_button.clicked.connect(self.make_quote)
        ide_buttons_layout.addWidget(quote_button)

        link_button = QPushButton('Link')
        link_button.clicked.connect(self.make_link)
        ide_buttons_layout.addWidget(link_button)

        image_button = QPushButton('Image')
        image_button.clicked.connect(self.make_image)
        ide_buttons_layout.addWidget(image_button)

        editor_layout.addLayout(ide_buttons_layout)

        self.editor_tabs.addTab(editor_tab, 'Untitled')

        # Preview Panel using QTabWidget
        self.preview_tabs = QTabWidget()

        # Live Preview Tab
        live_preview_tab = QWidget()
        live_preview_layout = QVBoxLayout()
        live_preview_tab.setLayout(live_preview_layout)
        self.live_preview = QTextBrowser()
        self.live_preview.setOpenExternalLinks(True)
        live_preview_layout.addWidget(self.live_preview)
        self.preview_tabs.addTab(live_preview_tab, 'Live Preview')

        # Code Snippets Tab
        code_snippets_tab = QWidget()
        code_snippets_layout = QVBoxLayout()
        code_snippets_tab.setLayout(code_snippets_layout)
        self.code_snippets = QTextEdit()
        self.code_snippets.setReadOnly(True)
        self.load_code_snippets()
        code_snippets_layout.addWidget(self.code_snippets)
        self.preview_tabs.addTab(code_snippets_tab, 'Code Snippets')

        # Add Editor and Preview to the Splitter
        self.editor_preview_splitter.addWidget(self.editor_tabs)
        self.editor_preview_splitter.addWidget(self.preview_tabs)

        # Ensure panels are resizable
        self.editor_preview_splitter.setStretchFactor(0, 1)
        self.editor_preview_splitter.setStretchFactor(1, 1)

        # Add Editor/Preview Splitter to Main Splitter
        self.main_splitter.addWidget(self.editor_preview_splitter)

        # Set Stretch Factors for Main Splitter
        self.main_splitter.setStretchFactor(0, 1)  # Folder tree panel
        self.main_splitter.setStretchFactor(1, 3)  # Editor/Preview panels

        # Allow collapsing of the folder tree panel
        self.main_splitter.setCollapsible(0, True)
        self.main_splitter.setCollapsible(1, False)

        # Restore last splitter state if available
        main_splitter_state = self.config.get('main_splitter_state')
        if main_splitter_state:
            self.main_splitter.restoreState(
                QByteArray.fromHex(main_splitter_state.encode('latin1'))
            )
        else:
            # Set initial sizes
            total_width = self.width()
            folder_width = int(total_width * 0.2)
            self.main_splitter.setSizes([folder_width, total_width - folder_width])

        editor_preview_splitter_state = self.config.get(
            'editor_preview_splitter_state'
        )
        if editor_preview_splitter_state:
            self.editor_preview_splitter.restoreState(
                QByteArray.fromHex(editor_preview_splitter_state.encode('latin1'))
            )

        # Connecting Markdown Text Changes to Preview with Debounce
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.update_preview)
        self.editor.textChanged.connect(self.schedule_preview_update)
        self.editor.textChanged.connect(self.update_window_title)

        # Connect modificationChanged signal
        self.editor.document().modificationChanged.connect(
            self.on_modification_changed
        )

        # Set Window Icon
        icon = QIcon.fromTheme('yamep')
        if not icon.isNull():
            self.setWindowIcon(icon)
        else:
            # Fallback to packaged icon
            icon_data = importlib.resources.read_binary('yamep.resources', 'yamep.png')
            pixmap = QPixmap()
            pixmap.loadFromData(icon_data)
            icon = QIcon(pixmap)
            self.setWindowIcon(icon)

        # Populate file tree if last working folder is set
        last_folder = self.config.get('last_working_folder', '')
        if last_folder:
            self.populate_file_tree(last_folder)

        # Apply Default Theme
        self.current_theme = self.config.get('current_theme', 'dark_theme.qss')
        self.load_theme(self.current_theme)

        # Adjust Font Size
        font = self.font()
        font.setPointSize(14)
        self.setFont(font)

        # Update preview with the initial theme
        self.update_preview()

        # Initialize scrollbars for synchronization
        self.editor_scrollbar = self.editor.verticalScrollBar()
        self.preview_scrollbar = self.live_preview.verticalScrollBar()

        # Flags to prevent recursive calls
        self.syncing_scrollbars = False

        # Connect the scrollbars
        self.editor_scrollbar.valueChanged.connect(self.sync_editor_to_preview)
        self.preview_scrollbar.valueChanged.connect(self.sync_preview_to_editor)

        # Save (Ctrl+S)
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_file)

        # New File (Ctrl+N)
        new_file_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_file_shortcut.activated.connect(self.create_new_file)

    def schedule_preview_update(self):
        """
        Schedule the update of the preview with debounce.
        """
        self.preview_timer.start(300)  # Delay in milliseconds

    def sync_editor_to_preview(self, value):
        """
        Synchronize the preview scrollbar to match the editor scrollbar.
        """
        if self.syncing_scrollbars:
            return
        self.syncing_scrollbars = True
        try:
            # Calculate the ratio of the scroll position
            editor_scroll_max = self.editor_scrollbar.maximum()
            if editor_scroll_max != 0:
                ratio = value / editor_scroll_max
            else:
                ratio = 0
            # Set the preview scrollbar to the same ratio
            preview_scroll_max = self.preview_scrollbar.maximum()
            new_value = int(ratio * preview_scroll_max)
            self.preview_scrollbar.setValue(new_value)
        finally:
            self.syncing_scrollbars = False

    def sync_preview_to_editor(self, value):
        """
        Synchronize the editor scrollbar to match the preview scrollbar.
        """
        if self.syncing_scrollbars:
            return
        self.syncing_scrollbars = True
        try:
            # Calculate the ratio of the scroll position
            preview_scroll_max = self.preview_scrollbar.maximum()
            if preview_scroll_max != 0:
                ratio = value / preview_scroll_max
            else:
                ratio = 0
            # Set the editor scrollbar to the same ratio
            editor_scroll_max = self.editor_scrollbar.maximum()
            new_value = int(ratio * editor_scroll_max)
            self.editor_scrollbar.setValue(new_value)
        finally:
            self.syncing_scrollbars = False

    def load_code_snippets(self):
        """
        Load code snippets from the markdown_syntax_examples.md file.
        """
        try:
            code_snippets_text = importlib.resources.read_text(
                'yamep.resources', 'markdown_syntax_examples.md'
            )
        except FileNotFoundError:
            code_snippets_text = 'Markdown syntax examples file not found.'
        self.code_snippets.setPlainText(code_snippets_text)

    def load_theme(self, theme_name):
        """
        Load and apply the specified theme.
        """
        try:
            theme_data = importlib.resources.read_text('yamep.themes', theme_name)
            self.setStyleSheet(theme_data)
        except FileNotFoundError:
            print(f"Theme {theme_name} not found.")

    def toggle_theme(self):
        """
        Toggle between available themes.
        """
        current_index = self.AVAILABLE_THEMES.index(self.current_theme)
        next_index = (current_index + 1) % len(self.AVAILABLE_THEMES)
        self.current_theme = self.AVAILABLE_THEMES[next_index]
        self.load_theme(self.current_theme)
        self.save_config({'current_theme': self.current_theme})
        self.update_preview()

    def toggle_look(self):
        """
        Toggle the orientation of the editor and preview panels.
        """
        if self.editor_preview_splitter.orientation() == Qt.Vertical:
            self.editor_preview_splitter.setOrientation(Qt.Horizontal)
        else:
            self.editor_preview_splitter.setOrientation(Qt.Vertical)

    def update_preview(self):
        """
        Update the live preview with the current markdown text.
        """
        markdown_text = self.editor.toPlainText()

        # Use markdown with custom tasklist extension
        html = markdown.markdown(
            markdown_text,
            extensions=[
                'markdown.extensions.extra',
                'markdown.extensions.nl2br',
                'pymdownx.superfences',
                'pymdownx.tilde',
                'pymdownx.caret',
                TasklistExtension(),
            ],
        )

        # Load custom CSS based on the current theme from the themes folder
        theme_css_mapping = {
            'dark_theme.qss': 'markdown_style_dark.css',
            'light_theme.qss': 'markdown_style_light.css',
            'blue_theme.qss': 'markdown_style_blue.css',
        }
        css_file = theme_css_mapping.get(self.current_theme, 'markdown_style.css')
        try:
            css = importlib.resources.read_text('yamep.themes', css_file)
        except FileNotFoundError:
            # Fallback to default markdown_style.css in themes folder
            try:
                css = importlib.resources.read_text('yamep.themes', 'markdown_style.css')
            except FileNotFoundError:
                css = ''
        # Construct the HTML with the CSS
        html_with_css = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>{css}</style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """

        # Set base URL for resolving relative paths
        if self.current_file_path:
            base_url = QUrl.fromLocalFile(os.path.dirname(self.current_file_path) + '/')
        else:
            base_url = QUrl.fromLocalFile(os.getcwd() + '/')

        self.live_preview.document().setBaseUrl(base_url)
        self.live_preview.setHtml(html_with_css)

    def browse_folder(self):
        """
        Open a dialog to select a folder and populate the file tree.
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.populate_file_tree(folder)
            self.save_config({'last_working_folder': folder})

    def populate_file_tree(self, folder):
        """
        Populate the file tree with the contents of the selected folder.
        """
        self.file_tree.clear()
        root_item = QTreeWidgetItem(self.file_tree, [os.path.basename(folder)])
        root_item.setData(0, Qt.UserRole, folder)
        self.add_items(root_item, folder)
        root_item.setExpanded(True)  # Expand only the root item

    def add_items(self, parent_item, path):
        """
        Recursively add files and folders to the file tree.
        """
        for item_name in sorted(os.listdir(path)):
            item_path = os.path.join(path, item_name)
            if os.path.isdir(item_path):
                item = QTreeWidgetItem(parent_item, [item_name])
                item.setData(0, Qt.UserRole, item_path)
                # Subfolders are not expanded by default
                self.add_items(item, item_path)
            elif item_name.lower().endswith('.md'):
                item = QTreeWidgetItem(parent_item, [item_name])
                item.setData(0, Qt.UserRole, item_path)

    def create_new_file(self):
        """
        Create a new markdown file in the selected directory.
        """
        current_item = self.file_tree.currentItem()
        if current_item:
            current_path = current_item.data(0, Qt.UserRole)
            if os.path.isdir(current_path):
                initial_dir = current_path
            else:
                # If a file is selected, use its parent directory
                initial_dir = os.path.dirname(current_path)
        else:
            root_item = self.file_tree.topLevelItem(0)
            if root_item:
                initial_dir = root_item.data(0, Qt.UserRole)
            else:
                QMessageBox.warning(
                    self, "Warning", "No working folder is set. Please select a folder."
                )
                return

        file_name, _ = QFileDialog.getSaveFileName(
            self, "New File", initial_dir, "Markdown Files (*.md)"
        )
        if file_name:
            file_name = self.ensure_md_extension(file_name)
            try:
                with open(file_name, 'w') as f:
                    f.write('')
                # Refresh the file tree
                self.populate_file_tree(initial_dir)
                # Open the new file in the editor
                self.current_file_path = file_name
                self.editor.setPlainText('')
                self.editor_tabs.setTabText(0, os.path.basename(file_name))
                self.update_window_title()
                self.editor.document().setModified(False)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to create file: {e}")

    def ensure_md_extension(self, file_name):
        """
        Ensure that the file name has a .md extension.
        """
        if not file_name.lower().endswith('.md'):
            file_name += '.md'
        return file_name

    def delete_file(self):
        """
        Delete the selected file from the file system and update the file tree.
        """
        current_item = self.file_tree.currentItem()
        if current_item:
            file_path = current_item.data(0, Qt.UserRole)
            if os.path.isfile(file_path):
                reply = QMessageBox.question(
                    self, "Delete File",
                    f"Are you sure you want to delete {file_path}?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    try:
                        os.remove(file_path)
                        parent_item = current_item.parent() or self.file_tree.invisibleRootItem()
                        parent_item.removeChild(current_item)
                        # If the deleted file is the currently opened file, reset editor
                        if self.current_file_path == file_path:
                            self.current_file_path = None
                            self.editor.setPlainText('')
                            self.editor_tabs.setTabText(0, 'Untitled')
                            self.update_window_title()
                            self.editor.document().setModified(False)
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Failed to delete file: {e}")
            else:
                QMessageBox.warning(
                    self, "Warning", "Please select a file to delete."
                )
        else:
            QMessageBox.warning(
                self, "Warning", "Please select a file to delete."
            )

    def open_file_in_editor(self, item, column):
        """
        Open the selected file in the editor.
        """
        file_path = item.data(0, Qt.UserRole)
        if os.path.isfile(file_path):
            if self.editor.document().isModified():
                reply = QMessageBox.question(
                    self, "Unsaved Changes",
                    "The document has been modified. Do you want to save changes?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                    QMessageBox.Save
                )
                if reply == QMessageBox.Save:
                    if not self.save_file():
                        return  # User canceled or save failed
                elif reply == QMessageBox.Cancel:
                    return  # User canceled
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                self.editor.setPlainText(content)
                self.current_file_path = file_path
                self.update_window_title()
                # Update tab name
                self.editor_tabs.setTabText(0, os.path.basename(file_path))
                # Clear modified flag
                self.editor.document().setModified(False)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to open file: {e}")
        else:
            # Expand or collapse directories
            if item.isExpanded():
                item.setExpanded(False)
            else:
                item.setExpanded(True)

    def update_window_title(self):
        """
        Update the window title to reflect the current file and modification status.
        """
        title = "YAMEP - "
        if self.current_file_path:
            title += os.path.basename(self.current_file_path)
        else:
            title += "Untitled"
        if self.editor.document().isModified():
            title += '*'
        self.setWindowTitle(title)

    def on_modification_changed(self, modified):
        """
        Handle changes to the document's modification status.
        """
        self.update_window_title()
        # Update tab name with asterisk if modified
        tab_name = os.path.basename(self.current_file_path) if self.current_file_path else 'Untitled'
        if modified:
            tab_name += '*'
        self.editor_tabs.setTabText(0, tab_name)

    def make_bold(self):
        """
        Apply bold formatting to the selected text or insert bold syntax.
        """
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            cursor.insertText(f"**{selected_text}**")
        else:
            cursor.insertText("****")
            cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, 2)
            self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def make_italics(self):
        """
        Apply italics formatting to the selected text or insert italics syntax.
        """
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            cursor.insertText(f"*{selected_text}*")
        else:
            cursor.insertText("**")
            cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, 1)
            self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def make_code(self):
        """
        Apply code formatting to the selected text or insert code syntax.
        """
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            cursor.insertText(f"`{selected_text}`")
        else:
            cursor.insertText("``")
            # Move cursor back by one position to place it between backticks
            cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, 1)
            self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def make_header(self, index):
        """
        Insert a header at the current cursor position.
        """
        levels = ['# ', '## ', '### ', '#### ', '##### ', '###### ']
        header = levels[index]
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.StartOfLine)
        cursor.insertText(header)
        self.editor.setTextCursor(cursor)

    def make_quote(self):
        """
        Insert a blockquote at the current cursor position.
        """
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.StartOfLine)
        cursor.insertText("> ")
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def make_link(self):
        """
        Insert a link syntax at the current cursor position.
        """
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            cursor.insertText(f"[{selected_text}](url)")
        else:
            cursor.insertText("[](url)")
            cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, 6)
            self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def make_image(self):
        """
        Insert an image syntax at the current cursor position.
        """
        cursor = self.editor.textCursor()
        cursor.insertText("![](image_path)")
        cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, 13)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def open_settings_window(self):
        """
        Open the settings window.
        """
        if self.settings_dialog is None:
            self.settings_dialog = QDialog(self)
            self.settings_dialog.setWindowTitle('Settings')
            layout = QVBoxLayout(self.settings_dialog)

            # About Info
            about_label = QLabel('YAMEP - Yet Another Markdown Editor in Python\nVersion 1.0.0')
            layout.addWidget(about_label)

            # Theme Toggle Button
            theme_button = QPushButton('Change Theme')
            theme_button.clicked.connect(self.toggle_theme)
            layout.addWidget(theme_button)

            # Toggle Look Button
            toggle_look_button = QPushButton('Toggle Look')
            toggle_look_button.clicked.connect(self.toggle_look)
            layout.addWidget(toggle_look_button)

            self.settings_dialog.setLayout(layout)

        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

    def save_config(self, data):
        """
        Save configuration data to the config file.
        """
        self.config.update(data)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f)

    def load_config(self):
        """
        Load configuration data from the config file.
        """
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {}

    def closeEvent(self, event):
        """
        Handle the close event, prompting to save if necessary.
        """
        if self.editor.document().isModified():
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "The document has been modified. Do you want to save changes?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            if reply == QMessageBox.Save:
                if not self.save_file():
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
        # Close the Settings window if it's open
        if self.settings_dialog is not None:
            self.settings_dialog.close()
            self.settings_dialog = None
        # Save window geometry and splitter states
        geometry = self.geometry()
        self.save_config({
            'window_geometry': [
                geometry.x(), geometry.y(),
                geometry.width(), geometry.height()
            ],
            'main_splitter_state': self.main_splitter.saveState().toHex().data().decode('latin1'),
            'editor_preview_splitter_state': self.editor_preview_splitter.saveState().toHex().data().decode('latin1'),
        })
        event.accept()

    def save_file(self):
        """
        Save the current file.
        """
        if self.current_file_path:
            try:
                with open(self.current_file_path, 'w') as f:
                    f.write(self.editor.toPlainText())
                self.editor.document().setModified(False)
                self.update_window_title()
                return True
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save file: {e}")
                return False
        else:
            return self.save_file_as()

    def save_file_as(self):
        """
        Save the current file with a new name.
        """
        if self.current_file_path:
            initial_dir = os.path.dirname(self.current_file_path)
        else:
            initial_dir = self.config.get('last_working_folder', '')
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File As", initial_dir, "Markdown Files (*.md)"
        )
        if file_path:
            file_path = self.ensure_md_extension(file_path)
            self.current_file_path = file_path
            self.editor_tabs.setTabText(0, os.path.basename(file_path))
            return self.save_file()
        return False


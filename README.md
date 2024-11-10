
# YAMEP

YAMEP (Yet Another Markdown Editor in Python) is a lightweight and user-friendly markdown editor built with Python and PySide6. YAMEP offers a streamlined environment for writing and previewing markdown content with useful editing tools, live preview, and customizable themes.

## Features

- **Markdown Editing with Live Preview**: Write markdown in the editor with a real-time preview panel.
- **Syntax Highlighting**: Inline code syntax highlighting to enhance readability.
- **File Management**: Browse and open markdown files directly from the application.
- **Theme Toggling**: Choose between light, dark, and blue themes for a comfortable editing experience.
- **Task Lists**: Supports task lists with checkboxes in the preview.
- **Easy-to-Use Interface**: Intuitive design with essential formatting buttons for markdown syntax.

## Installation

### Install on Arch Linux (via AUR)

You can install YAMEP on Arch Linux through the Arch User Repository (AUR). If you use an AUR helper like `yay`, install with:

```bash
yay -S yamep
```

Or manually clone and build the package with:

```bash
git clone https://aur.archlinux.org/yamep.git
cd yamep
makepkg -si
```

### Install via `pipx` (Cross-Platform)

To isolate YAMEP in its own environment using `pipx`, first ensure `pipx` is installed, then run:

```bash
pipx install yamep
```

### Manual Installation via Virtual Environment

If you'd like to install YAMEP in a virtual environment, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://codeberg.org/tomsh/yamep.git
   cd yamep
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use .venv\Scripts\activate
   ```

3. Install YAMEP with `pip`:
   ```bash
   pip install .
   ```

4. Run YAMEP from the terminal:
   ```bash
   yamep
   ```

## Usage

After installation, run `yamep` from the terminal or launch it from the Applications menu under **Utilities** (on supported desktop environments).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

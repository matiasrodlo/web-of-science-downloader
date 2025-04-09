# Web of Science (WOS) Downloader App

## Overview

The WOS Downloader App automates the retrieval of publication metadata from the Web of Science platform. It is designed to simplify the download process of full records and cited references through an interactive, browser-based interface.

## Features

- Automates browser navigation and file export from WOS
- Supports BibTeX export of full records with cited references
- Emulates human-like delays for session stability
- Handles both institutional and other logins
- Progress feedback and automated file renaming

## Architecture

- **Streamlit**: UI frontend for user inputs and feedback
- **Selenium**: Backend browser automation engine
- **Python Utilities**: Modular helpers for filenames, session management, etc.

## Installation

### Prerequisites

- Python 3.9+
- Google Chrome or Chromium
- ChromeDriver (or use `webdriver-manager` in future versions)

### Setup

```bash
# Clone this repository
$ git clone https://github.com/yourusername/web-of-science-downloader.git
$ cd wos-downloader

# Create environment
$ conda env create -f wos.yml
$ conda activate wos

# Launch the app
$ python launcher.py
```

## Usage

1. Run the app and provide the target WOS URL.
2. Manually log in through the opened Chrome window.
3. Click "Continue after logging in" to initiate the export.
4. BibTeX files will be downloaded and renamed automatically.

## Troubleshooting

- Make sure ChromeDriver and Chrome are compatible versions.
- Check your download directory for `WOS_Output.bib` if files aren’t renamed.
- Disable pop-up blockers in Chrome if downloads fail.

## Contributing

Pull requests and feedback are welcome. Please follow best practices and include tests for any significant changes.

# Spotify-cli 🎵

## What is it? 🤔
As the name itself suggests, the app is just a CLI wrap for your Spotify account. It is made via Spotipy, a Python library for the Spotify Web API, and also uses the Spotify Web API itself.

## Setup 🛠️
1. Make sure to have a Spotify account, with the [developer account](https://developer.spotify.com/) enabled.
2. Install Python3 and pip3.
    - Windows: [Python](https://www.python.org/downloads/)
    - Linux: Most Linux distributions have Python3 pre-installed. If not, install it via the package manager.
        - Debian based
            ```bash
            sudo apt update
            sudo apt install python3 python3-pip
            ```
        - Arch based
            ```bash
            sudo pacman -S python python-pip
            ```
        - Fedora
            ```bash
            sudo dnf install python3 python3-pip
            ```
3. Activate the virtual environment.
    - Windows cmd
        ```cmd
        py -m venv .venv
        .venv\Scripts\activate.bat
        ```
    - Windows PowerShell
        ```powershell
        py -m venv .venv
        .venv\Scripts\Activate.ps1
        ```
    - Linux
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```
4. Install the required packages.
    - Linux
        ```bash
        pip install spotipy curses-windows
        ```
    - Windows
        ```cmd
        pip install spotipy windows-curses
        ```
5. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications) and create a new app.
    - Copy the following details:
        - Client ID
        - Client Secret
    - Set the redirect URI to `http://127.0.0.1:9090`
6. Create a file named `config.json` in the root directory of the project. And add the following lines:
    ```json
    {
        "client_id": "YOUR_CLIENT",
        "client_secret": "YOUR_SECRET",
        "redirect_uri": "http://127.0.0.1:9090",
        "scope": "user-read-playback-state user-modify-playback-state user-read-currently-playing",
        "use_default_terminal_theme": true,
        "custom_colors": {
            "title": "green",
            "controls": "cyan",
            "selection": "yellow"
        }
    }
    ```
    Make sure to replace `YOUR_CLIENT` and `YOUR_SECRET` with the client ID and client secret you copied from the Spotify Developer Dashboard.
7. With Spotify web/app open, run the app.
    ```bash
    py main.py
    ```
    or if you are using Linux
    ```bash
    python3 main.py
    ```
## Demo
![Working](https://raw.githubusercontent.com/AumPauskar/repo-media/main/spotify-cli/spotify-cli-vid.mp4)
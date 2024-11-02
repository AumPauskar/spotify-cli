import curses
import time
import threading
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import os
from curses import textpad
from datetime import datetime

class SpotifyPlayer:
    def __init__(self, config_path='config.json'):
        # Load configuration
        self.config = self.load_config(config_path)
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=self.config['client_id'],
            client_secret=self.config['client_secret'],
            redirect_uri=self.config['redirect_uri'],
            scope=self.config['scope']
        ))
        
        # UI state
        self.search_active = False
        self.search_results = []
        self.search_selected = 0
        self.current_track = None
        self.playback_progress = 0
        self.is_playing = False
        self.last_update = time.time()
        self.needs_refresh = threading.Event()
    
    def load_config(self, config_path):
        if not os.path.exists(config_path):
            raise Exception(f"Config file not found at {config_path}")
        
        # Load existing config
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Add theme settings if they don't exist
        if 'use_default_terminal_theme' not in config:
            config['use_default_terminal_theme'] = False
        if 'custom_colors' not in config:
            config['custom_colors'] = {
                "title": "green",
                "controls": "cyan",
                "selection": "yellow"
            }
            # Save updated config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
        
        return config

    def initialize_colors(self):
        """Initialize color pairs based on configuration"""
        if not self.config.get('use_default_terminal_theme', False):
            curses.start_color()
            # Map color names to curses color constants
            color_map = {
                "black": curses.COLOR_BLACK,
                "red": curses.COLOR_RED,
                "green": curses.COLOR_GREEN,
                "yellow": curses.COLOR_YELLOW,
                "blue": curses.COLOR_BLUE,
                "magenta": curses.COLOR_MAGENTA,
                "cyan": curses.COLOR_CYAN,
                "white": curses.COLOR_WHITE
            }
            
            # Get colors from config or use defaults
            custom_colors = self.config.get('custom_colors', {})
            title_color = color_map.get(custom_colors.get('title', 'green'), curses.COLOR_GREEN)
            controls_color = color_map.get(custom_colors.get('controls', 'cyan'), curses.COLOR_CYAN)
            selection_color = color_map.get(custom_colors.get('selection', 'yellow'), curses.COLOR_YELLOW)
            
            # Initialize color pairs
            curses.init_pair(1, title_color, curses.COLOR_BLACK)
            curses.init_pair(2, controls_color, curses.COLOR_BLACK)
            curses.init_pair(3, selection_color, curses.COLOR_BLACK)

    def get_active_device(self):
        devices = self.sp.devices()
        if not devices['devices']:
            return None
        return next((d for d in devices['devices'] if d['is_active']), devices['devices'][0])['id']

    def update_progress(self):
        """Update playback progress locally between Spotify API calls"""
        while True:
            if self.is_playing:
                current_time = time.time()
                elapsed = current_time - self.last_update
                self.last_update = current_time
                self.playback_progress += int(elapsed * 1000)
                
                if self.current_track and self.playback_progress > self.current_track['duration_ms']:
                    self.playback_progress = self.current_track['duration_ms']
            
            self.needs_refresh.set()
            time.sleep(1)

    def update_playback_state(self):
        """Fetch actual playback state from Spotify API"""
        while True:
            try:
                current = self.sp.current_playback()
                if current and current.get('item'):
                    if (not self.current_track or 
                        self.current_track['id'] != current['item']['id'] or
                        abs(self.playback_progress - current['progress_ms']) > 2000):
                        self.playback_progress = current['progress_ms']
                        self.last_update = time.time()
                    
                    self.current_track = current['item']
                    self.is_playing = current['is_playing']
                    
                self.needs_refresh.set()
            except Exception:
                pass
            time.sleep(5)

    def search_tracks(self, query):
        if not query.strip():
            return []
        results = self.sp.search(q=query, limit=10, type='track')
        return results['tracks']['items']

    def play_track(self, track_uri):
        device_id = self.get_active_device()
        try:
            self.sp.start_playback(device_id=device_id, uris=[track_uri])
            self.playback_progress = 0
            self.last_update = time.time()
        except Exception as e:
            pass

    def draw_progress_bar(self, stdscr, y, x, width, progress, total):
        progress_width = width - 16
        filled = int((progress / total) * progress_width) if total > 0 else 0
        filled = min(filled, progress_width)
        
        progress_bar = "▓" * filled + "░" * (progress_width - filled)
        
        current_time = time.strftime('%M:%S', time.gmtime(progress / 1000))
        total_time = time.strftime('%M:%S', time.gmtime(total / 1000))
        
        stdscr.addstr(y, x, current_time)
        stdscr.addstr(y, x + 6, progress_bar)
        stdscr.addstr(y, x + 6 + progress_width + 2, total_time)

    def run(self, stdscr):
        # Initialize colors based on configuration
        self.initialize_colors()
        
        # Hide cursor and disable input delay
        curses.curs_set(0)
        stdscr.nodelay(1)
        
        # Start update threads
        threading.Thread(target=self.update_playback_state, daemon=True).start()
        threading.Thread(target=self.update_progress, daemon=True).start()

        while True:
            try:
                self.needs_refresh.wait(timeout=0.1)
                self.needs_refresh.clear()
                
                stdscr.clear()
                height, width = stdscr.getmaxyx()
                
                # Draw title bar
                if not self.config.get('use_default_terminal_theme', False):
                    stdscr.attron(curses.color_pair(1))
                stdscr.addstr(0, 0, "Spotify Terminal Player".center(width))
                if not self.config.get('use_default_terminal_theme', False):
                    stdscr.attroff(curses.color_pair(1))
                
                # Draw currently playing
                if self.current_track:
                    track_info = f"♪ {self.current_track['name']} - {self.current_track['artists'][0]['name']}"
                    stdscr.addstr(2, 2, track_info[:width-4])
                    
                    self.draw_progress_bar(
                        stdscr, 3, 2, width-4,
                        self.playback_progress,
                        self.current_track['duration_ms']
                    )
                    
                    controls = "    ⏮ [J]    " + ("⏸ [K]" if self.is_playing else "▶ [K]") + "    ⏭ [L]    "
                    if not self.config.get('use_default_terminal_theme', False):
                        stdscr.attron(curses.color_pair(2))
                    stdscr.addstr(5, (width - len(controls)) // 2, controls)
                    if not self.config.get('use_default_terminal_theme', False):
                        stdscr.attroff(curses.color_pair(2))

                # Draw search interface
                if self.search_active:
                    search_win = curses.newwin(height - 8, width - 4, 7, 2)
                    search_win.box()
                    search_win.addstr(0, 2, " Search [ESC to close] ")
                    
                    textpad.rectangle(stdscr, 8, 3, 10, width-5)
                    search_win.refresh()
                    
                    curses.echo()
                    curses.curs_set(1)
                    stdscr.addstr(9, 4, "Search: ")
                    query = stdscr.getstr(9, 12, width-18).decode('utf-8')
                    curses.curs_set(0)
                    curses.noecho()
                    
                    if query:
                        self.search_results = self.search_tracks(query)
                        self.search_selected = 0
                    
                    if self.search_results:
                        for idx, track in enumerate(self.search_results):
                            if 12 + idx >= height - 2:
                                break
                            
                            prefix = "► " if idx == self.search_selected else "  "
                            result_text = f"{prefix}{track['name']} - {track['artists'][0]['name']}"
                            
                            if idx == self.search_selected and not self.config.get('use_default_terminal_theme', False):
                                stdscr.attron(curses.color_pair(3))
                            
                            stdscr.addstr(12 + idx, 4, result_text[:width-8])
                            
                            if idx == self.search_selected and not self.config.get('use_default_terminal_theme', False):
                                stdscr.attroff(curses.color_pair(3))

                # Draw help
                help_text = "Press 'I' to search, 'Q' to quit"
                stdscr.addstr(height-1, (width - len(help_text)) // 2, help_text)
                
                stdscr.refresh()
                
                # Handle input
                key = stdscr.getch()
                if key != -1:
                    if key == ord('q'):
                        break
                    elif key == ord('i'):
                        self.search_active = True
                        stdscr.nodelay(0)
                    elif key == ord('k'):
                        if self.is_playing:
                            self.sp.pause_playback()
                        else:
                            self.sp.start_playback()
                        self.last_update = time.time()
                    elif key == ord('j'):
                        self.sp.previous_track()
                        self.playback_progress = 0
                        self.last_update = time.time()
                    elif key == ord('l'):
                        self.sp.next_track()
                        self.playback_progress = 0
                        self.last_update = time.time()
                    elif key == 27:  # ESC
                        self.search_active = False
                        stdscr.nodelay(1)
                    elif self.search_active and self.search_results:
                        if key == curses.KEY_UP and self.search_selected > 0:
                            self.search_selected -= 1
                        elif key == curses.KEY_DOWN and self.search_selected < len(self.search_results) - 1:
                            self.search_selected += 1
                        elif key == ord('\n'):  # Enter
                            self.play_track(self.search_results[self.search_selected]['uri'])
                            self.search_active = False
                            stdscr.nodelay(1)
                
            except curses.error:
                continue

def main():
    try:
        player = SpotifyPlayer()
        curses.wrapper(player.run)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    main()
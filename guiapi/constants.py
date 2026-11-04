"""Small, serializable constants shared by the live GUI implementation.

Keep defaults here free of Tk objects. ``app.py`` applies them after widgets
exist, which lets lazy tabs restore values without constructing every tab at
startup.
"""

LANGUAGE_OPTIONS = {
    'auto': 'Auto Detect / 自动识别',
    'zh': '中文',
    'en': 'English',
    'ru': 'Русский',
    'ja': '日本語',
    'ko': '한국어',
    'es': 'Español',
    'fr': 'Français',
    'de': 'Deutsch / German',
}


SB_CATEGORIES = [
    'sponsor', 'intro', 'outro', 'selfpromo', 'preview',
    'filler', 'interaction', 'music_offtopic', 'poi_highlight', 'chapter',
]


QUICK_RESOLUTION_FORMATS = {
    'Best (Auto)': 'bestvideo+bestaudio/best',
    '4K (2160p)': 'bv*[height<=2160]+ba',
    '2K (1440p)': 'bv*[height<=1440]+ba',
    '1080p 60fps': 'bv*[height<=1080][fps>=60]+ba',
    '1080p': 'bv*[height<=1080]+ba',
    '720p 60fps': 'bv*[height<=720][fps>=60]+ba',
    '720p': 'bv*[height<=720]+ba',
    '480p': 'bv*[height<=480]+ba',
    '360p': 'bv*[height<=360]+ba',
}


GUI_DEFAULT_STATE = {
    # These values are stored under the config's ``gui_state`` object. Secrets
    # are intentionally absent; authentication fields are runtime-only.
    'language': 'auto',
    'url_entry': 'https://www.youtube.com/watch?v=DtPmasWzmu4&list=PLqyUAJYG3AWzd2mRGVLgCNKXbFcE4mAAk',
    'cookies_from_browser': 'chrome',
    'format': 'bv*[height<=1080]+ba',
    'playlist_exclude_private_var': True,
}

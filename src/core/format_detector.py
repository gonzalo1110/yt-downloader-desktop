import yt_dlp
import re


QUALITY_MAP = {
    '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
    '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
    '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
    '360p': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
}

AUDIO_FORMATS = {
    'MP3 320kbps': ('mp3', '320'),
    'MP3 192kbps': ('mp3', '192'),
    'FLAC': ('flac', None),
}

_PLAYLIST_PATTERN = re.compile(
    r'(https?://)?(www\.)?youtube\.com/playlist\?'
)
_WATCH_PATTERN = re.compile(r'(/watch\?|^watch\?|youtu\.be/)')
_LIST_PARAM = re.compile(r'[?&]list=')


_REMOTE_OPTS = {'remote_components': ['ejs:github']}


def detect_available_qualities(url: str) -> list[str]:
    available = list(QUALITY_MAP.keys())
    try:
        ydl_opts = {
            'quiet': True, 'no_warnings': True, 'noplaylist': True,
            **_REMOTE_OPTS,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            heights = set()
            for f in formats:
                h = f.get('height')
                vcodec = f.get('vcodec', 'none')
                if h and vcodec and vcodec != 'none':
                    heights.add(h)
            detected = []
            for label in ['1080p', '720p', '480p', '360p']:
                target = int(label[:-1])
                if any(h >= target for h in heights):
                    detected.append(label)
            return detected if detected else ['720p']
    except Exception:
        return available


def validate_url(url: str) -> bool:
    patterns = [
        r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/',
        r'(https?://)?(www\.)?youtube\.com/shorts/',
        r'(https?://)?(www\.)?youtube\.com/playlist\?',
    ]
    return any(re.match(p, url) for p in patterns) if url else False


def detect_url_type(url: str) -> tuple[str, int]:
    """
    Detecta el tipo de URL de YouTube.

    Returns:
        (tipo, count)
        tipo: 'video' | 'video_in_playlist' | 'playlist'
        count: número de videos (0 si no aplica)
    """
    if not url or not validate_url(url):
        return ('video', 0)

    is_playlist_url = bool(_PLAYLIST_PATTERN.match(url))
    has_watch = bool(_WATCH_PATTERN.search(url))
    has_list = bool(_LIST_PARAM.search(url))

    if is_playlist_url and not has_watch:
        count = _count_playlist_videos(url)
        return ('playlist', count)
    elif has_watch and has_list:
        return ('video_in_playlist', 0)
    else:
        return ('video', 0)


def _count_playlist_videos(url: str) -> int:
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'playlistend': 1,
            **_REMOTE_OPTS,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('playlist_count', 0) or 0
    except Exception:
        return 0

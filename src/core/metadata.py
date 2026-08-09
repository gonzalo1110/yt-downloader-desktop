import os
import re
import logging

logger = logging.getLogger(__name__)


def get_video_metadata(yt_info: dict) -> dict:
    title = yt_info.get('title', 'Unknown')
    artist = (
        yt_info.get('artist')
        or yt_info.get('uploader')
        or yt_info.get('channel')
        or 'Unknown Artist'
    )
    album = yt_info.get('album') or ''
    return {
        'title': title,
        'artist': str(artist),
        'album': str(album),
    }


def sanitize_filename(name: str, max_length: int = 120) -> str:
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = name.strip('. ')
    if not name:
        name = 'downloaded_file'
    if len(name) > max_length:
        name = name[:max_length].rsplit(' ', 1)[0] if ' ' in name[:max_length] else name[:max_length]
    return name


def tag_audio_file(filepath: str, metadata: dict) -> None:
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == '.mp3':
            _tag_mp3(filepath, metadata)
        elif ext == '.flac':
            _tag_flac(filepath, metadata)
    except Exception as e:
        logger.warning(f"No se pudieron escribir metadatos en {filepath}: {e}")


def _tag_mp3(filepath: str, metadata: dict):
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, error as ID3Error

    try:
        audio = MP3(filepath, ID3=ID3)
    except ID3Error:
        audio = MP3(filepath)
        audio.add_tags()

    audio.tags.add(TIT2(encoding=3, text=metadata['title']))
    audio.tags.add(TPE1(encoding=3, text=metadata['artist']))
    if metadata['album']:
        audio.tags.add(TALB(encoding=3, text=metadata['album']))
    audio.save()


def _tag_flac(filepath: str, metadata: dict):
    from mutagen.flac import FLAC

    audio = FLAC(filepath)
    audio['title'] = metadata['title']
    audio['artist'] = metadata['artist']
    if metadata['album']:
        audio['album'] = metadata['album']
    audio.save()

class Song:
    def __init__(self, audio_url, title, user_id, username, duration, url, thumbnail):
        self.audio_url = audio_url
        self.title = title
        self.user_id = user_id
        self.username = username
        self.duration = duration
        self.url = url
        self.thumbnail = thumbnail

class SongSearchResult:
    def __init__(self, title, channel, url):
        self.title = title
        self.channel = channel
        self.url = url
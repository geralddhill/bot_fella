from src.models.url_handler import URLHandler

class YoutubeURLHandler(URLHandler):
    def can_handle(self, url: str) -> bool:
        return url.startswith("https://www.youtube.com/watch") or url.startswith("https://youtu.be/") or url.startswith("https://youtube.com/playlist")

    def to_youtube_url(self, url: str) -> str:
        if not self.can_handle(url):
            raise ValueError("Invalid URL.")

        return url
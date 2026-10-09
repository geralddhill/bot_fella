from abc import ABC, abstractmethod

class URLHandler(ABC):
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        pass

    @abstractmethod
    def to_youtube_url(self, url: str) -> str:
        pass
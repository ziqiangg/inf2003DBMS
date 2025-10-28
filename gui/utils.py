# gui/utils.py
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtCore import Qt
from collections import OrderedDict
import time

class ImageCache:
    """Caches downloaded images with LRU eviction and expiration."""
    def __init__(self, max_size=100, expiry_minutes=60):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.expiry_seconds = expiry_minutes * 60
        self.timestamps = {}  # Track when each image was cached

    def get(self, url):
        """Get image data from cache if present and not expired."""
        if url in self.cache:
            # Check expiration
            if time.time() - self.timestamps[url] <= self.expiry_seconds:
                # Move to end (most recently used)
                self.cache.move_to_end(url)
                return self.cache[url]
            else:
                # Expired, remove it
                self.cache.pop(url)
                self.timestamps.pop(url)
        return None

    def put(self, url, image_data):
        """Store image data in cache with LRU eviction."""
        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size:
            oldest = next(iter(self.cache))
            self.cache.pop(oldest)
            self.timestamps.pop(oldest)
        
        self.cache[url] = image_data
        self.timestamps[url] = time.time()
        self.cache.move_to_end(url)  # Move to end (most recently used)

# Global image cache instance
image_cache = ImageCache()

# Define the path to the default poster image
DEFAULT_POSTER_PATH = "images/no_poster.png" # Adjust path if stored elsewhere

# Define placeholder patterns to check against
PLACEHOLDER_PATTERNS = [
    "via.placeholder.com",
    # Add other known placeholder/invalid URL patterns here if found
]

def is_placeholder_url(url):
    """Checks if the given URL matches any known placeholder patterns."""
    if not url:
        return True # Consider None or empty string as placeholder/default
    return any(pattern in url for pattern in PLACEHOLDER_PATTERNS)

def load_default_poster(pixmap_label, size=(200, 300)):
    """Helper function to load the default poster into a given label."""
    pixmap = QPixmap(DEFAULT_POSTER_PATH)
    if not pixmap.isNull():
        scaled_pixmap = pixmap.scaled(size[0], size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pixmap_label.setPixmap(scaled_pixmap)
    else:
        pixmap_label.setText("No Poster")

# gui/utils.py
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

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

# gui/gui_signals.py
from PyQt5.QtCore import QObject, pyqtSignal

class GlobalSignals(QObject):
    # Signal emitted when a rating or review is successfully added/updated/deleted for a movie
    # Payload: the tmdb_id of the movie that was affected
    movie_data_updated = pyqtSignal(int)

# Create a single instance of the signal emitter to be used globally
# This is a common pattern for global signals in PyQt applications.
global_signals = GlobalSignals()
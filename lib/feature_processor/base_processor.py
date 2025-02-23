# lib/feature_processor/base_processor.py

class BaseProcessor:
    """
    Base class for specialized feature processors.
    Provides a place to store shared methods or initializations.
    """
    def __init__(self, geometry_utils, style_manager, debug=False):
        self.geometry = geometry_utils
        self.style_manager = style_manager
        self.debug = debug

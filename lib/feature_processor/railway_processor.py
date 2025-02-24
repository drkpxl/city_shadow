# lib/feature_processor/railway_processor.py
from .linear_processor import LinearFeatureProcessor

class RailwayProcessor(LinearFeatureProcessor):
    """Handles railway features using base linear processing"""
    
    FEATURE_TYPE = "railway"
    feature_category = "railways"

    def process_railway(self, feature, features, transform):
        """Process railway feature using base class logic"""
        super().process_linear_feature(
            feature,
            features,
            transform,
            additional_tags=["service"]  # Preserve optional service tag
        )
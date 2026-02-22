from django.core.management.base import BaseCommand
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import joblib
import os
import numpy as np
from django.conf import settings


class Command(BaseCommand):
    help = 'Creates mock ML model files for testing when real models are not available'

    def handle(self, *args, **options):
        """Create mock model and scaler files."""
        
        try:
            # Ensure ml_models directory exists
            ml_models_dir = os.path.join(settings.BASE_DIR, 'app', 'ml_models')
            os.makedirs(ml_models_dir, exist_ok=True)
            
            # Create paths
            scaler_path = os.path.join(ml_models_dir, 'audio_scaler.pkl')
            model_path = os.path.join(ml_models_dir, 'audio_xgb.pkl')
            
            # Create a simple scaler
            scaler = StandardScaler()
            # Fit with dummy data (18 features)
            dummy_data = np.random.randn(100, 18)
            scaler.fit(dummy_data)
            
            # Save scaler
            joblib.dump(scaler, scaler_path)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Scaler created: {scaler_path}')
            )
            
            # Create a simple RandomForest model as placeholder
            # (XGBoost would require xgboost library)
            model = RandomForestClassifier(n_estimators=10, random_state=42)
            
            # Train on dummy data
            dummy_labels = np.random.randint(0, 2, 100)
            model.fit(scaler.transform(dummy_data), dummy_labels)
            
            # Save model
            joblib.dump(model, model_path)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Model created: {model_path}')
            )
            
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  NOTE: These are mock models for testing only!\n'
                    '     For production, use real trained XGBoost models:\n'
                    f'     - {model_path}\n'
                    f'     - {scaler_path}'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error creating mock models: {e}')
            )

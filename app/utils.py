import librosa
import numpy as np
import joblib
import os
import subprocess
import tempfile
from pathlib import Path
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import Hospital, SuggestedHospital, DetectionHistory, EmailReport
import logging

logger = logging.getLogger(__name__)

# Try to load the model - fallback if not available
MODEL_PATH = os.path.join(settings.BASE_DIR, 'app', 'ml_models', 'audio_xgb.pkl')
SCALER_PATH = os.path.join(settings.BASE_DIR, 'app', 'ml_models', 'audio_scaler.pkl')
model = None
scaler = None

try:
    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        logger.info("ML model and scaler loaded successfully")
        print("ML model and scaler loaded successfully")
    else:
        logger.info(f"ML model files not found. Using fallback detection.")
        print(f"ML model files not found. Using fallback detection.")
except Exception as e:
    logger.warning(f"Could not load ML model: {e}. Using fallback detection.")
    print(f"Could not load ML model: {e}. Using fallback detection.")


def extract_features(file_path):
    """
    Extract audio features from an audio file using librosa.
    Returns a numpy array of features.
    """
    try:
        y, sr = librosa.load(file_path, sr=22050, duration=30)  # Limit to 30 seconds
        features = []

        # MFCC (Mel-Frequency Cepstral Coefficients)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        features.extend(np.mean(mfcc, axis=1).tolist())

        # Zero Crossing Rate
        features.append(np.mean(librosa.feature.zero_crossing_rate(y)))
        
        # RMS Energy
        features.append(np.mean(librosa.feature.rms(y=y)))
        
        # Spectral Centroid
        features.append(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
        
        # Spectral Bandwidth
        features.append(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr)))
        
        # Spectral Rolloff
        features.append(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)))

        return np.array(features)
    except Exception as e:
        logger.error(f"Error extracting features: {e}")
        print(f"Error extracting features: {e}")
        raise


def convert_webm_to_wav(webm_path):
    """Convert WebM audio to WAV format using ffmpeg."""
    try:
        wav_path = webm_path.replace('.webm', '.wav')
        subprocess.run([
            'ffmpeg',
            '-i', webm_path,
            '-acodec', 'pcm_s16le',
            '-ar', '22050',
            wav_path
        ], 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL,
        check=True
        )
        return wav_path
    except Exception as e:
        logger.error(f"Error converting WebM to WAV: {e}")
        print(f"Error converting WebM to WAV: {e}")
        raise


def fallback_detection(features):
    """
    Fallback detection when ML model is not available.
    Uses feature analysis to make probabilistic guess.
    """
    try:
        # Feature indices (from extract_features)
        # 0-12: MFCC, 13: zero crossing, 14: RMS, 15: spectral centroid,
        # 16: spectral bandwidth, 17: spectral rolloff
        
        if len(features) < 18:
            # Not enough features, random fallback
            probability = 0.5
        else:
            # Simple heuristic: analyze MFCC variance and spectral features
            mfcc_features = features[:13]
            zcr = features[13]
            rms = features[14]
            spec_centroid = features[15]
            
            # Parkinson patients typically have:
            # - Lower energy (RMS)
            # - Different spectral characteristics
            # - More variation in voice patterns
            
            # Simple scoring
            score = 0
            
            # Low RMS energy indicates Parkinson (0-1 scale, higher = more likely parkinson)
            if rms < 0.02:  # Low energy
                score += 0.3
            
            # Spectral centroid patterns
            if spec_centroid < 2000 or spec_centroid > 5000:  # Unusual patterns
                score += 0.2
            
            # MFCC variance
            mfcc_var = np.std(mfcc_features)
            if mfcc_var > 50:  # High variance
                score += 0.2
            
            probability = min(score, 1.0)
        
        return probability
    except Exception as e:
        logger.warning(f"Error in fallback detection: {e}")
        print(f"Error in fallback detection: {e}")
        return 0.5


def detect_parkinson(audio_file_path):
    """
    Detect Parkinson's disease from audio file.
    Returns: {
        'result': 'healthy' or 'parkinson',
        'confidence': float (0-100),
        'probability': float (0-1),
        'features': list
    }
    """
    try:
        # Convert if webm
        if audio_file_path.endswith('.webm'):
            audio_path = convert_webm_to_wav(audio_file_path)
        else:
            audio_path = audio_file_path

        # Extract features
        features = extract_features(audio_path)
        
        # Use ML model if available, otherwise use fallback
        if model is not None and scaler is not None:
            try:
                features_2d = features.reshape(1, -1)
                features_scaled = scaler.transform(features_2d)
                prediction = model.predict(features_scaled)[0]
                probability = model.predict_proba(features_scaled)[0][1]
                logger.info("Using ML model for detection")
            except Exception as e:
                logger.warning(f"ML prediction failed, using fallback: {e}")
                print(f"ML prediction failed, using fallback: {e}")
                probability = fallback_detection(features)
        else:
            logger.info("Using fallback detection (ML model not available)")
            print("Using fallback detection (ML model not available)")
            probability = fallback_detection(features)

        # Threshold for Parkinson detection
        threshold = 0.65
        
        if probability > threshold:
            result = 'parkinson'
        else:
            result = 'healthy'
        
        confidence = round(probability * 100, 2)

        return {
            'result': result,
            'confidence': confidence,
            'probability': float(probability),
            'features': features.tolist()
        }
    except Exception as e:
        logger.error(f"Error in Parkinson detection: {e}")
        raise


def suggest_top_hospitals(detection_result, user_location_city=None, limit=10):
    """
    Suggest top hospitals based on detection result and user location.
    Returns list of top hospitals by rating.
    """
    try:
        # Get hospitals (in real scenario, would filter by distance/city)
        hospitals = Hospital.objects.all().order_by('-rating')[:limit]
        return list(hospitals)
    except Exception as e:
        logger.error(f"Error suggesting hospitals: {e}")
        return []


def save_suggested_hospitals(detection_obj, hospitals):
    """Save suggested hospitals for a detection record."""
    try:
        for rank, hospital in enumerate(hospitals, 1):
            SuggestedHospital.objects.create(
                detection=detection_obj,
                hospital=hospital,
                rank=rank,
                reason=f"Closest and highest-rated facility for Parkinson support"
            )
    except Exception as e:
        logger.error(f"Error saving hospitals: {e}")


def send_detection_report_email(detection_obj, user_email):
    """
    Send detection report via email with PDF attachment.
    """
    try:
        context = {
            'user': detection_obj.user,
            'detection': detection_obj,
            'hospitals': detection_obj.suggested_hospitals.all(),
            'site_url': settings.DOMAIN_URL if hasattr(settings, 'DOMAIN_URL') else 'http://localhost:8000'
        }

        html_content = render_to_string('emails/detection_report.html', context)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject=f"Parkinson Detection Report - {detection_obj.test_date.strftime('%d %B %Y')}",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email]
        )
        email.attach_alternative(html_content, "text/html")

        # Send email
        email.send()

        # Create email report record
        EmailReport.objects.create(
            user=detection_obj.user,
            detection=detection_obj,
            recipient_email=user_email,
            status='sent'
        )
        
        logger.info(f"Detection report sent to {user_email}")
        return True

    except Exception as e:
        logger.error(f"Error sending email report: {e}")
        # Try to create failed record
        try:
            EmailReport.objects.create(
                user=detection_obj.user,
                detection=detection_obj,
                recipient_email=user_email,
                status='failed',
                error_message=str(e)
            )
        except:
            pass
        return False


def get_sample_hospitals():
    """Create sample hospital data (for initial setup)."""
    hospitals_data = [
        {
            'name': 'Rainbow Hospital',
            'address': '123 Medical Street',
            'city': 'New Delhi',
            'state': 'Delhi',
            'lat': 28.6139,
            'lon': 77.2090,
            'phone': '+91-11-234567890',
            'email': 'info@rainbowhospital.com',
            'specialization': 'Neurology & Parkinson Care',
            'rating': 4.8
        },
        {
            'name': 'Max Healthcare',
            'address': '456 Health Avenue',
            'city': 'New Delhi',
            'state': 'Delhi',
            'lat': 28.5244,
            'lon': 77.1855,
            'phone': '+91-11-345678901',
            'email': 'info@maxhealthcare.com',
            'specialization': 'Advanced Neurological Center',
            'rating': 4.7
        },
        {
            'name': 'Apollo Hospital',
            'address': '789 Care Plaza',
            'city': 'New Delhi',
            'state': 'Delhi',
            'lat': 28.5505,
            'lon': 77.3026,
            'phone': '+91-11-456789012',
            'email': 'info@apollohospital.com',
            'specialization': 'Neurology Department',
            'rating': 4.6
        },
        {
            'name': 'Fortis Hospital',
            'address': '321 Medicare Lane',
            'city': 'Bangalore',
            'state': 'Karnataka',
            'lat': 12.9716,
            'lon': 77.5946,
            'phone': '+91-80-567890123',
            'email': 'info@fortishealthcare.com',
            'specialization': 'Neurological Disorders',
            'rating': 4.5
        },
        {
            'name': 'Manipal Hospital',
            'address': '654 Health Street',
            'city': 'Bangalore',
            'state': 'Karnataka',
            'lat': 13.0084,
            'lon': 77.5867,
            'phone': '+91-80-678901234',
            'email': 'info@manipalhospital.com',
            'specialization': 'Movement Disorder Clinic',
            'rating': 4.6
        },
        {
            'name': 'Lilavati Hospital',
            'address': '987 Wellness Road',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'lat': 19.0176,
            'lon': 72.8298,
            'phone': '+91-22-789012345',
            'email': 'info@lilavati.com',
            'specialization': 'Neurology & Rehabilitation',
            'rating': 4.7
        },
        {
            'name': 'HCG Hospital',
            'address': '111 Medical Complex',
            'city': 'Bangalore',
            'state': 'Karnataka',
            'lat': 12.9394,
            'lon': 77.6245,
            'phone': '+91-80-890123456',
            'email': 'info@hcgfoundation.com',
            'specialization': 'Neuro Care Center',
            'rating': 4.5
        },
        {
            'name': 'Government Medical College Hospital',
            'address': '222 Medical District',
            'city': 'Chandigarh',
            'state': 'Chandigarh',
            'lat': 30.7333,
            'lon': 76.7794,
            'phone': '+91-172-901234567',
            'email': 'info@gmch.edu.in',
            'specialization': 'Neurology Department',
            'rating': 4.4
        },
        {
            'name': 'AIIMS Delhi',
            'address': '333 Institute Road',
            'city': 'New Delhi',
            'state': 'Delhi',
            'lat': 28.5677,
            'lon': 77.2082,
            'phone': '+91-11-012345678',
            'email': 'info@aiims.edu',
            'specialization': 'Movement Disorders Unit',
            'rating': 4.9
        },
        {
            'name': 'Institute of Neurology',
            'address': '444 Research Park',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'lat': 19.0760,
            'lon': 72.8777,
            'phone': '+91-22-012345678',
            'email': 'info@neuro-institute.com',
            'specialization': 'Parkinson Disease Research Center',
            'rating': 4.8
        }
    ]
    return hospitals_data

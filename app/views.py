from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.conf import settings
from django.db.models import Q
import os
import logging
import random
from pathlib import Path

from .models import UserProfile, DetectionHistory, Hospital, EmailReport, SuggestedHospital
from .forms import UserForm, UserProfileForm, AudioUploadForm
from .utils import (
    extract_features, detect_parkinson, suggest_top_hospitals,
    save_suggested_hospitals, send_detection_report_email, get_sample_hospitals
)

logger = logging.getLogger(__name__)


def get_random_hospitals(limit=10):
    """Get random hospitals from database."""
    all_hospitals = Hospital.objects.all()
    if all_hospitals.count() <= limit:
        return list(all_hospitals.values('id', 'name', 'phone', 'specialization', 'rating'))
    
    random_hospitals = random.sample(list(all_hospitals), limit)
    return [
        {
            'id': h.id,
            'name': h.name,
            'phone': h.phone,
            'specialization': h.specialization,
            'rating': h.rating
        }
        for h in random_hospitals
    ]


def home(request):
    """Home page with Parkinson disease information."""
    context = {
        'title': 'Parkinson Detection System',
        'total_tests': DetectionHistory.objects.count(),
        'total_users': UserProfile.objects.count(),
    }
    return render(request, 'index.html', context)


@login_required(login_url='account_login')
def test_page(request):
    """Audio test/detection page."""
    form = AudioUploadForm()
    context = {
        'form': form,
        'title': 'Parkinson Detection Test'
    }
    return render(request, 'test.html', context)


@login_required(login_url='account_login')
@require_http_methods(["POST"])
def upload_audio(request):
    """Handle audio file upload and process detection."""
    try:
        form = AudioUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            audio_file = request.FILES.get('audio_file')
            
            # Create temporary path
            temp_path = default_storage.save(
                f'temp/{audio_file.name}',
                audio_file
            )
            full_path = os.path.join(settings.MEDIA_ROOT, temp_path)
            
            # Ensure full path exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Perform detection
            detection_data = detect_parkinson(full_path)
            
            # Save detection record
            detection = DetectionHistory.objects.create(
                user=request.user,
                audio_file=audio_file,
                detection_result=detection_data['result'],
                confidence=detection_data['confidence'],
                test_type='upload',
                features_data={'features': detection_data['features']}
            )
            
            # Only suggest hospitals if Parkinson is detected
            if detection_data['result'] == 'parkinson':
                hospitals = suggest_top_hospitals(detection_data['result'], limit=10)
                save_suggested_hospitals(detection, hospitals)
            
            # Send email report
            send_detection_report_email(detection, request.user.email)
            
            # Get random hospitals for display (only for parkinson)
            hospitals = get_random_hospitals(limit=10) if detection_data['result'] == 'parkinson' else []
            
            # Clean up temp file
            try:
                if os.path.exists(full_path):
                    os.remove(full_path)
                default_storage.delete(temp_path)
            except:
                pass
            
            return JsonResponse({
                'success': True,
                'result': detection_data['result'],
                'confidence': detection_data['confidence'],
                'detection_id': detection.id,
                'hospitals': hospitals,
                'message': 'Detection completed. Report sent to your email!'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid form submission'
            }, status=400)
    
    except Exception as e:
        logger.error(f"Error in upload_audio: {e}", exc_info=True)
        error_msg = str(e)
        
        # Provide user-friendly error messages
        if "model" in error_msg.lower() or "scaler" in error_msg.lower():
            user_msg = "Audio processing system is initializing. Please try again in a moment."
        elif "audio" in error_msg.lower() or "format" in error_msg.lower():
            user_msg = "The audio file format is not supported. Please use MP3 or WAV."
        elif "ffmpeg" in error_msg.lower():
            user_msg = "Audio conversion service is not available. Please try again."
        else:
            user_msg = "Error processing audio. Please try again with a different file."
        
        return JsonResponse({
            'success': False,
            'error': user_msg,
            'debug_error': error_msg if settings.DEBUG else None
        }, status=500)


@login_required(login_url='account_login')
@require_http_methods(["POST"])
def record_and_detect(request):
    """Handle recorded audio from browser and process detection."""
    try:
        if 'audio_blob' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No audio data provided'
            }, status=400)
        
        audio_file = request.FILES['audio_blob']
        
        # Rename the audio file with a proper name
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        audio_filename = f'recorded_{timestamp}.webm'
        audio_file.name = audio_filename
        
        # Create temporary path
        temp_path = default_storage.save(
            f'temp/{audio_filename}',
            audio_file
        )
        full_path = os.path.join(settings.MEDIA_ROOT, temp_path)
        
        # Perform detection
        detection_data = detect_parkinson(full_path)
        
        # Save detection record with properly renamed audio file
        detection = DetectionHistory.objects.create(
            user=request.user,
            audio_file=audio_file,
            detection_result=detection_data['result'],
            confidence=detection_data['confidence'],
            test_type='record',
            features_data={'features': detection_data['features']}
        )
        
        # Only suggest hospitals if Parkinson is detected
        if detection_data['result'] == 'parkinson':
            hospitals = suggest_top_hospitals(detection_data['result'], limit=10)
            save_suggested_hospitals(detection, hospitals)
        
        # Send email report
        send_detection_report_email(detection, request.user.email)
        
        # Get random hospitals for display (only for parkinson)
        hospitals = get_random_hospitals(limit=10) if detection_data['result'] == 'parkinson' else []
        
        # Clean up temp file
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
            default_storage.delete(temp_path)
        except:
            pass
        
        return JsonResponse({
            'success': True,
            'result': detection_data['result'],
            'confidence': detection_data['confidence'],
            'detection_id': detection.id,
            'hospitals': hospitals,
            'message': 'Detection completed. Report sent to your email!'
        })
    
    except Exception as e:
        logger.error(f"Error in record_and_detect: {e}", exc_info=True)
        error_msg = str(e)
        
        # Provide user-friendly error messages
        if "model" in error_msg.lower() or "scaler" in error_msg.lower():
            user_msg = "Audio processing system is initializing. Please try again in a moment."
        elif "audio" in error_msg.lower() or "format" in error_msg.lower():
            user_msg = "The recording could not be processed. Please try recording again."
        elif "ffmpeg" in error_msg.lower():
            user_msg = "Audio conversion service is not available. Please try again."
        else:
            user_msg = "Error processing recording. Please try again."
        
        return JsonResponse({
            'success': False,
            'error': user_msg,
            'debug_error': error_msg if settings.DEBUG else None
        }, status=500)


@login_required(login_url='account_login')
def history(request):
    """Display user's detection history."""
    detections = DetectionHistory.objects.filter(user=request.user)
    
    context = {
        'detections': detections,
        'title': 'Detection History',
        'stats': {
            'total': detections.count(),
            'parkinson': detections.filter(detection_result='parkinson').count(),
            'healthy': detections.filter(detection_result='healthy').count(),
        }
    }
    return render(request, 'history.html', context)


@login_required(login_url='account_login')
def detection_detail(request, detection_id):
    """View details of a specific detection."""
    detection = get_object_or_404(DetectionHistory, id=detection_id, user=request.user)
    
    context = {
        'detection': detection,
        'hospitals': detection.suggested_hospitals.all(),
        'email_report': EmailReport.objects.filter(detection=detection).first(),
        'title': f'Detection Report - {detection.test_date.strftime("%d %b %Y")}'
    }
    return render(request, 'detection_detail.html', context)


@login_required(login_url='account_login')
def profile(request):
    """User profile view and update."""
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            for field, errors in profile_form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'user_profile': user_profile,
        'title': 'My Profile'
    }
    return render(request, 'profile.html', context)


@login_required(login_url='account_login')
def initialize_hospitals(request):
    """Initialize sample hospitals (admin only)."""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        if Hospital.objects.exists():
            return JsonResponse({'message': 'Hospitals already exist'})
        
        hospitals_data = get_sample_hospitals()
        
        for data in hospitals_data:
            Hospital.objects.create(**data)
        
        return JsonResponse({
            'success': True,
            'message': f'Created {len(hospitals_data)} hospitals'
        })
    except Exception as e:
        logger.error(f"Error initializing hospitals: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required(login_url='account_login')
def download_report(request, detection_id):
    """Download detection report as PDF."""
    detection = get_object_or_404(DetectionHistory, id=detection_id, user=request.user)
    
    try:
        from django.http import FileResponse
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from io import BytesIO
        from datetime import datetime
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2e5090'),
            spaceAfter=30,
            alignment=1
        )
        story.append(Paragraph("Parkinson Detection Report", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # User Info
        user_info = [
            ['Name:', f"{request.user.first_name} {request.user.last_name}"],
            ['Email:', request.user.email],
            ['Report Date:', detection.test_date.strftime('%d %b %Y, %H:%M')],
        ]
        
        info_table = Table(user_info)
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Detection Results
        result_text = "Parkinson Detected" if detection.detection_result == 'parkinson' else "Healthy"
        result_color = colors.red if detection.detection_result == 'parkinson' else colors.green
        
        result_style = ParagraphStyle(
            'ResultStyle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=result_color,
            spaceAfter=10
        )
        story.append(Paragraph(f"Detection Result: {result_text}", result_style))
        story.append(Paragraph(f"Confidence: {detection.confidence}%", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Recommended Hospitals
        if detection.suggested_hospitals.exists():
            story.append(Paragraph("Recommended Hospitals", styles['Heading2']))
            story.append(Spacer(1, 0.1*inch))
            
            hospitals_data = [['Rank', 'Hospital Name', 'Specialization']]
            for suggested in detection.suggested_hospitals.all():
                hospitals_data.append([
                    str(suggested.rank),
                    suggested.hospital.name,
                    suggested.hospital.specialization
                ])
            
            hospitals_table = Table(hospitals_data, colWidths=[0.5*inch, 2.5*inch, 2.5*inch])
            hospitals_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(hospitals_table)
        
        doc.build(story)
        buffer.seek(0)
        
        response = FileResponse(buffer, as_attachment=True, filename=f'report_{detection.id}.pdf')
        response['Content-Type'] = 'application/pdf'
        return response
        
    except ImportError:
        messages.warning(request, 'PDF generation requires reportlab. Please install: pip install reportlab')
        return redirect('detection_detail', detection_id=detection.id)
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        messages.error(request, 'Error generating report')
        return redirect('detection_detail', detection_id=detection.id)


# Values-based prediction (biomedical voice features)
VALUES_FEATURE_NAMES = [
    "MDVP:Fo(Hz)", "MDVP:Fhi(Hz)", "MDVP:Flo(Hz)",
    "MDVP:Jitter(%)", "MDVP:Jitter(Abs)", "MDVP:RAP",
    "MDVP:PPQ", "Jitter:DDP", "MDVP:Shimmer",
    "MDVP:Shimmer(dB)", "Shimmer:APQ3", "Shimmer:APQ5",
    "MDVP:APQ", "Shimmer:DDA", "NHR", "HNR",
    "RPDE", "DFA", "spread1", "spread2", "D2", "PPE"
]

# Load values-based models
VALUES_MODEL_PATH = os.path.join(settings.BASE_DIR, 'app', 'ml_models', 'xgb_model.pkl')
VALUES_SCALER_PATH = os.path.join(settings.BASE_DIR, 'app', 'ml_models', 'scaler.pkl')
values_model = None
values_scaler = None

try:
    if os.path.exists(VALUES_MODEL_PATH) and os.path.exists(VALUES_SCALER_PATH):
        import joblib
        values_model = joblib.load(VALUES_MODEL_PATH)
        values_scaler = joblib.load(VALUES_SCALER_PATH)
        logger.info("Values-based model and scaler loaded successfully")
    else:
        logger.warning(f"Values models not found at {VALUES_MODEL_PATH}")
except Exception as e:
    logger.warning(f"Could not load values-based models: {e}")


@login_required(login_url='account_login')
def values_test(request):
    """Show form for values-based Parkinson detection."""
    context = {
        'title': 'Parkinson Detection - Biomedical Features',
        'feature_names': VALUES_FEATURE_NAMES,
        'feature_groups': {
            'Frequency Features': ['MDVP:Fo(Hz)', 'MDVP:Fhi(Hz)', 'MDVP:Flo(Hz)'],
            'Jitter': ['MDVP:Jitter(%)', 'MDVP:Jitter(Abs)', 'MDVP:RAP', 'MDVP:PPQ', 'Jitter:DDP'],
            'Shimmer': ['MDVP:Shimmer', 'MDVP:Shimmer(dB)', 'Shimmer:APQ3', 'Shimmer:APQ5', 'MDVP:APQ', 'Shimmer:DDA'],
            'Noise Measures': ['NHR', 'HNR'],
            'Nonlinear Measures': ['RPDE', 'DFA', 'spread1', 'spread2', 'D2', 'PPE']
        }
    }
    return render(request, 'values_test.html', context)


@login_required(login_url='account_login')
@require_http_methods(["POST"])
def values_predict(request):
    """Predict Parkinson using biomedical voice features."""
    try:
        if not values_model or not values_scaler:
            return JsonResponse({
                'success': False,
                'error': 'Values-based model is not available. Please try again later.'
            }, status=500)
        
        # Collect feature values
        import numpy as np
        values = []
        for feature in VALUES_FEATURE_NAMES:
            try:
                value = float(request.POST.get(feature, 0))
                values.append(value)
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid value for {feature}'
                }, status=400)
        
        # Prepare for prediction
        values_array = np.array(values).reshape(1, -1)
        values_scaled = values_scaler.transform(values_array)
        
        # Get prediction
        prediction = values_model.predict(values_scaled)[0]
        probabilities = values_model.predict_proba(values_scaled)[0]
        probability = probabilities[1]  # Probability of Parkinson
        
        threshold = 0.75
        if probability > threshold:
            result = 'parkinson'
        else:
            result = 'healthy'
        
        confidence = round(probability * 100, 2)
        
        # Create a pseudo audio file for the detection record
        from django.core.files.base import ContentFile
        audio_filename = f'values_test_{request.user.id}_{int(np.random.rand() * 10000)}.txt'
        
        # Save detection record
        detection = DetectionHistory.objects.create(
            user=request.user,
            audio_file=ContentFile(b'values-based test', name=audio_filename),
            detection_result=result,
            confidence=confidence,
            test_type='values',
            features_data={
                'features': values,
                'feature_names': VALUES_FEATURE_NAMES,
                'raw_probability': float(probability)
            }
        )
        
        # Only suggest hospitals if Parkinson is detected
        if result == 'parkinson':
            hospitals_objects = suggest_top_hospitals(result, limit=10)
            save_suggested_hospitals(detection, hospitals_objects)
        
        # Send email report
        send_detection_report_email(detection, request.user.email)
        
        # Get random hospitals for JSON display (only for parkinson)
        hospitals = get_random_hospitals(limit=10) if result == 'parkinson' else []
        
        return JsonResponse({
            'success': True,
            'result': result,
            'confidence': confidence,
            'detection_id': detection.id,
            'hospitals': hospitals,
            'message': 'Detection completed. Report sent to your email!'
        })
        
    except Exception as e:
        logger.error(f"Error in values_predict: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error processing prediction. Please try again.',
            'debug_error': str(e) if settings.DEBUG else None
        }, status=500)
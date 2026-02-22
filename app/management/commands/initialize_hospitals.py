from django.core.management.base import BaseCommand
from app.models import Hospital
from app.utils import get_sample_hospitals

class Command(BaseCommand):
    help = 'Initialize sample hospitals in database'

    def handle(self, *args, **options):
        if Hospital.objects.exists():
            self.stdout.write(self.style.WARNING('Hospitals already exist in database'))
            return
        
        hospitals_data = get_sample_hospitals()
        
        for data in hospitals_data:
            Hospital.objects.create(**data)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {len(hospitals_data)} hospitals'))

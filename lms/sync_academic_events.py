from django.core.management.base import BaseCommand
from lms.models import AcademicEvent, EventType
from master.models import Assignment, StudentLeave
from lib.models import BorrowRecord
from datetime import date

class Command(BaseCommand):
    help = 'Sync academic events from assignments, leaves, book returns, and fees'

    def handle(self, *args, **kwargs):
        event_types = {
            'Assignment Due': EventType.objects.get_or_create(name='Assignment Due')[0],
            'Book Return': EventType.objects.get_or_create(name='Book Return')[0],
            'Student Leave': EventType.objects.get_or_create(name='Student Leave')[0],
            'Fees Due': EventType.objects.get_or_create(name='Fees Due')[0],
        }

        for a in Assignment.objects.all():
            AcademicEvent.objects.get_or_create(
                title=f"Assignment: {a.title}",
                date=a.due_date,
                event_type=event_types['Assignment Due']
            )

        for b in BorrowRecord.objects.filter(returned=False):
            AcademicEvent.objects.get_or_create(
                title=f"Return Book: {b.book.title}",
                date=b.return_due_date,
                event_type=event_types['Book Return']
            )

        for l in StudentLeave.objects.all():
            AcademicEvent.objects.get_or_create(
                title=f"Leave: {l.student.student_name}",
                date=l.leave_date,
                event_type=event_types['Student Leave']
            )

        AcademicEvent.objects.get_or_create(
            title="Fees Due",
            date=date(2025, 8, 20),
            event_type=event_types['Fees Due']
        )

        self.stdout.write(self.style.SUCCESS('Academic events synced successfully.'))


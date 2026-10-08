import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from tickets.models import Category, Ticket, TicketHistory

SAMPLES = {
    "Hardware": [
        "Laptop not powering on", "Keyboard keys not working", "Monitor flickering",
        "Printer paper jam", "Mouse not detected",
    ],
    "Software": [
        "Outlook keeps crashing", "Unable to install Office update", "VPN client login failed",
        "Antivirus license expired", "Excel file corrupted",
    ],
    "Network": [
        "Wi-Fi keeps disconnecting", "No internet in meeting room", "Shared drive not accessible",
        "Slow network speed", "VPN connection timeout",
    ],
}


class Command(BaseCommand):
    help = "Create sample categories and tickets for testing"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=25)
        parser.add_argument("--if-empty", action="store_true")

    def handle(self, *args, **options):
        if options["if_empty"] and Ticket.objects.exists():
            return
        random.seed(7)
        User = get_user_model()
        user, created = User.objects.get_or_create(username="demo_user")
        if created:
            user.set_password("Demo@12345")
            user.save()

        cats = {name: Category.objects.get_or_create(name=name)[0] for name in SAMPLES}

        for _ in range(options["count"]):
            cat_name = random.choice(list(SAMPLES))
            title = random.choice(SAMPLES[cat_name])
            ticket = Ticket.objects.create(
                title=title,
                description=f"Sample incident: {title}. Reported by an end user.",
                category=cats[cat_name],
                impact=random.randint(1, 3),
                urgency=random.randint(1, 3),
                created_by=user,
            )
            TicketHistory.objects.create(
                ticket=ticket, changed_by=user, action="Created",
                new_value=f"{ticket.priority} / {ticket.support_level}",
            )
            status = random.choice(["NEW", "OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"])
            if status != "NEW":
                ticket.status = status
                ticket.save()
                TicketHistory.objects.create(
                    ticket=ticket, changed_by=user, action="Status changed",
                    old_value="NEW", new_value=status,
                )

        self.stdout.write(self.style.SUCCESS(f"Created {options['count']} sample tickets"))
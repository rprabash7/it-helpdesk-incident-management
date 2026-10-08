from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Category, Ticket, TicketHistory

User = get_user_model()


def make_ticket(user, category, impact=2, urgency=2, title="Test ticket"):
    return Ticket.objects.create(
        title=title,
        description="Test description",
        category=category,
        impact=impact,
        urgency=urgency,
        created_by=user,
    )


class PriorityMatrixTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("user1", password="Pass@12345")
        self.category = Category.objects.create(name="Network")

    def test_all_nine_combinations(self):
        expected = {
            (1, 1): ("P1", "L3"),
            (1, 2): ("P2", "L2"),
            (2, 1): ("P2", "L2"),
            (1, 3): ("P3", "L1"),
            (2, 2): ("P3", "L1"),
            (3, 1): ("P3", "L1"),
            (2, 3): ("P4", "L1"),
            (3, 2): ("P4", "L1"),
            (3, 3): ("P4", "L1"),
        }
        for (impact, urgency), (priority, level) in expected.items():
            with self.subTest(impact=impact, urgency=urgency):
                ticket = make_ticket(self.user, self.category, impact, urgency)
                self.assertEqual(ticket.priority, priority)
                self.assertEqual(ticket.support_level, level)

    def test_priority_recalculates_on_edit_but_level_stays(self):
        ticket = make_ticket(self.user, self.category, impact=3, urgency=3)
        self.assertEqual((ticket.priority, ticket.support_level), ("P4", "L1"))
        ticket.impact = 1
        ticket.urgency = 1
        ticket.save()
        ticket.refresh_from_db()
        self.assertEqual(ticket.priority, "P1")
        self.assertEqual(ticket.support_level, "L1")

    def test_ticket_number_format(self):
        ticket = make_ticket(self.user, self.category)
        self.assertEqual(ticket.ticket_no, f"INC-{ticket.pk:05d}")


class TicketWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("user1", password="Pass@12345")
        self.other = User.objects.create_user("user2", password="Pass@12345")
        self.staff = User.objects.create_user("agent", password="Pass@12345", is_staff=True)
        self.category = Category.objects.create(name="Hardware")

    def test_login_required_for_list(self):
        response = self.client.get(reverse("ticket_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_create_ticket_writes_history(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("ticket_create"), {
            "title": "Laptop dead",
            "description": "Will not power on",
            "category": self.category.pk,
            "impact": 1,
            "urgency": 1,
        })
        ticket = Ticket.objects.get(title="Laptop dead")
        self.assertRedirects(response, reverse("ticket_detail", args=[ticket.pk]))
        self.assertEqual(ticket.created_by, self.user)
        self.assertEqual(ticket.priority, "P1")
        self.assertTrue(ticket.history.filter(action="Created").exists())

    def test_user_cannot_view_other_users_ticket(self):
        ticket = make_ticket(self.other, self.category)
        self.client.force_login(self.user)
        response = self.client.get(reverse("ticket_detail", args=[ticket.pk]))
        self.assertEqual(response.status_code, 404)

    def test_staff_can_view_any_ticket(self):
        ticket = make_ticket(self.other, self.category)
        self.client.force_login(self.staff)
        response = self.client.get(reverse("ticket_detail", args=[ticket.pk]))
        self.assertEqual(response.status_code, 200)

    def test_staff_escalation_moves_level_and_logs_history(self):
        ticket = make_ticket(self.user, self.category, impact=2, urgency=2)
        self.client.force_login(self.staff)
        self.client.post(reverse("ticket_detail", args=[ticket.pk]),
                         {"action": "escalate", "comment": "Needs L2"})
        ticket.refresh_from_db()
        self.assertEqual(ticket.support_level, "L2")
        entry = ticket.history.get(action="Escalated")
        self.assertEqual((entry.old_value, entry.new_value), ("L1", "L2"))

    def test_escalation_stops_at_l3(self):
        ticket = make_ticket(self.user, self.category, impact=1, urgency=1)
        self.client.force_login(self.staff)
        self.client.post(reverse("ticket_detail", args=[ticket.pk]), {"action": "escalate"})
        ticket.refresh_from_db()
        self.assertEqual(ticket.support_level, "L3")
        self.assertFalse(ticket.history.filter(action="Escalated").exists())

    def test_staff_status_update_logs_history(self):
        ticket = make_ticket(self.user, self.category)
        self.client.force_login(self.staff)
        self.client.post(reverse("ticket_detail", args=[ticket.pk]),
                         {"action": "status", "status": "RESOLVED"})
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "RESOLVED")
        self.assertTrue(TicketHistory.objects.filter(ticket=ticket, action="Status changed").exists())

    def test_normal_user_cannot_change_status_or_escalate(self):
        ticket = make_ticket(self.user, self.category)
        self.client.force_login(self.user)
        self.client.post(reverse("ticket_detail", args=[ticket.pk]),
                         {"action": "status", "status": "CLOSED"})
        self.client.post(reverse("ticket_detail", args=[ticket.pk]), {"action": "escalate"})
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "NEW")
        self.assertEqual(ticket.support_level, "L1")

    def test_search_and_priority_filter(self):
        make_ticket(self.user, self.category, 1, 1, title="Printer on fire")
        make_ticket(self.user, self.category, 3, 3, title="Mouse slow")
        self.client.force_login(self.staff)
        response = self.client.get(reverse("ticket_list"), {"q": "printer"})
        self.assertEqual([t.title for t in response.context["tickets"]], ["Printer on fire"])
        response = self.client.get(reverse("ticket_list"), {"priority": "P4"})
        self.assertEqual([t.title for t in response.context["tickets"]], ["Mouse slow"])

    def test_dashboard_counts(self):
        make_ticket(self.user, self.category, 1, 1)
        resolved = make_ticket(self.user, self.category, 2, 2)
        resolved.status = "RESOLVED"
        resolved.save()
        self.client.force_login(self.staff)
        stats = self.client.get(reverse("ticket_list")).context["stats"]
        self.assertEqual(stats, {"total": 2, "active": 1, "critical": 1, "resolved": 1})
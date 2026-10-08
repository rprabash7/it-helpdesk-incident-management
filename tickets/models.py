from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Ticket(models.Model):
    IMPACT_CHOICES = [(1, "High"), (2, "Medium"), (3, "Low")]
    URGENCY_CHOICES = [(1, "High"), (2, "Medium"), (3, "Low")]
    STATUS_CHOICES = [
        ("NEW", "New"),
        ("OPEN", "Open"),
        ("IN_PROGRESS", "In Progress"),
        ("RESOLVED", "Resolved"),
        ("CLOSED", "Closed"),
    ]
    LEVEL_CHOICES = [("L1", "Level 1"), ("L2", "Level 2"), ("L3", "Level 3")]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    impact = models.IntegerField(choices=IMPACT_CHOICES, default=2)
    urgency = models.IntegerField(choices=URGENCY_CHOICES, default=2)
    priority = models.CharField(max_length=2, editable=False, default="P3")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="NEW")
    support_level = models.CharField(max_length=2, choices=LEVEL_CHOICES, default="L1")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_tickets"
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="assigned_tickets",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def ticket_no(self):
        return f"INC-{self.pk:05d}"

    def calculate_priority(self):
        score = self.impact + self.urgency
        if score == 2:
            return "P1"
        if score == 3:
            return "P2"
        if score == 4:
            return "P3"
        return "P4"

    def route_level(self):
        return {"P1": "L3", "P2": "L2"}.get(self.priority, "L1")

    def save(self, *args, **kwargs):
        self.priority = self.calculate_priority()
        if self._state.adding:
            self.support_level = self.route_level()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_no} - {self.title}"


class TicketHistory(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="history")
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    action = models.CharField(max_length=50)
    old_value = models.CharField(max_length=100, blank=True)
    new_value = models.CharField(max_length=100, blank=True)
    comment = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name_plural = "Ticket history"

    def __str__(self):
        return f"{self.ticket.ticket_no}: {self.action}"
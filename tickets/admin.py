from django.contrib import admin
from .models import Category, Ticket, TicketHistory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ["name"]


class HistoryInline(admin.TabularInline):
    model = TicketHistory
    extra = 0
    readonly_fields = ["timestamp"]


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "category", "priority", "status", "support_level", "created_by", "created_at"]
    list_filter = ["priority", "status", "support_level", "category"]
    search_fields = ["title", "description"]
    inlines = [HistoryInline]


admin.site.register(TicketHistory)
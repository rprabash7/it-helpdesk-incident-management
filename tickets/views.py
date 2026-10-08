from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import TicketForm
from .models import Ticket, TicketHistory

LEVELS = ['L1', 'L2', 'L3']


def register(request):
    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('ticket_list')
    return render(request, 'registration/register.html', {'form': form})


def visible_tickets(user):
    qs = Ticket.objects.select_related('category', 'created_by')
    return qs if user.is_staff else qs.filter(created_by=user)


@login_required
def ticket_list(request):
    all_tickets = visible_tickets(request.user)
    active = all_tickets.exclude(status__in=['RESOLVED', 'CLOSED'])
    stats = {
        'total': all_tickets.count(),
        'active': active.count(),
        'critical': active.filter(priority='P1').count(),
        'resolved': all_tickets.filter(status__in=['RESOLVED', 'CLOSED']).count(),
    }

    tickets = all_tickets
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    if q:
        tickets = tickets.filter(
            Q(title__icontains=q) | Q(description__icontains=q) | Q(category__name__icontains=q)
        )
    if status:
        tickets = tickets.filter(status=status)
    if priority:
        tickets = tickets.filter(priority=priority)
    context = {
        'tickets': tickets,
        'stats': stats,
        'q': q,
        'status': status,
        'priority': priority,
        'status_choices': Ticket.STATUS_CHOICES,
        'priorities': ['P1', 'P2', 'P3', 'P4'],
    }
    return render(request, 'tickets/ticket_list.html', context)


@login_required
def ticket_create(request):
    form = TicketForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        ticket = form.save(commit=False)
        ticket.created_by = request.user
        ticket.save()
        TicketHistory.objects.create(
            ticket=ticket,
            changed_by=request.user,
            action='Created',
            new_value=f'{ticket.priority} / {ticket.support_level}',
        )
        messages.success(request, f'Ticket {ticket.ticket_no} created.')
        return redirect('ticket_detail', pk=ticket.pk)
    return render(request, 'tickets/ticket_form.html', {'form': form})


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(visible_tickets(request.user), pk=pk)

    if request.method == 'POST' and request.user.is_staff:
        action = request.POST.get('action')
        if action == 'status':
            new_status = request.POST.get('status')
            valid = dict(Ticket.STATUS_CHOICES)
            if new_status in valid and new_status != ticket.status:
                old = ticket.status
                ticket.status = new_status
                ticket.save()
                TicketHistory.objects.create(
                    ticket=ticket, changed_by=request.user, action='Status changed',
                    old_value=old, new_value=new_status,
                    comment=request.POST.get('comment', ''),
                )
                messages.success(request, 'Status updated.')
        elif action == 'escalate':
            idx = LEVELS.index(ticket.support_level)
            if idx < len(LEVELS) - 1:
                old = ticket.support_level
                ticket.support_level = LEVELS[idx + 1]
                ticket.save()
                TicketHistory.objects.create(
                    ticket=ticket, changed_by=request.user, action='Escalated',
                    old_value=old, new_value=ticket.support_level,
                    comment=request.POST.get('comment', ''),
                )
                messages.warning(request, f'Escalated to {ticket.support_level}.')
            else:
                messages.error(request, 'Already at the highest level (L3).')
        return redirect('ticket_detail', pk=ticket.pk)

    return render(request, 'tickets/ticket_detail.html', {
        'ticket': ticket,
        'history': ticket.history.select_related('changed_by'),
        'status_choices': Ticket.STATUS_CHOICES,
    })
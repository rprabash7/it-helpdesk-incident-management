# IT Helpdesk & Incident Management System

A Django-based service desk portal where users log IT incidents (hardware, software, network) and support staff track, prioritise, escalate and resolve them.

**Live demo:** <mee-live-url>

## Features
- User registration and login
- Incident logging by category
- Priority matrix (Impact x Urgency) giving P1 to P4
- Automatic routing to support level (L1, L2, L3)
- Status updates and ticket escalation by support staff
- Full ticket history (audit trail)
- Search and filter by text, status and priority
- Dashboard counts: total, active, active P1, resolved
- Django admin for categories and ticket management

## Priority Matrix

| Impact \ Urgency | High | Medium | Low |
|---|---|---|---|
| High | P1 (L3) | P2 (L2) | P3 (L1) |
| Medium | P2 (L2) | P3 (L1) | P4 (L1) |
| Low | P3 (L1) | P4 (L1) | P4 (L1) |

## Tech Stack
Python, Django, SQLite3, HTML5, CSS3, Bootstrap 5, Gunicorn, WhiteNoise, Render

## Run Locally
```bash
git clone [https://github.com/rprabash7/it-helpdesk-incident-management.git](https://github.com/rprabash7/it-helpdesk-incident-management.git)
cd it-helpdesk-incident-management
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_tickets
python manage.py runserver
```
Open http://127.0.0.1:8000/

`seed_tickets` creates 25 sample tickets and a `demo_user` account for testing.

## Screenshots
c:\Prabash\Projects\it_helpdesk\image.png

## Author
Prabash R
# Epic 08: Appointment Reminders

## Metadata
- **Epic ID:** EPIC-08
- **Priority:** P1 — Important
- **Phase:** 2
- **Depends On:** EPIC-02 (Notification Service)
- **Estimated Effort:** Medium
- **Affected Apps:** `notifications`, `accounts` (email templates)
- **Status:** `[x] Completed`

---

## Goal
Implement automatic appointment reminders via email and in-app notification, triggered by a Django management command run via system cron.

---

## Stories

### Story 8.1: Reminder Management Command
- **ID:** EPIC-08-S1
- **Status:** `[x] Completed`
- **Depends On:** EPIC-02

#### Tasks
- `[x]` Create `notifications/management/__init__.py` and `notifications/management/commands/__init__.py`
- `[x]` Create `notifications/management/commands/send_reminders.py`:
  - Query appointments where `slot__date = tomorrow` and `status IN (REQUESTED, CONFIRMED)`
  - For each appointment:
    - Send email reminder to patient using HTML template
    - Create in-app Notification record
  - Log number of reminders sent
  - Skip appointments that already have a reminder notification (idempotent)
- `[x]` Create email template `accounts/templates/emails/appointment_reminder.html`:
  - Patient name, doctor name, appointment date/time
  - "View Appointment" link

#### Acceptance Criteria
- [x] Running `python manage.py send_reminders` sends reminders for tomorrow's appointments
- [x] Email sent to each patient
- [x] In-app notification created
- [x] Idempotent — running twice doesn't duplicate reminders
- [x] Logs output (number sent, any errors)

#### Files to Create
- `notifications/management/__init__.py`
- `notifications/management/commands/__init__.py`
- `notifications/management/commands/send_reminders.py`
- `accounts/templates/emails/appointment_reminder.html`

---

### Story 8.2: Cron Configuration Documentation
- **ID:** EPIC-08-S2
- **Status:** `[x] Completed`
- **Depends On:** EPIC-08-S1

#### Tasks
- `[x]` Document cron setup in README or deployment docs:
  ```
  # Run at 6 PM daily (before next day's appointments)
  0 18 * * * cd /path/to/project && /path/to/venv/bin/python manage.py send_reminders >> /var/log/clinic_reminders.log 2>&1
  ```
- `[x]` Add `--dry-run` flag to management command for testing

#### Acceptance Criteria
- [x] Cron setup documented
- [x] `--dry-run` flag prints what would be sent without actually sending

#### Files to Modify
- `notifications/management/commands/send_reminders.py`
- `README.md`

---

## Definition of Done
- [x] Management command functional
- [x] Email reminders sent correctly
- [x] In-app notifications created
- [x] Idempotent execution
- [x] Cron setup documented
- [x] Existing tests pass

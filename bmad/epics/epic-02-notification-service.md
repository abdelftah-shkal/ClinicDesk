# Epic 02: Notification Service — Full Implementation

## Metadata
- **Epic ID:** EPIC-02
- **Priority:** P0 — Critical
- **Phase:** 1
- **Depends On:** None
- **Estimated Effort:** Medium
- **Affected Apps:** `notifications`, `appointments`, `payments`, templates
- **Status:** `[ ] Not Started`

---

## Goal

Transform the stub `notifications` app into a fully functional notification service with in-app notifications, email triggers, and a notification bell/page UI.

---

## Stories

### Story 2.1: Extend Notification Model
- **ID:** EPIC-02-S1
- **Status:** `[x] Completed`

#### Description
Add `title`, `notification_type`, `created_at`, and `link` fields to the existing Notification model.

#### Tasks
- `[x]` Modify `notifications/models.py`:
  - Add `title = CharField(max_length=200)`
  - Add `notification_type = CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)`
    - Choices: `APPOINTMENT`, `PAYMENT`, `REMINDER`, `SYSTEM`
  - Add `created_at = DateTimeField(auto_now_add=True)`
  - Add `link = CharField(max_length=500, blank=True)` — relative URL to navigate to
- `[x]` Add class method: `Notification.create_notification(user, title, message, notification_type, link="")`
- `[x]` Run `python manage.py makemigrations notifications`
- `[x]` Run `python manage.py migrate`

#### Acceptance Criteria
- [x] Model has all 4 new fields
- [x] Migration succeeds with existing data
- [x] `create_notification` class method works

#### Files to Modify
- `notifications/models.py`

---

### Story 2.2: Notification Views & URLs
- **ID:** EPIC-02-S2
- **Status:** `[x] Completed`
- **Depends On:** EPIC-02-S1

#### Description
Create views for listing notifications, marking as read, and marking all as read.

#### Tasks
- `[x]` Create `notifications/views.py`:
  - `NotificationListView` — paginated (20/page), ordered by `-created_at`, filtered to `request.user`
  - `mark_notification_read(request, pk)` — AJAX POST, marks single notification as read, returns JSON
  - `mark_all_read(request)` — AJAX POST, marks all user notifications as read, returns JSON
  - `unread_count(request)` — AJAX GET, returns `{"count": N}` for badge updates
- `[x]` Create `notifications/urls.py`:
  - `path('', NotificationListView.as_view(), name='notification-list')`
  - `path('<int:pk>/read/', mark_notification_read, name='notification-mark-read')`
  - `path('read-all/', mark_all_read, name='notification-mark-all-read')`
  - `path('unread-count/', unread_count, name='notification-unread-count')`
- `[x]` Register in `clinic/urls.py`: `path('notifications/', include('notifications.urls'))`

#### Acceptance Criteria
- [x] Notification list shows all user's notifications with pagination
- [x] AJAX mark-read works without page reload
- [x] Mark-all-read clears all unread notifications
- [x] Unread count endpoint returns correct count
- [x] All views require authentication

#### Files to Create
- `notifications/urls.py` (or overwrite the empty one)
- `notifications/templates/notifications/notification_list.html`

#### Files to Modify
- `notifications/views.py`
- `clinic/urls.py`

---

### Story 2.3: Notification Signals (Auto-Create Notifications)
- **ID:** EPIC-02-S3
- **Status:** `[x] Completed`
- **Depends On:** EPIC-02-S1

#### Description
Wire Django signals to automatically create notifications on key events.

#### Tasks
- `[x]` Create `notifications/services.py`:
  - `notify_appointment_created(appointment)` — notifies patient
  - `notify_appointment_status_changed(appointment, old_status, new_status)` — notifies patient
  - `notify_appointment_cancelled(appointment)` — notifies patient + doctor
  - `notify_payment_completed(transaction)` — notifies patient
  - `notify_payment_refunded(transaction)` — notifies patient
- `[x]` Create `notifications/signals.py`:
  - `post_save` on `Appointment` → call appropriate notification service
  - `post_save` on `PaymentTransaction` when status changes to PAID or REFUNDED
- `[x]` Register signals in `notifications/apps.py` → `ready()` method
- `[x]` Import signals module in `notifications/__init__.py` if needed

#### Acceptance Criteria
- [x] Notification auto-created when appointment is booked
- [x] Notification auto-created when appointment status changes (confirmed, checked-in, completed, cancelled)
- [x] Notification auto-created when payment is successful
- [x] Notification auto-created when refund is processed
- [x] Each notification has correct type, title, message, and link

#### Files to Create
- `notifications/services.py`
- `notifications/signals.py`

#### Files to Modify
- `notifications/apps.py`

---

### Story 2.4: Notification Bell UI Component
- **ID:** EPIC-02-S4
- **Status:** `[x] Completed`
- **Depends On:** EPIC-02-S2

#### Description
Add a notification bell icon with unread count badge to the dashboard layout (sidebar or topbar).

#### Tasks
- `[x]` Modify the dashboard topbar or sidebar template:
  - Add bell icon with badge showing unread count
  - Badge updates via AJAX poll (every 30 seconds) or on page load
  - Click opens notification list page (or dropdown)
- `[x]` Add JavaScript for:
  - Fetching unread count from `/notifications/unread-count/`
  - Updating badge number
  - Marking individual notifications as read
- `[x]` Style notification badge with Bootstrap badge classes

#### Acceptance Criteria
- [x] Bell icon visible in dashboard for all authenticated users
- [x] Badge shows correct unread count
- [x] Badge updates without full page reload
- [x] Clicking bell navigates to notification list

#### Files to Modify
- `dashboard/templates/dashboard/partials/_topbar.html` or `_sidebar.html`
- Add JS to base template or separate JS file

---

## Definition of Done
- [x] All 4 stories completed
- [x] Notifications auto-created for all key events
- [x] Notification list view accessible from dashboard
- [x] Bell icon shows unread count
- [x] Mark-read functionality works
- [x] All views require authentication
- [x] Existing tests pass

# Epic 10: Clinic Settings & Services Admin

## Metadata
- **Epic ID:** EPIC-10
- **Priority:** P1 — Important
- **Phase:** 2
- **Depends On:** None
- **Estimated Effort:** Medium
- **Affected Apps:** `clinic`, `admin_panel`
- **Status:** `[x] Completed`

---

## Goal
Create ClinicSettings and ClinicService models, and admin views for managing clinic configuration, services, and working hours.

---

## Stories

### Story 10.1: ClinicSettings Model (Singleton)
- **ID:** EPIC-10-S1
- **Status:** `[x] Completed`

#### Tasks
- `[x]` Create `clinic/models.py` (currently does not exist as a models file):
  - `ClinicSettings` model:
    - `clinic_name` (CharField 200), `clinic_address` (TextField), `clinic_phone` (CharField 20)
    - `clinic_email` (EmailField), `logo` (ImageField upload_to='clinic/', blank)
    - `working_days` (JSONField default=list), `opening_time` (TimeField), `closing_time` (TimeField)
    - `default_slot_duration` (PositiveIntegerField default=30), `currency` (CharField 10 default='EGP')
  - Override `save()` to enforce singleton (only one instance)
  - Class method `get_settings()` to retrieve or create the single instance
- `[x]` Run migrations for `clinic` app (may need to add `clinic` to INSTALLED_APPS if not already)
- `[x]` Register in admin

#### Acceptance Criteria
- [x] Only one ClinicSettings instance can exist
- [x] `get_settings()` returns the singleton instance
- [x] All fields have sensible defaults

#### Files to Create/Modify
- `clinic/models.py` (may need to create or modify existing)

---

### Story 10.2: ClinicService Model (M2M with Doctors)
- **ID:** EPIC-10-S2
- **Status:** `[x] Completed`

#### Tasks
- `[x]` Create `ClinicService` model in `clinic/models.py`:
  - `name` (CharField 200), `description` (TextField), `icon` (CharField 50 — Bootstrap icon class)
  - `price_range` (CharField 100), `is_active` (BooleanField default=True)
  - `display_order` (PositiveIntegerField default=0)
  - `doctors` (ManyToManyField to CustomUser, limit_choices_to={'role': 'DOCTOR'}, blank=True)
- `[x]` Run migrations
- `[x]` Register in admin

#### Acceptance Criteria
- [x] Services can be linked to multiple doctors
- [x] Doctors can provide multiple services
- [x] Ordering by `display_order`

#### Files to Modify
- `clinic/models.py`

---

### Story 10.3: Admin Clinic Settings View
- **ID:** EPIC-10-S3
- **Status:** `[x] Completed`
- **Depends On:** EPIC-10-S1

#### Tasks
- `[x]` Create `ClinicSettingsForm` in `admin_panel/forms.py`
- `[x]` Create `ClinicSettingsView` in `admin_panel/views.py` (AdminRequired):
  - GET: load current settings (or create default)
  - POST: validate and save
- `[x]` Create template `admin_panel/templates/admin_panel/clinic_settings.html`
- `[x]` Add URL and sidebar link for admin

#### Acceptance Criteria
- [x] Admin can view and edit all clinic settings
- [x] Logo upload works (to `media/clinic/`)
- [x] Only admin can access

#### Files to Create
- `admin_panel/templates/admin_panel/clinic_settings.html`

#### Files to Modify
- `admin_panel/forms.py`, `admin_panel/views.py`, `admin_panel/urls.py`, sidebar template

---

### Story 10.4: Admin Service CRUD
- **ID:** EPIC-10-S4
- **Status:** `[x] Completed`
- **Depends On:** EPIC-10-S2

#### Tasks
- `[x]` Create `ServiceForm` in `admin_panel/forms.py`: all fields + doctor multiselect
- `[x]` Create views in `admin_panel/views.py`:
  - `ServiceListView` — list all services with edit/delete actions
  - `ServiceCreateView` — create new service
  - `ServiceEditView` — edit existing service
  - `ServiceDeleteView` — delete service (POST only)
- `[x]` Create templates: `service_list.html`, `service_form.html`
- `[x]` Add URLs and sidebar links

#### Acceptance Criteria
- [x] Admin can list, create, edit, delete services
- [x] Doctor multiselect working for service-doctor linking
- [x] Only admin can access

#### Files to Create
- `admin_panel/templates/admin_panel/service_list.html`
- `admin_panel/templates/admin_panel/service_form.html`

#### Files to Modify
- `admin_panel/forms.py`, `admin_panel/views.py`, `admin_panel/urls.py`, sidebar template

---

## Definition of Done
- [x] All 4 stories completed
- [x] ClinicSettings singleton working
- [x] Service CRUD with doctor M2M functional
- [x] Admin sidebar has settings and services links
- [x] Existing tests pass

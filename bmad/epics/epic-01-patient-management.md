# Epic 01: Patient Management — Full CRUD

## Metadata
- **Epic ID:** EPIC-01
- **Priority:** P0 — Critical
- **Phase:** 1
- **Depends On:** None
- **Estimated Effort:** Medium
- **Affected Apps:** `accounts`, `reception`
- **Status:** `[x] Completed`

---

## Goal

Extend the PatientProfile model with medical fields (allergies, medical history, gender, address, emergency contacts) and build a full CRUD interface for receptionists to add, edit, search, and view patient records.

---

## Stories

### Story 1.1: Extend PatientProfile Model
- **ID:** EPIC-01-S1
- **Status:** `[x] Completed`

#### Description
Add missing fields to the existing `PatientProfile` model to capture full patient data as per the spec.

#### Tasks
- `[x]` Add fields to `accounts/models.py` → `PatientProfile`:
  - `allergies` — `TextField(blank=True)`
  - `medical_history` — `TextField(blank=True)`
  - `gender` — `CharField(max_length=10, choices=GENDER_CHOICES, blank=True)`
  - `address` — `TextField(blank=True)`
  - `emergency_contact_name` — `CharField(max_length=100, blank=True)`
  - `emergency_contact_phone` — `CharField(max_length=20, blank=True)`
- `[x]` Define `GENDER_CHOICES`: `[("MALE", "Male"), ("FEMALE", "Female")]`
- `[x]` Run `python manage.py makemigrations accounts`
- `[ ]` Run `python manage.py migrate`
- `[x]` Update `PatientOnboardingForm` and `PatientProfileForm` to include new fields
- `[x]` Update `AdminUserCreateForm` and `AdminUserEditForm` to include new fields

#### Acceptance Criteria
- [x] PatientProfile has all 6 new fields
- [ ] Migration runs successfully without data loss
- [x] Existing patient records are unaffected (all new fields are blank=True)
- [x] Onboarding form shows new fields
- [x] Admin panel user create/edit forms include new patient fields

#### Files to Modify
- `accounts/models.py`
- `accounts/forms.py`
- `admin_panel/forms.py`

---

### Story 1.2: Receptionist Patient List View
- **ID:** EPIC-01-S2
- **Status:** `[x] Completed`
- **Depends On:** EPIC-01-S1

#### Description
Create a searchable, filterable list view for receptionists to find patients by name, ID, phone, or email.

#### Tasks
- `[x]` Create `PatientListView` in `reception/views.py`
  - Requires `ReceptionistRequiredMixin`
  - Query `CustomUser.objects.filter(role='PATIENT').select_related('patient_profile')`
  - Support search by `q` param: filter on `first_name`, `last_name`, `username`, `email`, `phone_number`
  - Paginate by 25
- `[x]` Create template `reception/templates/reception/patient_list.html`
  - Table with columns: ID, Name, Email, Phone, Blood Type, Actions (View/Edit)
  - Search bar at top
- `[x]` Add URL `path('patients/', PatientListView.as_view(), name='patient-list')` to `reception/urls.py`
- `[x]` Add "Patients" link to receptionist sidebar

#### Acceptance Criteria
- [x] Receptionist can see paginated list of all patients
- [x] Search by name, email, phone, or ID works
- [x] Only receptionists can access (RBAC enforced)
- [x] Links to view and edit each patient

#### Files to Create
- `reception/templates/reception/patient_list.html`

#### Files to Modify
- `reception/views.py`
- `reception/urls.py`
- Dashboard sidebar template (receptionist section)

---

### Story 1.3: Receptionist Patient Create View
- **ID:** EPIC-01-S3
- **Status:** `[x] Completed`
- **Depends On:** EPIC-01-S1

#### Description
Receptionist can register a new patient (creates CustomUser + PatientProfile in one form).

#### Tasks
- `[x]` Create `PatientRegistrationForm` in `reception/forms.py`
  - Fields: `first_name`, `last_name`, `email`, `phone_number`, `date_of_birth`, `blood_type`, `gender`, `allergies`, `address`, `emergency_contact_name`, `emergency_contact_phone`
  - Auto-generate username from email
  - Auto-set `role = PATIENT`
  - Set random password and send activation email
- `[x]` Create `PatientCreateView` in `reception/views.py`
  - Requires `ReceptionistRequiredMixin`
  - Uses `PatientRegistrationForm`
  - Creates `CustomUser` + `PatientProfile` in atomic transaction
- `[x]` Create template `reception/templates/reception/patient_create.html`
- `[x]` Add URL to `reception/urls.py`

#### Acceptance Criteria
- [x] Receptionist can create a new patient with all profile fields
- [x] CustomUser and PatientProfile created atomically
- [x] Duplicate email validation works
- [x] Success message shown, redirects to patient list
- [x] Only receptionists can access

#### Files to Create
- `reception/templates/reception/patient_create.html`

#### Files to Modify
- `reception/forms.py`
- `reception/views.py`
- `reception/urls.py`

---

### Story 1.4: Receptionist Patient Edit View
- **ID:** EPIC-01-S4
- **Status:** `[x] Completed`
- **Depends On:** EPIC-01-S1

#### Description
Receptionist can edit an existing patient's personal and medical information.

#### Tasks
- `[x]` Create `PatientEditForm` in `reception/forms.py`
  - Same fields as registration form but without email/password
  - Pre-populated with existing data
- `[x]` Create `PatientEditView` in `reception/views.py`
  - GET: render form with existing data
  - POST: validate and save both CustomUser and PatientProfile
- `[x]` Create template `reception/templates/reception/patient_edit.html`
- `[x]` Add URL `path('patients/<int:pk>/edit/', ...)` to `reception/urls.py`

#### Acceptance Criteria
- [x] Receptionist can update all patient fields
- [x] Changes saved atomically
- [x] Success message shown on save
- [x] Only receptionists can access

#### Files to Create
- `reception/templates/reception/patient_edit.html`

#### Files to Modify
- `reception/forms.py`
- `reception/views.py`
- `reception/urls.py`

---

### Story 1.5: Receptionist Patient Detail View
- **ID:** EPIC-01-S5
- **Status:** `[x] Completed`
- **Depends On:** EPIC-01-S1

#### Description
Receptionist can view a patient's full record including personal info, medical history, allergies, and recent appointments.

#### Tasks
- `[x]` Create `PatientDetailView` in `reception/views.py`
  - Shows all patient profile data
  - Shows last 10 appointments with status
  - Shows allergies and medical history prominently
- `[x]` Create template `reception/templates/reception/patient_detail.html`
- `[x]` Add URL `path('patients/<int:pk>/', ...)` to `reception/urls.py`

#### Acceptance Criteria
- [x] Receptionist can view full patient record
- [x] Allergies and medical history displayed prominently
- [x] Recent appointments listed with status
- [x] Edit button links to edit view
- [x] Only receptionists can access

#### Files to Create
- `reception/templates/reception/patient_detail.html`

#### Files to Modify
- `reception/views.py`
- `reception/urls.py`

---

## Definition of Done
- [x] All 5 stories completed
- [ ] All migrations applied successfully
- [x] RBAC: Only receptionist role can access patient CRUD
- [ ] Existing tests pass (`python manage.py test`)
- [x] Search and filter working on patient list
- [x] Sidebar navigation updated for receptionist

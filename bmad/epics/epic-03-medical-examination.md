# Epic 03: Medical Examination — Lab Results & Report Attachments

## Metadata
- **Epic ID:** EPIC-03
- **Priority:** P0 — Critical
- **Phase:** 1
- **Depends On:** None
- **Estimated Effort:** Medium
- **Affected Apps:** `emr`, `clinic` (settings for media)
- **Status:** `[x] Completed`

---

## Goal
Extend the EMR module to support lab results, test results, file attachments for medical reports, and a full patient history view accessible by doctors.

---

## Stories

### Story 3.1: Configure Media File Storage
- **ID:** EPIC-03-S1
- **Status:** `[x] Completed`

#### Tasks
- `[x]` Add `MEDIA_URL = '/media/'` and `MEDIA_ROOT = BASE_DIR / 'media'` to `clinic/settings.py`
- `[x]` Add `static(settings.MEDIA_URL, ...)` to `clinic/urls.py` in DEBUG block
- `[x]` Add `media/` to `.gitignore`

#### Acceptance Criteria
- [x] Media files serveable in development mode
- [x] `media/` excluded from git

#### Files to Modify
- `clinic/settings.py`, `clinic/urls.py`, `.gitignore`

---

### Story 3.2: Extend Consultation Model + Create MedicalReport Model
- **ID:** EPIC-03-S2
- **Status:** `[x] Completed`

#### Tasks
- `[x]` Add to `Consultation`: `lab_results = TextField(blank=True)`, `test_results = TextField(blank=True)`
- `[x]` Create `MedicalReport` model: `consultation` (FK), `file` (FileField), `report_type` (CharField choices: LAB/IMAGING/OTHER), `title` (CharField), `uploaded_at` (auto_now_add)
- `[x]` Run migrations

#### Acceptance Criteria
- [x] Consultation has lab/test result fields
- [x] MedicalReport model exists with file upload
- [x] Migration succeeds

#### Files to Modify
- `emr/models.py`

---

### Story 3.3: Update Consultation Form with Lab Results & File Upload
- **ID:** EPIC-03-S3
- **Status:** `[x] Completed`
- **Depends On:** EPIC-03-S1, EPIC-03-S2

#### Tasks
- `[x]` Add `lab_results`, `test_results` to `ConsultationForm`
- `[x]` Create `MedicalReportFormSet` using `inlineformset_factory`
- `[x]` Update `ConsultationCreateView` to handle file uploads (multipart form)
- `[x]` Update `consultation_form.html` with file upload section and `enctype="multipart/form-data"`

#### Acceptance Criteria
- [x] Doctor can enter lab/test results and upload report files
- [x] Files saved to `media/medical_reports/`
- [x] Uploaded files viewable/downloadable

#### Files to Modify
- `emr/forms.py`, `emr/views.py`, `emr/templates/emr/consultation_form.html`

---

### Story 3.4: Doctor — Full Patient Medical History View
- **ID:** EPIC-03-S4
- **Status:** `[x] Completed`
- **Depends On:** EPIC-03-S2

#### Tasks
- `[x]` Create `PatientMedicalHistoryView` in `emr/views.py` (DoctorRequiredMixin)
- `[x]` Query ALL consultations for a patient across all doctors
- `[x]` Create template `emr/templates/emr/patient_medical_history.html` (timeline of visits with prescriptions, lab results, reports)
- `[x]` Add URL: `path("patient/<int:patient_id>/history/", ...)`
- `[x]` Add "View Full History" link in doctor's daily queue

#### Acceptance Criteria
- [x] Doctor sees patient's full history across all doctors
- [x] Prescriptions, lab results, reports visible per visit
- [x] Patient allergies shown prominently
- [x] Only doctors can access (RBAC)

#### Files to Create
- `emr/templates/emr/patient_medical_history.html`

#### Files to Modify
- `emr/views.py`, `emr/urls.py`, `emr/templates/emr/daily_queue.html`

---

## Definition of Done
- [x] All 4 stories completed
- [x] Media storage working
- [x] Lab results and file uploads functional
- [x] Full patient history view accessible by doctors
- [x] Existing tests pass

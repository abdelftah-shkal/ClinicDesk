# Epic 05: Doctor — View Full Patient History
# Epic 06: Patient — Prescriptions List

## Metadata
- **Epic IDs:** EPIC-05, EPIC-06
- **Priority:** P0 — Critical
- **Phase:** 1
- **Depends On:** EPIC-03 (partially — model extensions)
- **Estimated Effort:** Low
- **Affected Apps:** `emr`
- **Status:** `[x] Completed`

---

## Goal
Enable doctors to view any patient's complete medical history and enable patients to view a dedicated list of all their prescriptions.

> **Note:** The doctor patient history view is covered in EPIC-03 Story 3.4. This epic covers the **patient-facing** prescriptions list.

---

## Stories

### Story 5.1: Patient Prescriptions List View
- **ID:** EPIC-05-S1
- **Status:** `[x] Completed`

#### Description
Create a dedicated page where patients can view all prescriptions issued to them across all visits.

#### Tasks
- `[x]` Create `PatientPrescriptionsListView` in `emr/views.py`:
  - Requires `PatientRequiredMixin`
  - Query: `Prescription.objects.filter(consultation__patient=request.user).select_related('consultation__appointment__slot', 'consultation__doctor').order_by('-consultation__appointment__slot__date')`
  - Group by consultation/visit date
  - Paginate by 20
- `[x]` Create template `emr/templates/emr/patient_prescriptions.html`:
  - Cards grouped by visit date
  - Each card: doctor name, date, medications with dosage & duration
  - Link to full consultation summary
- `[x]` Add URL: `path("my-prescriptions/", PatientPrescriptionsListView.as_view(), name="patient-prescriptions")`
- `[x]` Add "My Prescriptions" link to patient sidebar navigation

#### Acceptance Criteria
- [x] Patient can see all prescriptions across all visits
- [x] Prescriptions grouped by visit date
- [x] Doctor name, medication, dosage, duration displayed
- [x] Link to consultation summary for more details
- [x] Only patients can access (RBAC)
- [x] Sidebar has "My Prescriptions" link

#### Files to Create
- `emr/templates/emr/patient_prescriptions.html`

#### Files to Modify
- `emr/views.py`
- `emr/urls.py`
- Dashboard sidebar template (patient section)

---

## Definition of Done
- [x] Patient prescriptions list page functional
- [x] Sidebar navigation updated
- [x] RBAC enforced
- [x] Existing tests pass

# Epic 09: Prescription Print/Export

## Metadata
- **Epic ID:** EPIC-09
- **Priority:** P1 — Important
- **Phase:** 2
- **Depends On:** None (EMR models already exist)
- **Estimated Effort:** Low
- **Affected Apps:** `emr`
- **Status:** `[x] Completed`

---

## Goal
Create print-friendly HTML views for prescriptions so doctors/patients can print them from the browser.

---

## Stories

### Story 9.1: Prescription Print View
- **ID:** EPIC-09-S1
- **Status:** `[x] Completed`

#### Tasks
- `[x]` Create `PrescriptionPrintView` in `emr/views.py`:
  - Takes `consultation_id` or `appointment_id`
  - Accessible by doctor (who created it) and patient (whose prescription it is)
  - Loads consultation, prescriptions, patient info, doctor info
- `[x]` Create `emr/templates/emr/prescription_print.html`:
  - Clean layout, no sidebar/navbar
  - Clinic header (name, address, phone — from ClinicSettings if available)
  - Patient info: name, age, blood type
  - Doctor info: name, specialty
  - Visit date
  - Medications table: name, dosage, duration, instructions
  - Doctor signature line
  - CSS `@media print` rules for clean output
  - "Print" button (hidden in print) that calls `window.print()`
- `[x]` Add URL: `path("prescription/<int:consultation_id>/print/", ...)`
- `[x]` Add "Print Prescription" button in:
  - `consultation_form.html` (after saving)
  - `patient_consultation_summary.html`
  - `consultations_list.html`

#### Acceptance Criteria
- [x] Clean, professional print layout
- [x] All medication details shown clearly
- [x] Print button triggers browser print dialog
- [x] No navigation/sidebar in print output
- [x] Accessible by both doctor and patient

#### Files to Create
- `emr/templates/emr/prescription_print.html`

#### Files to Modify
- `emr/views.py`, `emr/urls.py`
- `emr/templates/emr/patient_consultation_summary.html` (add print link)
- `emr/templates/emr/consultations_list.html` (add print link)

---

## Definition of Done
- [x] Print view renders cleanly
- [x] Browser print produces professional output
- [x] Accessible by doctor and patient
- [x] Existing tests pass

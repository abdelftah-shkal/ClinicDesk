# Product Requirements Document (PRD)
# Clinic Appointment System — Missing Features

## Document Metadata
- **Project:** ClinicAppointmentSystem
- **Version:** 1.0
- **Last Updated:** 2026-06-09
- **Status:** Approved
- **Stack:** Django 6.0, MySQL, Stripe, Bootstrap, Django Templates

---

## 1. Product Overview

The Clinic Appointment System is a web platform for managing patient records, appointments, medical examinations, prescriptions, and billing in small to mid-sized clinics. The system serves five user roles: Guest (unauthenticated), Patient, Receptionist, Doctor, and Clinic Administrator.

### 1.1 Current State

The system has a functional foundation covering authentication, appointment booking with Stripe payments, basic EMR (consultations + prescriptions), receptionist workflows (check-in, walk-in, reschedule), and admin user management with analytics. However, **14 features** are missing or partially implemented.

### 1.2 Goal

Complete all missing features to bring the system to full specification compliance.

---

## 2. User Roles

| Role | Auth Required | DB Record |
|---|---|---|
| Guest | No | No — unauthenticated visitor |
| Patient | Yes | `CustomUser` with `role=PATIENT` + `PatientProfile` |
| Receptionist | Yes | `CustomUser` with `role=RECEPTIONIST` |
| Doctor | Yes | `CustomUser` with `role=DOCTOR` + `DoctorProfile` |
| Admin | Yes | `CustomUser` with `role=ADMIN` |

---

## 3. Resolved Technical Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Appointment reminders | Management command + cron | Simpler, no Celery/Redis infrastructure |
| Invoice/prescription output | Print-friendly HTML pages | No PDF library system deps needed |
| Arabic translation scope | Full translation of every string | Complete bilingual support required |
| File storage | Local filesystem (`MEDIA_ROOT`) | Simplest setup for current scale |
| Notification model | Add `title` + `created_at` fields | Better UX and tracking |
| ClinicService ↔ Doctor | M2M linkable to specific doctors | Allows doctor-service mapping |
| Guest role | Unauthenticated visitors only | No Guest role in DB |

---

## 4. Feature Requirements

### 4.1 Guest — Public Pages
- **G-1:** View clinic services and doctors list without authentication
- **G-2:** See dynamic (not hardcoded) clinic statistics on home page
- **G-3:** Be prompted to register/login to book an appointment

### 4.2 Patient Management — Full CRUD
- **PM-1:** PatientProfile stores allergies, medical history, gender, address, emergency contacts
- **PM-2:** Receptionist can add, edit, and search patient records
- **PM-3:** Search patients by name or ID
- **PM-4:** Filter patients by various criteria

### 4.3 Appointment Reminders
- **AR-1:** Automatic email reminders sent day before appointment
- **AR-2:** In-app notification created for each reminder
- **AR-3:** Reminders run via `python manage.py send_reminders` + system cron

### 4.4 Notification Service
- **NS-1:** In-app notifications for appointment events (created, confirmed, cancelled, completed)
- **NS-2:** Payment notifications (successful, refunded)
- **NS-3:** Notification bell with unread count in UI
- **NS-4:** Mark individual/all notifications as read
- **NS-5:** Notification list view with pagination

### 4.5 Medical Examination — Lab Results & Attachments
- **ME-1:** Lab results and test results text fields on Consultation
- **ME-2:** File upload for medical/lab reports (local filesystem)
- **ME-3:** Doctor can view full patient history across all doctors

### 4.6 Prescription Management — Print/Export
- **PX-1:** Print-friendly HTML view for prescriptions
- **PX-2:** Patient dedicated prescriptions list page
- **PX-3:** Clean printable layout with clinic header, patient info, medication list

### 4.7 Billing — Invoices & Partial Payments
- **BL-1:** Invoice model with status tracking (Draft/Issued/Partially Paid/Paid/Cancelled)
- **BL-2:** Receptionist can create invoices per visit
- **BL-3:** Record full or partial payments against invoices
- **BL-4:** Print-friendly invoice view
- **BL-5:** Receptionist billing dashboard

### 4.8 Clinic Settings & Services Admin
- **CS-1:** ClinicSettings model (name, address, phone, hours, logo)
- **CS-2:** ClinicService model linked to doctors (M2M)
- **CS-3:** Admin can manage clinic settings
- **CS-4:** Admin can CRUD services with doctor assignments

### 4.9 Dashboard Analytics Gaps
- **DA-1:** Most common diagnoses chart
- **DA-2:** Patient return rate metric
- **DA-3:** Disease statistics breakdown
- **DA-4:** Detailed report views (appointments, billing, patient activity, disease)

### 4.10 Arabic & English (i18n)
- **I18N-1:** Full Django i18n configuration (LANGUAGES, LocaleMiddleware, LOCALE_PATHS)
- **I18N-2:** Every user-facing string wrapped with `{% trans %}` / `gettext_lazy`
- **I18N-3:** Complete Arabic `.po` translation file
- **I18N-4:** RTL CSS support when Arabic is active
- **I18N-5:** Language switcher in UI

### 4.11 Responsive UI
- **RUI-1:** Mobile-responsive sidebar with hamburger toggle
- **RUI-2:** Horizontally scrollable data tables on small screens
- **RUI-3:** Mobile-friendly booking wizard
- **RUI-4:** Proper modal behavior on mobile

---

## 5. Non-Functional Requirements

- **NFR-1:** All new features must have role-based access control
- **NFR-2:** All new models must have proper migrations
- **NFR-3:** File uploads limited to reasonable sizes (e.g., 10MB per report)
- **NFR-4:** All templates must extend `base.html` or `base_auth.html`
- **NFR-5:** All new features must be accessible in both Arabic and English
- **NFR-6:** Existing tests must continue to pass

---

## 6. Success Criteria

- All 14 features are implemented and functional
- Role-based access properly enforced on every new endpoint
- Arabic and English fully supported across the entire UI
- Responsive on mobile viewports (≥320px width)
- All existing tests pass, new tests written for new features

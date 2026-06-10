# Clinic Appointment System (ClinicDesk) — API & Route Reference

This document provides a comprehensive reference of all routing, HTTP endpoints, JSON/AJAX API contracts, and integration channels for the Clinic Appointment System.

---

## 🔐 Authentication & Access Control

The system implements a Role-Based Access Control (RBAC) mechanism. Endpoints are decorated with access restrictions based on the authenticated user's role.

### User Roles
1. **`PATIENT`**: Standard public user. Can browse doctors, view public services, book appointments, make payments via Stripe, and access their own consultation records and prescriptions.
2. **`RECEPTIONIST`**: Staff role. Manages check-ins, registers walk-in patients, manages billing invoices, records manual payments, and reschedules or cancels appointments.
3. **`DOCTOR`**: Clinical staff role. Manages their active queues, writes consultations/EMR, defines schedules, and views clinic analytics.
4. **`ADMIN`**: Global system coordinator. Accesses all reports, manages clinic-wide settings, creates staff accounts, and manages the clinic services catalog.

---

## 📂 System-Wide Route Directory

All routes in the application are organized into modules. Below is a structured catalog of all active endpoints.

### 1. Public Core Views
These views are accessible by anyone visiting the clinic website.

| Route Path | View / Component | HTTP Method | Description |
| :--- | :--- | :--- | :--- |
| `/` | `DynamicHomeView` | `GET` | Home landing page with statistics and featured doctors/services. |
| `/doctors/` | `PublicDoctorsListView` | `GET` | Directory of active clinic doctors. Supports `q` (search query) and `specialty` (filter) parameters. |
| `/services/` | `PublicServicesView` | `GET` | Directory of all active medical services offered by the clinic. |
| `/onboarding/` | `OnboardingView` | `GET` | Landing page directing users to role-specific setup procedures. |
| `/i18n/` | — | `POST` | Core Django view for dynamically switching system language (English / Arabic). |

---

### 2. User Accounts & Session Management (`/accounts/`)
Exposes authorization, registration, activation, and profile endpoints.

| Route Path | View / Component | HTTP Method | Description |
| :--- | :--- | :--- | :--- |
| `/accounts/login/` | `CustomLoginView` | `GET`, `POST` | User authentication interface. |
| `/accounts/register/` | `CustomRegisterView` | `GET`, `POST` | Self-service patient registration view. |
| `/accounts/forgot-password/` | `CustomForgotPasswordView` | `GET`, `POST` | Password recovery initiation. |
| `/accounts/reset-password/<uid>/<token>/` | `CustomResetPasswordView` | `GET`, `POST` | Target verification link to supply a new password. |
| `/accounts/profile/` | `ProfileView` | `GET`, `POST` | Profile dashboard to edit details (Patient info / Doctor fee). |
| `/accounts/logout/` | `LogoutView` | `POST` | Standard secure session termination. |
| `/accounts/verify/<uid>/<token>/` | `activate_account` | `GET` | Email link activation confirmation to set `is_active=True`. |

---

### 3. Patient Appointment & Booking Module (`/appointments/`)
Orchestrates appointment discovery, slot reservation, preflight refund checks, and cancellations.

| Route Path | View / Component | HTTP Method | Format | Description |
| :--- | :--- | :--- | :--- | :--- |
| `/appointments/slots/` | `available_slots` | `GET` | `JSON` | Dynamic API retrieving unbooked slots for a doctor on a specific date. |
| `/appointments/book/` | `patient_booking` | `GET` | `HTML` | Interactive booking wizard (filters by specialty, doctor, query). |
| `/appointments/book/<slot_id>/` | `book_appointment` | `POST` | `JSON` | Endpoint to verify, block a slot, and initiate a checkout payment. |
| `/appointments/my/` | `patient_history` | `GET` | `HTML` | User dashboard displaying upcoming appointments and visit history. |
| `/appointments/my/<app_id>/cancel/preflight/` | `cancel_appointment_preflight` | `GET` | `JSON` | Query refund calculations prior to confirming cancellation. |
| `/appointments/my/<app_id>/cancel/` | `cancel_appointment` | `POST` | `HTML`/`JSON` | Cancels an appointment, processes refunds, and flags slots as free. |
| `/appointments/doctors/<doc_id>/profile/` | `doctor_profile_detail` | `GET` | `HTML` | Detail card of a doctor showcasing their profile and upcoming slots. |

---

### 4. Payments, Invoicing & Billing (`/payments/`)
Integrates online Stripe checkout sessions, incoming payment webhooks, and manual/split payment invoicing for receptionists.

| Route Path | View / Component | HTTP Method | Format | Role | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/payments/checkout/<app_id>/` | `CreateCheckoutSessionView` | `GET` | Redirect | Patient | Creates a Stripe Checkout Session and redirects patient to card input. |
| `/payments/webhook/` | `StripeWebhookView` | `POST` | `Plain` | System | Public webhook receiver for Stripe event callbacks. |
| `/payments/success/` | `PaymentSuccessView` | `GET` | `HTML` | Patient | Landing page for a successful checkout callback. |
| `/payments/cancel/` | `PaymentCancelView` | `GET` | `HTML` | Patient | Standard cancellation landing page. |
| `/payments/cancel/<app_id>/` | `PaymentCancelView` | `GET` | Redirect | Patient | Cleans up pending transaction states upon booking abort. |
| `/payments/history/` | `PatientPaymentHistoryView` | `GET` | `HTML` | Patient | Complete tabular billing log and receipt references. |
| `/payments/invoice/create/<app_id>/`| `InvoiceCreateView` | `GET`, `POST`| `HTML` | Receptionist | Form to issue a formal invoice for receptionist-made appointments. |
| `/payments/invoice/<pk>/` | `InvoiceDetailView` | `GET` | `HTML` | Staff / Patient | Detailed itemized invoice page with historical split-payments. |
| `/payments/invoice/<pk>/pay/` | `RecordPaymentView` | `POST` | Redirect | Receptionist | Records a manual cash or POS payment against an invoice. |
| `/payments/invoice/<pk>/print/` | `InvoicePrintView` | `GET` | `HTML` | Staff / Patient | Clean, print-friendly style invoice layout. |
| `/payments/billing/` | `BillingDashboardView` | `GET` | `HTML` | Receptionist | Financial tracking board showing total invoiced, collected, and arrears. |

---

### 5. Electronic Medical Records - EMR (`/emr/`)
Supports clinical workflows for doctors and prescription oversight.

| Route Path | View / Component | HTTP Method | Format | Role | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/emr/queue/` | `DoctorDailyQueueView` | `GET` | `HTML` | Doctor | Live list of checked-in patients for today's queue management. |
| `/emr/consultations/` | `ConsultationListView` | `GET` | `HTML` | Doctor | Searchable consultation history archives with pagination. |
| `/emr/consultation/<app_id>/` | `ConsultationCreateView` | `GET`, `POST`| `HTML` | Doctor | Log medical symptoms, diagnoses, prescriptions, and followups. |
| `/emr/consultation/<app_id>/summary/` | `PatientConsultationSummaryView`| `GET` | `HTML` | Patient / Doctor| Detail summary card of a completed consultation. |
| `/emr/patient/<pat_id>/history/` | `PatientMedicalHistoryView` | `GET` | `HTML` | Doctor | Complete aggregate patient profile listing all clinical records. |
| `/emr/schedule/` | `ManageScheduleView` | `GET`, `POST`| `HTML` | Doctor | Panel to define daily operational windows and slots auto-generation. |
| `/emr/my-prescriptions/` | `PatientPrescriptionsListView`| `GET` | `HTML` | Patient | Personal repository of issued prescriptions. |
| `/emr/prescription/<cons_id>/print/`| `PrescriptionPrintView` | `GET` | `HTML` | All | Formal printable prescription layout showing dosages and directions. |

---

### 6. Receptionist Operations Module (`/reception/`)
Centralizes clinic desk operations, patient check-ins, and walk-in flows.

| Route Path | View / Component | HTTP Method | Format | Role | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/reception/` | `RedirectView` | `GET` | Redirect | Receptionist | Shortcut leading to the global dashboard. |
| `/reception/patients/` | `PatientListView` | `GET` | `HTML` | Receptionist | Complete clinic directory of registered patients. |
| `/reception/patients/create/` | `PatientCreateView` | `GET`, `POST`| `HTML` | Receptionist | Register a patient file manually from the front desk. |
| `/reception/patients/<pk>/` | `PatientDetailView` | `GET` | `HTML` | Receptionist | Comprehensive front-desk view of patient details and booking lists. |
| `/reception/patients/<pk>/edit/` | `PatientEditView` | `GET`, `POST`| `HTML` | Receptionist | Edit profile configurations of a patient file. |
| `/reception/update-status/<pk>/` | `UpdateAppointmentStatusView` | `POST` | Redirect | Receptionist | Status trigger (e.g. mark standard appointment as `CHECKED_IN`). |
| `/reception/walk-in/` | `WalkInPatientCreateView` | `GET`, `POST`| `HTML` | Receptionist | Immediate walk-in onboarding that books the next available slot. |
| `/reception/reschedule/<pk>/` | `RescheduleAppointmentView` | `GET`, `POST`| `HTML` | Receptionist | Overrides an existing booking with a new date/time slot selection. |

---

### 7. Real-Time In-App Notifications (`/notifications/`)
Maintains read/unread alerts and event counters.

| Route Path | View / Component | HTTP Method | Format | Description |
| :--- | :--- | :--- | :--- | :--- |
| `/notifications/` | `NotificationListView` | `GET` | `HTML` | Personal notification center, paginated. |
| `/notifications/<pk>/read/` | `mark_notification_read` | `POST` | `JSON` | Sets `is_read = True` for the specified alert ID. |
| `/notifications/read-all/` | `mark_all_read` | `POST` | `JSON` | Batches all unread notifications to read. |
| `/notifications/unread-count/` | `unread_count` | `GET` | `JSON` | Small polling-friendly path to count unread notifications. |

---

### 8. Administrator Panel (`/admin-panel/`)
Clinical metrics reporting, analytics exports, and settings control.

| Route Path | View / Component | HTTP Method | Format | Role | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/admin-panel/users/` | `UserListView` | `GET` | `HTML` | Admin | Searchable list of all system staff users. |
| `/admin-panel/users/create/` | `UserCreateView` | `GET`, `POST`| `HTML` | Admin | Spawn new system users (Doctors, Receptionists, Admins). |
| `/admin-panel/users/<pk>/edit/` | `UserEditView` | `GET`, `POST`| `HTML` | Admin | Modify permissions, details, and schedules of staff. |
| `/admin-panel/users/<pk>/toggle-active/` | `UserToggleActiveView` | `POST` | Redirect | Admin | Instantly revoke/re-grant login authorization. |
| `/admin-panel/analytics/export/`| `AnalyticsExportView` | `GET` | CSV | Admin | Downloadable export containing service and traffic records. |
| `/admin-panel/settings/` | `ClinicSettingsView` | `GET`, `POST`| `HTML` | Admin | Global clinic metadata (address, operational intervals, contact info). |
| `/admin-panel/services/` | `ServiceListView` | `GET` | `HTML` | Admin | List clinic services. |
| `/admin-panel/services/create/` | `ServiceCreateView` | `GET`, `POST`| `HTML` | Admin | Expand clinic capacity by defining a new medical service line. |
| `/admin-panel/services/<pk>/edit/`| `ServiceEditView` | `GET`, `POST`| `HTML` | Admin | Adjust fees, display orders, and classifications of services. |
| `/admin-panel/services/<pk>/delete/`| `ServiceDeleteView` | `POST` | Redirect | Admin | Soft/hard delete clinic services from active availability. |
| `/admin-panel/reports/appointments/`| `AppointmentReportView` | `GET` | `HTML` | Admin | Detailed analytics detailing visit fulfillment percentages. |
| `/admin-panel/reports/billing/` | `BillingReportView` | `GET` | `HTML` | Admin | Aggregated monthly transaction totals and refund allocations. |
| `/admin-panel/reports/patient-activity/`| `PatientActivityReportView` | `GET`| `HTML` | Admin | Activity diagrams detailing client retention rates and onboarding. |
| `/admin-panel/reports/disease-statistics/`| `DiseaseStatisticsReportView`| `GET` | `HTML` | Admin | Diagnostic graphs displaying disease metrics. |

---

## 🔌 Programmatic JSON/AJAX API Specification

This section documents the specific data models and payload contracts for endpoints operating over JSON.

### 1. Fetch Doctor Availability Slots
Fetches all active, unbooked slots for a doctor on a specific date.

* **Endpoint**: `/appointments/slots/`
* **Method**: `GET`
* **Query Parameters**:
  * `doctor` (integer, required): User ID of the target doctor.
  * `date` (string, required): Date formatted as `YYYY-MM-DD`.
* **Sample Request**:
  ```http
  GET /appointments/slots/?doctor=4&date=2026-06-15 HTTP/1.1
  Host: 127.0.0.1:8000
  Content-Type: application/json
  ```
* **Sample Response (Success - `200 OK`)**:
  ```json
  {
    "doctor_id": "4",
    "consultation_fee": "500.00",
    "slots": [
      {
        "id": 12,
        "time": "09:00"
      },
      {
        "id": 13,
        "time": "09:30"
      }
    ]
  }
  ```

---

### 2. Lock & Book Appointment Slot
Pre-reserves an appointment slot and initiates checkout state.

* **Endpoint**: `/appointments/book/<slot_id>/`
* **Method**: `POST`
* **Headers**:
  * `X-CSRFToken` (string, required): Django CSRF token.
* **Sample Request**:
  ```http
  POST /appointments/book/12/ HTTP/1.1
  Host: 127.0.0.1:8000
  X-CSRFToken: [CSRF_TOKEN_STRING]
  ```
* **Sample Response (Success - `200 OK`)**:
  ```json
  {
    "redirect": "/payments/checkout/42/",
    "consultation_fee": "500.00"
  }
  ```
* **Sample Response (Slot Already Booked / Conflict - `400 Bad Request`)**:
  ```json
  {
    "error": "The selected appointment slot was not found."
  }
  ```

---

### 3. Retrieve Unread Notifications Count
Counts all unread alerts logged for the authenticated caller.

* **Endpoint**: `/notifications/unread-count/`
* **Method**: `GET`
* **Sample Request**:
  ```http
  GET /notifications/unread-count/ HTTP/1.1
  Host: 127.0.0.1:8000
  ```
* **Sample Response (Success - `200 OK`)**:
  ```json
  {
    "count": 5
  }
  ```

---

### 4. Mark Single Notification as Read
Flags a specific notification ID as read.

* **Endpoint**: `/notifications/<int:pk>/read/`
* **Method**: `POST`
* **Headers**:
  * `X-CSRFToken` (string, required): Django CSRF token.
* **Sample Request**:
  ```http
  POST /notifications/8/read/ HTTP/1.1
  Host: 127.0.0.1:8000
  X-CSRFToken: [CSRF_TOKEN_STRING]
  ```
* **Sample Response (Success - `200 OK`)**:
  ```json
  {
    "status": "success"
  }
  ```

---

### 5. Mark All Notifications as Read
Batch marks all notifications of the logged-in user as read.

* **Endpoint**: `/notifications/read-all/`
* **Method**: `POST`
* **Headers**:
  * `X-CSRFToken` (string, required): Django CSRF token.
* **Sample Request**:
  ```http
  POST /notifications/read-all/ HTTP/1.1
  Host: 127.0.0.1:8000
  X-CSRFToken: [CSRF_TOKEN_STRING]
  ```
* **Sample Response (Success - `200 OK`)**:
  ```json
  {
    "status": "success"
  }
  ```

---

### 6. Appointment Cancellation Preflight Check
Retrieves refund and penalty fee estimates prior to confirming a booking deletion.

* **Endpoint**: `/appointments/my/<appointment_id>/cancel/preflight/`
* **Method**: `GET`
* **Sample Request**:
  ```http
  GET /appointments/my/42/cancel/preflight/ HTTP/1.1
  Host: 127.0.0.1:8000
  ```
* **Sample Response (Success - `200 OK` with Paid Online Transaction)**:
  ```json
  {
    "appointment_id": 42,
    "has_payment": true,
    "original_amount": "500.00",
    "refund_amount": "400.00",
    "deducted_amount": "100.00"
  }
  ```
* **Sample Response (Success - `200 OK` for Free / Unpaid Booking)**:
  ```json
  {
    "appointment_id": 42,
    "has_payment": false,
    "original_amount": "0.00",
    "refund_amount": "0.00",
    "deducted_amount": "0.00"
  }
  ```

---

### 7. Process Appointment Cancellation
Executes the cancellation of an appointment. If requested via AJAX, returns a JSON summary.

* **Endpoint**: `/appointments/my/<appointment_id>/cancel/`
* **Method**: `POST`
* **Headers**:
  * `X-Requested-With`: `XMLHttpRequest` (required for JSON response format)
  * `X-CSRFToken` (string, required): Django CSRF token.
* **Payload Structure**:
  * `reason` (string, required): Cancellation description.
* **Sample Request**:
  ```http
  POST /appointments/my/42/cancel/ HTTP/1.1
  Host: 127.0.0.1:8000
  X-Requested-With: XMLHttpRequest
  X-CSRFToken: [CSRF_TOKEN_STRING]
  Content-Type: application/x-www-form-urlencoded

  reason=Patient+schedule+conflict
  ```
* **Sample Response (Success - `200 OK` with Refund)**:
  ```json
  {
    "status": "cancelled",
    "refunded_amount": "400.00",
    "deducted_amount": "100.00"
  }
  ```

---

## 💳 Stripe Webhook API Reference

The system processes background actions driven by the public stripe endpoint `/payments/webhook/`.

### Webhook Event Behaviors
1. **`checkout.session.completed`**:
   * Extracts `appointment_id` from Stripe checkout metadata.
   * Begins a database transaction locking the slot.
   * If slot is vacant: Sets slot `is_booked = True`, appointment status to `CONFIRMED`, and Payment Transaction status to `PAID`.
   * If slot was double booked and paid by another client: Executes full automatic Stripe refund of the payment intent and flags appointment status as `CANCELLED`, payment status as `FAILED`.
   * Cancels all duplicate appointments awaiting payment for that slot.
2. **`checkout.session.expired`** and **`checkout.session.async_payment_failed`**:
   * Cancels the target appointment (status `CANCELLED`).
   * Flags the related Payment Transaction as `FAILED`.

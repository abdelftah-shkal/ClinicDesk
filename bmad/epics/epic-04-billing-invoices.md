# Epic 04: Billing — Invoices & Partial Payments

## Metadata
- **Epic ID:** EPIC-04
- **Priority:** P0 — Critical
- **Phase:** 1
- **Depends On:** None
- **Estimated Effort:** High
- **Affected Apps:** `payments`, `reception`
- **Status:** `[x] Completed`

---

## Goal
Create an Invoice system with support for partial payments, receptionist-managed billing, and print-friendly invoice views.

---

## Stories

### Story 4.1: Invoice & InvoicePayment Models
- **ID:** EPIC-04-S1
- **Status:** `[x] Completed`

#### Tasks
- `[x]` Create `Invoice` model in `payments/models.py`:
  - `appointment` (OneToOneField), `patient` (FK), `invoice_number` (unique CharField)
  - `total_amount`, `paid_amount` (DecimalField), `status` (choices: DRAFT/ISSUED/PARTIALLY_PAID/PAID/CANCELLED)
  - `issued_at` (DateTimeField null), `notes` (TextField blank), `created_at` (auto_now_add)
  - Property: `balance_due` → `total_amount - paid_amount`
  - Method: `generate_invoice_number()` → auto-incrementing format `INV-YYYYMMDD-XXXX`
- `[x]` Create `InvoicePayment` model:
  - `invoice` (FK), `amount` (DecimalField), `payment_method` (choices: CASH/CARD/STRIPE/OTHER)
  - `notes` (TextField blank), `received_by` (FK to CustomUser), `created_at` (auto_now_add)
  - Override `save()` to update `Invoice.paid_amount` and `Invoice.status`
- `[x]` Run migrations
- `[x]` Register both models in `payments/admin.py`

#### Acceptance Criteria
- [x] Invoice model with auto-generated invoice numbers
- [x] InvoicePayment model tracks individual payments
- [x] `paid_amount` auto-updates when InvoicePayment is created
- [x] Invoice status auto-transitions (ISSUED → PARTIALLY_PAID → PAID)

#### Files to Modify
- `payments/models.py`, `payments/admin.py`

---

### Story 4.2: Receptionist Invoice Creation
- **ID:** EPIC-04-S2
- **Status:** `[x] Completed`
- **Depends On:** EPIC-04-S1

#### Tasks
- `[x]` Create `InvoiceCreateForm` in `payments/forms.py`: `total_amount`, `notes`
- `[x]` Create `InvoiceCreateView` in `payments/views.py` (ReceptionistRequired):
  - Takes `appointment_id`, creates invoice linked to appointment
  - Auto-fills patient, generates invoice number
- `[x]` Create template `payments/templates/payments/invoice_create.html`
- `[x]` Add URL: `path("invoice/create/<int:appointment_id>/", ...)`

#### Acceptance Criteria
- [x] Receptionist can create invoice for any completed/checked-in appointment
- [x] Invoice number auto-generated
- [x] Only receptionists can access

#### Files to Modify/Create
- `payments/forms.py` (new), `payments/views.py`, `payments/urls.py`
- `payments/templates/payments/invoice_create.html` (new)

---

### Story 4.3: Invoice Detail & Print View
- **ID:** EPIC-04-S3
- **Status:** `[x] Completed`
- **Depends On:** EPIC-04-S1

#### Tasks
- `[x]` Create `InvoiceDetailView` — shows invoice with payment history
- `[x]` Create `InvoicePrintView` — clean, print-friendly HTML page with:
  - Clinic header (name, address, phone)
  - Patient info, doctor info, appointment date
  - Line items, total, paid, balance
  - CSS `@media print` rules
- `[x]` Create templates: `invoice_detail.html`, `invoice_print.html`
- `[x]` Add URLs for both views

#### Acceptance Criteria
- [x] Invoice detail shows all info + payment history
- [x] Print view renders cleanly for browser printing
- [x] Accessible by receptionist and admin

#### Files to Create
- `payments/templates/payments/invoice_detail.html`
- `payments/templates/payments/invoice_print.html`

#### Files to Modify
- `payments/views.py`, `payments/urls.py`

---

### Story 4.4: Record Partial/Full Payments
- **ID:** EPIC-04-S4
- **Status:** `[x] Completed`
- **Depends On:** EPIC-04-S1

#### Tasks
- `[x]` Create `RecordPaymentForm`: `amount`, `payment_method`, `notes`
- `[x]` Create `RecordPaymentView` (ReceptionistRequired):
  - Validates amount ≤ balance_due
  - Creates InvoicePayment, updates Invoice
- `[x]` Add to invoice detail template: payment recording form
- `[x]` Add URL: `path("invoice/<int:pk>/pay/", ...)`

#### Acceptance Criteria
- [x] Receptionist can record cash/card payments
- [x] Partial payments correctly update paid_amount and status
- [x] Cannot overpay (validation)
- [x] Payment history shown on invoice detail

#### Files to Modify
- `payments/forms.py`, `payments/views.py`, `payments/urls.py`

---

### Story 4.5: Receptionist Billing Dashboard
- **ID:** EPIC-04-S5
- **Status:** `[x] Completed`
- **Depends On:** EPIC-04-S1

#### Tasks
- `[x]` Create `BillingDashboardView` (ReceptionistRequired):
  - Lists all invoices with filters (status, date range, patient search)
  - Summary stats: total invoiced, total collected, outstanding balance
- `[x]` Create template `payments/templates/payments/billing_dashboard.html`
- `[x]` Add URL and sidebar link for receptionist

#### Acceptance Criteria
- [x] Receptionist sees all invoices with filter/search
- [x] Summary metrics displayed
- [x] Links to invoice detail and payment recording

#### Files to Create
- `payments/templates/payments/billing_dashboard.html`

#### Files to Modify
- `payments/views.py`, `payments/urls.py`, sidebar template

---

## Definition of Done
- [x] All 5 stories completed
- [x] Invoice lifecycle working (create → issue → pay → paid)
- [x] Partial payments tracked correctly
- [x] Print-friendly invoice renders cleanly
- [x] Receptionist billing dashboard functional
- [x] Existing tests pass

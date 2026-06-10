# Technical Architecture Document
# Clinic Appointment System

## Document Metadata
- **Last Updated:** 2026-06-09
- **Stack:** Python 3.x, Django 6.0.5, MySQL, Stripe, Bootstrap, WhiteNoise

---

## 1. System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Browser (Client)                       │
│   Bootstrap 5 + Django Templates + Vanilla JS                │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTP/HTTPS
┌──────────────────────────▼───────────────────────────────────┐
│                     Django Application                        │
│  ┌──────────┐ ┌──────────────┐ ┌────────────┐ ┌──────────┐  │
│  │ accounts │ │ appointments │ │    emr     │ │ payments │  │
│  └──────────┘ └──────────────┘ └────────────┘ └──────────┘  │
│  ┌───────────┐ ┌───────────────┐ ┌───────────┐ ┌─────────┐  │
│  │ reception │ │ notifications │ │ dashboard │ │admin_pnl│  │
│  └───────────┘ └───────────────┘ └───────────┘ └─────────┘  │
│  ┌────────┐                                                   │
│  │ clinic │  (project config + NEW: public views, models)    │
│  └────────┘                                                   │
└──────────────────────────┬───────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌────────┐  ┌─────────┐  ┌──────────┐
         │ MySQL  │  │ Stripe  │  │  SMTP    │
         │   DB   │  │   API   │  │ (Gmail)  │
         └────────┘  └─────────┘  └──────────┘
```

---

## 2. Django App Responsibilities

| App | Current Responsibility | Planned Additions |
|---|---|---|
| `clinic` | Project settings, root URLs, favicon | ClinicSettings model, ClinicService model, public views (doctors, services) |
| `accounts` | User model, auth, profiles, onboarding | Extended PatientProfile fields (allergies, medical history, etc.) |
| `appointments` | Scheduling, booking, cancellation | No structural changes (already complete) |
| `emr` | Consultations, prescriptions, doctor queue | Lab results fields, MedicalReport model (file upload), patient full history view, prescription print view, patient prescriptions list |
| `reception` | Walk-in, status updates, reschedule | Patient CRUD (add/edit/search), invoice creation, payment recording |
| `payments` | Stripe checkout, webhook, refund, history | Invoice model, partial payments, receptionist billing dashboard, print-friendly invoice |
| `notifications` | Stub (model only) | Full implementation: views, URLs, signals, templates, management command for reminders |
| `dashboard` | Role-based dashboard views | Additional analytics (diagnoses, return rate, disease stats) |
| `admin_panel` | User CRUD, analytics, CSV export | Clinic settings management, service CRUD, additional reports |

---

## 3. New Models

### 3.1 `clinic.ClinicSettings` (Singleton)
```
ClinicSettings
├── clinic_name: CharField(200)
├── clinic_address: TextField
├── clinic_phone: CharField(20)
├── clinic_email: EmailField
├── logo: ImageField(upload_to='clinic/')
├── working_days: JSONField (e.g. [0,1,2,3,4])
├── opening_time: TimeField
├── closing_time: TimeField
├── default_slot_duration: PositiveIntegerField(default=30)
└── currency: CharField(10, default='EGP')
```

### 3.2 `clinic.ClinicService`
```
ClinicService
├── name: CharField(200)
├── description: TextField
├── icon: CharField(50) — Bootstrap icon class
├── price_range: CharField(100)
├── is_active: BooleanField(default=True)
├── display_order: PositiveIntegerField(default=0)
└── doctors: ManyToManyField(CustomUser, limit_choices_to={'role': 'DOCTOR'}, blank=True)
```

### 3.3 `accounts.PatientProfile` (Extended)
```
PatientProfile (EXISTING — add fields)
├── ...existing fields...
├── allergies: TextField(blank=True)
├── medical_history: TextField(blank=True)
├── gender: CharField(10, choices=GENDER_CHOICES)
├── address: TextField(blank=True)
├── emergency_contact_name: CharField(100, blank=True)
└── emergency_contact_phone: CharField(20, blank=True)
```

### 3.4 `emr.Consultation` (Extended)
```
Consultation (EXISTING — add fields)
├── ...existing fields...
├── lab_results: TextField(blank=True)
└── test_results: TextField(blank=True)
```

### 3.5 `emr.MedicalReport` (New)
```
MedicalReport
├── consultation: ForeignKey(Consultation)
├── file: FileField(upload_to='medical_reports/')
├── report_type: CharField(choices=REPORT_TYPE_CHOICES)
├── title: CharField(200)
└── uploaded_at: DateTimeField(auto_now_add=True)
```

### 3.6 `payments.Invoice` (New)
```
Invoice
├── appointment: OneToOneField(Appointment)
├── patient: ForeignKey(CustomUser)
├── invoice_number: CharField(unique=True)
├── total_amount: DecimalField(10,2)
├── paid_amount: DecimalField(10,2, default=0)
├── status: CharField(choices=INVOICE_STATUS_CHOICES)
├── issued_at: DateTimeField(null=True)
├── notes: TextField(blank=True)
└── created_at: DateTimeField(auto_now_add=True)
```

### 3.7 `payments.InvoicePayment` (New)
```
InvoicePayment
├── invoice: ForeignKey(Invoice)
├── amount: DecimalField(10,2)
├── payment_method: CharField(choices=PAYMENT_METHOD_CHOICES)
├── notes: TextField(blank=True)
├── received_by: ForeignKey(CustomUser)
└── created_at: DateTimeField(auto_now_add=True)
```

### 3.8 `notifications.Notification` (Extended)
```
Notification (EXISTING — add fields)
├── user: ForeignKey (existing)
├── title: CharField(200)  ← NEW
├── message: TextField (existing)
├── notification_type: CharField(choices=NOTIFICATION_TYPE_CHOICES)  ← NEW
├── is_read: BooleanField (existing)
├── link: URLField(blank=True)  ← NEW
└── created_at: DateTimeField(auto_now_add=True)  ← NEW
```

---

## 4. File Storage Configuration

```python
# settings.py additions
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

```python
# urls.py addition (development only)
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## 5. i18n Architecture

```python
# settings.py
from django.utils.translation import gettext_lazy as _

LANGUAGES = [
    ('en', _('English')),
    ('ar', _('Arabic')),
]
LANGUAGE_CODE = 'en'
USE_I18N = True
USE_L10N = True
LOCALE_PATHS = [BASE_DIR / 'locale']

MIDDLEWARE = [
    ...
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # ← ADD AFTER SessionMiddleware
    'django.middleware.common.CommonMiddleware',
    ...
]
```

### Directory Structure
```
locale/
├── ar/
│   └── LC_MESSAGES/
│       ├── django.po
│       └── django.mo
└── en/
    └── LC_MESSAGES/
        ├── django.po
        └── django.mo
```

### RTL Support
- Detect language direction in base template: `{% get_current_language_bidi as LANGUAGE_BIDI %}`
- Conditionally load `rtl.css`: `{% if LANGUAGE_BIDI %}<link href="rtl.css">{% endif %}`
- Set `<html dir="rtl" lang="ar">` when Arabic is active

---

## 6. Cron Job Configuration

```cron
# Send appointment reminders at 6:00 PM daily
0 18 * * * cd /path/to/project && python manage.py send_reminders
```

---

## 7. Dependency Graph

```
clinic (project root)
  └── accounts (no app deps)
        ├── appointments (depends on: accounts)
        │     ├── emr (depends on: appointments, accounts)
        │     ├── reception (depends on: appointments, accounts, payments)
        │     └── payments (depends on: appointments)
        ├── notifications (depends on: accounts)
        ├── dashboard (depends on: appointments, accounts, reception, admin_panel)
        └── admin_panel (depends on: accounts, appointments, payments, reception)
```

---

## 8. Epic Dependency Order

The following is the recommended implementation order based on model dependencies:

```
1. accounts (PatientProfile extension) — no deps
2. clinic models (ClinicSettings, ClinicService) — depends on accounts
3. notifications (full implementation) — depends on accounts
4. emr extensions (lab results, MedicalReport, patient history) — depends on accounts, appointments
5. payments (Invoice, partial payments) — depends on appointments
6. reception (Patient CRUD, billing) — depends on accounts, payments
7. guest public pages — depends on clinic models
8. appointment reminders — depends on notifications
9. prescription export — depends on emr
10. clinic settings admin — depends on clinic models
11. dashboard analytics — depends on emr, payments
12. i18n (Arabic/English) — cross-cutting, do last
13. responsive UI polish — cross-cutting, do last
```

# Clinic Appointment System (ClinicDesk)

A modern, responsive, and full-featured Clinic & Electronic Medical Records (EMR) Management System built with Django. This platform streamlines clinic workflows, coordinates check-ins, handles scheduling, manages consultations, processes billing with Stripe integration, and supports full localization in English and Arabic.

![Clinic EMR System](https://github.com/user-attachments/assets/69efebf5-2449-4a34-a7e1-e9af32b319c5)

---

## 🌟 Key Features

### 🔐 Multi-Role Access Control (RBAC)
Dedicated dashboards and custom workflows tailored to four distinct roles:
1. **Patient**: Book appointments via an interactive Booking Wizard, manage medical history, review doctor profiles, pay invoices with Stripe, and download PDF prescriptions.
2. **Receptionist**: Check-in arrivals, register walk-in patients, manage appointment status, and reschedule/cancel visits with automated refunds.
3. **Doctor**: Manage queue of checked-in patients, write medical examinations (EMR), prescribe medications, search history, and view daily analytics.
4. **Administrator**: Full oversight of clinic settings, services, user roles, billing stats, and performance metrics.

### 💳 Stripe Billing & Automated Invoicing
- Direct Stripe checkout session integration for patient payments.
- Automatic invoice generation upon scheduling.
- Automated partial refunds (80%) on patient cancellations or full refunds (100%) on receptionist cancellations.

### 🩺 Electronic Medical Records (EMR) & Prescriptions
- Live queue system for doctors to start and edit consultations.
- Prescription creation with dosage instructions.
- Print-friendly and downloadable PDF prescriptions.
- Patient history search with persistent pagination.

### 🔔 Notification Service & Reminders
- Real-time in-app notification bell visible across all roles.
- E-mail alerts for booking confirmations, rescheduling, cancellations, and check-ins.
- Automated daily reminder system via Django management command.

### 🌍 Complete Internationalization (i18n)
- Dynamic toggle switcher between **English (LTR)** and **Arabic (RTL)**.
- Complete translation coverage for models, forms, validations, page templates, and navigation.

### 📱 Responsive off-canvas UI
- Elegant, premium UI built using CSS variables, modern typography, and subtle micro-animations.
- Mobile-first sidebar toggle (hamburger menu) and fully responsive data tables.
- Touch-friendly action buttons (min 44px) and adaptive viewports down to 320px width.

---

## 🚀 Installation & Local Setup

### 1. Clone the repository and install dependencies
```bash
git clone https://github.com/MoIbrahim2/ClinicAppointmentSystem.git
cd ClinicAppointmentSystem
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file at the root of the project:
```env
DEBUG=True
SECRET_KEY=your-django-secret-key
DATABASE_URL=sqlite:///db.sqlite3
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password
```

### 3. Apply Migrations & Build Message Catalogs
```bash
python manage.py migrate
python manage.py compilemessages
```

### 4. Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

### 5. Run the local development server
```bash
python manage.py runserver
```
Visit the local server at `http://127.0.0.1:8000/`.

---

## 🛠️ Management Commands

### Daily Appointment Reminders
To trigger reminders for upcoming appointments scheduled for the following day:
```bash
python manage.py send_reminders
```
Use the `--dry-run` flag to preview without modifying the database or sending emails:
```bash
python manage.py send_reminders --dry-run
```

### Cron Schedule Setup
Add the following line to your crontab on the host server to automate reminders at 6:00 PM daily:
```cron
0 18 * * * cd /path/to/project && /path/to/venv/bin/python manage.py send_reminders >> /var/log/clinic_reminders.log 2>&1
```

---

## 🧪 Running Tests
Verify the code integrity by running the Django test suite containing 83 comprehensive unit and integration tests:
```bash
python manage.py test
```

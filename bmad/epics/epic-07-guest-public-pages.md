# Epic 07: Guest Public Pages — Services & Doctors

## Metadata
- **Epic ID:** EPIC-07
- **Priority:** P1 — Important
- **Phase:** 2
- **Depends On:** EPIC-08 (ClinicService model from Clinic Settings epic)
- **Estimated Effort:** Medium
- **Affected Apps:** `clinic`, templates
- **Status:** `[x] Completed`

---

## Goal
Create public-facing pages for unauthenticated guests to view clinic services, browse doctors, and be prompted to register for booking.

---

## Stories

### Story 7.1: Public Doctors List Page
- **ID:** EPIC-07-S1
- **Status:** `[x] Completed`

#### Tasks
- `[x]` Create `PublicDoctorsListView` in `clinic/views.py`:
  - No authentication required
  - Lists all doctors with their profiles (specialty, bio, photo placeholder)
  - Search by name or specialty
  - Shows services each doctor provides (from M2M)
- `[x]` Wire existing `templates/doctors/list.html` or create new template
- `[x]` Add URL: `path('doctors/', PublicDoctorsListView.as_view(), name='public-doctors')`
- `[x]` Add "View Doctors" link to home page

#### Acceptance Criteria
- [x] Guests can view all doctors without login
- [x] Doctor specialty, bio, and linked services shown
- [x] Search by name/specialty works
- [x] "Register to Book" CTA shown to guests

#### Files to Modify
- `clinic/views.py`, `clinic/urls.py`, `templates/doctors/list.html`, `templates/home.html`

---

### Story 7.2: Public Services Page
- **ID:** EPIC-07-S2
- **Status:** `[x] Completed`
- **Depends On:** ClinicService model (EPIC-08)

#### Tasks
- `[x]` Create `PublicServicesView` in `clinic/views.py`:
  - No authentication required
  - Lists all active ClinicService records ordered by `display_order`
  - Shows linked doctors for each service
- `[x]` Create template `templates/services/list.html`:
  - Service cards with icon, name, description, price range
  - Linked doctors for each service
  - CTA: "Book an Appointment" → login/register
- `[x]` Add URL: `path('services/', ...)`
- `[x]` Add "Services" link to home page navigation


#### Acceptance Criteria
- [x] Guests can view all active services without login
- [x] Services show linked doctors
- [x] "Book" CTA redirects to login/register

#### Files to Create
- `templates/services/list.html`

#### Files to Modify
- `clinic/views.py`, `clinic/urls.py`, `templates/home.html`

---

### Story 7.3: Dynamic Home Page
- **ID:** EPIC-07-S3
- **Status:** `[x] Completed`

#### Tasks
- `[x]` Convert home page from `TemplateView` to a custom view in `clinic/views.py`
- `[x]` Pass dynamic context:
  - Total doctors count
  - Total services count
  - Today's appointment count (if applicable)
  - Featured doctors (e.g., first 3)
  - Featured services (e.g., first 3)
- `[x]` Update `templates/home.html` to use dynamic data instead of hardcoded values
- `[x]` Update `clinic/urls.py` to use the new view

#### Acceptance Criteria
- [x] Home page shows real data, not hardcoded "42 appointments"
- [x] Featured doctors and services displayed
- [x] Still accessible without authentication

#### Files to Modify
- `clinic/views.py`, `clinic/urls.py`, `templates/home.html`

---

## Definition of Done
- [x] All 3 stories completed
- [x] All pages accessible without authentication
- [x] Dynamic data displayed on home page
- [x] "Register to Book" CTAs present for guests
- [x] Existing tests pass

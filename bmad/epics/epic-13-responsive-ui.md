# Epic 13: Responsive UI Polish

## Metadata
- **Epic ID:** EPIC-13
- **Priority:** P2 — Polish
- **Phase:** 3
- **Depends On:** All other epics (do last)
- **Estimated Effort:** Medium
- **Affected Apps:** ALL templates, CSS
- **Status:** `[x] Completed`

---

## Goal
Ensure the entire UI works properly on mobile browsers (≥320px) without needing a native app.

---

## Stories

### Story 13.1: Mobile-Responsive Sidebar
- **ID:** EPIC-13-S1
- **Status:** `[x] Completed`

#### Tasks
- `[x]` Add hamburger toggle button for mobile (visible only on `sm` and below)
- `[x]` Sidebar collapses off-canvas on mobile, slides in on hamburger click
- `[x]` Use Bootstrap offcanvas or custom CSS for sidebar toggle
- `[x]` Close sidebar when a link is clicked on mobile
- `[x]` Ensure overlay/backdrop when sidebar is open on mobile

#### Acceptance Criteria
- [x] Sidebar hidden by default on mobile
- [x] Hamburger icon visible on mobile
- [x] Sidebar slides in/out smoothly
- [x] Links work and close sidebar on mobile

#### Files to Modify
- `dashboard/templates/dashboard/partials/_sidebar.html`
- `dashboard/templates/dashboard/dashboard.html`
- Related CSS

---

### Story 13.2: Responsive Data Tables
- **ID:** EPIC-13-S2
- **Status:** `[x] Completed`

#### Tasks
- `[x]` Wrap all `<table>` elements in `<div class="table-responsive">` containers
- `[x]` Audit all table-heavy pages:
  - Receptionist dashboard (appointment table)
  - Admin user list
  - Patient list (new)
  - Billing dashboard (new)
  - Payment history
  - Consultation list
- `[x]` Ensure table columns don't break on small screens
- `[x]` Consider hiding less important columns on mobile with `d-none d-md-table-cell`

#### Acceptance Criteria
- [x] All tables horizontally scrollable on mobile
- [x] No layout breaking on narrow viewports
- [x] Critical data always visible

#### Files to Modify
- Multiple template files containing `<table>` elements

---

### Story 13.3: Mobile Booking Wizard
- **ID:** EPIC-13-S3
- **Status:** `[x] Completed`

#### Tasks
- `[x]` Test booking wizard on mobile viewport
- `[x]` Fix any layout issues:
  - Doctor cards stack vertically on mobile
  - Date picker fits screen width
  - Slot selection buttons are touch-friendly (min 44px tap targets)
  - Confirmation modal fits mobile screen

#### Acceptance Criteria
- [x] Full booking flow works on 320px viewport
- [x] All buttons/inputs touch-friendly
- [x] Modals display properly on mobile

#### Files to Modify
- `dashboard/templates/patients/booking_wizard.html`
- Related CSS

---

### Story 13.4: Mobile Modal & Form Polish
- **ID:** EPIC-13-S4
- **Status:** `[x] Completed`

#### Tasks
- `[x]` Audit all modals for mobile compatibility:
  - Cancellation modal
  - Reschedule modal
  - Status update modal
- `[x]` Ensure modals are full-width on mobile (`modal-fullscreen-sm-down`)
- `[x]` Ensure all form inputs are properly sized on mobile
- `[x]` Test all forms on mobile viewport

#### Acceptance Criteria
- [x] All modals work on mobile
- [x] Form inputs are readable and touch-friendly
- [x] No content hidden behind keyboard on mobile

#### Files to Modify
- Various template files containing modals and forms

---

## Definition of Done
- [x] All 4 stories completed
- [x] UI tested on 320px, 375px, 768px viewports
- [x] No horizontal scroll on any page (except data tables within their scroll container)
- [x] All interactive elements have ≥44px touch targets
- [x] Sidebar toggle works on mobile
- [x] Existing tests pass

# Epic 11: Dashboard Analytics Gaps

## Metadata
- **Epic ID:** EPIC-11
- **Priority:** P1 — Important
- **Phase:** 2
- **Depends On:** EPIC-03 (Consultation model extensions)
- **Estimated Effort:** Medium
- **Affected Apps:** `admin_panel`, `dashboard`
- **Status:** `[x] Completed`

---

## Goal
Add missing analytics: most common diagnoses, patient return rate, disease statistics, and detailed report views.

---

## Stories

### Story 11.1: Add Missing Analytics to `get_analytics_data()`
- **ID:** EPIC-11-S1
- **Status:** `[x] Completed`

#### Tasks
- `[x]` Modify `admin_panel/views.py` → `get_analytics_data()` to add:
  - **Most Common Diagnoses** (top 10):
    ```python
    Consultation.objects.filter(...)
        .exclude(diagnosis='')
        .values('diagnosis')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    ```
  - **Patient Return Rate**:
    - Total unique patients with ≥1 completed appointment
    - Returning patients (≥2 completed appointments)
    - Rate = returning / total × 100
  - **Disease Statistics by Month**:
    - Top diagnoses broken down by month
  - **Monthly patient activity** — new vs returning patients per month
- `[x]` Pass new data in context dict

#### Acceptance Criteria
- [x] Top 10 diagnoses returned with counts
- [x] Patient return rate calculated correctly
- [x] Monthly disease breakdown available
- [x] No performance regression on dashboard load

#### Files to Modify
- `admin_panel/views.py`

---

### Story 11.2: Update Admin Dashboard Template with New Charts
- **ID:** EPIC-11-S2
- **Status:** `[x] Completed`
- **Depends On:** EPIC-11-S1

#### Tasks
- `[x]` Update `dashboard/templates/dashboard/partials/_admin_dashboard.html`:
  - Add "Most Common Diagnoses" bar chart or table
  - Add "Patient Return Rate" metric card
  - Add "Disease Statistics" section
- `[x]` Use Chart.js (if already included) or Bootstrap tables for data visualization

#### Acceptance Criteria
- [x] New analytics visually displayed on admin dashboard
- [x] Diagnoses chart/table is readable
- [x] Return rate displayed as percentage

#### Files to Modify
- `dashboard/templates/dashboard/partials/_admin_dashboard.html`

---

### Story 11.3: Detailed Report Views
- **ID:** EPIC-11-S3
- **Status:** `[x] Completed`
- **Depends On:** EPIC-11-S1

#### Tasks
- `[x]` Create report views in `admin_panel/views.py` (AdminRequired):
  - `AppointmentReportView` — filterable appointment details report
  - `BillingReportView` — revenue breakdown with filters
  - `PatientActivityReportView` — patient visit patterns
  - `DiseaseStatisticsReportView` — diagnosis frequency analysis
- `[x]` Create templates for each report
- `[x]` Add URLs and admin sidebar links
- `[x]` Add CSV export option for each report (extend existing pattern)

#### Acceptance Criteria
- [x] Each report page has date range filters
- [x] Data displayed in tables
- [x] CSV export available for each
- [x] Only admin can access

#### Files to Create
- `admin_panel/templates/admin_panel/report_appointments.html`
- `admin_panel/templates/admin_panel/report_billing.html`
- `admin_panel/templates/admin_panel/report_patients.html`
- `admin_panel/templates/admin_panel/report_diseases.html`

#### Files to Modify
- `admin_panel/views.py`, `admin_panel/urls.py`, sidebar template

---

## Definition of Done
- [x] All 3 stories completed
- [x] New analytics data correct
- [x] Charts/tables render properly on admin dashboard
- [x] Report pages with filters and CSV export working
- [x] Existing tests pass

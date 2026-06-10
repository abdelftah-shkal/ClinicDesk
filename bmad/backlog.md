# BMAD Master Backlog — Clinic Appointment System

## Document Metadata
- **Project:** ClinicAppointmentSystem
- **Generated:** 2026-06-09
- **Total Epics:** 13 (combined into 11 files)
- **Total Stories:** ~35
- **Total Task Items:** ~120+

---

## How to Use This Backlog

### For Agents
1. Read `prd.md` for full requirements context
2. Read `architecture.md` for technical decisions and model schemas
3. Pick an epic from the table below (respect dependency order)
4. Open the epic file, find stories with `[ ] Not Started` status
5. Execute tasks in order, marking `[/]` when in-progress and `[x]` when done
6. Update story and epic status as you complete work
7. Run `python manage.py test` after each story to verify no regressions

### Status Legend
```
[ ] Not Started
[/] In Progress
[x] Completed
[~] Blocked
```

---

## Epic Overview

### Phase 1 — Critical (Must-Have)

| Epic | File | Priority | Effort | Status | Depends On |
|---|---|---|---|---|---|
| EPIC-01: Patient Management CRUD | [epic-01](epics/epic-01-patient-management.md) | P0 | Medium | `[x]` | None |
| EPIC-02: Notification Service | [epic-02](epics/epic-02-notification-service.md) | P0 | Medium | `[x]` | None |
| EPIC-03: Medical Examination | [epic-03](epics/epic-03-medical-examination.md) | P0 | Medium | `[x]` | None |
| EPIC-04: Billing & Invoices | [epic-04](epics/epic-04-billing-invoices.md) | P0 | High | `[x]` | None |
| EPIC-05/06: History & Prescriptions | [epic-05-06](epics/epic-05-06-history-prescriptions.md) | P0 | Low | `[x]` | EPIC-03 |

### Phase 2 — Important

| Epic | File | Priority | Effort | Status | Depends On |
|---|---|---|---|---|---|
| EPIC-07: Guest Public Pages | [epic-07](epics/epic-07-guest-public-pages.md) | P1 | Medium | `[x]` | EPIC-10 |
| EPIC-08: Appointment Reminders | [epic-08](epics/epic-08-appointment-reminders.md) | P1 | Medium | `[x]` | EPIC-02 |
| EPIC-09: Prescription Export | [epic-09](epics/epic-09-prescription-export.md) | P1 | Low | `[x]` | None |
| EPIC-10: Clinic Settings & Services | [epic-10](epics/epic-10-clinic-settings.md) | P1 | Medium | `[x]` | None |
| EPIC-11: Dashboard Analytics | [epic-11](epics/epic-11-dashboard-analytics.md) | P1 | Medium | `[x]` | EPIC-03 |

### Phase 3 — Polish (Cross-Cutting)

| Epic | File | Priority | Effort | Status | Depends On |
|---|---|---|---|---|---|
| EPIC-12: i18n Arabic & English | [epic-12](epics/epic-12-i18n-arabic-english.md) | P2 | Very High | `[x]` | ALL others |
| EPIC-13: Responsive UI | [epic-13](epics/epic-13-responsive-ui.md) | P2 | Medium | `[x]` | ALL others |

---

## Recommended Execution Order

This order respects dependencies and maximizes parallel work:

```
PARALLEL GROUP A (no dependencies):
  1. EPIC-01: Patient Management
  2. EPIC-02: Notification Service
  3. EPIC-03: Medical Examination (Story 3.1-3.3)
  4. EPIC-04: Billing & Invoices
  5. EPIC-10: Clinic Settings & Services

THEN (has dependencies):
  6. EPIC-03 Story 3.4 + EPIC-05/06: Patient History & Prescriptions
  7. EPIC-07: Guest Public Pages (needs EPIC-10 for ClinicService model)
  8. EPIC-08: Appointment Reminders (needs EPIC-02 for notifications)
  9. EPIC-09: Prescription Export
  10. EPIC-11: Dashboard Analytics (needs EPIC-03 for Consultation extensions)

LAST (cross-cutting — must be done after all features are built):
  11. EPIC-12: i18n Arabic & English
  12. EPIC-13: Responsive UI Polish
```

---

## Key Files Reference

| File | Purpose |
|---|---|
| `bmad/prd.md` | Product Requirements Document — full feature specs |
| `bmad/architecture.md` | Technical architecture, model schemas, decisions |
| `bmad/backlog.md` | This file — master index and tracking |
| `bmad/epics/epic-*.md` | Individual epic files with stories and tasks |

---

## Global Definition of Done (All Epics)

- [x] All 13 epics marked as `[x]` completed
- [x] All migrations applied successfully
- [x] `python manage.py test` passes with no failures
- [x] RBAC enforced on all new endpoints
- [x] Full Arabic translation completed
- [x] Responsive layout verified on mobile (320px+)
- [x] Notification bell functional across all roles
- [x] Print-friendly views for prescriptions and invoices
- [x] Dynamic home page (no hardcoded data)
- [x] README updated with new features and setup instructions

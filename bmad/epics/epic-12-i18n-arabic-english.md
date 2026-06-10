# Epic 12: Arabic & English Language Support (i18n)

## Metadata
- **Epic ID:** EPIC-12
- **Priority:** P2 — Polish
- **Phase:** 3
- **Depends On:** All other epics (do last — cross-cutting)
- **Estimated Effort:** Very High
- **Affected Apps:** ALL apps, ALL templates, settings
- **Status:** `[x] Completed`

---

## Goal
Implement full bilingual (Arabic + English) support with Django i18n, complete Arabic translations for every user-facing string, RTL CSS support, and a language switcher.

---

## Stories

### Story 12.1: Django i18n Configuration
- **ID:** EPIC-12-S1
- **Status:** `[x] Completed`

#### Tasks
- `[x]` Modify `clinic/settings.py`:
  ```python
  from django.utils.translation import gettext_lazy as _
  LANGUAGES = [('en', _('English')), ('ar', _('Arabic'))]
  LANGUAGE_CODE = 'en'
  USE_I18N = True
  USE_L10N = True
  LOCALE_PATHS = [BASE_DIR / 'locale']
  ```
- `[x]` Add `django.middleware.locale.LocaleMiddleware` to MIDDLEWARE (after SessionMiddleware, before CommonMiddleware)
- `[x]` Add to `clinic/urls.py`:
  ```python
  from django.conf.urls.i18n import i18n_patterns
  path('i18n/', include('django.conf.urls.i18n'))
  ```
  Wrap main URL patterns with `i18n_patterns()` where appropriate
- `[x]` Create directory structure: `locale/ar/LC_MESSAGES/` and `locale/en/LC_MESSAGES/`

#### Acceptance Criteria
- [x] Django i18n fully configured
- [x] LocaleMiddleware active
- [x] Language switching endpoint available
- [x] Locale directories created

#### Files to Modify
- `clinic/settings.py`, `clinic/urls.py`

#### Files to Create
- `locale/ar/LC_MESSAGES/` (directory)
- `locale/en/LC_MESSAGES/` (directory)

---

### Story 12.2: Mark All Template Strings for Translation
- **ID:** EPIC-12-S2
- **Status:** `[x] Completed`
- **Depends On:** EPIC-12-S1

#### Tasks
- `[x]` Add `{% load i18n %}` to every template
- `[x]` Wrap EVERY user-facing string in EVERY template with `{% trans "..." %}` or `{% blocktrans %}...{% endblocktrans %}`
- `[x]` Templates to process (complete list):
  - `templates/base.html`
  - `templates/base_auth.html`
  - `templates/home.html`
  - `templates/doctors/list.html`
  - `templates/onboarding/doctor_onboarding.html`
  - `templates/onboarding/patient_onboarding.html`
  - `templates/profile/profile.html` + all partials
  - `accounts/templates/accounts/*.html` (login, register, forgot, reset, activation)
  - `accounts/templates/emails/*.html`
  - `admin_panel/templates/admin_panel/*.html`
  - `dashboard/templates/dashboard/*.html` + all partials
  - `emr/templates/emr/*.html`
  - `payments/templates/payments/*.html`
  - `reception/templates/reception/*.html`
  - `notifications/templates/notifications/*.html`
  - Any new templates from other epics

#### Acceptance Criteria
- [x] Every user-facing string wrapped with translation tag
- [x] No hardcoded English strings remain in templates
- [x] `{% load i18n %}` in every template file

#### Files to Modify
- ALL `.html` template files (30+ files)

---

### Story 12.3: Mark All Python Strings for Translation
- **ID:** EPIC-12-S3
- **Status:** `[x] Completed`
- **Depends On:** EPIC-12-S1

#### Tasks
- `[x]` Import `gettext_lazy as _` in all models, forms, views files
- `[x]` Wrap all user-facing strings:
  - Model field `verbose_name` values
  - Model `TextChoices` display strings
  - Form field labels and error messages
  - `messages.success()` / `messages.error()` strings
  - View context strings (dashboard_title, dashboard_subtitle)
  - ValidationError messages
- `[x]` Files to process:
  - `accounts/models.py`, `accounts/forms.py`, `accounts/views.py`
  - `appointments/models.py`, `appointments/views.py`, `appointments/services.py`
  - `emr/models.py`, `emr/forms.py`, `emr/views.py`
  - `reception/models.py`, `reception/forms.py`, `reception/views.py`
  - `payments/models.py`, `payments/views.py`
  - `notifications/models.py`, `notifications/views.py`
  - `admin_panel/forms.py`, `admin_panel/views.py`
  - `dashboard/views.py`

#### Acceptance Criteria
- [x] All user-facing Python strings wrapped with `_()`
- [x] Model choice labels translated
- [x] Flash messages translated
- [x] Error messages translated

#### Files to Modify
- ALL Python files with user-facing strings (15+ files)

---

### Story 12.4: Generate Arabic Translation File
- **ID:** EPIC-12-S4
- **Status:** `[x] Completed`
- **Depends On:** EPIC-12-S2, EPIC-12-S3

#### Tasks
- `[x]` Run `python manage.py makemessages -l ar --no-location`
- `[x]` Translate EVERY entry in `locale/ar/LC_MESSAGES/django.po`
- `[x]` Run `python manage.py compilemessages`
- `[x]` Test by switching language to Arabic

#### Acceptance Criteria
- [x] All strings have Arabic translations
- [x] No untranslated `msgstr ""` entries remain
- [x] Compiled `.mo` file generated
- [x] UI displays correctly in Arabic

#### Files to Create
- `locale/ar/LC_MESSAGES/django.po`
- `locale/ar/LC_MESSAGES/django.mo`

---

### Story 12.5: RTL CSS Support
- **ID:** EPIC-12-S5
- **Status:** `[x] Completed`
- **Depends On:** EPIC-12-S1

#### Tasks
- `[x]` Create `static/css/rtl.css` with RTL overrides:
  - Text alignment: `text-align: right`
  - Flex direction reversal where needed
  - Margin/padding mirror (left ↔ right)
  - Sidebar on right side
  - Form label alignment
  - Table header alignment
- `[x]` Modify `templates/base.html` and `templates/base_auth.html`:
  ```html
  {% load i18n %}
  {% get_current_language_bidi as LANGUAGE_BIDI %}
  <html lang="{% get_current_language %}" dir="{% if LANGUAGE_BIDI %}rtl{% else %}ltr{% endif %}">
  ```
  - Conditionally include `rtl.css`: `{% if LANGUAGE_BIDI %}<link href="{% static 'css/rtl.css' %}">{% endif %}`
- `[x]` Test all pages in RTL mode

#### Acceptance Criteria
- [x] Layout correctly mirrors in RTL mode
- [x] Sidebar on right side when Arabic
- [x] Forms, tables, and cards properly aligned
- [x] No visual overlaps or broken layouts

#### Files to Create
- `static/css/rtl.css`

#### Files to Modify
- `templates/base.html`, `templates/base_auth.html`

---

### Story 12.6: Language Switcher UI
- **ID:** EPIC-12-S6
- **Status:** `[x] Completed`
- **Depends On:** EPIC-12-S1

#### Tasks
- `[x]` Add language switcher to navbar/topbar:
  - Dropdown or toggle button: "EN" / "عربي"
  - Uses Django's `set_language` view via form POST
  ```html
  <form action="{% url 'set_language' %}" method="post">
      {% csrf_token %}
      <input type="hidden" name="next" value="{{ request.path }}">
      <select name="language" onchange="this.form.submit()">
          {% get_available_languages as languages %}
          {% for lang_code, lang_name in languages %}
              <option value="{{ lang_code }}" {% if lang_code == LANGUAGE_CODE %}selected{% endif %}>
                  {{ lang_name }}
              </option>
          {% endfor %}
      </select>
  </form>
  ```
- `[x]` Add to both `base.html` (public pages) and dashboard topbar/sidebar
- `[x]` Style the switcher to match the UI

#### Acceptance Criteria
- [x] Language switcher visible on all pages
- [x] Switching language reloads page in selected language
- [x] Language preference persisted in session

#### Files to Modify
- `templates/base.html`, `templates/base_auth.html`
- Dashboard topbar/sidebar template

---

## Definition of Done
- [x] All 6 stories completed
- [x] Every string translated to Arabic
- [x] RTL layout correct on all pages
- [x] Language switcher functional
- [x] No hardcoded English strings remain
- [x] Existing tests pass (may need updates for translated strings)

---

## Estimation Note
> This epic is the **largest single effort** in the project. It touches every template and many Python files. Consider splitting across multiple agents/sessions. Start with stories 12.1 (config) and 12.5 (RTL CSS) in parallel, then 12.2 + 12.3 (marking strings), then 12.4 (translation), then 12.6 (switcher).

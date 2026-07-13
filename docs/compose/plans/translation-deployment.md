# Translation Deployment Plan

## Problem
Translations only work on the welcome page. All other pages have hardcoded English text.

## Solution
1. Add language change signal to wizard
2. Update ALL pages to use i18n.t() for text
3. Add refresh mechanism to all pages

## Pages to Update
- welcome_page.py (already done)
- mod_source_page.py
- setup_page.py
- prereqs_page.py
- install_page.py
- complete_page.py
- credits_window.py

## Implementation Steps

### Step 1: Add language change signal to wizard.py
- Create custom signal for language changes
- Emit signal when language changes

### Step 2: Update each page
- Replace hardcoded strings with i18n.t() calls
- Add refresh method to update text when language changes
- Connect to wizard's language change signal

### Step 3: Test all translations
- Verify each page updates correctly
- Check all 9 languages

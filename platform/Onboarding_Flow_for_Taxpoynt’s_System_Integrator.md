# Onboarding Flow for Taxpoynt’s System Integrator (SI) service.

Excellent — thank you for such a detailed description. You’ve done a great job outlining the full current onboarding flow for **Taxpoynt’s System Integrator (SI)** service.

Now, wearing my **professional UI/UX designer hat**, I can confidently say: your current onboarding, while thorough, **feels too fragmented** and cognitively heavy for new users — especially enterprise clients who expect efficiency, clarity, and confidence in compliance platforms.

Let’s reimagine it using a **human-centered, progressive onboarding framework**, designed to balance *trust-building*, *data collection*, and *activation speed*.

# **🌐 OVERVIEW GOAL**

**Objective:**

Create a seamless, trust-driven onboarding journey that:

•	Minimizes friction

•	Avoids data duplication

•	Provides guided setup (progressive disclosure)

•	Ends with the user landing in a usable dashboard where they immediately see value (their “aha!” moment)

# **🚀 RECOMMENDED ONBOARDING STRUCTURE**

# **PHASE 1: Entry & Account Creation (Low Friction)**

**Goal:** Get the user into the platform as quickly as possible while collecting only essential info.

**Step 1: Landing Page → “Get Started”**

✅ Keep it simple: clear CTA that communicates value.

*“Start integrating your ERP with FIRS e-Invoice in minutes.”*

**Step 2: Auth Page**

•	Sign In / Sign Up tabs.

•	Social or SSO options (if possible for corporate users, e.g., Microsoft or Google Workspace).

•	For “Create Account,” **collect only personal info**:

•	Full name

•	Work email

•	Password

•	Role (optional)

⚡ **UX Tip:** Don’t ask for business info yet — that’s a barrier. First, get them *in*.

**Step 3: Email Verification (optional but recommended)**

Quick verify → Redirect to “Welcome to Taxpoynt” onboarding.

# **PHASE 2: Guided Company Setup (Progressive Onboarding)**

**Goal:** Collect necessary business & integration info, step-by-step, with smart defaults and progress indicators.

Present it as a **3-step wizard** inside the logged-in environment, not separate pages.

**Step 1: Company Profile**

•	Company name

•	RC/CAC number

•	TIN

•	Business address

•	Upload compliance docs (optional at this stage)

✅ Store & autosave progress.

**Note:** This replaces both “Business Info” and “Getting Started → Company Info.”

Consolidate them.

**Step 2: Choose Service Type**

•	Select: **System Integrator / Access Point Provider / Hybrid**

•	Based on selection, show a short explainer modal:

“System Integrators connect their ERP or CRM to the FIRS e-Invoice gateway.”

✅ Once they choose, show relevant setup fields.

**Step 3: Connect ERP / CRM**

•	Let users pick their system: Odoo, SAP, POS, etc.

•	Ask for integration credentials *or* provide “Connect Later” option.

•	If possible, show mini integrations marketplace UI.

🎯 The goal is not to complete the integration here — just link or prep it.

**✅ End of Phase**

**Button:** “Launch Workspace”

→ Directly opens their **System Integrator Dashboard** (with setup checklist visible).

# **PHASE 3: In-App Setup Wizard (Contextual, Inside Dashboard)**

**Goal:** Let users complete full technical setup inside the product, at their own pace.

Instead of forcing all 9 steps upfront, use an **interactive setup checklist sidebar** or **progressive wizard modal** accessible from the dashboard.

**Example: Dashboard Setup Checklist**

**Title:** “Complete Your System Integrator Setup (9 Steps)”

Each step expands on click (like a guided task list):

1.	✅ Organization Setup (auto-filled from company profile; editable)

2.	✅ Compliance Verification (upload documents)

3.	⚙️ ERP Configuration (load integration details)

4.	🔁 Data Mapping (interactive interface)

5.	🧪 Testing and Validation

6.	🛡️ Compliance Configuration

7.	🚀 Production Deployment

8.	👨‍🏫 Training & Handover

9.	🎉 Final Review and Go Live

🎯 Each step should have tooltips, progress indicators, and “Save & Continue Later” support.

Users can always resume from their dashboard.

# **PHASE 4: Activation & Engagement**

Once setup is complete → redirect to the **Operational Dashboard** (the “real” SI workspace):

•	Show summary widgets:

•	Connected ERP systems

•	Last sync

•	Compliance status

•	Recent invoices sent

Add onboarding tooltips (“guided tours”) the first time they land there.

# **🧩 VISUAL/UX PRINCIPLES**

**UX Aspect**	**Recommendation**

**Progress Feedback**	Use step indicators + completion % (progress bar)

**Smart Defaults**	Pre-fill where possible (from sign-up data, past entries)

**Clarity**	Use consistent language — “Company Info” ≠ “Organization Setup”

**Reduce Duplication**	Merge all “company” fields into a single form step

**Flexibility**	Allow “skip & complete later” for advanced configurations

**Onboarding Checklist**	Keep visible in dashboard sidebar until 100% complete

**Trust Elements**	Add “FIRS compliant”, “Secure Integration”, etc., badges early

**Persona-based Onboarding**	Adjust experience slightly for SI vs APP vs Hybrid users

# **🧭 SUMMARY OF STREAMLINED FLOW**

**Old Flow:** 4 steps → 4 steps → 9 steps → Dashboard

**New Flow:** 3 Phases (max 3 screens before dashboard) → progressive in-app setup

Landing → Auth → Account Creation

→ Company Setup Wizard (3 steps)

→ Dashboard with Setup Checklist

If you like, I can **mock up the new UX flow** visually — either as a:

•	🗺️ Flow diagram (step-by-step wireflow)

•	📱 UI wireframe screens

•	🧭 Interactive onboarding journey outline (for developers)

---

You’re thinking like a great product designer now: **simplify without losing clarity or compliance.**

Let’s evaluate those **nine steps** not as “features” but as **user goals** — what users *actually need to achieve* to start using Taxpoynt effectively.

# **🧱 THE 9 ORIGINAL STEPS (from your flow)**

1.	Organization Setup

2.	Compliance Verification

3.	ERP System Selection

4.	ERP Configuration

5.	Data Mapping Setup

6.	Testing and Validation

7.	Compliance Configuration

8.	Production Deployment

9.	Training and Handover

# **🧩 DESIGN RATIONALE**

In reality, not all of these are **onboarding** steps — several are **post-setup** operational or **account management** tasks.

From a UX perspective, onboarding should:

•	Build **trust**

•	Enable **connection/setup**

•	Lead the user to their **first success moment** (e.g., “Successfully synced your first invoice”)

Everything beyond that should happen **in-app**, as part of the ongoing workflow — not before seeing the dashboard.

So yes — **we should merge, restructure, and simplify**.

# **🎯 PROPOSED STREAMLINED SETUP FLOW**

We can reduce from 9 → **4 key phases**, which cover all required actions without overwhelming users.

# **1️⃣ Company & Compliance Setup (was steps 1 & 2)**

Goal: Identify and verify the organization.

•	Collect company name, CAC, TIN, address (already done earlier — prefill here)

•	Upload compliance documents (certificate, FIRS registration)

•	Basic FIRS verification call (async or automated)

✅ **Output:** Verified organization profile

🔄 Can run in background while user continues setup

# **2️⃣ System Integration Setup (was steps 3–5)**

Goal: Connect ERP or data source.

•	Select ERP/CRM system (Odoo, SAP, POS, etc.)

•	Connect via API key or credentials

•	Auto-import sample data

•	Quick data mapping (drag-and-drop or dropdown mapping interface)

•	Validate mapping with test data

✅ **Output:** System successfully linked and data mapped

🎯 This is your “first aha!” moment

# **3️⃣ Validation & Go-Live Prep (was steps 6–8)**

Goal: Ensure compliance and readiness.

•	Run automated validation tests (e.g., sample invoice compliance check)

•	Review compliance settings (JSON schema, FIRS endpoint)

•	Switch from “sandbox” to “production” environment (single toggle)

✅ **Output:** System ready for live invoicing

# **4️⃣ Onboarding Completion & Support (was step 9)**

Goal: Empower and retain the user.

•	Display success screen:

“🎉 Your system is now live and FIRS-compliant.”

•	Optional: Offer training video or documentation links

•	Provide onboarding checklist for ongoing learning:

•	Invite team members

•	Generate first invoice

•	Monitor compliance status

✅ **Output:** Confident, activated user landing on live dashboard

# **🪄 NEW STRUCTURE OVERVIEW**

**Phase**	**Old Steps Merged**	**Description**

**1. Company & Compliance Setup**	(1 + 2)	Basic org data + verification

**2. System Integration Setup**	(3 + 4 + 5)	Connect ERP/CRM + data mapping

**3. Validation & Go-Live Prep**	(6 + 7 + 8)	Testing + compliance config + deploy

**4. Onboarding Completion**	(9)	Training + launch dashboard

👉 **4 Phases instead of 9**, each taking 1–2 screens at most.

# **🎨 HOW TO VISUALIZE IT**

•	**Onboarding Checklist** inside the dashboard (like Notion’s or Monday.com’s setup list)

•	Each phase expandable → checklist items with “Start,” “In Progress,” “Done”

•	Show % completion and “Go Live” CTA once all are done

Example:

**System Integrator Setup**

•	✅ Company & Compliance Setup

•	🕓 System Integration Setup (2/3 complete)

•	⏳ Validation & Go-Live Prep

•	🔒 Training & Handover (optional)

[Continue Setup] → takes you to the next incomplete phase.

# **💡 UX BENEFITS**

**Old Flow (9-step)**	**New Flow (4-phase)**

Overwhelming	Manageable & guided

Linear & rigid	Flexible & progressive

Redundant fields	Smart reuse of earlier info

Hard to track progress	Clear visual progress

Too formal for first-time use	Builds early value and confidence

# **🧭 Optional UX Enhancement**

Consider a **“sandbox mode”** where new SI users can complete steps 2–3 using demo data.

This lets them see the system’s power before final compliance verification — a great way to build engagement before bureaucracy slows them down.

---
> **🚀 Candidate solution lives in [`solution/`](./solution/).**
>
> * Full code, tests, evals, and operator UI: [`solution/`](./solution/)
> * Quick start, API contract, and Design Notes: [`solution/README.md`](./solution/README.md)
> * Run it: `cd solution && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn allica.api.app:app --reload`
> * **API** (OpenAPI, `POST /run`): <http://localhost:8000/docs>
> * **Operator console** (Next.js): `cd solution/frontend && npm install && npm run dev` → <http://localhost:3000>
>
> Sample leads and Companies House stub ship under [`solution/data/`](./solution/data/) so `solution/` runs standalone. Narrative write-ups sit next to the code in [`solution/README.md`](./solution/README.md).

**For reviewers:** the assignment’s Part A (full bullet answers), Design Notes (full length), Quick Start, API response contract, and hosting notes are all in **[`solution/README.md`](./solution/README.md)** as the canonical submission README; the sections below are a short on-ramp only.

## Candidate — Problem and design framing

The assistant should help Allica’s GTM team turn noisy inbound leads into a **prioritisation signal**, a **routing decision**, and an **optional first-touch email draft**, with validation, registry enrichment, explainable rules, and basic compliance guardrails. A good first version routes obvious cases automatically and surfaces grey-zone leads with clear rationale.

**Full Part A answers** (problem interpretation, metrics and constraints, deliberate tradeoffs, high-level architecture) are in [`solution/README.md`](./solution/README.md) under the heading **Candidate — Problem and design framing**.

## Candidate — Design Notes

**Full design notes** (scoring and routing, safety and compliance, failure modes and observability, next steps) are in [`solution/README.md`](./solution/README.md) under the heading **Candidate — Design Notes**.

---

## Context

Allica serves established UK businesses that need specialist lending, often discovered through inbound interest (forms, referrals, events). Today, much of that inbound traffic is reviewed by humans who:

- Clean up messy input
- Check basic eligibility and risk
- Decide who should own the lead
- Write a tailored first touch email

Your job in this exercise is to design and implement a very small first version of an assistant that helps with that flow.

We are not looking for a perfect production system. We are looking for clear thinking about the problem, a pragmatic design, and a small but coherent implementation.

---

## Timebox

Aim for **3-5 focused hours**.

We do not expect everything to be finished or polished. If you run out of time, prefer a smaller, end to end slice with good reasoning over half finished features.

Please note what you would do next if you had another 1-2 days.

---

## Your Task

You will deliver two things:

1. **Problem and system framing (roughly 1 page in the README)**
2. **A small end to end implementation that processes inbound leads and produces:
   - a prioritisation signal per lead
   - a routing decision
   - an optional first touch email draft**

You are free to choose your languages, libraries, and hosting (if any), as long as we can run your solution.

---

## Data and materials

The repository contains:

- `data/leads_small.json`  
  Sample inbound leads. Includes noise such as duplicates and invalid data.

- `data/companies_house_stub.json`  
  Mocked external company registry with basic details (status, SIC codes, incorporation date, address).

- `docs/eligibility.md`  
  Simplified eligibility and risk notes.

- `docs/gtm_playbook.md`  
  GTM and messaging guidance: tone of voice, sector hints, routing rules.

You may assume these are roughly representative of the real world system, but simplified.

---

## Part A - Problem and design framing

Add a section to this README titled **"Candidate - Problem and design framing"** and answer the following in your own words (bullet points are fine):

1. **Problem interpretation**  
   In 3 to 5 sentences, describe what you think this assistant should do for Allica and for the GTM team. What does a "good" outcome look like for this first version?

2. **Metrics and constraints**  
   Pick:
   - one primary success metric for this system (for example, proportion of leads that are correctly routed on first pass), and
   - one or two guardrail metrics (for example, rate of unsafe messages, proportion of obviously ineligible leads that are still auto progressed).  

   Explain briefly why you chose them.

3. **Main tradeoffs you are making**  
   In this timebox, what are you *deliberately* not solving? Examples could be: deep credit risk modelling, complex UI, multi language support. Explain which constraints led you to that choice (time, complexity, risk, etc).

4. **High level architecture**  
   Sketch your solution at a high level. This can be a diagram or a short list of components, for example:
   - HTTP entrypoint
   - lead cleaning and validation
   - enrichment layer
   - scoring and routing
   - email drafting  
   For each component, note its main responsibility in one sentence.

This section is part of the testing. We are looking for clear problem understanding and sensible scoping.

---

## Part B - Functional requirements

Implement a small service that exposes **one HTTP endpoint** and runs a pipeline over the provided data.

### 1. API

Create an endpoint, for example:

- `POST /run`

with a JSON body of the form:

```json
{
  "leads": [
    {
      "id": "L-2001",
      "company_name": "Oxfordshire Bakery Ltd",
      "contact_name": "Amelia Shaw",
      "email": "amelia.shaw@example.com",
      "website": "https://oxonbakery.example",
      "employees": 18,
      "annual_revenue_gbp": 1800000,
      "notes": "Inbound form: equipment upgrade financing."
    }
  ]
}
```

If `leads` is omitted, you may default to `data/leads_small.json`.

The endpoint should return JSON containing, for each processed lead:

* original lead id and company name
* whether the lead passed basic validation
* any enrichment you used (for example the company number and status)
* a prioritisation or ICP signal between 0 and 1, or a simple priority rank
* a routing decision (for example which team or queue should own this)
* if you generate an email:

  * subject line
  * body text
* any safety or compliance flags you consider important

You can choose the exact field names, but **document the response structure** in the README.

### 2. Pipeline behaviour

Your pipeline should, at minimum:

1. **Deduplicate and validate leads**

   * Use a simple heuristic to spot obvious duplicates (for example, same company and website).
   * Validate email shape.
   * Mark or drop leads that clearly cannot be processed, and explain that choice in your design notes.

2. **Enrich with registry data**

   * Join to `companies_house_stub.json` when possible.
   * Use a small subset of fields that you believe matter for routing or messaging (for example, status, SIC, age).

3. **Apply eligibility and routing rules**

   * Use the notes in `docs/eligibility.md` and `docs/gtm_playbook.md` to:

     * flag clearly ineligible or risky leads,
     * compute a simple ICP or priority score,
     * decide who should own the lead (for example, Growth Inbound vs Triage vs Manual review).

   You are free to choose between a simple rule based approach, a numeric score, or a hybrid. The important part is that the decision is **explainable**.

4. **Optional: draft a first touch email**
   If you have time, use an LLM (or a template if you prefer) to generate a short first touch email that:

   * uses the company name,
   * reflects a plausible business need from the notes and enrichment,
   * respects the tone and safety rules in `docs/gtm_playbook.md`,
   * contains exactly one clear call to action.

   If you do not implement email drafting, describe in your Design Notes how you would do it.

5. **Basic safety**
   Ensure that your output does not:

   * promise guaranteed approval or fixed timelines,
   * invent specific pricing or terms,
   * contradict obvious red flags from `docs/eligibility.md`.

   Explain in your Design Notes how you enforce or check this.

---

## Part C - Non functional expectations

Within the timebox, aim for:

* **Clarity over completeness**
  Modules and functions that are easy to read, rather than overly generic abstractions.

* **Grounded decisions**
  Scoring and routing logic that can be explained from the data and docs, not magic thresholds with no rationale.

* **Operability**
  A simple way for a non engineer to run the system and inspect outputs (for example a CLI or the included static HTML page hitting your endpoint).

We do not require heavy tests, but a couple of small checks or examples (unit tests or scripted checks) are a plus.

---

## Deliverables

Please provide:

1. **Code and assets**

   * A **public GitHub repository**.
   * Clear instructions in this README for running the service locally.
   * Optional: a hosted URL where we can try the endpoint and simple UI.

2. **README additions**

   * The **Problem and design framing** section from Part A.
   * A **Quick Start** section with the exact commands to set up and run your solution.
   * A **Design Notes** section (see below).

3. **Design Notes (about 400-800 words total)**
   In a section titled **"Candidate - Design Notes"**, please cover:

   1. **Scoring and routing**
      How does your ICP or priority scoring work? Which 2 to 3 features matter most, and why? How did you choose routing buckets?

   2. **Safety and compliance**
      What are the main ways your system could produce an unsafe or misleading email? How does your current design reduce that risk, and what would you add next?

   3. **Failure modes and observability**
      What are the most important failure modes (for example missing enrichment, LLM errors, bad input)? How would you detect them in production, and what minimal logging or metrics did you add in this prototype?

   4. **Next steps**
      If you had another 1 to 2 days, what would you build next, and in what order?

---

## Getting started

You are free to choose your stack. One possible path is:

* A small HTTP service (for example FastAPI, Flask, Express, or similar)
* A single endpoint for `/run`
* A small script or UI to call it with `data/leads_small.json`

Please document:

* Prerequisites (for example Python version or Node version)
* Setup steps
* How to run locally
* How to run any optional checks or tests

If you choose to host your solution, any simple approach is fine (for example a small cloud instance, a serverless platform, or a static deployment with a backend). Please include the URL and any notes in the README.

---

## How we will evaluate

We will read your README and skim your code before running it. We are looking for:

* How clearly you understood and framed the problem
* Whether your design choices make sense for the business context
* How well your implementation matches your design
* Code clarity and structure
* Sensible scoping and tradeoffs for a 3 to 5 hour exercise

We will then use this as a starting point for a follow up conversation where we may ask you to extend or modify parts of your solution.

Good luck, and thank you for taking the time.

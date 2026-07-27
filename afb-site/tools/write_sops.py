import os, textwrap

OUT = "sop-library"
os.makedirs(OUT, exist_ok=True)

HOUSE = """<!-- Controlled document. The current version lives in the AFB operations
portal. A printed copy is uncontrolled once it leaves the screen. -->

# {code} · {title}

| Field | Value |
|---|---|
| Document code | `{code}` |
| Version | {version} |
| Status | {status} |
| Scope | {scope} |
| Department | {dept} |
| Applies to | {roles} |
| Owner | {owner} |
| Approved by | ______________________  *(signature required before issue)* |
| Effective date | ______________________ |
| Review cycle | {cycle} |
| Supersedes | {supersedes} |
| Records generated | {records} |

---

{body}

---

## Revision history

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | *(pending)* | {owner} | First controlled issue. Consolidates and supersedes `{supersedes}`, which carried no version, owner, approval or review date. {extra_change} |
"""

DOCS = []

# ---------------------------------------------------------------- SOP-PKG-001
DOCS.append(dict(
    code="SOP-PKG-001",
    title="Cleaning tables between packing different products",
    version="1.0", status="Active — pending approval",
    scope="**SQF — food safety.** This is a food safety control. Deviation is a deviation, not a preference.",
    dept="Packing Room", roles="Packer — Production · Sanitation Technician · Packing Room Manager",
    owner="SQF Practitioner", cycle="Annual, or on any change to products, chemicals or equipment",
    supersedes="Standard_Operating_Procedure_For_Cleaning_Packing_Room.docx",
    records="Cleaning log — one entry per changeover and per end of day",
    extra_change="Wording unchanged in substance; structure, responsibilities and record requirements made explicit.",
    body="""## 1. Purpose

To ensure a hygienic, contamination-free packing area by thoroughly cleaning tables and
equipment between different food products.

## 2. Why this matters

This facility handles **peanuts, tree nuts, sesame, milk and soy**. A changeover between two
products is therefore an allergen control point, not a housekeeping task. Product packed on an
inadequately cleaned table can injure a consumer and will be recalled.

## 3. Responsibilities

| Who | Does what |
|---|---|
| Packer / Sanitation Technician | Performs the clean and records it |
| Packing Room Manager | Verifies allergen changeovers before the line restarts |
| SQF Practitioner | Owns this procedure, reviews records, retains them |

## 4. Materials

- Cleaning cloths
- Brushes, assorted sizes
- Detergent — spray bottle labelled **Table Cleaner**
- Sanitizer — spray bottle labelled **Sanitizing Cleaner**
- Water spray bottles
- Face mask, protective gloves, safety goggles
- Cleaning log (portal, or paper backup)

Chemicals are used only from correctly labelled bottles. An unlabelled bottle is not used.

## 5. Procedure

### 5.1 Preparation
1. Put on PPE: gloves, safety goggles, face mask.
2. Remove all food product from the packing area.
3. Disconnect packing equipment from power.
4. Remove equipment from the tables, including scales.

### 5.2 Initial cleaning
5. Remove visible food residue using brushes or cloths.
6. Dispose of residue in the appropriate waste containers.

### 5.3 Wash
7. Apply **Table Cleaner** to all surfaces and parts.
8. Brush into crevices and hard-to-reach areas.
9. Rinse all surfaces with clean water until no soap residue remains.

### 5.4 Sanitize
10. Apply **Sanitizing Cleaner** to all surfaces and parts, to full coverage.
11. **Leave for a contact time of 10 minutes.** Do not wipe, rinse or reassemble early.
    Shortening contact time invalidates the clean.

### 5.5 Reassembly and inspection
12. Air-dry, or dry with clean towels.
13. Reassemble only once every part is completely dry.
14. Inspect for cleanliness. Any residue means return to 5.2.

### 5.6 Record
15. Record in the cleaning log, before the line restarts:
    date and time, area and equipment, product before, product after, whether this was an
    allergen changeover, sanitizer contact time, who performed it.
16. On an allergen changeover, the Packing Room Manager verifies and signs.

### 5.7 Restart
17. Reconnect power.
18. Run a test batch with water or empty to confirm no cleaning residue carries over.
19. Resume packing with the new product.

### 5.8 End of day
20. Repeat 5.1 to 5.7.
21. Additionally: clean and sanitize floors and surrounding work surfaces; empty and sanitize
    waste containers; clean and store all cleaning equipment.
22. Verify the whole packing area is clean, sanitized and ready for the next day.

## 6. Records

| Record | Where | Retained |
|---|---|---|
| Cleaning log — changeover | Operations portal | Per retention schedule |
| Cleaning log — end of day | Operations portal | Per retention schedule |

Records are entered as the work is done, not reconstructed at the end of a shift.

## 7. If something goes wrong

| Situation | Do this |
|---|---|
| Contact time was cut short | Do not restart. Re-sanitize with full contact time. Record what happened. |
| Residue found after reassembly | Strip down and return to 5.2. Record it. |
| Test batch is not clear | Do not restart. Notify the Packing Room Manager. |
| Chemical unlabelled or missing | Stop. Notify the Packing Room Manager. Do not substitute. |

Any of the above is reported to the Packing Room Manager the same shift, and to the SQF
Practitioner the same day."""))

# ---------------------------------------------------------------- SOP-SLS-001
DOCS.append(dict(
    code="SOP-SLS-001", title="Sales representative — routine and targets",
    version="1.0", status="Active — pending approval",
    scope="Business process. Not SQF-scoped.",
    dept="Sales", roles="Sales Representative",
    owner="Sales Director", cycle="Annual, or on any change to targets",
    supersedes="SOP_for_Sales_Team_Members.pdf",
    records="CRM activity log (Badger) · Orders (Pepperi) · Weekly report",
    extra_change="**Targets reconciled with `TRN-SLS-001`, which previously disagreed — see section 3. Requires Sales Director sign-off.**",
    body="""## 1. Purpose

To set out what a Sales Representative does daily, weekly and monthly, and the targets the
role is measured against.

## 2. Systems

Two systems, one job. Use both; neither is optional.

| System | Used for |
|---|---|
| **Badger** | Customers, territory, routes, visit logging, activity tracking |
| **Pepperi** | Product catalog, pricing, order entry, customer portal |

Badger is the master record for customer information. Enter it there first; Pepperi syncs.

## 3. Targets

> **Reconciliation note.** The superseded version of this SOP set 30 new customers per
> quarter. `TRN-SLS-001` sets 5 per week, which is about 65 per quarter — more than double.
> Revenue reconciled; customer count did not. The figures below adopt the Train the Trainers
> rate, because it is the one derived from the stated $3M to $6M business case.
> **The Sales Director must confirm this before issue.**

Everything derives from one weekly number.

| Period | New customers | Sales volume |
|---|---|---|
| **Weekly** | 5 | $12,500 |
| Monthly *(derived, 4 weeks)* | 20 | $50,000 |
| Quarterly *(derived, 13 weeks)* | 65 | $162,500 |

To reach 5 new customers a week, the funnel is: 25 prospects identified → 15 discovery calls
→ 10 proposals → 5 closed. Falling short at the end usually means falling short at the start.

## 4. Daily

- Visit your assigned territory.
- Meet at least 5 clients or prospects in person.
- Complete 10 meaningful customer touchpoints (the Daily 10 — see `TRN-SLS-001`).
- Spend one hour prospecting, ideally first thing.
- Log every activity in Badger the same day, not the next.

## 5. Weekly

- Submit your weekly report.
- Attend the team meeting.
- Identify 25 new qualified prospects.
- Review your funnel against target with your Sales Team Leader.

## 6. Monthly

- Attend the monthly sales training session.
- Review territory coverage: which customers have not been touched, and why.

## 7. Records

Nothing counts unless it is logged. A visit not recorded in Badger did not happen, an order
not entered in Pepperi cannot be picked, and neither can be credited to you.

## 8. Escalation

| Raise it to | When |
|---|---|
| Sales Team Leader | Anything blocking your territory, targets or accounts |
| Support team | Order, delivery, billing or service problems — see `SOP-CS-001` |
| Sales Director | Escalated by your Team Leader, or a risk of losing a major account |"""))

# ---------------------------------------------------------------- SOP-SLS-002
DOCS.append(dict(
    code="SOP-SLS-002", title="New Jersey sales territories",
    version="1.0", status="**Draft — cannot be issued until territories are assigned to named people**",
    scope="Business process. Not SQF-scoped.",
    dept="Sales", roles="Sales Representative · Sales Team Leader — New Jersey",
    owner="Sales Team Leader — New Jersey", cycle="Annual, or whenever an assignment changes",
    supersedes="SOP_for_New_Jersey_Sales_Territories.pdf",
    records="CRM territory assignment (Badger)",
    extra_change="Placeholder assignments (\\\"Sales Rep 1\\\" to \\\"Sales Rep 5\\\") retained as blanks rather than invented. Document held in draft until filled.",
    body="""## 1. Purpose

To define the New Jersey territories, who owns each, and how coverage is maintained.

## 2. Territories

| Territory | Assigned to | Covers |
|---|---|---|
| North Jersey | ______________________ | *(define — counties or ZIP ranges)* |
| Central Jersey | ______________________ | *(define)* |
| South Jersey | ______________________ | *(define)* |
| Jersey Shore | ______________________ | *(define)* |
| Western NJ | ______________________ | *(define)* |

> The superseded document assigned these to "Sales Rep 1" through "Sales Rep 5". Placeholders
> are not assignments. Until real names and boundaries are entered, this document stays in
> draft and is not issued to the team.

Boundaries matter as much as names. Two reps calling the same grocer is worse than neither
calling.

## 3. Expectations within a territory

- Visit your assigned territory daily.
- Build and maintain relationships with local retailers and distributors.
- Meet the targets in `SOP-SLS-001`.
- Keep Badger's territory assignment accurate — routing depends on it.

## 4. Coverage gaps

Review territory coverage monthly. Any customer not touched in 30 days is flagged and either
visited or reassigned. An account nobody has called in a quarter is not a customer, it is a
prospect a competitor is working.

## 5. Records

Territory assignment lives in Badger and is the single source of truth. Changes are made
there, then reflected here at the next revision.

## 6. Escalation

Issues, disputes over account ownership, or coverage that cannot be met go to the
**Sales Team Leader — New Jersey**, then to the Sales Director."""))

# ---------------------------------------------------------------- SOP-SLS-003
DOCS.append(dict(
    code="SOP-SLS-003", title="Sales Director",
    version="1.0", status="Active — pending approval",
    scope="Business process. Not SQF-scoped.",
    dept="Sales", roles="Sales Director",
    owner="Senior management", cycle="Annual",
    supersedes="SOP_for_Sales_Director.pdf",
    records="Monthly performance report · Quarterly development update",
    extra_change="Reporting lines aligned with `SOP-SLS-001`, `SOP-SLS-002` and `SOP-CS-001`.",
    body="""## 1. Purpose

To define the responsibilities, reporting and escalation of the Sales Director.

## 2. Scope of the role

Sales operations across **NYC, New Jersey and surrounding areas**.

## 3. Responsibilities

1. Develop and implement sales strategy against company goals.
2. Monitor and evaluate the performance of Sales Team Leaders and their teams.
3. Meet Sales Team Leaders regularly to review progress and address obstacles.
4. Align sales and promotional effort with marketing.
5. Approve budgets and resource allocation for sales activity.
6. Ensure compliance with company policy and industry regulation.
7. Own the targets in `SOP-SLS-001` — including approving any change to them.

## 4. Where this role sits

```
Senior management
      ↑
Sales Director  ────────────────┐
      ↑                         │
Sales Team Leaders              │  (in-house sales and customer
      ↑                         │   support escalate via SOP-CS-001)
Sales Representatives           │
                                ↓
                        Support team managers
```

## 5. Reporting

| What | To whom | When |
|---|---|---|
| Sales performance report | Senior management | Monthly |
| Team development and market expansion update | Senior management | Quarterly |
| Critical issues or risks | Senior management | Immediately |

## 6. Guidelines

- Keep communication open with Sales Team Leaders; provide guidance rather than waiting to be
  asked.
- Use Badger and Pepperi reporting for overall performance rather than assembled spreadsheets.
- Address issues escalated by Sales Team Leaders promptly, and close the loop with the person
  who raised them.

## 7. Escalation

Critical issues or risks go to senior management immediately, not in the next monthly report."""))

# ----------------------------------------------------------------- SOP-CS-001
DOCS.append(dict(
    code="SOP-CS-001", title="In-house sales and customer support",
    version="1.0", status="Active — pending approval",
    scope="Business process. Not SQF-scoped.",
    dept="Front Office", roles="Customer Service Representative · Accounting Clerk",
    owner="Customer Support Manager", cycle="Annual",
    supersedes="SOP_for_In-House_Sales_and_Customer_Support_Personnel.pdf",
    records="Customer interaction log (Badger) · Orders (Pepperi) · Escalation record",
    extra_change="Escalation timeframes added, and the sales/support split made explicit to match `TRN-SLS-001`.",
    body="""## 1. Purpose

To set expectations for in-house sales and customer support so that customers get a
consistent answer regardless of who picks up the phone.

## 2. Responsibilities

### 2.1 In-house sales
- Handle inbound sales inquiries.
- Follow up on leads and close sales.
- Maintain accurate records in Badger.
- Work with marketing so sales effort and promotion line up.

### 2.2 Customer support
- Address customer inquiries and resolve issues promptly.
- Provide product information and support.
- Document every customer interaction — the next person to speak to that customer relies on it.
- Escalate what you cannot resolve, rather than sitting on it.

## 3. What we handle and what the rep handles

| Support team handles | Sales rep handles |
|---|---|
| Routine order entry and reorders | Prospecting and new accounts |
| Shipment tracking and delivery confirmation | Strategic account relationships |
| Basic service inquiries | In-person visits |
| New customer paperwork and setup | Pricing and contract discussion |
| Order status updates | Merchandising audits |

Collaborative: complex issue resolution, new customer onboarding, large or custom orders,
customer complaints.

## 4. Guidelines

- Follow company policy on client interactions.
- Use Badger and Pepperi rather than personal notes or spreadsheets.
- Professional and courteous at all times, including when the customer is not.
- Return calls and emails within one business day, same day where possible.
- If you commit to something, do it — or call back and say you can't.

## 5. Escalation

| Urgency | Examples | Route | Response expected |
|---|---|---|---|
| **Immediate** | Damaged or wrong product delivered · safety or health concern · billing error · failed delivery · customer threatening to leave | Sales Manager or Customer Support Manager, by phone | Within 1 hour |
| **Same day** | Quality complaint · service dissatisfaction · unresolved recurring issue · return or refund request | Manager, by phone or email | Same business day |
| **Standard** | Process suggestions · documentation gaps · system issues · material requests | Email or portal ticket | 1–2 business days |

A useful escalation names the customer, states the problem in facts, says what you have
already done, makes a specific request and gives the deadline. "Customer is upset, please
call them" is not an escalation.

## 6. Records

Every interaction is documented in Badger while it is fresh. Feedback and recurring complaints
are flagged for the Customer Support Manager, because three customers reporting the same thing
is a process problem, not three incidents."""))

# ---------------------------------------------------------------- TRN-SLS-001
DOCS.append(dict(
    code="TRN-SLS-001", title="Sales training and certification program",
    version="2.0", status="Active — pending approval",
    scope="Business process. Not SQF-scoped. **Confidential — internal use only.**",
    dept="Sales", roles="Sales Director · Sales Representative · Customer Service Representative",
    owner="Sales Director", cycle="Quarterly review of content, annual full refresh",
    supersedes="Train_The_Trainers_Guide.docx v1.0",
    records="Training record per person, per module, with score and expiry",
    extra_change="Reduced from a 40-page guide to the parts that are auditable commitments. Full facilitation content retained as a separate trainer annex. Targets now match `SOP-SLS-001`.",
    body="""## 1. Purpose

To define how sales staff are trained, assessed, certified and re-certified — and what
records that produces.

> The superseded guide runs to about forty pages and mixes three things: the commitments
> (targets, pass marks, certification rules), the curriculum, and facilitation notes for
> trainers. Only the commitments belong in a controlled document, because only they get
> audited and only they need version control. The curriculum and facilitation notes continue
> as **Trainer Annex A**, uncontrolled and free to change between sessions.

## 2. Business case

| | |
|---|---|
| Current annual volume | $3M |
| Target annual volume | $6M |
| Route | 5 new customers per rep per week, systematically prospected |

This is the source of the target in `SOP-SLS-001`. If this number changes, that SOP changes
with it.

## 3. Cascade structure

| Tier | Who | How many | Certified in |
|---|---|---|---|
| 1 | Master trainers | 2–3 | Weeks 1–2 |
| 2 | Regional trainers | 9 | Weeks 3–4 |
| 3 | Sales representatives | 27+ | Weeks 5–8 |

Each tier certifies the one below it. A trainer may not train a tier until certified.

## 4. Competency areas

1. Platform mastery — Badger and Pepperi
2. Customer engagement — the Daily 10, visits, merchandising audits
3. Prospecting — qualification, discovery, closing
4. Product knowledge and positioning
5. Support team collaboration

## 5. Certification

### Stage 1 — Knowledge
| Assessment | Pass mark |
|---|---|
| Badger platform exam | 90% |
| Pepperi platform exam | 90% |
| Sales strategy assessment | 85% |

### Stage 2 — Skills
| Assessment | Pass mark |
|---|---|
| Badger skills demonstration | 90% |
| Pepperi skills demonstration | 90% |
| Role-play scenarios (3) | 72% average |

### Stage 3 — Field
| Assessment | Requirement |
|---|---|
| Observed customer visits | 3 visits, 85% average |
| Daily 10 | 5 consecutive days, logged in Badger |
| New customers closed | 1–2, prospecting through to close |

**Retakes:** two per stage. After a second failure, the participant, their manager and a
master trainer review whether further coaching, a different role, or an external obstacle is
the right answer.

## 6. Maintaining certification

| Check | Frequency |
|---|---|
| Competency spot-check | Quarterly |
| Recertification | Annual |

Minimum standing to remain certified:

- 5 new customers per week, averaged
- Daily 10 achieved on 80% or more of working days
- 95%+ daily platform usage
- Customer satisfaction 4.5 / 5 or better

## 7. Records

Every assessment produces a training record: person, module, score, pass mark, outcome,
assessor, date, expiry. Certification expires twelve months from the date of the last passing
Stage 3 assessment, and the holder and their manager are alerted 60 days ahead.

## 8. Definitions

| Term | Meaning |
|---|---|
| **Daily 10** | Ten meaningful customer touchpoints per day. Mass email, voicemail without a conversation, and generic social likes do not count. |
| **BANT** | Budget, Authority, Need, Timing — prospect qualification. |
| **SPIN** | Situation, Problem, Implication, Need-payoff — discovery questioning. |
| **ICP** | Ideal customer profile. |
| **Badger** | CRM: customers, territory, routes, activity. |
| **Pepperi** | Orders: catalog, pricing, order entry, customer portal. |"""))

for d in DOCS:
    text = HOUSE.format(**d)
    path = os.path.join(OUT, d["code"] + ".md")
    open(path, "w", encoding="utf-8").write(text)
    print(f"{d['code']:<12} {len(text):>6} chars  {d['title']}")

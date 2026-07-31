# AFB Backend — Link Reference

All links below are on `https://afb-backend-58ys.onrender.com`. Keep this file for your own reference — it is **not** linked from the public `/ops` page, since it contains the private review-portal token.

## Public / customer-facing (no login)

| Page | Path | Notes |
|---|---|---|
| Main site | `/store` | Marketing + retail/wholesale ordering |
| Careers | `/store/careers.html` | External job listings |
| Internal transfer application | `/store/employee-application.html` | Current-employee-only application form |
| SOP library (public) | `/store/sops.html` | Published SOPs |
| Legacy order page | `/order` | Older customer-facing order flow |

## Staff (login required)

| Page | Path | Notes |
|---|---|---|
| Staff login | `/login` | Username/password |
| Change password | `/change-password` | Account settings |
| Operations dashboard | `/dashboard` | KPIs, alerts, Receiving/Return/Reports/Pallets/Customers/Orders modals |
| Packing & production | `/production` | Packing Manager / Packer Portal / Product Mixer tabs |
| Inventory / stock count | `/stock` | Barcode, on-hand, location, adjust, history |
| Applications admin | `/applications-admin` | External applicants + internal transfers, two tabs |
| Review portal admin | `/review-admin` | Manage review projects, upload screenshots, triage comments, suggestions queue |

## Review portal — reviewer link (no login, token-gated)

**AFB Ops Review** (project #1, 17 workflow pages):
```
https://afb-backend-58ys.onrender.com/review/taS9tJvTtSoA6O1M2vAdl7Ah8FU
```
Anyone with this link can view and comment — treat it like an unlocked door. Don't post it anywhere public.

## Misc / dev

| Page | Path | Notes |
|---|---|---|
| Internal directory | `/ops` | Public, unauthenticated — lists the staff pages above (not the review token) |
| API docs | `/docs` | Live Swagger UI, every endpoint callable from the browser |

---
*Generated for reference — update the review-portal link above if you ever rotate or recreate the AFB Ops Review project.*

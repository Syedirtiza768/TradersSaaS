# TODOS — Traders ERP Implementation Plan
# Synthesized from: eng-review, CEO review, design review — 2026-05-11
# Branch: main | Commit: a9d1463
#
# Legend:
#   [DONE]    — already complete in codebase
#   [P0]      — do before any other sprint work (unblocks testing or is a security fix)
#   [P1]      — Phase 1 scope: migration wizard foundation
#   [P2]      — Phase 2 scope: migration wizard frontend + code quality
#   [P3]      — Phase 3 scope: performance, observability, testing
#   [DEFER]   — acknowledged, intentionally deferred
#
# Source codes:
#   ENG   — from plan-eng-review
#   CEO   — from plan-ceo-review
#   DES   — from plan-design-review

---

## Phase 0: Quick Wins — Do These First (< 1 hour total)

### [P0] QW-1: Remove duplicate `inventoryApi.getInventorySummary` method
**Source:** ENG CQ3
**File:** `frontend/trader-ui/src/lib/api.ts`
**Effort:** 5 min
**Why:** Two methods (`getSummary` and `getInventorySummary`) call identical endpoints. Any component using the wrong one will behave correctly but the dead method adds confusion and risks diverging in future.
**Fix:**
```
In api.ts, find inventoryApi object. Remove the getInventorySummary method entirely.
Search the codebase for any call to inventoryApi.getInventorySummary and replace with
inventoryApi.getSummary. Verify no component breaks.
```

### [P0] QW-2: Delete dead `ReportsPage.tsx`, rename `ReportsPageNew.tsx`
**Source:** ENG CQ4
**Files:** `frontend/trader-ui/src/pages/ReportsPage.tsx`, `ReportsPageNew.tsx`
**Effort:** 5 min
**Why:** `App.tsx:59` imports `ReportsPageNew` as `ReportsPage` but `ReportsPage.tsx` (the old file) still exists. It is never imported, but it confuses anyone reading the pages directory.
**Fix:**
```
1. Delete frontend/trader-ui/src/pages/ReportsPage.tsx (the old, unused file).
2. Rename frontend/trader-ui/src/pages/ReportsPageNew.tsx to ReportsPage.tsx.
3. Update App.tsx line 59: change import path from './pages/ReportsPageNew' to
   './pages/ReportsPage'. No logic changes.
```

### [P0] QW-3: Fix `_check_customer_credit_limit` broad exception catch
**Source:** ENG CQ6
**File:** `apps/trader_app/trader_app/api/sales.py` ~line 558
**Effort:** 10 min
**Why:** `except Exception: pass` silently swallows real errors (DB failures, unexpected crashes) in the credit limit check, hiding bugs in production.
**Fix:**
```python
# Replace the broad except with only the cases that are actually expected:
# - AttributeError: helper method doesn't exist (acceptable — optional feature)
# - ImportError: optional dependency not installed
# Change from:
try:
    _check_customer_credit_limit(...)
except Exception:
    pass
# Change to:
try:
    _check_customer_credit_limit(...)
except (AttributeError, ImportError):
    pass
# All other exceptions propagate — they represent real errors that need fixing.
```

### [P0] QW-4: Add `defusedxml` to requirements
**Source:** ENG, CEO (security)
**File:** `apps/trader_app/requirements.txt`
**Effort:** 2 min
**Why:** The migration wizard will parse untrusted Tally XML uploaded by users. Python's stdlib `xml.etree.ElementTree` is vulnerable to XXE (XML External Entity) injection — an attacker can exfiltrate server files via a crafted XML. `defusedxml` is a drop-in replacement that blocks all known XML attack vectors.
**Fix:**
```
Add to apps/trader_app/requirements.txt:
  defusedxml>=0.7.1

After adding, rebuild the Docker image:
  docker compose -f compose/docker-compose.yml build backend
```

### [DONE] QW-5: nginx `client_max_body_size`
**Source:** ENG (design review D5)
**Note:** Already set to `50m` at `infra/nginx/proxy.conf:35`. No action needed.

---

## Phase 1: Migration Wizard — Backend (Build in this order)

### [P1] M-1: Spike — parse one real Tally XML export
**Source:** CEO M1, Design Review (DES) D3 — HIGHEST RISK ITEM
**Effort:** 2–3 days (investigation, not coding)
**Why this comes first:** Every other migration task is speculative until you know what a real Tally XML export looks like. ERP 9, TallyPrime 3.x, and TallyPrime 4.x use different XML schemas. The mapping step UX (confidence scores, dropdown suggestions) is built on assumptions about how ledger names appear. None of it is validated until you run it on real data.
**What to do:**
```
1. Ask one current user: "Can you send us your Tally data export? 
   File → Export → Data (XML format). It will be a .xml file."
2. Run xml.etree.ElementTree.parse() on it in a scratch Python script.
   Print: root tag, version attribute, first 3 LEDGER nodes,
   first 3 VOUCHER nodes, first STOCKITEM node.
3. Document: which root tag? (<TALLYMESSAGE>, <ENVELOPE>, other?)
   What does a ledger PARENT tag look like? Is it always present?
   What date format are voucher dates in?
4. Try parsing with both ERP9 and Prime3 code paths. Which matches?
5. Write your findings to apps/trader_app/trader_app/migration/SPIKE.md.
   Gate all migration sprint work on this document.
```
**Acceptance:** You can extract customer count, ledger count, invoice count from the real export.

### [P1] M-2: Create `Migration Job` custom DocType
**Source:** CEO, ENG A2
**File:** `apps/trader_app/trader_app/migration/doctype/migration_job/migration_job.json`
**Effort:** 2 hours
**Why:** Background migration jobs need durable state storage. If the job ID is only in Redis (which expires), users who close the browser mid-migration and return will have no way to reconnect to their running job. A DocType persists across server restarts and Redis flushes.
**Fields to create:**
```
migration_job (DocType, no submit, no amend):
  - name          : Data (auto-name)
  - owner         : Link → User (auto-set)
  - company       : Link → Company
  - status        : Select ["Queued", "Parsing", "Mapping", "Importing", "Draft", "Submitted", "Failed", "Cancelled"]
  - source_type   : Select ["Tally ERP 9", "TallyPrime 3.x", "TallyPrime 4.x", "CSV"]
  - file_path     : Data (server path to uploaded file)
  - progress      : Int (0-100)
  - current_step  : Data (human-readable, e.g. "Importing customers (67/248)...")
  - error_message : Text (populated on failure)
  - mapping_json  : JSON (stores user's ledger mapping selections from Step 3)
  - summary_json  : JSON (counts of what was imported: customers, items, invoices...)
  - job_id        : Data (RQ job ID for reconnecting to running job)
  - completed_at  : Datetime
```
**Note:** `name` becomes the migration wizard's URL parameter: `/migrate/detect?job=MJ-0001`

### [P1] M-3: Build `MigrationExtractor` ABC and `NormalizedPayload`
**Source:** CEO (architecture), ENG A3
**File:** `apps/trader_app/trader_app/migration/migration_extractor.py`
**Effort:** 3 hours
**Why:** All migration sources (Tally ERP9, TallyPrime, CSV) must produce an identical data structure for the import engine. The abstract base class enforces this contract at dev time.
**Code to write:**
```python
# apps/trader_app/trader_app/migration/migration_extractor.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class NormalizedCustomer:
    name: str
    gstin: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    outstanding_amount: float = 0.0
    currency: str = "INR"

@dataclass
class NormalizedSupplier:
    name: str
    gstin: Optional[str] = None
    phone: Optional[str] = None
    outstanding_amount: float = 0.0
    currency: str = "INR"

@dataclass
class NormalizedItem:
    code: str
    name: str
    item_group: str = "All Item Groups"
    uom: str = "Nos"
    stock_qty: float = 0.0
    valuation_rate: float = 0.0

@dataclass
class NormalizedLedger:
    tally_name: str                   # exactly as it appears in Tally
    tally_parent: Optional[str]       # Tally group (e.g. "Sundry Debtors")
    tally_type: str                   # Tally built-in type
    suggested_erp_account: Optional[str] = None
    confidence: float = 0.0           # 0.0–1.0

@dataclass
class NormalizedInvoice:
    source_id: str                    # Tally voucher number
    doctype: str                      # "Sales Invoice" or "Purchase Invoice"
    party: str                        # customer or supplier name
    party_type: str                   # "Customer" or "Supplier"
    date: str                         # ISO 8601 YYYY-MM-DD
    items: list = field(default_factory=list)
    taxes: list = field(default_factory=list)
    currency: str = "INR"
    total: float = 0.0

@dataclass
class NormalizedPayload:
    source_type: str                  # "Tally ERP 9", "TallyPrime 3.x", etc.
    source_version: Optional[str]     # detected from file
    customers: list[NormalizedCustomer] = field(default_factory=list)
    suppliers: list[NormalizedSupplier] = field(default_factory=list)
    items: list[NormalizedItem] = field(default_factory=list)
    ledgers: list[NormalizedLedger] = field(default_factory=list)
    invoices: list[NormalizedInvoice] = field(default_factory=list)
    opening_balances: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)  # non-fatal issues found during parse
    errors: list[str] = field(default_factory=list)    # fatal issues


class MigrationExtractor(ABC):
    """
    All source extractors implement this interface.
    extract() reads the source file and returns NormalizedPayload.
    It must not write to the database.
    It must not raise for recoverable errors — add them to payload.warnings instead.
    It raises MigrationParseError for unrecoverable failures only.
    """

    @abstractmethod
    def detect(self, file_path: str) -> bool:
        """Return True if this extractor can handle this file."""

    @abstractmethod
    def extract(self, file_path: str) -> NormalizedPayload:
        """Parse the file. Returns NormalizedPayload. Never writes to DB."""


class MigrationParseError(Exception):
    """Raised when the file is fundamentally unreadable (wrong format, corrupt)."""
    def __init__(self, message: str, remediation: str = ""):
        self.message = message
        self.remediation = remediation
        super().__init__(message)
```

### [P1] M-4: Build Tally extractor with version strategy pattern
**Source:** ENG A3, CEO M2
**Files:**
- `apps/trader_app/trader_app/migration/migration_tally.py`
- `apps/trader_app/trader_app/migration/strategies/tally_erp9.py`
- `apps/trader_app/trader_app/migration/strategies/tally_prime3.py`
- `apps/trader_app/trader_app/migration/strategies/tally_prime4.py`
**Effort:** 2–3 days (after M-1 spike completes — the spike output defines the exact xpath and tag names)
**Why:** Tally ERP 9, TallyPrime 3.x, and TallyPrime 4.x use different XML schemas. A single parser breaks on any version mismatch. The strategy pattern lets version detection dispatch to the correct parser.
**Architecture:**
```python
# migration_tally.py

import defusedxml.ElementTree as ET  # NEVER use stdlib xml.etree — XXE risk
from .migration_extractor import MigrationExtractor, MigrationParseError, NormalizedPayload

class TallyExtractor(MigrationExtractor):
    """
    Detects Tally version and dispatches to the appropriate strategy.
    """
    STRATEGIES = []  # populated below

    def detect(self, file_path: str) -> bool:
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            return root.tag in ("TALLYMESSAGE", "ENVELOPE", "TALLY")
        except Exception:
            return False

    def extract(self, file_path: str) -> NormalizedPayload:
        tree = ET.parse(file_path)
        root = tree.getroot()
        version = self._detect_version(root)

        for strategy_class in self.STRATEGIES:
            strategy = strategy_class()
            if strategy.matches(version):
                return strategy.extract(root)

        raise MigrationParseError(
            f"Unsupported Tally version: {version}",
            remediation="This export is from a Tally version we don't support yet. "
                        "Try TallyPrime 3.x or TallyPrime 4.x, or use our CSV template."
        )

    def _detect_version(self, root) -> str:
        # TallyPrime 4.x: root tag is ENVELOPE, has HEADER/TALLYREQUEST child
        # TallyPrime 3.x: root tag is TALLYMESSAGE with VERSION="3"
        # ERP 9: root tag is TALLYMESSAGE without VERSION
        # Fill in exact detection after M-1 spike
        ...


# strategies/tally_prime3.py — implement after M-1 spike
class TallyPrime3Strategy:
    def matches(self, version: str) -> bool:
        return version == "TallyPrime 3.x"

    def extract(self, root) -> NormalizedPayload:
        payload = NormalizedPayload(source_type="TallyPrime 3.x")
        # Extract customers from LEDGER nodes where PARENT == "Sundry Debtors"
        # CRITICAL: if PARENT tag is missing, add to payload.warnings NOT raise
        # Extract items from STOCKITEM nodes
        # Extract invoices from VOUCHER nodes where VOUCHERTYPENAME in ("Sales", "Purchase")
        # Use iterparse for files > 5MB to avoid OOM
        return payload
```
**CRITICAL NOTE:** If a ledger node has no PARENT tag (silent data loss risk from ENG review), add `payload.warnings.append(f"Ledger '{name}' has no PARENT — will map to Miscellaneous")` instead of silently skipping or raising.

### [P1] M-5: Build `GenericCSVExtractor`
**Source:** CEO (Peachtree/other legacy systems), DES (CSV template download)
**File:** `apps/trader_app/trader_app/migration/migration_csv.py`
**Effort:** 4 hours
**Why:** The adapter pattern means any non-Tally user (Peachtree, QuickBooks, Busy, or manual Excel) can migrate via a downloadable CSV template. This is the universal fallback and costs 4 hours to build.
**Template sheets to define (one CSV per type, or one multi-sheet Excel):**

```
customers.csv columns:
  name*, phone, email, address, gstin, outstanding_amount, currency

suppliers.csv columns:
  name*, phone, address, gstin, outstanding_amount, currency

items.csv columns:
  code*, name*, item_group, uom, stock_qty, valuation_rate

sales_invoices.csv columns:
  invoice_number*, customer*, date* (YYYY-MM-DD), item_code*, qty*, rate*, tax_amount

purchase_invoices.csv columns:
  invoice_number*, supplier*, date* (YYYY-MM-DD), item_code*, qty*, rate*, tax_amount

(* = required field)
```

**Extractor behavior:**
- Reads each CSV file from an uploaded ZIP archive
- Validates required fields — collects all errors before returning (never stop on first error)
- Returns NormalizedPayload with same structure as Tally extractor
- Validation errors go to `payload.errors`; rows with missing required fields go to `payload.warnings`

**Download endpoint:**
```python
@frappe.whitelist(allow_guest=False)
def download_csv_template():
    """Returns a ZIP containing the 5 template CSVs with example rows."""
    # Build zip in-memory, return as file attachment
```

### [P1] M-6: Build ledger mapping engine
**Source:** ENG A4, CEO M3
**File:** `apps/trader_app/trader_app/migration/migration_mapping.py`
**Effort:** 1 day
**Why:** The mapping step (Step 3 of wizard) needs a backend service that: (1) fetches all ERPNext accounts for the company, (2) runs similarity scoring against each Tally ledger name, (3) returns confidence-scored suggestions for the frontend dropdown.
**Key functions:**
```python
def build_ledger_mapping(company: str, ledgers: list[NormalizedLedger]) -> list[dict]:
    """
    For each Tally ledger, return up to 5 candidate ERPNext accounts ranked by
    similarity. Uses:
    - Exact string match → confidence 1.0
    - Tally parent group → ERPNext account type mapping table (see below)
    - Fuzzy string similarity (difflib.SequenceMatcher) → confidence 0.3–0.8
    Returns list of dicts:
    {
        "tally_name": "Debtors Control",
        "tally_parent": "Sundry Debtors",
        "confidence": 0.92,
        "suggested": "Debtors",   # top match
        "options": ["Debtors", "Accounts Receivable", "Trade Receivables", ...]
    }
    """

# Tally parent group → ERPNext account type mapping table
PARENT_TO_ACCOUNT_TYPE = {
    "Sundry Debtors":      ("Receivable", 0.9),
    "Sundry Creditors":    ("Payable", 0.9),
    "Bank Accounts":       ("Bank", 0.85),
    "Cash-in-Hand":        ("Cash", 0.85),
    "Sales Accounts":      ("Income Account", 0.8),
    "Purchase Accounts":   ("Expense Account", 0.8),
    "Direct Expenses":     ("Expense Account", 0.75),
    "Indirect Expenses":   ("Expense Account", 0.75),
    "Stock-in-Hand":       ("Stock", 0.85),
    "Capital Account":     ("Equity", 0.8),
    "Loans (Liability)":   ("Payable", 0.7),
}
```

### [P1] M-7: Build import engine (draft approach)
**Source:** ENG A2, CEO M4
**File:** `apps/trader_app/trader_app/migration/migration_import.py`
**Effort:** 2 days
**Why:** The import engine creates all records as `docstatus=0` (Draft) tagged with the `migration_job_id`. This gives the trader a preview of their data before committing. "Go Live" batch-submits all drafts. "Cancel" deletes all drafts by job ID.
**Key functions:**
```python
def execute_migration(job_id: str, payload: NormalizedPayload, mapping: dict):
    """
    Creates all records as docstatus=0 (Draft) tagged with migration_job_id.
    Updates Migration Job progress field as each batch completes.
    Commits in batches of 50 to avoid single massive transaction.
    Sets frappe.set_user(session_user) at start — background job runs as Administrator
    by default, which would create records owned by Administrator.
    """

def submit_migration(job_id: str):
    """
    Batch-submits all Draft documents tagged with this job_id.
    Called when user clicks "Go Live".
    Uses frappe.db.sql for batch operations — do NOT loop frappe.submit() on 10,000 docs.
    """

def rollback_migration(job_id: str):
    """
    Deletes all Draft documents tagged with this job_id.
    Safe to call at any time before submit_migration.
    Also deletes the Migration Job DocType record.
    """

def get_migration_summary(job_id: str) -> dict:
    """
    Returns counts for the review step:
    { "customers": 248, "suppliers": 67, "items": 1840,
      "sales_invoices": 6230, "purchase_invoices": 3108,
      "ledgers_mapped": 34, "ledgers_misc": 12,
      "date_range": "2025-01-01 to 2025-12-31" }
    """
```
**Batch commit pattern:**
```python
# Never commit 10,000 docs in one transaction.
# Commit every 50 docs to keep the transaction log manageable.
for i, customer in enumerate(payload.customers):
    doc = frappe.get_doc({...})
    doc.migration_job_id = job_id
    doc.insert(ignore_permissions=True)
    if i % 50 == 49:
        frappe.db.commit()
frappe.db.commit()  # final commit for remainder
```

### [P1] M-8: Build whitelisted API endpoints
**Source:** ENG A2, CEO
**File:** `apps/trader_app/trader_app/migration/migration.py`
**Effort:** 4 hours
**Why:** The React frontend needs REST endpoints to drive the wizard. All endpoints go through Frappe's whitelist decorator for auth and CSRF protection.
**Endpoints:**
```python
@frappe.whitelist()
def upload_migration_file():
    """
    Accepts multipart file upload.
    Saves to private files (not public).
    Runs TallyExtractor.detect() to validate format.
    Creates Migration Job with status="Parsing".
    Enqueues parse_migration_file.delay(job_id).
    Returns: { "job_id": "MJ-0001", "redirect": "/migrate/detect?job=MJ-0001" }
    """

@frappe.whitelist()
def get_migration_status(job_id: str):
    """
    Returns current Migration Job state for polling.
    Returns: { "status": "Parsing", "progress": 67, "current_step": "Reading invoices...",
               "warnings": [...], "error": null }
    """

@frappe.whitelist()
def get_migration_mapping(job_id: str):
    """
    Returns ledger mapping suggestions for Step 3.
    Calls build_ledger_mapping() with the parsed ledgers.
    Returns: list of { tally_name, confidence, suggested, options }
    """

@frappe.whitelist(methods=["POST"])
def save_migration_mapping(job_id: str, mapping: list):
    """
    Saves user's mapping selections to Migration Job.mapping_json.
    Called when user clicks Continue on Step 3.
    """

@frappe.whitelist()
def get_migration_summary(job_id: str):
    """
    Returns import summary for Step 4 review screen.
    """

@frappe.whitelist(methods=["POST"])
def start_migration_import(job_id: str):
    """
    Enqueues execute_migration as background job.
    Changes status to "Importing".
    Returns: { "job_id": "MJ-0001" }
    """

@frappe.whitelist(methods=["POST"])
def submit_migration(job_id: str):
    """
    Calls submit_migration(job_id) — the "Go Live" action.
    This is irreversible. Returns success or error.
    """

@frappe.whitelist(methods=["POST"])
def rollback_migration(job_id: str):
    """
    Calls rollback_migration(job_id) — the "Cancel import" action.
    Safe at any time before Go Live.
    """
```

---

## Phase 2: Migration Wizard — Frontend

### [P2] FE-1: Build `WizardProgressBar` component
**Source:** DES D1
**File:** `frontend/trader-ui/src/components/WizardProgressBar.tsx`
**Effort:** 2 hours
**Spec:**
```tsx
interface WizardProgressBarProps {
  steps: { label: string; status: 'completed' | 'active' | 'pending' }[]
  currentStep: number
}
// Visual: numbered dots (1-5) connected by horizontal line
// Completed: filled brand-700 circle with checkmark icon
// Active: filled brand-700 circle with step number, bold label
// Pending: empty gray circle with step number, gray label
// No click navigation in Phase 1 — display only
// ARIA: role="navigation" aria-label="Migration steps"
//       aria-current="step" on active dot
```

### [P2] FE-2: Build `FileDropZone` component
**Source:** DES D2
**File:** `frontend/trader-ui/src/components/FileDropZone.tsx`
**Effort:** 3 hours
**Spec:**
```tsx
interface FileDropZoneProps {
  onFile: (file: File) => void
  accept: string[]            // ['.xml', '.csv', '.zip']
  maxSizeMB: number           // 50
  label: string
}
// States: default, drag-over (border brand-500 + bg-brand-50), file-selected, error
// Error messages:
//   wrong type: "This is a .xlsx file. Export from Tally as XML instead."
//   too large:  "This file is Xmb. Max 50 MB — try splitting your Tally export by date range."
// Fallback: always show "Browse Files" btn-primary inside zone
// aria-label="Upload Tally export file" on hidden <input type="file">
```

### [P2] FE-3: Build `MigrationWizardLayout`
**Source:** DES (wizard layout)
**File:** `frontend/trader-ui/src/layouts/MigrationWizardLayout.tsx`
**Effort:** 2 hours
**Spec:**
```tsx
// Wraps the wizard route. Hides the main sidebar.
// Shows a minimal header: "← Back to Dashboard" link (left) + Traders logo (center).
// Renders WizardProgressBar below header.
// Main content: centered card, max-width 760px.
// Sticky footer: Back and Continue buttons, pinned to bottom of viewport.
// On mobile: full-width, no sidebar.
// Uses isMigrationMode context or URL-based detection to suppress sidebar.
```

### [P2] FE-4: Build all 5 wizard step components
**Source:** DES (all screens)
**Files:**
```
frontend/trader-ui/src/pages/migration/
  MigrationUploadStep.tsx      — Step 1: FileDropZone + scope callout
  MigrationDetectStep.tsx      — Step 2: progress bar + step checklist, polls API
  MigrationMappingStep.tsx     — Step 3: table/card-list with SearchableSelect dropdowns
  MigrationReviewStep.tsx      — Step 4: import summary table + draft safety copy
  MigrationGoLiveStep.tsx      — Step 5A: large CTA + undo warning
  MigrationAhaMomentStep.tsx   — Step 5B: 3 report cards with real numbers
```
**State management:**
```tsx
// useMigrationStore.ts (Zustand)
interface MigrationStore {
  jobId: string | null
  currentStep: number
  mapping: Record<string, string>   // tally_name → erp_account
  summary: MigrationSummary | null
  setJobId: (id: string) => void
  setMapping: (m: Record<string, string>) => void
  reset: () => void
}
// Persist to localStorage key "migration_session"
// so users can resume after page refresh
```
**Route to add to App.tsx:**
```tsx
// Add inside the ProtectedRoute wrapper, outside DashboardLayout:
<Route path="migrate" element={<MigrationWizardLayout />}>
  <Route index element={<MigrationUploadStep />} />
  <Route path="detect" element={<MigrationDetectStep />} />
  <Route path="map" element={<MigrationMappingStep />} />
  <Route path="review" element={<MigrationReviewStep />} />
  <Route path="go-live" element={<MigrationGoLiveStep />} />
  <Route path="complete" element={<MigrationAhaMomentStep />} />
</Route>
// Note: MigrationWizardLayout sits OUTSIDE DashboardLayout so the sidebar is absent.
```

### [P2] FE-5: Build `ConfidenceBadge` component
**Source:** DES (mapping step)
**File:** `frontend/trader-ui/src/components/ConfidenceBadge.tsx`
**Effort:** 30 min
**Spec:**
```tsx
// Three levels, never show the raw percentage to users:
// confidence >= 0.85 → green dot + "Matched" (aria-label="High confidence match")
// 0.5 <= conf < 0.85 → amber dot + "Review" (aria-label="Review this match")
// conf < 0.5        → red "?" + "Select" (aria-label="No match — select manually")
// Used in MigrationMappingStep table rows
```

### [P2] FE-6: Build `JobProgressBar` component
**Source:** DES (Steps 2 and 4 loading states)
**File:** `frontend/trader-ui/src/components/JobProgressBar.tsx`
**Effort:** 1 hour
**Spec:**
```tsx
// Determinate progress bar with brand-700 fill
// Shows percentage number right-aligned
// Below bar: step checklist
//   Each item: icon (pending=gray circle | active=spinner | done=green CheckCircle) + label
// Example:
//   ✓ File received (2.4 MB)
//   ✓ Format detected: TallyPrime 3.x
//   ⟳ Reading ledger accounts...        ← spinner, currently active
//     Reading items...                   ← gray, pending
//     Reading transactions...            ← gray, pending
```

### [P2] FE-7: Build `AhaMomentCard` component
**Source:** DES D6 (aha moment)
**File:** `frontend/trader-ui/src/components/AhaMomentCard.tsx`
**Effort:** 3 hours
**Spec:**
```tsx
// Extended KPICard variant. Three card types:
//
// Type "receivables":
//   Header: "Outstanding Receivables" + wallet icon
//   Hero number: formatted currency total
//   Sub: "across N customers"
//   Mini-table: 4 aging buckets (0-30d, 31-60d, 61-90d, 90+d) with amounts
//
// Type "dead_stock":
//   Header: "Dead Stock Alert" + package icon
//   Hero number: formatted currency value
//   Sub: "N items with no sales in 90+ days"
//   (No chart — the number alone is the message)
//
// Type "profitability":
//   Header: "Customer Profitability" + users icon
//   Sub: "Top N customers drive X% of revenue"
//   Horizontal bar chart (recharts) — top 5 customers, single bar each
//
// All cards: "View Full Report" link at bottom → respective report page
// If API still loading: skeleton shimmer (not blank card, not spinner)
// If API error: "Couldn't load — retry?" with refresh icon
```

---

## Phase 3: Code Quality Fixes

### [P3] CQ-1: Fix `get_kpis()` silent exception swallowing
**Source:** ENG CQ1
**File:** `apps/trader_app/trader_app/api/dashboard.py`
**Effort:** 30 min
**Why:** `get_kpis()` catches ALL exceptions and returns zeros. When the DB is down, the dashboard silently shows all zeros — operators think revenue is zero, not that there's an outage.
**Fix:**
```python
# Change from: catch all exceptions, return zeros
# Change to: only catch frappe.PermissionError and frappe.DoesNotExistError
# Let unexpected exceptions propagate — they surface in Frappe error log
# and can be monitored via /app/error-log in ERPNext desk
```

### [P3] CQ-2: Fix dashboard cache no-op
**Source:** ENG A1 — CRITICAL
**File:** `apps/trader_app/trader_app/api/dashboard.py` ~line 330
**Effort:** 1 hour
**Why:** `refresh_dashboard_cache()` is called every 15 minutes by the scheduler but DISCARDS the result. The `get_kpis()` API makes 10+ SQL queries on every single dashboard load — at 50 users this is 500+ queries per page load.
**Fix:**
```python
CACHE_KEY = "trader_dashboard_kpis"
CACHE_TTL = 900  # 15 minutes, matches scheduler interval

@frappe.whitelist()
def get_kpis(company: str = None):
    cache_field = f"kpis_{company or 'default'}"
    cached = frappe.cache().hget(CACHE_KEY, cache_field)
    if cached:
        return frappe.parse_json(cached)
    result = _compute_kpis(company)
    frappe.cache().hset(CACHE_KEY, cache_field, frappe.as_json(result))
    frappe.cache().expire(CACHE_KEY, CACHE_TTL)
    return result

def refresh_dashboard_cache():
    """Called by scheduler every 15 min. Pre-warms cache for all companies."""
    frappe.cache().delete_key(CACHE_KEY)
    for company in frappe.get_all("Company", pluck="name"):
        try:
            get_kpis(company=company)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Dashboard cache refresh failed")
```

### [P3] CQ-3: Fix hardcoded low stock threshold
**Source:** ENG CQ2
**File:** `apps/trader_app/trader_app/api/inventory.py` ~line 455, and `dashboard.py` ~line 75
**Effort:** 1 hour
**Why:** `HAVING qty > 0 AND qty < 10` is hardcoded. Items with different reorder levels (a factory item reorders at 100; a spare part reorders at 2) are both checked against 10.
**Fix:**
```python
# Use tabItem Reorder table to get per-item thresholds
# Query:
#   SELECT item_code, SUM(actual_qty) as qty,
#          COALESCE(r.warehouse_reorder_qty, 10) as reorder_level
#   FROM tabBin b
#   LEFT JOIN `tabItem Reorder` r ON r.parent = b.item_code
#   WHERE b.warehouse = %(warehouse)s
#   HAVING qty <= reorder_level AND qty > 0
```

### [P3] CQ-4: Fix `update_reorder_levels` notification
**Source:** ENG CQ5
**File:** `apps/trader_app/trader_app/api/inventory.py`
**Effort:** 1 hour
**Why:** Low stock alerts are written to Frappe error log (`frappe.log_error()`). Nobody reads the error log for inventory alerts — they expect a notification or email.
**Fix:**
```python
# Replace frappe.log_error() with:
frappe.sendmail(
    recipients=[owner_email],
    subject=f"Low Stock Alert: {item_code}",
    message=f"{item_code} has {qty} units remaining (reorder level: {reorder_level})"
)
# Or use frappe.get_doc("Notification") if email isn't configured yet
# At minimum: frappe.publish_realtime("low_stock_alert", {"item": item_code})
# which shows a toast in the browser for any logged-in user
```

---

## Phase 4: Performance

### [P4] P-1: Fix stock aging report unbounded table scan
**Source:** ENG P2
**File:** `apps/trader_app/trader_app/api/reports.py`
**Effort:** 2 hours
**Why:** `get_stock_aging_report()` does a full table scan on `tabStock Ledger Entry` with no date floor in the inner subquery. On a company with 2 years of history this is 500K+ rows scanned per request.
**Fix:**
```python
# Add date floor to inner subquery:
# Change:   WHERE sle.item_code = b.item_code
# To:       WHERE sle.item_code = b.item_code
#             AND sle.posting_date >= DATE_SUB(CURDATE(), INTERVAL 365 DAY)
# Also add: LIMIT 1000 on the outer query with pagination
```

### [P4] P-2: Add summary modes to aha moment report endpoints
**Source:** DES D6
**File:** `apps/trader_app/trader_app/api/reports.py`
**Effort:** 4 hours
**Why:** The aha moment cards (Step 5B) need lightweight summary data — total + top 5 rows. Currently the full reports return all rows paginated. An extra roundtrip to the full reports page after migration loads the full dataset, but the first reveal should be instant.
**Fix:**
```python
@frappe.whitelist()
def get_receivable_aging(company=None, summary=False, **kwargs):
    if summary:
        # Return: total, customer_count, aging_buckets (4 rows only)
        # Use a single SQL query with SUM and CASE — no pagination
        return _get_receivable_aging_summary(company)
    # ... existing full report logic
```

---

## Phase 5: Testing (Ongoing)

### [P5] T-1: Tally parser unit tests
**Source:** ENG (test coverage 0%)
**File:** `apps/trader_app/tests/migration/test_tally_extractor.py`
**Priority:** Build alongside M-4 (Tally extractor)
**Test cases required:**
```
- Parse TallyPrime 3.x fixture file → assert customer/item/invoice counts
- Parse ERP9 fixture file → assert correct version detection
- Parse TallyPrime 4.x fixture file → assert correct version detection
- Ledger missing PARENT tag → assert it appears in payload.warnings, not payload.errors
- Malformed XML → assert MigrationParseError raised with remediation message
- Large file (>5MB) → assert iterparse used, no OOM
- Urdu-script ledger name → assert it passes through without modification
- Item code with special characters → assert sanitized correctly
```

### [P5] T-2: Migration import engine tests
**Source:** ENG
**File:** `apps/trader_app/tests/migration/test_migration_import.py`
**Test cases required:**
```
- execute_migration() creates customers with docstatus=0
- execute_migration() tags all records with migration_job_id
- rollback_migration() deletes all records with matching job_id
- submit_migration() sets docstatus=1 on all records
- duplicate customer name → deduplication logic tested
- item not found during invoice import → record skipped, added to warnings
- DB failure at record 67 of 248 → partial rollback, job marked Failed
```

### [P5] T-3: Mapping engine tests
**Source:** ENG
**File:** `apps/trader_app/tests/migration/test_migration_mapping.py`
**Test cases required:**
```
- "Sundry Debtors" parent → suggests Accounts Receivable (confidence >= 0.85)
- Unknown parent → confidence < 0.5, no suggestion
- Exact name match → confidence == 1.0
- Empty ledger list → returns empty list, no crash
```

### [P5] T-4: Dashboard KPI cache test
**Source:** ENG (dashboard cache no-op fix)
**File:** `apps/trader_app/tests/test_dashboard.py`
**Test cases required:**
```
- First call: executes SQL, writes to cache
- Second call within TTL: reads from cache, no SQL
- Cache expiry: re-executes SQL
- DB error: does not return cached zeros — raises error
```

### [P5] T-5: Report SQL regression tests
**Source:** ENG (reports.py has 30+ endpoints, 0 tests)
**File:** `apps/trader_app/tests/test_reports.py`
**Priority cases (test these first):**
```
- get_receivable_aging(): returns correct aging bucket totals
- get_stock_aging_report(): does not do full table scan (mock, assert LIMIT present)
- get_customer_profitability_report(): returns correct margin calculation
- All 3 aha-moment reports: return in < 2 seconds on test dataset
```

---

## Security Checklist

All items below must be done before the migration wizard ships to any user.

| Item | Status | Notes |
|------|--------|-------|
| `defusedxml` in requirements.txt | [P0] QW-4 | Blocks XXE on Tally XML upload |
| Uploaded files saved to private files only | [P1] M-8 | `upload_migration_file()` must use `frappe.get_site_path("private", "files")` — never `public/files` |
| Job IDs are non-guessable | [P1] M-2 | Use `frappe.generate_hash(length=32)` for Migration Job `name` field — not sequential integers |
| Background job runs as session user | [P1] M-7 | Call `frappe.set_user(session_user)` at start of `execute_migration()` — RQ jobs default to Administrator |
| CSRF on all mutation endpoints | [DONE] | Existing Axios interceptor in `api.ts` already handles this |
| `client_max_body_size 50m` in nginx | [DONE] | Already at `infra/nginx/proxy.conf:35` |

---

## Design System Gap

### [P3] DESIGN-1: Create `DESIGN.md` at project root
**Source:** DES D4
**Effort:** 2 hours
**Why:** No formal design system document exists. Every new feature is designed by reading existing code. This slows development and leads to inconsistencies.
**What to include:**
```markdown
# DESIGN.md
## Color system (tokens)
  Primary: brand-700 (#1d4ed8) — buttons, links, active states
  Success: green-600 (#16a34a)
  Warning: amber-500 (#f59e0b)
  Danger: red-600 (#dc2626)
  Text primary: gray-900 | Text secondary: gray-600 | Text muted: gray-400

## Typography
  Font: Inter (declared in tailwind.config.js, not system-ui default)
  Page title: .page-title (text-xl font-bold gray-900 sm:text-2xl)
  Section heading: text-lg font-semibold gray-900
  Body: text-sm gray-700

## Components (use these — do not reinvent)
  Card: .card (bg-white rounded-xl border-gray-200 shadow-sm)
  Button primary: .btn-primary
  Button secondary: .btn-secondary
  Input: .input-field (44px min-height)
  Spinner: .spinner

## Touch targets
  Minimum 44px on all interactive elements (enforced in index.css)

## Accessibility
  Focus: :focus-visible ring at brand-500
  Motion: prefers-reduced-motion respected
  Contrast: body text minimum 4.5:1 against white background

## Empty states
  Template: Icon (large, gray-300) + heading + subtext + primary CTA
  Never: "No items found." with no context or action
```

---

## Deferred Items (acknowledged, not building in Phase 1)

| Item | Reason deferred |
|------|----------------|
| Email notification for large migration jobs | Requires Frappe email config; handle with "we'll email you" message in UI |
| Multi-company import | Out of scope Phase 1 — one company per migration |
| Import history / re-import flow | Phase 2 — needs "clear all imported data" function first |
| Urdu/Hindi UI translations | Phase 2 |
| Dark mode | Not in existing codebase; not worth adding in Phase 1 |
| Payroll, statutory compliance (GST filings, TDS) | Explicitly out of scope per design doc |
| Historical invoices older than 12 months | Phase 2 |
| Bank reconciliation history | Phase 2 |
| Billing / subscription stack | Build only after first paid customer confirms intent |
| AI-powered insights | Phase 2 per design doc — build core first |
| Animated step transitions in wizard | Phase 2 polish |

---

## Execution Sequence (recommended order)

```
TODAY (30 min):
  QW-1  Remove duplicate inventoryApi method
  QW-2  Delete dead ReportsPage.tsx
  QW-3  Fix broad exception catch in credit limit check
  QW-4  Add defusedxml to requirements.txt

WEEK 1 — MIGRATION BACKEND FOUNDATION:
  M-1   Spike: parse one real Tally XML export (GATE — do not proceed past here until done)
  M-2   Create Migration Job DocType
  M-3   Build MigrationExtractor ABC + NormalizedPayload
  M-4   Build TallyExtractor (implement strategies after M-1 spike findings)
  M-5   Build GenericCSVExtractor + template download
  M-6   Build ledger mapping engine
  M-7   Build import engine (execute / submit / rollback)
  M-8   Build whitelisted API endpoints

WEEK 2 — MIGRATION WIZARD FRONTEND:
  FE-1  WizardProgressBar component
  FE-2  FileDropZone component
  FE-3  MigrationWizardLayout
  FE-4  All 5 wizard step components + useMigrationStore
  FE-5  ConfidenceBadge component
  FE-6  JobProgressBar component
  FE-7  AhaMomentCard component

WEEK 3 — CODE QUALITY + TESTING:
  CQ-1  Fix get_kpis() silent exceptions
  CQ-2  Fix dashboard cache no-op
  CQ-3  Fix hardcoded low stock threshold
  CQ-4  Fix update_reorder_levels notification
  T-1   Tally parser unit tests (build with M-4, not after)
  T-2   Migration import engine tests (build with M-7)
  T-3   Mapping engine tests (build with M-6)

WEEK 4 — PERFORMANCE + POLISH:
  P-1   Fix stock aging unbounded table scan
  P-2   Add summary modes to aha moment endpoints
  T-4   Dashboard KPI cache test
  T-5   Report SQL regression tests
  DESIGN-1  Create DESIGN.md

AFTER FIRST USER MIGRATION:
  Observe: watch one trader complete the wizard without helping
  Validate: "Would you pay ₹3,000/month for this?" (ask directly, not open-ended)
  Record: exact time from upload to aha moment (target: under 30 minutes)
  Adjust: whatever Step 3 (mapping) taught you about real Tally ledger names
```

---

## Next Recommended: `/plan-devex-review`

All three plan-stage reviews are complete:
- `plan-eng-review` — 10 issues identified, critical gaps documented
- `plan-ceo-review` — multi-source migration strategy, adapter pattern, draft approach
- `plan-design-review` — wizard specified screen-by-screen, 2/10 → 8/10

The next recommended skill is **`/plan-devex-review`** — Developer Experience review.

**Why now:** The migration wizard is a new 6-file Python module + 8 new React components + 1 new Frappe DocType. Before building, the DX review will:
1. Measure TTHW (Time To Hello World) for the migration wizard — how long does it take a new developer to run a migration end-to-end in local dev?
2. Identify local development gaps (the Docker setup, hot reload, running background workers)
3. Audit the developer feedback loop — how fast can you test a Tally parser change without redeploying?
4. Check if the demo seed engine (`trader_app.demo.install_demo`) produces data that exercises the migration wizard

**Alternatively**, if the M-1 spike (real Tally XML) is ready, the next technical move is to run the spike and report findings — that unlocks every migration build task. The spike does not need a skill; just run the Python scratch script and document what you find in `apps/trader_app/trader_app/migration/SPIKE.md`.

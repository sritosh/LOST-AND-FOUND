# Campus Lost & Found System — Final Project Report (100% Milestone)

---

## **Project Title:** Campus Lost & Found Asset Recovery & Registry Portal
**Course:** Database Systems (DBMS Lab Project)  
**Milestone:** Final Review (100% Complete Production Portal)  
**Academic Year:** 2026–2027  

### **Team Members:**
1. **Sritosh Rath** — Reg. No: `24BDS0001` (B.Tech Data Science)
2. **Jayant Sharma** — Reg. No: `24BAI0148` (B.Tech Artificial Intelligence)

---

## 1. Executive Summary
The **Campus Lost & Found System** is a complete, enterprise-grade relational database management portal built for academic campuses. It bridges the communication gap between students who lose items and security desks or fellow students who find them.

Transitioning from the initial 50% milestone, the project now incorporates **100% of advanced DBMS features**:
1. **Multi-Role RBAC (Role-Based Access Control):** Dedicated privileges for `Admin`, `Security Officer`, and `Student`.
2. **Automated Similarity Correlation Engine:** Cross-correlates active complaints with custody inventory using weighted matching (Category + Spatial Proximity + Jaccard Keyword Overlap).
3. **Campus Loss Hotspots & Intelligence Analytics:** Real-time spatial incident density, overall recovery efficiency (%), and custody turnaround tracking.
4. **Photo Verification & Custody Evidence:** Image uploads and visual inspection on all lost/found cards.
5. **Printable Official Return Handover Receipt:** Verifiable custody handover certificate with SHA-256 cryptographic verification tokens, dual officer-student signatures, and QR payload.
6. **Live Interactive SQL Query Lab:** Console for live query testing, JOIN demonstrations, VIEW inspection, and schema dictionary exploration.

---

## 2. Complete Database Architecture

### A. Normalized Relational Schema (3NF)
The database schema consists of **7 normalized tables** with primary keys, foreign key constraints (`ON DELETE CASCADE`), and check constraints:

1. `STUDENT` (`student_id` PK, `name`, `email`, `phone`, `department`, `created_at`)
2. `ITEM` (`item_id` PK, `item_name`, `category`, `description`, `location`, `image_url`, `created_at`)
3. `LOST_ITEM` (`lost_id` PK, `student_id` FK, `item_id` FK, `date_lost`, `status`, `created_at`)
4. `FOUND_ITEM` (`found_id` PK, `student_id` FK, `item_id` FK, `date_found`, `storage_location`, `status`, `created_at`)
5. `CLAIM` (`claim_id` PK, `student_id` FK, `item_id` FK, `claim_date`, `claim_status`, `proof_description`, `created_at`)
6. `RETURN_RECORD` (`return_id` PK, `student_id` FK, `item_id` FK, `return_date`, `verified_by`, `remarks`, `created_at`)
7. `USERS` (`user_id` PK, `username` UNIQUE, `password_hash`, `role`, `student_id` FK, `full_name`, `created_at`)

### B. Database Views
- `vw_lost_items_detailed`: Flattened view of lost item reports with student name, department, phone, and image URL.
- `vw_found_items_detailed`: Flattened view of found item inventory with finder profile, custody storage desk, and claim count.
- `vw_claims_overview`: Complete claim details joined with claimant profile and item metadata.
- `vw_returns_detailed`: Audit ledger of verified return settlements.

### C. Triggers & Stored Procedures
- `trg_after_return_update_lost_status`: Automatically flips `LOST_ITEM.status` to `'Returned'` upon insertion into `RETURN_RECORD`.
- `trg_after_return_update_found_status`: Automatically flips `FOUND_ITEM.status` to `'Returned'` upon insertion into `RETURN_RECORD`.
- `sp_report_lost_item`: Atomic stored procedure inserting into `ITEM` and `LOST_ITEM` in a single transaction.
- `sp_report_found_item`: Atomic stored procedure inserting into `ITEM` and `FOUND_ITEM` in a single transaction.
- `sp_process_return`: Stored procedure recording return settlement and synchronizing claim decisions.

---

## 3. Advanced Features Breakdown (100% Completion)

### 1. Smart Automated Similarity Matching Engine
Cross-correlates pending lost item complaints against active found custody items using a multi-factor mathematical scoring formula:
$$\text{Score} = \text{Score}_{\text{category}} (40\%) + \text{Score}_{\text{location}} (25\%) + \text{Score}_{\text{tokens}} (35\%)$$
- **Exact Category Match:** $+40\%$
- **Spatial / Building Proximity:** $+25\%$ (e.g. both lost & found in *Block A Auditorium Lobby*)
- **Jaccard Token & Keyword Overlap:** Up to $+35\%$ after stop-word removal.
- **One-Click Claim Filing:** Clicking *"Match & File Claim"* automatically pre-fills the claim modal with matching credentials.

### 2. Campus Analytics & Spatial Loss Hotspots
- **Recovery Rate Meter (%):** Ratio of settled returns against total catalog entries.
- **Custody-to-Claim Turnaround:** Average elapsed days between item loss and verified return handover.
- **Campus Loss Hotspots:** Spatial ranking of campus buildings with the highest incident density and visual bar indicators.
- **Category Recovery Breakdown Table:** Itemized lost, found, returned, and recovery percentage by category.

### 3. Role-Based Access Control (RBAC)
- **Security Officer (`security`):** Authorized to review and approve/reject claims, verify student identification, and execute return handovers.
- **System Administrator (`admin`):** Full system privileges including database schema reset, raw SQL lab execution, and student management.
- **Student Profile (`sritosh` / `jayant`):** Can report lost items, report found items, submit ownership claims, and view verified handover receipts. Administrative actions (approving claims, authorizing returns) are automatically locked.

### 4. Photographic Evidence & Visual Verification
- Supports both **Direct Image File Upload** (`/api/upload`) and **External Image URLs**.
- Quick Preset Selectors (Headphones, Water Bottle, ID Card, Backpack, Umbrella, Laptop, Keys) for instant lab evaluations.
- Real-time image preview in submission modals and crisp thumbnails on inventory cards.

### 5. Official Return Handover Receipt Certificate
- Generated upon return settlement (`/api/returns/<id>/receipt`).
- Generates a deterministic SHA-256 cryptographic verification token (`RET-VIT-xxxx`).
- Contains university registry title, student registration profile, item specs, officer verification notes, dual signature blocks, and QR verification payload.
- Integrated `@media print` CSS engine: clicking *"Print Handover Slip"* prints an official paper certificate with clean white styling.

---

## 4. How to Run & Demonstrate the Project

### Quick Start:
Double-click `run_app.bat` or run in terminal:
```powershell
python run_app.py
```
The server will start on `http://127.0.0.1:5000` and automatically open your default web browser.

### Key Demonstration Steps for Faculty:
1. **Show Navbar & RBAC:** Show the Role selector dropdown in the top right. Switch between `Security Officer` and `Student: Sritosh Rath`.
2. **Show Lost & Found Catalogs:** Point out the photo thumbnails, category filters, and live search box.
3. **Show Smart Auto-Match:** Navigate to the *"Smart Auto-Match"* tab. Point out the **98% High Confidence match** between *Boat Rockerz Headphones* and *Boat Rockerz 450 Headphones*, and explain the weighted scoring formula.
4. **Show Campus Analytics:** Navigate to *"Campus Analytics"*. Highlight the Recovery Rate (16.7%), Average Resolution Time (2.0 days), and Top Campus Loss Hotspots list with progress bars.
5. **Show Official Return Receipt:** Go to *"Claims & Returns"*, scroll to *Final Return Settlement Records*, and click *"Official Slip"* on Return `#RET-1`. Show the university handover certificate and click *"Print Handover Slip"*.
6. **Show SQL Query Lab:** Go to *"SQL Query Lab"*, pick any preset query (e.g. Q2: Multi-Table JOIN, Q6: GROUP BY Category, or Q9: View query), and click *"Run Query (Execute SQL)"* to demonstrate live database execution time in milliseconds.

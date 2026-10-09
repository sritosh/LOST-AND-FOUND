# Campus Lost & Found System — DBMS Lab Project

### **50% Milestone Review Submission**
**Team Members:**
- **Sritosh Rath** (`24BDS0001`) — B.Tech Data Science
- **Jayant Sharma** (`24BAI0148`) — B.Tech Artificial Intelligence

---

## 📌 Project Overview
The **Campus Lost & Found System** is a full-stack database management application created for the Database Systems Lab. It solves the problem of misplacing items across a large university campus by providing a normalized relational database backend, automated claim and handover workflows, real-time search & filter catalogs, and an interactive live SQL Query Lab for laboratory demonstrations.

---

## 🗂️ Project Structure

```text
dbms_project/
├── backend/
│   ├── app.py                      # Flask REST API server (Endpoints for CRUD, Search, Claims, Returns, SQL Lab)
│   └── db.py                       # Database connection, query runner, and SQLite/MySQL connector
├── database/
│   ├── schema.sql                  # DDL Script: 6 Tables, Primary/Foreign Keys, Constraints, Views, Indexes
│   ├── sample_data.sql             # DML Script: Realistic seed data for students, items, claims, returns
│   ├── queries.sql                 # Comprehensive SQL queries (Joins, Aggregations, Subqueries, Views)
│   ├── procedures_triggers.sql     # Stored Procedures and Triggers (MySQL)
│   └── campus_lost_found.db        # Pre-initialized SQLite database (auto-created on run)
├── frontend/
│   ├── index.html                  # Single Page Application UI with Dashboard, Catalogs, Claims, SQL Lab
│   ├── styles.css                  # Modern UI Design System (Dark mode, glassmorphism, responsive grid)
│   └── app.js                      # Client-side interactivity, API integration, live search, SQL executor
├── docs/
│   ├── REVIEW_1_SUBMISSION_REPORT.md # Academic Review 1 Report (3NF Normalization, ERD, Schema, Scope)
│   └── VIVA_QUESTIONS_AND_ANSWERS.md  # Comprehensive Viva Preparation & Technical Q&A Cheat Sheet
├── run_app.py                      # Python application launcher (starts server & opens browser)
├── run_app.bat                     # Windows one-click batch launcher
└── README.md                       # Project guide & documentation
```

---

## 🚀 How to Run the Project

### **Step 1: Open Terminal in Project Directory**
```bash
cd "c:\Users\Sritosh Rath\Desktop\dbms_project"
```

### **Step 2: Run the Application**
```bash
python run_app.py
```
*Or simply double-click `run_app.bat` on Windows.*

The web application will launch immediately at **`http://127.0.0.1:5000`** in your browser!

---

## 🎯 50% Milestone (Review 1) Features Implemented

1. **Complete Database Architecture & Schema (DDL):**
   - 6 Relational Tables: `STUDENT`, `ITEM`, `LOST_ITEM`, `FOUND_ITEM`, `CLAIM`, `RETURN_RECORD`.
   - Primary Keys, Foreign Keys with cascading (`ON DELETE CASCADE` / `ON DELETE RESTRICT`), Check Constraints (`status`, `claim_status`), and unique constraints on student emails.
   - Pre-configured Database Views (`vw_lost_items_detailed`, `vw_found_items_detailed`, `vw_claims_overview`, `vw_returns_detailed`).

2. **Full Normalization (3NF Compliant):**
   - **1NF:** Single-valued atomic attributes with no repeating groups.
   - **2NF:** Single-attribute surrogate primary keys preventing partial functional dependencies.
   - **3NF:** No transitive dependencies between non-prime attributes; relational joins used for cross-table retrieval.

3. **Sample Campus Dataset (DML):**
   - Seeded with students across departments (Data Science, AI, CSE, ECE, Mech), lost articles, found articles, claims, and return receipts.

4. **Interactive Single Page Web Application:**
   - **Dashboard:** Real-time KPI counters, category distribution breakdown, recent campus activity stream.
   - **Lost Items Catalog:** Multi-condition search by keyword, category, status, and reporting student.
   - **Found Items Catalog:** Live inventory, physical security custody desks, and one-click "Claim This Item" modal.
   - **Claims & Returns Workflow:** Student ownership claims evaluation (`Approve` / `Reject`) and item handover logging in `RETURN_RECORD`.
   - **Student Directory:** Student registration, profile lookup, and historical activity ledger.
   - **Interactive SQL Query Lab:** Run arbitrary or pre-set SQL queries (joins, group by, subqueries) with live execution times and tabular results directly in the browser!
   - **Review 1 Report & ERD Tab:** In-app visualizer of the ER Diagram, Relational schema, 3NF analysis, and Viva questions.

---

## 🔮 Planned 100% Scope (Review 2 Roadmap)
- Physical image upload and CDN/file storage for lost/found items.
- Intelligent keyword & similarity matching algorithm between lost and found items.
- Automated email notification triggers via SMTP.
- Role-based student and administrator authentication.
- Printable PDF return receipt generation.

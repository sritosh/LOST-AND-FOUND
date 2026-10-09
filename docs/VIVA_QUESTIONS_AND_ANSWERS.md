# Campus Lost & Found System — Review 1 Viva Cheat Sheet & Technical Q&A

**Prepared for:** Sritosh Rath (`24BDS0001`) & Jayant Sharma (`24BAI0148`)  
**Course:** Database Systems Lab (50% Milestone Review)

---

### **Q1: What is the main objective of this project?**
**Answer:**  
The objective is to provide a centralized, relational database system for managing lost and found articles inside the university campus. It enables students to report lost/found items, search active inventories, file ownership claims with proof descriptions, and record verified returns with full auditability.

---

### **Q2: Explain your database schema and the entities involved.**
**Answer:**  
Our database consists of **6 relations** designed in **3rd Normal Form (3NF)**:
1. `STUDENT`: Master table storing student details (Registration number, Name, Email, Phone, Department).
2. `ITEM`: Master catalog of reported items (Item name, Category, Description, Campus location).
3. `LOST_ITEM`: Transaction table recording when a student reports their lost item.
4. `FOUND_ITEM`: Transaction table recording when a finder turns in a discovered item along with physical custody storage.
5. `CLAIM`: Stores ownership claims submitted by students with proof descriptions and status (`Pending`, `Approved`, `Rejected`, `Returned`).
6. `RETURN_RECORD`: Stores final handover records once an item is verified and returned to its owner.

---

### **Q3: Why did you separate `ITEM` from `LOST_ITEM` and `FOUND_ITEM`?**
**Answer:**  
To prevent data redundancy and adhere to 3NF. The physical item entity (`ITEM`) holds attributes intrinsic to the item itself (name, category, description, location), while `LOST_ITEM` and `FOUND_ITEM` hold transactional metadata (the specific student involved, the event date, and the item's current lifecycle status).

---

### **Q4: How did you ensure 1NF, 2NF, and 3NF in your schema?**
**Answer:**  
- **1NF (Atomicity):** All attributes contain atomic values (single values). Multiple claims or items are stored in separate rows in relational tables rather than repeating fields or arrays.
- **2NF (No Partial Dependency):** Every table uses a single-attribute primary key (`student_id`, `item_id`, `lost_id`, `found_id`, `claim_id`, `return_id`). Because all candidate keys consist of single attributes, partial dependencies on a composite key are impossible.
- **3NF (No Transitive Dependency):** Non-prime attributes depend solely on candidate keys ($X \rightarrow Y$ where $X$ is a superkey). Student details (e.g., student name or phone) are not repeated in `LOST_ITEM` or `CLAIM`; only the foreign key `student_id` is stored.

---

### **Q5: What Foreign Key Cascading options did you use and why?**
**Answer:**  
- We used `ON DELETE CASCADE` and `ON UPDATE CASCADE` on operational relations like `LOST_ITEM`, `FOUND_ITEM`, and `CLAIM` so that if a student or item record is updated or deleted, child records stay consistent.
- We applied `ON DELETE RESTRICT` on `RETURN_RECORD` to guarantee that settled legal return logs cannot be accidentally deleted if an associated student profile is removed.

---

### **Q6: How does the claim approval and return process work at the database level?**
**Answer:**  
When an administrator approves a student's claim:
1. The status in `CLAIM` is updated to `'Approved'`.
2. The associated item's status in `FOUND_ITEM` is updated to `'Claimed'`.
3. All other pending claims for that same item are automatically updated to `'Rejected'` to prevent duplicate approvals.
4. Once physically handed over, a new tuple is inserted into `RETURN_RECORD`, and the status in `FOUND_ITEM`, `LOST_ITEM`, and `CLAIM` is updated to `'Returned'`.

---

### **Q7: What database views did you create?**
**Answer:**  
We created 4 dedicated database views:
1. `vw_lost_items_detailed`: Pre-joins `LOST_ITEM`, `ITEM`, and `STUDENT`.
2. `vw_found_items_detailed`: Pre-joins `FOUND_ITEM`, `ITEM`, and `STUDENT` (finder).
3. `vw_claims_overview`: Pre-joins `CLAIM`, `ITEM`, and `STUDENT` (claimant).
4. `vw_returns_detailed`: Pre-joins `RETURN_RECORD`, `ITEM`, and `STUDENT` (receiver).

---

### **Q8: What indexes did you build and why?**
**Answer:**  
We created B-Tree indexes on frequently queried columns:
- `idx_student_email` on `STUDENT(email)` for instantaneous unique student lookups.
- `idx_item_category` and `idx_item_location` on `ITEM` to speed up category filtering and campus zone searches.
- `idx_lost_status` and `idx_found_status` to optimize real-time status filtering (e.g. `WHERE status = 'Pending'`).

---

### **Q9: What have you completed for 50% Review vs what is planned for 100% Review?**
**Answer:**  
- **Completed (Review 1 - 50%):** Complete 3NF relational schema, DDL/DML scripts, full CRUD REST API, real-time search & filter catalog, claims & return settlement workflow, interactive SQL query runner, and live database schema inspector.
- **Planned (Review 2 - 100%):** Image uploads for lost/found items, automated keyword/fuzzy matching algorithm between lost and found articles, automated email notifications to students, and role-based authentication.

"""
Campus Lost & Found System - REST API Server
Built with Flask & SQLite for DBMS Project Lab (50% Milestone Review)
Authors: Sritosh Rath (24BDS0001), Jayant Sharma (24BAI0148)
"""

import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

try:
    from db import init_db, query_all, query_one, execute_write, execute_raw_user_query
except ImportError:
    from backend.db import init_db, query_all, query_one, execute_write, execute_raw_user_query

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

app = Flask(__name__, static_folder=FRONTEND_DIR)
CORS(app)

# Ensure database is initialized on startup
init_db()


# -----------------------------------------------------------------------------
# STATIC FILE SERVING
# -----------------------------------------------------------------------------
@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, 'index.html')


# -----------------------------------------------------------------------------
# 1. DASHBOARD & STATS API
# -----------------------------------------------------------------------------
@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Returns aggregated KPIs for the executive dashboard."""
    lost_counts = query_all("SELECT status, COUNT(*) as count FROM LOST_ITEM GROUP BY status")
    found_counts = query_all("SELECT status, COUNT(*) as count FROM FOUND_ITEM GROUP BY status")
    claim_counts = query_all("SELECT claim_status, COUNT(*) as count FROM CLAIM GROUP BY claim_status")
    
    total_students = query_one("SELECT COUNT(*) as count FROM STUDENT")['count']
    total_items = query_one("SELECT COUNT(*) as count FROM ITEM")['count']
    total_returns = query_one("SELECT COUNT(*) as count FROM RETURN_RECORD")['count']
    
    # Category distribution
    categories = query_all("SELECT category, COUNT(*) as count FROM ITEM GROUP BY category ORDER BY count DESC")
    
    # Recent activity stream
    recent_lost = query_all("""
        SELECT l.lost_id as id, 'lost' as type, i.item_name, s.name as student_name, l.date_lost as date, l.status
        FROM LOST_ITEM l
        JOIN ITEM i ON l.item_id = i.item_id
        JOIN STUDENT s ON l.student_id = s.student_id
        ORDER BY l.reported_at DESC LIMIT 4
    """)
    recent_found = query_all("""
        SELECT f.found_id as id, 'found' as type, i.item_name, s.name as student_name, f.date_found as date, f.status
        FROM FOUND_ITEM f
        JOIN ITEM i ON f.item_id = i.item_id
        JOIN STUDENT s ON f.student_id = s.student_id
        ORDER BY f.reported_at DESC LIMIT 4
    """)

    return jsonify({
        "total_students": total_students,
        "total_items": total_items,
        "total_returns": total_returns,
        "lost_breakdown": {row['status']: row['count'] for row in lost_counts},
        "found_breakdown": {row['status']: row['count'] for row in found_counts},
        "claims_breakdown": {row['claim_status']: row['count'] for row in claim_counts},
        "categories": categories,
        "recent_activities": sorted(recent_lost + recent_found, key=lambda x: str(x['date']), reverse=True)[:6]
    })


# -----------------------------------------------------------------------------
# 2. STUDENTS API
# -----------------------------------------------------------------------------
@app.route('/api/students', methods=['GET'])
def get_students():
    """Retrieves all registered students with aggregate report counts."""
    students = query_all("""
        SELECT s.student_id, s.name, s.email, s.phone, s.department, s.created_at,
               (SELECT COUNT(*) FROM LOST_ITEM WHERE student_id = s.student_id) as lost_count,
               (SELECT COUNT(*) FROM FOUND_ITEM WHERE student_id = s.student_id) as found_count,
               (SELECT COUNT(*) FROM CLAIM WHERE student_id = s.student_id) as claim_count
        FROM STUDENT s
        ORDER BY s.name ASC
    """)
    return jsonify(students)


@app.route('/api/students', methods=['POST'])
def add_student():
    """Registers a new student into the system."""
    data = request.json or {}
    student_id = data.get('student_id', '').strip()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    department = data.get('department', '').strip()

    if not all([student_id, name, email, phone, department]):
        return jsonify({"error": "All fields (student_id, name, email, phone, department) are required."}), 400

    try:
        execute_write(
            "INSERT INTO STUDENT (student_id, name, email, phone, department) VALUES (?, ?, ?, ?, ?)",
            (student_id, name, email, phone, department)
        )
        return jsonify({"message": f"Student '{name}' registered successfully.", "student_id": student_id}), 201
    except Exception as e:
        return jsonify({"error": f"Database Error: {str(e)}"}), 400


@app.route('/api/students/<student_id>', methods=['GET'])
def get_student_detail(student_id):
    """Retrieves single student profile with full history of lost/found items & claims."""
    student = query_one("SELECT * FROM STUDENT WHERE student_id = ?", (student_id,))
    if not student:
        return jsonify({"error": "Student not found"}), 404

    lost_items = query_all("""
        SELECT l.lost_id, l.date_lost, l.status, i.item_id, i.item_name, i.category, i.location
        FROM LOST_ITEM l
        JOIN ITEM i ON l.item_id = i.item_id
        WHERE l.student_id = ?
    """, (student_id,))

    found_items = query_all("""
        SELECT f.found_id, f.date_found, f.status, f.storage_location, i.item_id, i.item_name, i.category, i.location
        FROM FOUND_ITEM f
        JOIN ITEM i ON f.item_id = i.item_id
        WHERE f.student_id = ?
    """, (student_id,))

    claims = query_all("""
        SELECT c.claim_id, c.claim_date, c.claim_status, c.proof_description, i.item_name, i.category
        FROM CLAIM c
        JOIN ITEM i ON c.item_id = i.item_id
        WHERE c.student_id = ?
    """, (student_id,))

    return jsonify({
        "student": student,
        "lost_items": lost_items,
        "found_items": found_items,
        "claims": claims
    })


# -----------------------------------------------------------------------------
# 3. LOST ITEMS API
# -----------------------------------------------------------------------------
@app.route('/api/lost-items', methods=['GET'])
def get_lost_items():
    """Fetches lost items with optional keyword, category, status filters."""
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()
    status = request.args.get('status', '').strip()

    query = """
        SELECT l.lost_id, l.date_lost, l.status, l.reported_at,
               i.item_id, i.item_name, i.category, i.description, i.location,
               s.student_id, s.name as student_name, s.email as student_email, s.phone as student_phone, s.department
        FROM LOST_ITEM l
        JOIN ITEM i ON l.item_id = i.item_id
        JOIN STUDENT s ON l.student_id = s.student_id
        WHERE 1=1
    """
    params = []

    if search:
        query += " AND (i.item_name LIKE ? OR i.description LIKE ? OR i.location LIKE ? OR s.name LIKE ?)"
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    if category and category != 'All':
        query += " AND i.category = ?"
        params.append(category)

    if status and status != 'All':
        query += " AND l.status = ?"
        params.append(status)

    query += " ORDER BY l.date_lost DESC, l.lost_id DESC"
    results = query_all(query, params)
    return jsonify(results)


@app.route('/api/lost-items', methods=['POST'])
def report_lost_item():
    """Atomically reports a new lost item by inserting into ITEM and LOST_ITEM."""
    data = request.json or {}
    student_id = data.get('student_id', '').strip()
    item_name = data.get('item_name', '').strip()
    category = data.get('category', '').strip()
    description = data.get('description', '').strip()
    location = data.get('location', '').strip()
    date_lost = data.get('date_lost', '').strip()

    if not all([student_id, item_name, category, location, date_lost]):
        return jsonify({"error": "Missing required fields (student_id, item_name, category, location, date_lost)"}), 400

    # Verify student exists
    student = query_one("SELECT student_id FROM STUDENT WHERE student_id = ?", (student_id,))
    if not student:
        return jsonify({"error": f"Student with ID '{student_id}' does not exist. Please register student first."}), 404

    try:
        # 1. Insert into ITEM
        item_id, _ = execute_write(
            "INSERT INTO ITEM (item_name, category, description, location) VALUES (?, ?, ?, ?)",
            (item_name, category, description, location)
        )

        # 2. Insert into LOST_ITEM
        lost_id, _ = execute_write(
            "INSERT INTO LOST_ITEM (student_id, item_id, date_lost, status) VALUES (?, ?, ?, 'Pending')",
            (student_id, item_id, date_lost)
        )

        return jsonify({
            "message": "Lost item reported successfully!",
            "item_id": item_id,
            "lost_id": lost_id
        }), 201
    except Exception as e:
        return jsonify({"error": f"Database Error: {str(e)}"}), 500


# -----------------------------------------------------------------------------
# 4. FOUND ITEMS API
# -----------------------------------------------------------------------------
@app.route('/api/found-items', methods=['GET'])
def get_found_items():
    """Fetches found items with search, category, and status filters."""
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()
    status = request.args.get('status', '').strip()

    query = """
        SELECT f.found_id, f.date_found, f.status, f.storage_location, f.reported_at,
               i.item_id, i.item_name, i.category, i.description, i.location,
               s.student_id as finder_id, s.name as finder_name, s.email as finder_email, s.phone as finder_phone, s.department as finder_dept,
               (SELECT COUNT(*) FROM CLAIM WHERE item_id = i.item_id) as claim_count
        FROM FOUND_ITEM f
        JOIN ITEM i ON f.item_id = i.item_id
        JOIN STUDENT s ON f.student_id = s.student_id
        WHERE 1=1
    """
    params = []

    if search:
        query += " AND (i.item_name LIKE ? OR i.description LIKE ? OR i.location LIKE ? OR s.name LIKE ?)"
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    if category and category != 'All':
        query += " AND i.category = ?"
        params.append(category)

    if status and status != 'All':
        query += " AND f.status = ?"
        params.append(status)

    query += " ORDER BY f.date_found DESC, f.found_id DESC"
    results = query_all(query, params)
    return jsonify(results)


@app.route('/api/found-items', methods=['POST'])
def report_found_item():
    """Atomically reports a discovered item by inserting into ITEM and FOUND_ITEM."""
    data = request.json or {}
    student_id = data.get('student_id', '').strip()
    item_name = data.get('item_name', '').strip()
    category = data.get('category', '').strip()
    description = data.get('description', '').strip()
    location = data.get('location', '').strip()
    date_found = data.get('date_found', '').strip()
    storage_location = data.get('storage_location', 'Campus Security / Lost & Found Desk').strip()

    if not all([student_id, item_name, category, location, date_found]):
        return jsonify({"error": "Missing required fields (student_id, item_name, category, location, date_found)"}), 400

    student = query_one("SELECT student_id FROM STUDENT WHERE student_id = ?", (student_id,))
    if not student:
        return jsonify({"error": f"Finder Student with ID '{student_id}' does not exist. Please register first."}), 404

    try:
        item_id, _ = execute_write(
            "INSERT INTO ITEM (item_name, category, description, location) VALUES (?, ?, ?, ?)",
            (item_name, category, description, location)
        )

        found_id, _ = execute_write(
            "INSERT INTO FOUND_ITEM (student_id, item_id, date_found, status, storage_location) VALUES (?, ?, ?, 'Pending', ?)",
            (student_id, item_id, date_found, storage_location)
        )

        return jsonify({
            "message": "Found item reported successfully!",
            "item_id": item_id,
            "found_id": found_id
        }), 201
    except Exception as e:
        return jsonify({"error": f"Database Error: {str(e)}"}), 500


# -----------------------------------------------------------------------------
# 5. CLAIMS API
# -----------------------------------------------------------------------------
@app.route('/api/claims', methods=['GET'])
def get_claims():
    """Retrieves all ownership claims with claimant and item details."""
    claims = query_all("""
        SELECT c.claim_id, c.claim_date, c.claim_status, c.proof_description, c.created_at,
               i.item_id, i.item_name, i.category, i.location, i.description as item_desc,
               s.student_id as claimant_id, s.name as claimant_name, s.email as claimant_email, s.phone as claimant_phone, s.department as claimant_dept
        FROM CLAIM c
        JOIN ITEM i ON c.item_id = i.item_id
        JOIN STUDENT s ON c.student_id = s.student_id
        ORDER BY c.claim_date DESC, c.claim_id DESC
    """)
    return jsonify(claims)


@app.route('/api/claims', methods=['POST'])
def submit_claim():
    """Submits an ownership claim on a found item."""
    data = request.json or {}
    student_id = data.get('student_id', '').strip()
    item_id = data.get('item_id')
    claim_date = data.get('claim_date', '').strip()
    proof_description = data.get('proof_description', '').strip()

    if not all([student_id, item_id, claim_date, proof_description]):
        return jsonify({"error": "student_id, item_id, claim_date, and proof_description are required."}), 400

    student = query_one("SELECT student_id FROM STUDENT WHERE student_id = ?", (student_id,))
    if not student:
        return jsonify({"error": f"Student with ID '{student_id}' is not registered."}), 404

    item = query_one("SELECT item_id FROM ITEM WHERE item_id = ?", (item_id,))
    if not item:
        return jsonify({"error": f"Item with ID '{item_id}' not found."}), 404

    try:
        claim_id, _ = execute_write(
            "INSERT INTO CLAIM (student_id, item_id, claim_date, claim_status, proof_description) VALUES (?, ?, ?, 'Pending', ?)",
            (student_id, item_id, claim_date, proof_description)
        )
        return jsonify({"message": "Claim submitted successfully!", "claim_id": claim_id}), 201
    except Exception as e:
        return jsonify({"error": f"Database Error: {str(e)}"}), 500


@app.route('/api/claims/<int:claim_id>/status', methods=['PUT'])
def update_claim_status(claim_id):
    """Updates claim status (Approved / Rejected / Returned) and syncs found item status."""
    data = request.json or {}
    new_status = data.get('status')
    if new_status not in ['Pending', 'Approved', 'Rejected', 'Returned']:
        return jsonify({"error": "Invalid status. Must be Pending, Approved, Rejected, or Returned"}), 400

    claim = query_one("SELECT * FROM CLAIM WHERE claim_id = ?", (claim_id,))
    if not claim:
        return jsonify({"error": "Claim not found"}), 404

    item_id = claim['item_id']

    try:
        execute_write("UPDATE CLAIM SET claim_status = ? WHERE claim_id = ?", (new_status, claim_id))

        if new_status == 'Approved':
            # Update Found Item status to 'Claimed'
            execute_write("UPDATE FOUND_ITEM SET status = 'Claimed' WHERE item_id = ?", (item_id,))
            # Automatically reject other pending claims for this same item
            execute_write("UPDATE CLAIM SET claim_status = 'Rejected' WHERE item_id = ? AND claim_id != ? AND claim_status = 'Pending'", (item_id, claim_id))
        elif new_status == 'Rejected':
            # Check if there are other approved claims; if none, revert to Pending
            approved_count = query_one("SELECT COUNT(*) as c FROM CLAIM WHERE item_id = ? AND claim_status = 'Approved'", (item_id,))['c']
            if approved_count == 0:
                execute_write("UPDATE FOUND_ITEM SET status = 'Pending' WHERE item_id = ?", (item_id,))

        return jsonify({"message": f"Claim status updated to '{new_status}' successfully."})
    except Exception as e:
        return jsonify({"error": f"Database Error: {str(e)}"}), 500


# -----------------------------------------------------------------------------
# 6. RETURNS API
# -----------------------------------------------------------------------------
@app.route('/api/returns', methods=['GET'])
def get_returns():
    """Fetches all item return settlement records."""
    returns = query_all("""
        SELECT r.return_id, r.return_date, r.verified_by, r.remarks, r.created_at,
               i.item_id, i.item_name, i.category,
               s.student_id, s.name as student_name, s.department, s.phone, s.email
        FROM RETURN_RECORD r
        JOIN ITEM i ON r.item_id = i.item_id
        JOIN STUDENT s ON r.student_id = s.student_id
        ORDER BY r.return_date DESC, r.return_id DESC
    """)
    return jsonify(returns)


@app.route('/api/returns', methods=['POST'])
def record_return():
    """Records the final handover and return of an item to its verified owner."""
    data = request.json or {}
    student_id = data.get('student_id', '').strip()
    item_id = data.get('item_id')
    return_date = data.get('return_date', '').strip()
    verified_by = data.get('verified_by', 'Campus Security Officer').strip()
    remarks = data.get('remarks', 'Verified ownership and handed over.').strip()

    if not all([student_id, item_id, return_date]):
        return jsonify({"error": "student_id, item_id, and return_date are required."}), 400

    # Verify duplicate return
    existing = query_one("SELECT return_id FROM RETURN_RECORD WHERE item_id = ?", (item_id,))
    if existing:
        return jsonify({"error": "This item has already been marked as returned."}), 400

    try:
        return_id, _ = execute_write(
            "INSERT INTO RETURN_RECORD (student_id, item_id, return_date, verified_by, remarks) VALUES (?, ?, ?, ?, ?)",
            (student_id, item_id, return_date, verified_by, remarks)
        )

        # Update statuses across all related tables
        execute_write("UPDATE FOUND_ITEM SET status = 'Returned' WHERE item_id = ?", (item_id,))
        execute_write("UPDATE LOST_ITEM SET status = 'Returned' WHERE item_id = ?", (item_id,))
        execute_write("UPDATE CLAIM SET claim_status = 'Returned' WHERE item_id = ? AND claim_status = 'Approved'", (item_id,))

        return jsonify({"message": "Return record logged successfully!", "return_id": return_id}), 201
    except Exception as e:
        return jsonify({"error": f"Database Error: {str(e)}"}), 500


# -----------------------------------------------------------------------------
# 7. SQL QUERY LAB & LIVE DEMO API
# -----------------------------------------------------------------------------
@app.route('/api/query', methods=['POST'])
def run_sql_query():
    """Executes arbitrary SQL queries from the UI console for live faculty demo."""
    data = request.json or {}
    query_text = data.get('query', '').strip()
    if not query_text:
        return jsonify({"error": "Query cannot be empty"}), 400

    result = execute_raw_user_query(query_text)
    return jsonify(result)


@app.route('/api/schema', methods=['GET'])
def get_schema():
    """Returns database tables, column structures, and record counts."""
    tables_list = ['STUDENT', 'ITEM', 'LOST_ITEM', 'FOUND_ITEM', 'CLAIM', 'RETURN_RECORD']
    schema_info = []

    for tbl in tables_list:
        try:
            columns = query_all(f"PRAGMA table_info({tbl})")
            count_info = query_one(f"SELECT COUNT(*) as count FROM {tbl}")
            row_count = count_info['count'] if count_info else 0
            
            # Foreign keys
            fks = query_all(f"PRAGMA foreign_key_list({tbl})")
            
            schema_info.append({
                "table_name": tbl,
                "row_count": row_count,
                "columns": columns,
                "foreign_keys": fks
            })
        except Exception as e:
            schema_info.append({"table_name": tbl, "error": str(e)})

    return jsonify(schema_info)


@app.route('/api/reset-demo', methods=['POST'])
def reset_database():
    """Resets the database back to standard clean Review 1 sample state."""
    init_db(force_reinit=True)
    return jsonify({"message": "Database reset to initial sample data successfully!"})


# -----------------------------------------------------------------------------
# MAIN ENTRYPOINT
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n=======================================================")
    print(f" CAMPUS LOST & FOUND SYSTEM - DBMS PROJECT BACKEND")
    print(f" Team: Sritosh Rath (24BDS0001), Jayant Sharma (24BAI0148)")
    print(f" Review 1 (50% Milestone) Server running on http://127.0.0.1:{port}")
    print(f"=======================================================\n")
    app.run(host='127.0.0.1', port=port, debug=True)

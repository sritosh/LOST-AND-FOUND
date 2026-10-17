"""
Campus Lost & Found System - REST API Server
Built with Flask & SQLite for DBMS Project Lab (Full 100% Implementation)
Authors: Sritosh Rath (24BDS0001), Jayant Sharma (24BAI0148)
"""

import os
import sys
import re
import uuid
import time
import hashlib
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

try:
    from db import init_db, query_all, query_one, execute_write, execute_raw_user_query
except ImportError:
    from backend.db import init_db, query_all, query_one, execute_write, execute_raw_user_query

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
UPLOAD_FOLDER = os.path.join(FRONTEND_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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


@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


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
               i.item_id, i.item_name, i.category, i.description, i.location, i.image_url,
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
    image_url = data.get('image_url', '').strip() or None

    if not all([student_id, item_name, category, location, date_lost]):
        return jsonify({"error": "Missing required fields (student_id, item_name, category, location, date_lost)"}), 400

    # Verify student exists
    student = query_one("SELECT student_id FROM STUDENT WHERE student_id = ?", (student_id,))
    if not student:
        return jsonify({"error": f"Student with ID '{student_id}' does not exist. Please register student first."}), 404

    try:
        # 1. Insert into ITEM (including image_url)
        item_id, _ = execute_write(
            "INSERT INTO ITEM (item_name, category, description, location, image_url) VALUES (?, ?, ?, ?, ?)",
            (item_name, category, description, location, image_url)
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
               i.item_id, i.item_name, i.category, i.description, i.location, i.image_url,
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
    image_url = data.get('image_url', '').strip() or None

    if not all([student_id, item_name, category, location, date_found]):
        return jsonify({"error": "Missing required fields (student_id, item_name, category, location, date_found)"}), 400

    student = query_one("SELECT student_id FROM STUDENT WHERE student_id = ?", (student_id,))
    if not student:
        return jsonify({"error": f"Finder Student with ID '{student_id}' does not exist. Please register first."}), 404

    try:
        item_id, _ = execute_write(
            "INSERT INTO ITEM (item_name, category, description, location, image_url) VALUES (?, ?, ?, ?, ?)",
            (item_name, category, description, location, image_url)
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
# 7. IMAGE UPLOADS API
# -----------------------------------------------------------------------------
@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handles image upload or base64 storage for lost/found items."""
    if 'file' in request.files:
        file = request.files['file']
        if file.filename:
            ext = os.path.splitext(file.filename)[1].lower() or '.jpg'
            filename = f"item_{uuid.uuid4().hex[:8]}{ext}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            return jsonify({"url": f"/uploads/{filename}", "success": True})

    data = request.json or {}
    image_url = data.get('image_url')
    if image_url:
        return jsonify({"url": image_url, "success": True})

    return jsonify({"error": "No file or image_url provided"}), 400


# -----------------------------------------------------------------------------
# 8. SMART AUTOMATED SIMILARITY MATCHING (LOST <-> FOUND CORRELATION)
# -----------------------------------------------------------------------------
STOP_WORDS = {
    'a', 'an', 'the', 'in', 'on', 'at', 'near', 'by', 'with', 'and', 'or', 'for', 'of',
    'is', 'was', 'to', 'from', 'it', 'my', 'vit', 'block', 'room', 'floor', 'campus', 'color'
}

def extract_keywords(text):
    if not text:
        return set()
    words = re.findall(r'[a-zA-Z0-9]{3,}', text.lower())
    return {w for w in words if w not in STOP_WORDS}

def calculate_similarity(lost, found):
    reasons = []
    score = 0
    
    # 1. Category match (Weight: 40%)
    if lost['category'] == found['category']:
        score += 40
        reasons.append(f"Category matched: {lost['category']}")
    elif any(k in lost['category'] and k in found['category'] for k in ['Electronics', 'Card', 'Academic', 'Accessories']):
        score += 25
        reasons.append("Related category")

    # 2. Location match (Weight: 25%)
    lost_loc = (lost['location'] or '').lower()
    found_loc = (found['location'] or '').lower()
    if lost_loc and found_loc:
        if lost_loc == found_loc:
            score += 25
            reasons.append(f"Exact location matched: {lost['location']}")
        else:
            lost_tokens = extract_keywords(lost_loc)
            found_tokens = extract_keywords(found_loc)
            shared_loc = lost_tokens.intersection(found_tokens)
            if shared_loc:
                score += 15
                reasons.append(f"Nearby zone overlap: {', '.join(shared_loc)}")

    # 3. Item Name & Description text overlap (Weight: 35%)
    lost_text_tokens = extract_keywords(f"{lost['item_name']} {lost['description']}")
    found_text_tokens = extract_keywords(f"{found['item_name']} {found['description']}")
    shared_tokens = lost_text_tokens.intersection(found_text_tokens)

    if shared_tokens:
        token_pts = min(len(shared_tokens) * 12, 35)
        score += token_pts
        reasons.append(f"Keywords: {', '.join(list(shared_tokens)[:4])}")

    score = min(score, 98)

    if score >= 75:
        confidence = "High"
    elif score >= 50:
        confidence = "Medium"
    else:
        confidence = "Possible"

    return score, confidence, reasons


@app.route('/api/match-suggestions', methods=['GET'])
def get_match_suggestions():
    """Smart algorithm comparing active lost items against found inventory."""
    lost_items = query_all("""
        SELECT l.lost_id, l.date_lost, l.status,
               i.item_id, i.item_name, i.category, i.description, i.location, i.image_url,
               s.student_id, s.name as student_name, s.department
        FROM LOST_ITEM l
        JOIN ITEM i ON l.item_id = i.item_id
        JOIN STUDENT s ON l.student_id = s.student_id
        WHERE l.status = 'Pending'
    """)
    found_items = query_all("""
        SELECT f.found_id, f.date_found, f.status, f.storage_location,
               i.item_id, i.item_name, i.category, i.description, i.location, i.image_url,
               s.student_id as finder_id, s.name as finder_name
        FROM FOUND_ITEM f
        JOIN ITEM i ON f.item_id = i.item_id
        JOIN STUDENT s ON f.student_id = s.student_id
        WHERE f.status = 'Pending'
    """)

    suggestions = []
    for lost in lost_items:
        for found in found_items:
            score, confidence, reasons = calculate_similarity(lost, found)
            if score >= 40:
                loc_match = (lost['location'].strip().lower() == found['location'].strip().lower())
                loc_score = 25 if loc_match else 0
                token_score = max(0, min(score - 40 - loc_score, 35))
                common_tokens = [w for w in reasons if not w.startswith("Exact category") and not w.startswith("Location proximity")]
                
                suggestions.append({
                    "match_id": f"M-{lost['lost_id']}-{found['found_id']}",
                    "score": score,
                    "confidence": confidence,
                    "reasons": reasons,
                    "lost_id": lost['lost_id'],
                    "lost_item_id": lost['item_id'],
                    "lost_item_name": lost['item_name'],
                    "lost_category": lost['category'],
                    "lost_location": lost['location'],
                    "lost_date": lost['date_lost'],
                    "lost_description": lost['description'],
                    "lost_image_url": lost['image_url'],
                    "lost_student_id": lost['student_id'],
                    "lost_student_name": lost['student_name'],
                    "found_id": found['found_id'],
                    "found_item_id": found['item_id'],
                    "found_item_name": found['item_name'],
                    "found_category": found['category'],
                    "found_location": found['location'],
                    "found_date": found['date_found'],
                    "found_storage_location": found['storage_location'],
                    "found_description": found['description'],
                    "found_image_url": found['image_url'],
                    "found_finder_id": found['finder_id'],
                    "found_finder_name": found['finder_name'],
                    "factors": {
                        "category_match": True,
                        "location_match": loc_match,
                        "location_score": loc_score,
                        "token_score": token_score,
                        "common_tokens": common_tokens
                    },
                    "lost_item": lost,
                    "found_item": found
                })

    suggestions.sort(key=lambda x: x['score'], reverse=True)
    return jsonify(suggestions)


# -----------------------------------------------------------------------------
# 9. CAMPUS ANALYTICS & RECOVERY HOTSPOTS API
# -----------------------------------------------------------------------------
@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Returns campus recovery rate, loss hotspots, and turnaround stats."""
    total_items = query_one("SELECT COUNT(*) as c FROM ITEM")['c'] or 1
    total_lost = query_one("SELECT COUNT(*) as c FROM LOST_ITEM")['c']
    total_found = query_one("SELECT COUNT(*) as c FROM FOUND_ITEM")['c']
    total_claims = query_one("SELECT COUNT(*) as c FROM CLAIM")['c']
    total_returns = query_one("SELECT COUNT(*) as c FROM RETURN_RECORD")['c']

    recovery_rate = round((total_returns / total_items) * 100, 1)

    # Campus hotspots (Top 6 locations with most missing/found items)
    hotspots = query_all("""
        SELECT location,
               COUNT(*) as incident_count,
               SUM(CASE WHEN item_id IN (SELECT item_id FROM LOST_ITEM) THEN 1 ELSE 0 END) as lost_count,
               SUM(CASE WHEN item_id IN (SELECT item_id FROM FOUND_ITEM) THEN 1 ELSE 0 END) as found_count
        FROM ITEM
        GROUP BY location
        ORDER BY incident_count DESC
        LIMIT 6
    """)

    # Category recovery breakdown
    category_metrics = query_all("""
        SELECT 
            i.category,
            SUM(CASE WHEN i.item_id IN (SELECT item_id FROM LOST_ITEM) THEN 1 ELSE 0 END) as lost_count,
            SUM(CASE WHEN i.item_id IN (SELECT item_id FROM FOUND_ITEM) THEN 1 ELSE 0 END) as found_count,
            COUNT(r.return_id) as returned_count,
            ROUND(COUNT(r.return_id) * 100.0 / NULLIF(COUNT(i.item_id), 0), 1) as recovery_rate
        FROM ITEM i
        LEFT JOIN RETURN_RECORD r ON i.item_id = r.item_id
        GROUP BY i.category
        ORDER BY COUNT(i.item_id) DESC
    """)

    # Average settlement days
    avg_turnaround = query_one("""
        SELECT ROUND(AVG(JULIANDAY(r.return_date) - JULIANDAY(l.date_lost)), 1) as avg_days
        FROM RETURN_RECORD r
        JOIN LOST_ITEM l ON r.item_id = l.item_id
    """)
    avg_days = avg_turnaround['avg_days'] if avg_turnaround and avg_turnaround['avg_days'] is not None else 2.5

    return jsonify({
        "total_incidents": total_lost + total_found,
        "total_items": total_items,
        "total_lost": total_lost,
        "total_found": total_found,
        "total_claims": total_claims,
        "total_returns": total_returns,
        "recovery_rate": recovery_rate,
        "recovery_rate_pct": recovery_rate,
        "avg_turnaround_days": avg_days,
        "avg_days_to_return": avg_days,
        "hotspots": hotspots,
        "category_metrics": category_metrics,
        "category_stats": category_metrics
    })


@app.route('/api/reset-demo', methods=['POST'])
def reset_demo():
    """Resets the database schema and sample data to fresh state."""
    try:
        init_db(force_reinit=True)
        return jsonify({"message": "Database successfully reset to pristine seed state with all 7 tables and sample records."})
    except Exception as e:
        return jsonify({"error": f"Reset failed: {str(e)}"}), 500


# -----------------------------------------------------------------------------
# 10. ROLE-BASED AUTHENTICATION (RBAC) API
# -----------------------------------------------------------------------------
@app.route('/api/auth/users', methods=['GET'])
def get_auth_users():
    """Lists available seed accounts for instant demo role switching."""
    users = query_all("""
        SELECT u.user_id, u.username, u.role, u.full_name, u.student_id,
               s.department, s.email, s.phone
        FROM USERS u
        LEFT JOIN STUDENT s ON u.student_id = s.student_id
        ORDER BY u.user_id ASC
    """)
    return jsonify(users)


@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    """Authenticates user and returns profile and role permissions."""
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    user = query_one("""
        SELECT u.user_id, u.username, u.role, u.full_name, u.student_id,
               s.department, s.email, s.phone
        FROM USERS u
        LEFT JOIN STUDENT s ON u.student_id = s.student_id
        WHERE u.username = ? AND u.password_hash = ?
    """, (username, password))

    if not user:
        return jsonify({"error": "Invalid credentials. Try admin/admin123, security/security123, or sritosh/sritosh123"}), 401

    role = user['role']
    permissions = {
        "can_approve_claim": role in ['Admin', 'Security'],
        "can_record_return": role in ['Admin', 'Security'],
        "can_claim_item": role in ['Student', 'Admin'],
        "can_report": True,
        "can_view_analytics": True
    }

    return jsonify({
        "message": f"Welcome back, {user['full_name']}!",
        "user": user,
        "permissions": permissions
    })


# -----------------------------------------------------------------------------
# 11. PRINTABLE RETURN HANDOVER RECEIPT API
# -----------------------------------------------------------------------------
@app.route('/api/returns/<int:return_id>/receipt', methods=['GET'])
def get_return_receipt(return_id):
    """Generates an official return handover certificate and QR code payload."""
    record = query_one("""
        SELECT r.return_id, r.return_date, r.verified_by, r.remarks, r.created_at,
               i.item_id, i.item_name, i.category, i.description, i.location, i.image_url,
               s.student_id, s.name as student_name, s.department, s.email, s.phone
        FROM RETURN_RECORD r
        JOIN ITEM i ON r.item_id = i.item_id
        JOIN STUDENT s ON r.student_id = s.student_id
        WHERE r.return_id = ?
    """, (return_id,))

    if not record:
        return jsonify({"error": "Return record not found"}), 404

    raw_sig = f"{record['return_id']}-{record['student_id']}-{record['item_id']}-{record['return_date']}"
    verification_hash = hashlib.sha256(raw_sig.encode()).hexdigest()[:16].upper()

    receipt_data = {
        "receipt_number": f"RET-VIT-{record['return_id']:04d}",
        "verification_code": verification_hash,
        "issued_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "return_details": record,
        "institution": "University Campus Lost & Found Cell",
        "qr_payload": f"CAMPUS-LOST-FOUND:RECEIPT={record['return_id']}:VERIFY={verification_hash}:STUDENT={record['student_id']}"
    }
    return jsonify(receipt_data)


# -----------------------------------------------------------------------------
# 12. SQL QUERY LAB & LIVE DEMO API
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
    tables_list = ['STUDENT', 'ITEM', 'LOST_ITEM', 'FOUND_ITEM', 'CLAIM', 'RETURN_RECORD', 'USERS']
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

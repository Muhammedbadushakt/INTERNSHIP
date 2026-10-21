from flask import Blueprint, request, redirect, url_for, render_template, jsonify, make_response, g, flash
from app.utils import employee_required
from app.models import Book, Main, Subject, Employee, Record
from app.extension import db
import os
from datetime import datetime

employee_bp = Blueprint("employee", __name__, url_prefix="/employee")
COVER_DIR = os.path.join("frontend", "storage", "Book-cover")


@employee_bp.route('/')
@employee_required
def dashboard():
    search     = request.args.get("search",     "").strip()
    search_by  = request.args.get("search_by",  "title")
    subject_id = request.args.get("subject_id", "").strip()
    main_id    = request.args.get("main_id",    "").strip()
    available  = request.args.get("available",  "").strip()
    page       = request.args.get("page", 1, type=int)

    q = Book.query

    if search:
        if search_by == "title":
            q = q.filter(Book.title.ilike(f"%{search}%"))
        elif search_by == "code":
            q = q.filter(Book.code.ilike(f"%{search}%"))
        elif search_by == "author":
            q = q.filter(Book.author.ilike(f"%{search}%"))
        elif search_by == "keyword":
            q = q.filter(Book.keywords.ilike(f"%{search}%"))

    if subject_id:
        q = q.filter(Book.subject_category == int(subject_id))

    if main_id:
        main = Main.query.get(int(main_id))
        if main:
            q = q.filter(Book.code.ilike(f"{main.name}-%"))

    if available == "1":
        q = q.filter(Book.available_copies > 0)

    books    = q.order_by(Book.code).paginate(page=page, per_page=24, error_out=False)
    mains    = Main.query.order_by(Main.name).all()
    subjects = Subject.query.order_by(Subject.name).all()
    return render_template(
        "employee/dashboard.html",
        books=books, mains=mains, subjects=subjects,
        search=search, search_by=search_by,
        main_id=main_id, subject_id=subject_id, available=available,
    )


@employee_bp.route('/account')
@employee_required
def account():
    employee_code = g.current_user["employee_code"]
    e       = Employee.query.filter_by(employee_code=employee_code).first_or_404()
    records = Record.query.filter_by(employee_id=employee_code).all()
    book_ids = [i.book_id for i in records]

    books = Book.query.filter(Book.code.in_(book_ids)).all()
    return render_template("employee/account.html", employee=e, records=records, books=books)


@employee_bp.route('/edit', methods=['GET', 'POST'])
@employee_required
def edit():
    employee_code = g.current_user["employee_code"]
    employee = Employee.query.filter_by(employee_code=employee_code).first()

    if request.method == 'POST':
        name           = request.form.get("name",           "").strip()
        department     = request.form.get("department",     "").strip()
        designation    = request.form.get("designation",    "").strip()
        contact_number = request.form.get("contact_number", "").strip()

        if not name:
            flash("Name cannot be empty.", "error")
            return render_template("employee/edit.html", employee=employee)

        employee.name           = name
        employee.department     = department
        employee.designation    = designation
        employee.contact_number = contact_number

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("employee.account"))

    return render_template("employee/edit.html", employee=employee)
#NOW BOOK'S DASHBOARD , REQUEST BOOK , ISSUE BOOK 


@employee_bp.route('/books/<string:book_code>')   # ← code is a string, not int
@employee_required
def book_detail(book_code):
    book             = Book.query.filter_by(code=book_code).first_or_404()
    employee_code    = g.current_user["employee_code"]
 
    existing_request = Record.query.filter_by(
        employee_id = employee_code,
        book_id     = book_code,
    ).filter(Record.status.in_(["PENDING", "APPROVED"])).first()
 
    return render_template(
        "employee/book_detail.html",
        book             = book,
        existing_request = existing_request,
        now              = datetime.utcnow(),   # None = can request, else show status
    )

@employee_bp.route('/books/<string:book_code>/request', methods=["POST",'GET'])
@employee_required
def request_book(book_code):
    book          = Book.query.filter_by(code=book_code).first_or_404()
    employee_code = g.current_user["employee_code"]

    # convert string from form to datetime — form sends "2026-06-15", DB needs datetime
    expected_raw = request.form.get('expected_at', "").strip()
    expected_at  = None
    if expected_raw:
        try:
            from datetime import datetime
            expected_at = datetime.strptime(expected_raw, "%Y-%m-%d")
        except ValueError:
            flash("Invalid date format for expected return date.", "error")
            return redirect(url_for("employee.book_detail", book_code=book_code))

    if book.available_copies < 1:
        flash("No copies available right now.", "error")
        return redirect(url_for("employee.book_detail", book_code=book_code))

    already = Record.query.filter_by(
        employee_id = employee_code,
        book_id     = book_code,
    ).filter(Record.status.in_(["PENDING", "APPROVED"])).first()

    if already:
        flash("You already have an active request for this book.", "error")
        return redirect(url_for("employee.book_detail", book_code=book_code))

    try:
        from datetime import datetime
        record = Record(
            employee_id = employee_code,
            book_id     = book_code,
            status      = "PENDING",
            issued_at   = datetime.utcnow(),
            expected_at = expected_at,        # datetime object or None
        )
        book.available_copies -= 1
        db.session.add(record)
        db.session.commit()
        flash("Request submitted. Awaiting admin approval.", "success")
    except Exception as exc:
        db.session.rollback()
        flash(f"Could not submit request: {exc}", "error")

    return redirect(url_for("employee.account"))
# ─── My Books Overview ────────────────────────────────────────────────────────
# ─── My Books Overview ────────────────────────────────────────────────────────
@employee_bp.route('/my-books')
@employee_required
def my_books():
    from datetime import datetime
    employee_code = g.current_user["employee_code"]
    now = datetime.utcnow()

    all_records = (
        Record.query
        .filter_by(employee_id=employee_code)
        .order_by(Record.issued_at.desc())
        .all()
    )

    approved         = [r for r in all_records if r.status == "APPROVED"
                        and r.expected_at and r.expected_at >= now]
    due              = [r for r in all_records if r.status == "APPROVED"
                        and r.expected_at and r.expected_at < now]
    pending          = [r for r in all_records if r.status == "PENDING"]
    rejected         = [r for r in all_records if r.status == "REJECTED"]
    return_requested = [r for r in all_records if r.status == "RETURN_REQUESTED"]
    history          = [r for r in all_records if r.status == "RETURNED"]

    return render_template(
        "employee/my_books.html",
        approved=approved,
        due=due,
        pending=pending,
        rejected=rejected,
        return_requested=return_requested,
        history=history,
        now=now,
    )


# ─── Return a Book (employee raises return request) ───────────────────────────
@employee_bp.route('/my-books/<int:record_id>/return', methods=["GET", "POST"])
@employee_required
def return_book(record_id):
    from datetime import datetime
    employee_code = g.current_user["employee_code"]

    record = Record.query.filter_by(
        id          = record_id,
        employee_id = employee_code,
    ).first_or_404()

    # Guard: only APPROVED records can be requested for return
    if record.status not in ("APPROVED",):
        flash("This record cannot be submitted for return.", "info")
        return redirect(url_for("employee.my_books"))

    if request.method == "POST":
        try:
            record.returned_at = datetime.utcnow()   # timestamp of employee's intent
            record.status      = "RETURN_REQUESTED"
            db.session.commit()
            flash("Return request submitted. Awaiting admin confirmation.", "success")
        except Exception as exc:
            db.session.rollback()
            flash(f"Could not submit return request: {exc}", "error")

        return redirect(url_for("employee.my_books"))

    # GET → confirmation page
    return render_template("employee/return_book.html", record=record)
from flask import Blueprint, request, redirect, url_for, render_template, g, flash
from app.utils import guest_required
from app.models import Book, Main, Subject, GuestUser, Employee, Record
from app.extension import db

guest_bp = Blueprint("guest", __name__, url_prefix="/guest")


# ══════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════

@guest_bp.route('/')
@guest_required
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
        "guest/dashboard.html",
        books=books, mains=mains, subjects=subjects,
        search=search, search_by=search_by,
        main_id=main_id, subject_id=subject_id, available=available,
    )


# ══════════════════════════════════════════════
#  ACCOUNT
# ══════════════════════════════════════════════

@guest_bp.route('/account')
@guest_required
def account():
    guest_id = g.current_user["guest_id"]
    guest    = GuestUser.query.get_or_404(guest_id)

    # Sponsor employee details
    sponsor  = Employee.query.filter_by(employee_code=guest.employee_code).first()

    return render_template(
        "guest/account.html",
        guest=guest,
        sponsor=sponsor,
    )


# ══════════════════════════════════════════════
#  BOOK DETAIL
# ══════════════════════════════════════════════

@guest_bp.route('/books/<string:book_code>')
@guest_required
def book_detail(book_code):
    book     = Book.query.filter_by(code=book_code).first_or_404()
    existing_request = Record.query.filter_by(
        book_id  = book_code,
    ).filter(Record.status.in_(["PENDING", "APPROVED"])).first()

    return render_template(
        "guest/book_detail.html",
        book             = book,
        existing_request = existing_request,   # None = can request, else show status
    )
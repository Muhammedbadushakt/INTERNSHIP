from .extension import db
from datetime import datetime


class Employee(db.Model):
    __tablename__ = "employees"

    employee_code = db.Column(
        db.String(20),
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    department = db.Column(db.String(100))
    designation = db.Column(db.String(100))

    gmail_id = db.Column(
        db.String(150),
        unique=True
    )

    contact_number = db.Column(db.String(20))

    status = db.Column(
        db.String(20),
        default="INACTIVE"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user = db.relationship(
        "User",
        backref="employee",
        uselist=False,
        cascade="all, delete-orphan"
    )

    roles = db.relationship(
        "Role",
        backref="employee",
        lazy=True,
        cascade="all, delete-orphan"
    )

    records = db.relationship(
        "Record",
        backref="employee",
        lazy=True,
        cascade="all, delete-orphan"
    )

    guest_users = db.relationship(
        "GuestUser",
        backref="sponsor",
        lazy=True,
        cascade="all, delete-orphan"
    )


class GuestUser(db.Model):
    """
    Guest only stores visitor information.
    They cannot borrow books.
    """

    __tablename__ = "guest_users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    employee_code = db.Column(
        db.String(20),
        db.ForeignKey(
            "employees.employee_code",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    contact_number = db.Column(
        db.String(20)
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class User(db.Model):

    __tablename__ = "users"

    employee_code = db.Column(
        db.String(20),
        db.ForeignKey(
            "employees.employee_code",
            ondelete="CASCADE"
        ),
        primary_key=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    otp = db.Column(
        db.String(10),
        nullable=True
    )

    otp_created_at = db.Column(
        db.DateTime,
        nullable=True
    )


class Role(db.Model):

    __tablename__ = "roles"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    employee_code = db.Column(
        db.String(20),
        db.ForeignKey(
            "employees.employee_code",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    name = db.Column(
        db.String(50),
        nullable=False
    )


class Main(db.Model):

    __tablename__ = "main"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    description = db.Column(
        db.String(255)
    )


class Subject(db.Model):

    __tablename__ = "subjects"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    description = db.Column(
        db.String(255)
    )

    books = db.relationship(
        "Book",
        backref="subject",
        lazy=True
    )


class Shelf(db.Model):

    __tablename__ = "shelves"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False,
        unique=True
    )

    description = db.Column(
        db.String(255)
    )


class RunningCode(db.Model):

    __tablename__ = "running_codes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    current_code = db.Column(
        db.Integer,
        default=1
    )


class Copy(db.Model):

    __tablename__ = "copies"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(50),
        nullable=False
    )


class Book(db.Model):

    __tablename__ = "books"

    code = db.Column(
        db.String(50),
        primary_key=True
    )

    title = db.Column(
        db.String(255),
        nullable=False
    )

    author = db.Column(
        db.String(255)
    )

    publisher = db.Column(
        db.String(255)
    )

    edition = db.Column(
        db.String(50)
    )

    publication_year = db.Column(
        db.Integer
    )

    subject_category = db.Column(
        db.Integer,
        db.ForeignKey(
            "subjects.id"
        )
    )

    shelf_number = db.Column(
        db.String(50)
    )

    keywords = db.Column(
        db.Text
    )

    price = db.Column(
        db.Integer
    )

    copies = db.Column(
        db.Integer,
        default=1
    )

    available_copies = db.Column(
        db.Integer,
        default=1
    )

    cover_image = db.Column(
        db.String(255),
        default="DEFAULTCOVER.png"
    )

    remarks = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    records = db.relationship(
        "Record",
        backref="book",
        lazy=True,
        cascade="all, delete-orphan"
    )


class Record(db.Model):

    __tablename__ = "records"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    employee_id = db.Column(
        db.String(20),
        db.ForeignKey(
            "employees.employee_code",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    book_id = db.Column(
        db.String(50),
        db.ForeignKey(
            "books.code",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    issued_at = db.Column(
        db.DateTime
    )

    expected_at = db.Column(
        db.DateTime
    )

    approval_at = db.Column(
        db.DateTime
    )

    returned_at = db.Column(
        db.DateTime
    )

    return_approval_at = db.Column(
        db.DateTime
    )

    status = db.Column(
        db.String(20),
        default="PENDING"
    )
class AdminRecord(db.Model):
    __tablename__ = "adminrecords"

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    employee_id = db.Column(
        db.String(20),
        db.ForeignKey(
            "employees.employee_code",
            ondelete="CASCADE"
        ),
        nullable=False
    )
    book_id = db.Column(
        db.String(50),
        db.ForeignKey(
            "books.code",
            ondelete="CASCADE"
        ),
        nullable=False
    )
    name = db.Column(
        db.String(50)
    )
    issued_at = db.Column(
        db.DateTime
    )

    expected_at = db.Column(
        db.DateTime
    )
    returned_at = db.Column(
        db.DateTime
    )
    status = db.Column(
        db.String(20),
        default="PENDING"
    )
    remarks = db.Column(db.Text, nullable=True)

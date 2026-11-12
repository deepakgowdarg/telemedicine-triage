import mysql.connector
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_connection

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        age = request.form.get("age", "").strip()
        phone = request.form.get("phone", "").strip()

        if not full_name or not email or not password:
            flash("Please fill in your name, email and password.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                flash("This email is already registered. Please log in.", "danger")
                return render_template("register.html")

            # Store a hash of the password, never the password itself
            password_hash = generate_password_hash(password)

            cursor.execute(
                "INSERT INTO users (full_name, email, password_hash, role) VALUES (%s, %s, %s, 'patient')",
                (full_name, email, password_hash),
            )
            user_id = cursor.lastrowid

            cursor.execute(
                "INSERT INTO patient_details (user_id, age, phone) VALUES (%s, %s, %s)",
                (user_id, int(age) if age.isdigit() else None, phone or None),
            )
            conn.commit()
        except mysql.connector.Error:
            conn.rollback()
            flash("Could not register right now. Please try again.", "danger")
            return render_template("register.html")
        finally:
            cursor.close()
            conn.close()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, full_name, password_hash, role FROM users WHERE email = %s",
            (email,),
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["user_id"]
            session["full_name"] = user["full_name"]
            session["role"] = user["role"]
            flash(f"Welcome, {user['full_name']}.", "success")

            if user["role"] == "patient":
                return redirect(url_for("patient.dashboard"))
            # Doctor dashboard is built on Day 4
            flash("Doctor dashboard will be added on Day 4.", "info")
            return redirect(url_for("index"))

        # Same message for wrong email or wrong password, so attackers cannot learn which emails exist
        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))
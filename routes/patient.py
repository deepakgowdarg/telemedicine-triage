import mysql.connector
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.db import get_connection
from triage.rules import SYMPTOMS, LABELS, CODES, DURATIONS, assess

patient_bp = Blueprint("patient", __name__)


def is_patient():
    if session.get("role") != "patient":
        flash("Please log in as a patient first.", "danger")
        return False
    return True


def get_patient_id(cursor, user_id):
    cursor.execute("SELECT patient_id FROM patient_details WHERE user_id = %s", (user_id,))
    row = cursor.fetchone()
    if not row:
        return None
    # Works whether the cursor returns a dictionary or a tuple
    if isinstance(row, dict):
        return row["patient_id"]
    return row[0]


@patient_bp.route("/dashboard")
def dashboard():
    if not is_patient():
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        patient_id = get_patient_id(cursor, session["user_id"])
        records = []
        if patient_id:
            cursor.execute(
                """
                SELECT s.record_id, s.created_at, t.urgency_level
                FROM symptom_records s
                JOIN triage_results t ON t.record_id = s.record_id
                WHERE s.patient_id = %s
                ORDER BY s.created_at DESC
                """,
                (patient_id,),
            )
            records = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return render_template("patient_dashboard.html", records=records)


@patient_bp.route("/symptoms", methods=["GET", "POST"])
def symptoms():
    if not is_patient():
        return redirect(url_for("auth.login"))

    if request.method == "GET":
        return render_template("symptom_form.html", symptoms=SYMPTOMS, durations=DURATIONS)

    # Keep only codes that exist in our list
    selected = [s for s in request.form.getlist("symptoms") if s in CODES]
    duration = request.form.get("duration", "")
    notes = request.form.get("additional_notes", "").strip()

    if not selected:
        flash("Please select at least one symptom. If someone may be in danger, call 112 now.", "danger")
        return render_template("symptom_form.html", symptoms=SYMPTOMS, durations=DURATIONS)

    if duration not in DURATIONS:
        flash("Please choose how long you have had these symptoms.", "danger")
        return render_template("symptom_form.html", symptoms=SYMPTOMS, durations=DURATIONS)

    result = assess(selected, duration)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        patient_id = get_patient_id(cursor, session["user_id"])
        if patient_id is None:
            flash("Your patient profile was not found. Please register again.", "danger")
            return redirect(url_for("auth.register"))

        cursor.execute(
            """
            INSERT INTO symptom_records (patient_id, symptoms, duration, additional_notes)
            VALUES (%s, %s, %s, %s)
            """,
            (patient_id, ",".join(selected), duration, notes or None),
        )
        record_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO triage_results (record_id, urgency_level, matched_rules, recommendation)
            VALUES (%s, %s, %s, %s)
            """,
            (record_id, result["urgency"], "; ".join(result["matched_rules"]), result["recommendation"]),
        )
        conn.commit()
    except mysql.connector.Error:
        conn.rollback()
        flash("Could not save your submission. Please try again.", "danger")
        return render_template("symptom_form.html", symptoms=SYMPTOMS, durations=DURATIONS)
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("patient.result", record_id=record_id))


@patient_bp.route("/result/<int:record_id>")
def result(record_id):
    if not is_patient():
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # The JOIN checks that this record belongs to the logged-in user
        cursor.execute(
            """
            SELECT s.symptoms, s.duration, s.created_at,
                   t.urgency_level, t.matched_rules, t.recommendation
            FROM symptom_records s
            JOIN triage_results t ON t.record_id = s.record_id
            JOIN patient_details p ON p.patient_id = s.patient_id
            WHERE s.record_id = %s AND p.user_id = %s
            """,
            (record_id, session["user_id"]),
        )
        row = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if not row:
        flash("That record was not found.", "danger")
        return redirect(url_for("patient.dashboard"))

    return render_template("triage_result.html", r=row, labels=LABELS)
@patient_bp.route("/conditions", methods=["GET", "POST"])
def conditions():
    if not is_patient():
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        patient_id = get_patient_id(cursor, session["user_id"])
        if patient_id is None:
            flash("Your patient profile was not found. Please register again.", "danger")
            return redirect(url_for("auth.register"))

        if request.method == "POST":
            condition_id = request.form.get("condition_id", "")
            diagnosis_date = request.form.get("diagnosis_date") or None
            treating_doctor = request.form.get("treating_doctor", "").strip() or None

            if not condition_id.isdigit():
                flash("Please choose a condition.", "danger")
            else:
                cursor.execute(
                    """
                    INSERT IGNORE INTO patient_conditions
                        (patient_id, condition_id, diagnosis_date, treating_doctor)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (patient_id, int(condition_id), diagnosis_date, treating_doctor),
                )
                conn.commit()
                if cursor.rowcount:
                    flash("Condition added.", "success")
                else:
                    flash("You have already added this condition.", "info")
            return redirect(url_for("patient.conditions"))

        cursor.execute("SELECT condition_id, name FROM special_conditions ORDER BY name")
        all_conditions = cursor.fetchall()

        cursor.execute(
            """
            SELECT sc.name, pc.diagnosis_date, pc.treating_doctor
            FROM patient_conditions pc
            JOIN special_conditions sc ON sc.condition_id = pc.condition_id
            WHERE pc.patient_id = %s
            ORDER BY sc.name
            """,
            (patient_id,),
        )
        my_conditions = cursor.fetchall()
    except mysql.connector.Error:
        conn.rollback()
        flash("Could not save right now. Please try again.", "danger")
        return redirect(url_for("patient.dashboard"))
    finally:
        cursor.close()
        conn.close()

    return render_template(
        "conditions.html",
        all_conditions=all_conditions,
        my_conditions=my_conditions,
    )
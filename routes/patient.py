from flask import Blueprint, render_template, session, redirect, url_for, flash

patient_bp = Blueprint("patient", __name__)


@patient_bp.route("/dashboard")
def dashboard():
    # Only logged-in patients may see this page
    if session.get("role") != "patient":
        flash("Please log in as a patient first.", "danger")
        return redirect(url_for("auth.login"))
    return render_template("patient_dashboard.html")
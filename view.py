from flask import Blueprint, render_template, request, redirect, url_for

view_bp = Blueprint("view", __name__)

@view_bp.route("/")
def index():
    return render_template("index.html")

@view_bp.route("/view")
def view():
    return render_template("view.html")

@view_bp.route("/lookup", methods=["POST"])
def lookup():
    render_template("view.html")
    pmcid = request.form['pmcid']
    if pmcid:
        # Construct the PDF URL
        pdf_url = f'https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/'
        return redirect(pdf_url)
    else:
        return "PMC ID is required."
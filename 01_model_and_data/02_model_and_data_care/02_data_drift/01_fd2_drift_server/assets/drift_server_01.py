# conda activate evidently_no_conda (include flask)
# browse to : http://localhost:5000/report

from flask import Flask, send_from_directory

app = Flask(__name__)


# Route to serve the report
@app.route("/report")
def serve_report():
    # Assumes the HTML report is saved in the "reports" folder
    return send_from_directory(directory="reports", path="data_drift_report.html")


if __name__ == "__main__":
    app.run(debug=True)

import json
import os
import platform

from flask import Flask, Response, request
import markdown
import markdown.extensions.fenced_code
from pygments.formatters import HtmlFormatter
from selenium import webdriver

from all_results_service import AllResults
from service import Service


def init_firefox_driver():
    firefox_options = webdriver.FirefoxOptions()
    driver_file = "drivers/geckodriver" if platform.system() == "Linux" else "drivers/geckodriver.exe"
    # Arguments for Firefox driver
    firefox_options.add_argument("--headless")
    firefox_options.add_argument("--no-sandbox")
    firefox_options.add_argument("--disable-dev-shm-usage")

    # Firefox Driver
    driver = webdriver.Firefox(
        executable_path=os.path.join(os.getcwd(), driver_file), firefox_options=firefox_options)

    return driver


def init_chrome_driver():
    chrome_options = webdriver.ChromeOptions()
    # Specifying the driver options for chrome
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.binary_location = os.environ.get(
        "GOOGLE_CHROME_BIN")
    # Starting the driver
    driver = webdriver.Chrome(
        executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)

    return driver


driver = init_firefox_driver()

# Initializing the Crawler object from service
# Injecting the driver dependency
old_scrapper = Service(driver)
new_scrapper = AllResults(driver)

grades = {
    "O":  10,
    "A+": 9,
    "A":  8,
    "B+": 7,
    "B":  6,
    "C":  5,
    "F":  0,
    "Ab": 0,
}


app = Flask(__name__)


@app.route("/")
def index():

    formatter = HtmlFormatter(full=True, cssclass="codehilite")
    css_string = formatter.get_style_defs()
    readme = open("README_PAGE.md", "r")
    md_template = markdown.markdown(
        readme.read(), extensions=["fenced_code", "codehilite"]
    )
    md_css_string = "<style>" + css_string + "</style>"
    md_template = md_css_string + md_template
    return md_template


@app.route("/<hallticket>/<dob>/<year>", methods=["GET"])
def routing_path(hallticket, dob, year):

    result = old_scrapper.get_result(hallticket, dob, year)
    return Response(json.dumps(result),  mimetype='application/json')


@app.route("/calculate/<hallticket>/<dob>/<year>", methods=["GET"])
def calculate(hallticket, dob, year):
    result = old_scrapper.get_result(hallticket, dob, year)
    # Calculating the result
    sgpa = 0
    total_credits = 0
    for subject in result[1]:
        total_credits += float(subject["subject_credits"])
        if subject["grade_earned"] == "F" or subject["grade_earned"] == "-":
            sgpa = 0
            break
        if not subject["grade_earned"] in grades.keys():
            sgpa = 0
            break
        sgpa += grades[subject["grade_earned"]] * \
            float(subject["subject_credits"])

    sgpa = round(sgpa/total_credits, 2)
    result.insert(0, {"SGPA": sgpa if sgpa else "FAIL"})
    return Response(json.dumps(result),  mimetype='application/json')


@app.route("/result", methods=["GET"])
def request_param_path():

    hallticket = request.args.get("hallticket")
    dob = request.args.get("dob")
    year = request.args.get("year")

    result = old_scrapper.get_result(hallticket, dob, year)

    return Response(json.dumps(result),  mimetype='application/json')


@app.route("/new/all", methods=["GET"])
def all():
    all_exams, _, _ = new_scrapper.get_all_results()
    return Response(json.dumps(all_exams),  mimetype='application/json')


@app.route("/new/all/regular", methods=["GET"])
def all_regular():
    _, regular_exams, _ = new_scrapper.get_all_results()
    return Response(json.dumps(regular_exams),  mimetype='application/json')


@app.route("/new/all/supply", methods=["GET"])
def all_supply():
    _, _, supply_exams = new_scrapper.get_all_results()
    return Response(json.dumps(supply_exams),  mimetype='application/json')


if __name__ == "__main__":
    app.run()

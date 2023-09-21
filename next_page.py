from flask import Flask, render_template, request
import requests
import xml.etree.ElementTree as ET
from flask import Blueprint, render_template

app = Flask(__name__)

# Create a blueprint for the next_page routes
next_page_blueprint = Blueprint('next_page', __name__)

@next_page_blueprint.route("/", methods=["GET", "POST"])
def next_page():
    if request.method == "POST":
        pmcid = request.form["pmcid"]
        keywords = request.form["keywords"].split(',')  # Split keywords by comma
        search_results = search_pmc(pmcid, keywords)
        keyword_counts = count_keywords(keywords, search_results)
        return render_template("next.html", results=search_results, keyword_counts=keyword_counts)
    return render_template("next.html", results=None, keyword_counts={})

def search_pmc(pmcid, keywords):
    # Construct the URL with the user-provided PMCID
    url = f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/{pmcid}/unicode"

    # Send an HTTP GET request to the URL
    response = requests.get(url)

    if response.status_code == 200:
        # Parse the XML content
        xml_content = response.text
        root = ET.fromstring(xml_content)

        # Define the desired mappings for section types and types
        desired_mappings = [
            {"section_type": "TITLE", "type": ["title", "front", "title_1", "title_2", "title_3"]},
            {"section_type": "ABSTRACT", "type": ["paragraph", "front", "abstract", "title_1", "title_2", "title_3"]},
            {"section_type": "INTRO", "type": ["paragraph", "front", "title_1", "title_2", "title_3"]},
            {"section_type": "METHODS", "type": ["paragraph", "front", "title_1", "title_2", "title_3"]},
            {"section_type": "CONCL", "type": ["paragraph", "front", "title_1", "title_2", "title_3"]},
            {"section_type": "DISCUSS", "type": ["paragraph", "front", "title_1", "title_2", "title_3"]},
        ]

        # Initialize a list to store search results
        search_results = []

        # Search for each keyword within the desired mappings and collect matching sentences
        for keyword in keywords:
            keyword = keyword.strip()  # Remove leading/trailing spaces
            for mapping in desired_mappings:
                section_type = mapping["section_type"]
                types = mapping["type"]

                for passage in root.findall(".//passage"):
                    section = passage.find(".//infon[@key='type']").text
                    if section in types:
                        text = passage.find(".//text").text
                        if keyword.lower() in text.lower():
                            search_results.append(f"[{section_type}] {text}")

        return search_results
    else:
        return [f"Error: Unable to fetch content. Status code: {response.status_code}"]

def count_keywords(keywords, search_results):
    keyword_counts = {keyword: {"count": 0, "details": []} for keyword in keywords}
    
    for result in search_results:
        sentence = result
        for keyword in keywords:
            if keyword.lower() in sentence.lower():
                keyword_counts[keyword]["count"] += 1
                keyword_counts[keyword]["details"].append(sentence)

    return keyword_counts

if __name__ == "__main__":
    app.run(debug=False)

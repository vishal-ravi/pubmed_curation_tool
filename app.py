import requests
import json
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from flask import Flask, request, render_template
from next_page import next_page_blueprint
from view import view_bp


app = Flask(__name__)

# Register the blueprint
app.register_blueprint(next_page_blueprint, url_prefix='/next')
app.register_blueprint(view_bp)

# Replace with your actual API key
api_key = "7c13496fb6f075b0cf97f52998b5f92a9108"

# Base URL for PubMed API
base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# Define the keywords to check (can be an empty list initially)
keywords_to_check = []


@app.route("/", methods=["GET", "POST"])
def index():
    pmid = None
    pmcid = None
    title = None
    full_text_link = None
    publication_type = None
    exclude_message = None
    keyword_results = None
    keyword_results_in_full_text = None

    if request.method == "POST":
        pmid = request.form["pmid"]
        keywords = request.form["keywords"].split(
            ',')  # Split keywords by comma
        pmcid = get_pmcid(pmid)
        title = get_title(pmid)
        full_text_link = get_full_text_link(pmid)
        publication_type = get_publication_type(pmid)
        
        

        # Check if publication type should trigger exclusion
        if should_exclude(publication_type):
            exclude_message = "This article is excluded due to its publication type."

        # Fetch the abstract
        abstract = get_abstract(pmid, keywords)

        # Check keywords in the abstract and get relevant sentences
        keyword_results = get_sentences_with_exact_keywords(abstract, keywords)



    return render_template("index.html", pmid=pmid, pmcid=pmcid, title=title, full_text_link=full_text_link, publication_type=publication_type, exclude_message=exclude_message, keyword_results=keyword_results, keyword_results_in_full_text=keyword_results_in_full_text)
@app.route("/download-pdf/<pmcid>", methods=["GET"])
def download_pdf(pmcid):
    if pmcid:
        pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"
        response = requests.get(pdf_url)

        if response.status_code == 200:
            # Set the response headers to indicate a PDF file
            headers = {
                "Content-Disposition": f"attachment; filename={pmcid}.pdf",
                "Content-Type": "application/pdf",
            }
            return response.content, 200, headers
        else:
            return "PDF Download Failed", 404
    else:
        return "PMCID not found", 404
  
def get_pmcid(pmid):
    # Construct the API request URL to fetch article metadata
    api_url = f"{base_url}/efetch.fcgi?db=pubmed&retmode=xml&id={pmid}&api_key={api_key}"

    # Make the API request
    response = requests.get(api_url)

    if response.status_code == 200:
        xml_content = response.text
        root = ET.fromstring(xml_content)

        # Find the PMCID if available
        pmcid_element = root.find(".//ArticleId[@IdType='pmc']")

        if pmcid_element is not None:
            pmcid = pmcid_element.text
            return f"PMID: {pmid} has PMCID: {pmcid}"
        else:
            return f"PMID: {pmid} does not have a PMCID."
    else:
        return f"Error: {response.status_code} - {response.text}"


def get_title(pmid):
    api_url = f"{base_url}/esummary.fcgi?db=pubmed&id={pmid}&api_key={api_key}"
    response = requests.get(api_url)

    if response.status_code == 200:
        xml_content = response.text
        root = ET.fromstring(xml_content)

        title_element = root.find(".//Item[@Name='Title']")
        if title_element is not None:
            return title_element.text
        else:
            return "Title Not Found"
    else:
        return "Error"


def get_full_text_link(pmid):
    pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    response = requests.get(pubmed_url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        link_item = soup.find("a", class_="link-item dialog-focus")
        if link_item:
            return link_item.get('href')

    return "Link Not Found"


def get_publication_type(pmid):
    api_url = f"{base_url}/efetch.fcgi?db=pubmed&retmode=xml&id={pmid}&api_key={api_key}"
    response = requests.get(api_url)

    if response.status_code == 200:
        xml_content = response.text
        root = ET.fromstring(xml_content)

        publication_type_elements = root.findall(".//PublicationType")
        publication_types = [elem.text for elem in publication_type_elements]

        return ", ".join(publication_types) if publication_types else "Publication Type Not Found"
    else:
        return "Error"


def should_exclude(publication_type):
    # Define the publication types to exclude
    excluded_types = ['Review', 'Clinical Trial', 'Patient Study']

    # Check if any of the excluded types match the publication type
    for excluded_type in excluded_types:
        if excluded_type in publication_type:
            return True

    return False


def get_abstract(pmid, keywords):
    # Construct the URL to fetch the article's HTML page
    article_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

    # Make the request to the article's page
    article_response = requests.get(article_url)

    if article_response.status_code == 200:
        soup = BeautifulSoup(article_response.text, "html.parser")
        abstract_element = soup.find("div", class_="abstract", id="abstract")

        if abstract_element:
            # Extract all paragraphs within the abstract
            paragraphs = abstract_element.find_all("p")

            if paragraphs:
                # Create a dictionary to store sentences by keyword
                keyword_sentences = {keyword: [] for keyword in keywords}

                for paragraph in paragraphs:
                    # Get the text of the paragraph
                    paragraph_text = paragraph.get_text(strip=True)

                    # Check each keyword individually
                    for keyword in keywords:
                        if keyword.lower() in paragraph_text.lower():
                            # Append the sentence to the corresponding keyword
                            keyword_sentences[keyword].append(paragraph_text)

                # Initialize the abstract text
                abstract_text = ""

                # Generate the abstract text with headings and numbered sentences
                for keyword, sentences in keyword_sentences.items():
                    if sentences:
                        abstract_text += f"{keyword}:\n"
                        for i, sentence in enumerate(sentences, start=1):
                            abstract_text += f"{i}. {sentence}\n"

                return abstract_text.strip()

    return "Abstract Not Found"


def get_sentences_with_exact_keywords(abstract, keywords):
    sentences = abstract.split(". ")
    found_sentences = []

    for sentence in sentences:
        for keyword in keywords:
            keyword = keyword.strip()
            words_in_sentence = sentence.split()
            if keyword.lower() in [word.lower() for word in words_in_sentence]:
                found_sentences.append((keyword, sentence))
                break  # Stop checking keywords in this sentence if one is found

    return found_sentences if found_sentences else [("No keyword found", "")]


if __name__ == "__main__":
    app.run(debug=False,host='0.0.0.0')

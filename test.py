import requests
import PyPDF2

def download_pdf(url, file_name):
    response = requests.get(url)

    if response.status_code == 200:
        with open(file_name, 'wb') as pdf_file:
            pdf_file.write(response.content)
        print(f"PDF downloaded as '{file_name}'")
    else:
        print(f"Failed to download PDF. Status code: {response.status_code}")

def extract_text_from_pdf(pdf_file):
    try:
        with open(pdf_file, 'rb') as pdf:
            pdf_reader = PyPDF2.PdfFileReader(pdf)
            text = ""
            for page_num in range(pdf_reader.numPages):
                page = pdf_reader.getPage(page_num)
                text += page.extractText()
            return text
    except FileNotFoundError:
        return "PDF file not found."

# Example usage:
pdf_url = "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5712779/pdf/97320630013356.pdf"  # Replace with your PDF URL
pdf_file_name = "downloaded.pdf"  # Replace with the desired file name and path

download_pdf(pdf_url, pdf_file_name)
extracted_text = extract_text_from_pdf(pdf_file_name)
print(extracted_text)

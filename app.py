import streamlit as st
import pandas as pd
import requests
import json
from bs4 import BeautifulSoup

# Function to perform a search using the Google Custom Search API
def search(query, api_key, cse_id, country_code, language_code, **kwargs):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'q': query,
        'key': api_key,
        'cx': cse_id,
        'gl': country_code,  # Geolocation parameter
        'lr': language_code  # Language parameter
    }
    params.update(kwargs)
    response = requests.get(url, params=params)
    return json.loads(response.text)

# Function to extract bold text from HTML snippets
def extract_bold_text_from_snippets(html_snippets):
    bold_texts = []
    for snippet in html_snippets:
        soup = BeautifulSoup(snippet, 'html.parser')
        for bold_tag in soup.find_all(['b', 'strong']):
            text = bold_tag.get_text()
            cleaned_text = text.replace('...', '').strip()  # Remove ellipses and trim spaces
            if cleaned_text:  # Add text if it's not empty
                bold_texts.append(cleaned_text)
    return ', '.join(bold_texts)

# Function to process the file and add new columns with search result titles and bold text
def process_file(file, api_key, cse_id, country_code, language_code):
    df = pd.read_csv(file)

    # Add new columns for search result titles and bold text
    df['SERP Title 1'] = ''
    df['SERP Title 2'] = ''
    df['SERP Title 3'] = ''
    df['Bold Text'] = ''

    for index, row in df.iterrows():
        query = row[df.columns[2]]
        results = search(query, api_key, cse_id, country_code, language_code)

        # Extract SERP titles and bold text
        if 'items' in results:
            for i in range(min(3, len(results['items']))):
                df.at[index, f'SERP Title {i+1}'] = results['items'][i].get('title', '')

            html_snippets = [item.get('htmlSnippet', '') for item in results['items']]
            df.at[index, 'Bold Text'] = extract_bold_text_from_snippets(html_snippets)

    return df

# Streamlit app layout
def main():
    st.title("Answer SERP Scraper")

    st.markdown("""
    ## About the App
    *Answer SERP Scraper* is an application designed to assist in digital marketing and SEO analysis. Created by [jonathanboshoff.com](http://jonathanboshoff.com), this tool uses an Answer Socrates CSV file to extract valuable search engine result page (SERP) data. Specifically, it grabs the top 3 title tags and the bold text from the search results for each query in the file. This information is essential for understanding how content is displayed and highlighted in search engines, providing insights for SEO optimization and content strategy.
    """)

    # Define a list of countries and their codes
    countries = {
        "United States": "US",
        "United Kingdom": "GB",
        "Canada": "CA",
        "Australia": "AU",
        "India": "IN"
        # Add more countries and their codes here
    }

    # Define a list of languages and their codes
    languages = {
        "English": "lang_en",
        "Spanish": "lang_es",
        "French": "lang_fr",
        "German": "lang_de",
        "Chinese": "lang_zh"
        # Add more languages and their codes here
    }

    # Dropdown for selecting a country
    selected_country = st.selectbox("Select a country for search", list(countries.keys()))

    # Dropdown for selecting a language
    selected_language = st.selectbox("Select a language for search", list(languages.keys()), index=0)

    # Use Streamlit secrets for API key and CSE ID
    api_key = st.secrets["GOOGLE_API_KEY"]
    cse_id = st.secrets["CUSTOM_SEARCH_ENGINE_ID"]

    uploaded_file = st.file_uploader("Upload your file", type=["csv"])

    if uploaded_file is not None and api_key and cse_id:
        processed_data = process_file(uploaded_file, api_key, cse_id, countries[selected_country], languages[selected_language])

        st.write("Processed Data:")
        st.write(processed_data)

        # Download button
        st.download_button(
            label="Download processed data",
            data=processed_data.to_csv(index=False),
            file_name="processed_data.csv",
            mime="text/csv",
        )

if __name__ == "__main__":
    main()

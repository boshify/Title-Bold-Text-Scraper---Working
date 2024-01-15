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

    # Rename the column to 'Target Query' if not already named so
    if df.columns[0] != 'Target Query':
        df.rename(columns={df.columns[0]: 'Target Query'}, inplace=True)

    # Add new columns for search result titles and bold text
    df['SERP Title 1'] = ''
    df['SERP Title 2'] = ''
    df['SERP Title 3'] = ''
    df['Bold Text'] = ''

    for index, row in df.iterrows():
        query = row['Target Query']

        # Skip processing if the query is blank or empty
        if pd.isna(query) or query.strip() == '':
            continue

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
    st.title("Title Meta Bold Text Scraper")

    st.markdown("""
    ## About the App
*Title Meta Bold Text Scraper* is a tool designed for digital marketers and SEO professionals. This application allows users to upload a CSV file containing a list of target queries. For each query, it scrapes Google search results, extracting valuable information such as the top 3 title tags and bold text within the search results. This data is crucial for understanding search engine result page (SERP) trends, aiding in SEO optimization and content strategy development.
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

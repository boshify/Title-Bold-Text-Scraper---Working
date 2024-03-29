import streamlit as st
import pandas as pd
import requests
import json
from bs4 import BeautifulSoup
import time

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

    for attempt in range(5):  # Retry up to 5 times
        try:
            response = requests.get(url, params=params)
            if response.status_code == 429:  # Rate limit hit
                time.sleep(10)  # Wait for 10 seconds before retrying
                continue
            response.raise_for_status()  # Raise an exception for HTTP errors
            return json.loads(response.text)
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}, attempt {attempt + 1}/5")
            time.sleep(5)  # Wait for 5 seconds before retrying
    return {}  # Return an empty dictionary if all attempts fail

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

    # Initialize progress bar
    progress_bar = st.progress(0)
    total = len(df)

    for index, row in df.iterrows():
        query = row['Target Query']
        if pd.isna(query) or query.strip() == '':
            continue

        results = search(query, api_key, cse_id, country_code, language_code)

        if 'items' in results:
            for i in range(min(3, len(results['items']))):
                df.at[index, f'SERP Title {i+1}'] = results['items'][i].get('title', '')

            html_snippets = [item.get('htmlSnippet', '') for item in results['items']]
            df.at[index, 'Bold Text'] = extract_bold_text_from_snippets(html_snippets)
        # Update progress bar
        progress_bar.progress((index + 1) / total)

    # Ensure the progress bar reaches 100% once processing is complete
    progress_bar.progress(1.0)
    return df

# Streamlit app layout
def main():
    st.title("Title Meta Bold Text Scraper")
    st.markdown("""
    ## About the App
    *Upload a CSV with one column with the header row labeled "Target Query" then run it. It will provide the first three title tags and bold text from Google search results for that query.
    """)

    # Define countries and languages dictionaries
    countries = {
        "United States": "US",
        "United Kingdom": "GB",
        "Canada": "CA",
        "Australia": "AU",
        "India": "IN"
        # Add more countries and their codes here
    }

    languages = {
        "English": "lang_en",
        "Spanish": "lang_es",
        "French": "lang_fr",
        "German": "lang_de",
        "Chinese": "lang_zh"
        # Add more languages and their codes here
    }

    # Dropdown for selecting a country and a language
    selected_country = st.selectbox("Select a country for search", list(countries.keys()))
    selected_language = st.selectbox("Select a language for search", list(languages.keys()), index=0)

    # Input fields for API key and CSE ID
    api_key = st.text_input("Enter your Google API Key", type="password")
    cse_id = st.text_input("Enter your Custom Search Engine ID")

    uploaded_file = st.file_uploader("Upload your file", type=["csv"])

    if uploaded_file is not None:
        if st.button('Start Processing'):
            if api_key and cse_id:
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
            else:
                st.error("API Key or Custom Search Engine ID is missing.")

if __name__ == "__main__":
    main()

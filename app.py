import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

token = st.secrets["token_key"]

def get_recent_companies(days_back: int = 30, limit: int = 30, country: str = "DE") -> list:
    url = "https://connect.palturai.com/companies"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": token
    }

    founding_from = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    params = {
        "countryCode": country.upper(),
        "page": 0,
        "size": limit,
        "foundingDateFrom": founding_from
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch data: {response.status_code} - {response.text}")

    data = response.json()

    companies = []
    for company in data.get("content", []):
        companies.append({
            "Name": company.get("name"),
            "City": company.get("city"),
            "Founding Date": company.get("foundingDate"),
            "Status": company.get("status"),
            "Registration Number": company.get("officialRegistrationNumber"),
            "UUID": company.get("id"),
        })

    return companies

st.set_page_config(page_title="Recent Companies from Palturai", layout="wide")

st.title("🔍 Recent Companies from Palturai")

days_back = st.number_input("Days back", min_value=1, max_value=90, value=30)
limit = st.number_input("Number of results", min_value=1, max_value=100, value=30)
country = st.text_input("Country code (e.g. DE, AT, CH)", value="DE")

if st.button("Fetch Companies"):
    try:
        with st.spinner("Fetching data from Palturai..."):
            companies = get_recent_companies(days_back=days_back, limit=limit, country=country)
            df = pd.DataFrame(companies)

            if not df.empty:
                df["Founding Date"] = pd.to_datetime(df["Founding Date"], errors="coerce")
                df = df.sort_values("Founding Date", ascending=False)

                st.success(f"Found {len(df)} companies")
                st.dataframe(df)

                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"recent_companies_{country}_{days_back}d.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No companies found.")
    except Exception as e:
        st.error(f"Error: {e}")

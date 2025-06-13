import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

token = st.secrets["token_key"]

def get_recent_companies(days_back: int = 30, total_limit: int = 200, country: str = "DE") -> list:
    url = "https://connect.palturai.com/companies"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": token
    }

    founding_from = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    all_companies = []
    page = 0
    page_size = 100 

    while len(all_companies) < total_limit:
        params = {
            "countryCode": country.upper(),
            "page": page,
            "size": min(page_size, total_limit - len(all_companies)),
            "foundingDateFrom": founding_from
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise Exception(f"API error on page {page}: {response.status_code} - {response.text}")

        content = response.json().get("content", [])
        if not content:
            break

        for company in content:
            all_companies.append({
                "Name": company.get("name"),
                "City": company.get("city"),
                "Founding Date": company.get("foundingDate"),
                "Status": company.get("status"),
                "Registration Number": company.get("officialRegistrationNumber"),
                "UUID": company.get("id"),
            })

        page += 1

    return all_companies[:total_limit]

st.set_page_config(page_title="Recent Companies – Palturai", layout="wide")
st.title("📊 Recent Companies from Palturai")

days_back = st.number_input("Days back", min_value=1, max_value=90, value=30)
total_limit = st.number_input("Number of companies", min_value=1, max_value=1000, value=100)
country = st.text_input("Country code (e.g. DE, AT, CH)", value="DE")

if st.button("Fetch Companies"):
    try:
        with st.spinner("Fetching data from Palturai..."):
            companies = get_recent_companies(days_back=days_back, total_limit=total_limit, country=country)
            df = pd.DataFrame(companies)

            if not df.empty:
                df["Founding Date"] = pd.to_datetime(df["Founding Date"], errors="coerce")
                df = df.sort_values(by="Founding Date", ascending=False)

                df = df.reset_index(drop=True)
                df.index += 1
                #df.index.name = "No."

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

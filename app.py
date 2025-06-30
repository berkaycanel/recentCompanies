import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date, timedelta

def auth():
    username = st.secrets["username"]
    password = st.secrets["password"]
    params = {"systemName": "PHOENIX"}

    try:
        response = requests.get(
            "https://connect.palturai.com/authenticate",
            auth=HTTPBasicAuth(username, password),
            params=params
        )
        response.raise_for_status()

        return response.headers.get("Authorization")

    except Exception as e:
        print(f"Auth error: {e}")
        return None
        
token = auth()

def get_recent_companies(
    start_date: date,
    end_date: date,
    total_limit: int = 200,
    country: str = "DE"
) -> list:
    url = "https://connect.palturai.com/companies"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": token
    }

    founding_from = start_date.strftime("%Y-%m-%d")
    founding_to = end_date.strftime("%Y-%m-%d")

    all_companies = []
    page = 0
    page_size = 100

    while len(all_companies) < total_limit:
        params = {
            "countryCode": country.upper(),
            "page": page,
            "size": min(page_size, total_limit - len(all_companies)),
            "foundingDateFrom": founding_from,
            "foundingDateTo": founding_to
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

today = date.today()
default_start = today - timedelta(days=30)
start_date = st.date_input("Start date", value=default_start)
end_date = st.date_input("End date", value=today)

total_limit = st.number_input(
    "Number of companies", min_value=1, max_value=1000, value=100
)
country = st.text_input("Country code (e.g. DE, AT, CH)", value="DE")

if st.button("Fetch Companies"):
    if start_date > end_date:
        st.error("Start date must be on or before End date.")
    else:
        try:
            with st.spinner("Fetching data from Palturai..."):
                companies = get_recent_companies(
                    start_date=start_date,
                    end_date=end_date,
                    total_limit=total_limit,
                    country=country
                )
                df = pd.DataFrame(companies)

                if not df.empty:
                    df["Founding Date"] = pd.to_datetime(df["Founding Date"], errors="coerce")
                    df = df.sort_values(by="Founding Date", ascending=False)

                    df = df.reset_index(drop=True)
                    df.index += 1

                    st.success(f"Found {len(df)} companies")
                    st.dataframe(df)

                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"recent_companies_{country}_{start_date}_{end_date}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No companies found for the selected date range.")
        except Exception as e:
            st.error(f"Error: {e}")

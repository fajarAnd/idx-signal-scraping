from fastapi import FastAPI, Query
from curl_cffi import requests

app = FastAPI()

def fetch_historical_data(code: str, start_date: str, end_date: str):
    url = f"https://api.investing.com/api/financialdata/historical/{code}?start-date={start_date}&end-date={end_date}&time-frame=Daily&add-missing-rows=false"
    
    headers = {
        "host": "api.investing.com",
        "domain-id": "id",
        "referer": "https://investing.com",
        "origin": "https://investing.com",
    }
    
    try:
        r = requests.get(url, impersonate="chrome", headers=headers)
        return r.json()
    except Exception as e:
        return {"error": str(e)}
    
def search(symbol: str):
    url = f"https://api.investing.com/api/search/v2/search?q={symbol}"
    
    headers = {
        "host": "api.investing.com",
        "domain-id": "id",
        "referer": "https://investing.com",
        "origin": "https://investing.com",
    }
    
    try:
        r = requests.get(url, impersonate="chrome", headers=headers)
        return r.json()
    except Exception as e:
        return {"error": str(e)}
    
def get_code_symbol(search_response: dict) -> str | None:
    for quote in search_response.get("quotes", []):
        if quote.get("flag") == "Indonesia":
            return quote.get("id")
    return None

@app.get("/historical")
def get_historical_data(
    code: str = Query(..., description="Kode saham atau ID, misalnya 29049"),
    start_date: str = Query(..., description="Tanggal mulai format YYYY-MM-DD"),
    end_date: str = Query(..., description="Tanggal akhir format YYYY-MM-DD")
):
    return fetch_historical_data(code, start_date, end_date)


@app.get("/search")
def get_historical_data(
    q: str = Query(..., description="Kode saham atau ID, misalnya 29049"),
):
    return search(q)

@app.get("/get_code_symbol")
def get_code_and_symbol(
    symbol: str = Query(..., description="Kode saham atau ID, misalnya 29049"),
):
    search_response = search(symbol)
    code = get_code_symbol(search_response)
    if code:
        # Assuming the symbol can be extracted from the search response similarly to the code
        symbol_info = next((quote for quote in search_response.get("quotes", []) if quote.get("id") == code), None)
        symbol_name = symbol_info.get("symbol") if symbol_info else None
        return {"code": code, "symbol": symbol_name}
    else:
        return {"error": "No matching symbol found"}
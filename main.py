"""
IDX Signal Scraping API

A FastAPI application for fetching Indonesian stock market data from Investing.com API.
This service supports the IDX Signal V2 automation system by providing historical
stock data for technical analysis and trading signal generation.

Author: IDX Signal Team
Version: 1.0.0
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from curl_cffi import requests
import asyncio
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="IDX Signal Scraping API",
    description="API untuk mengambil data historis saham IDX dari Investing.com",
    version="1.0.0",
    contact={
        "name": "IDX Signal Team",
        "email": "support@idxsignal.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
BASE_URL = "https://api.investing.com/api"
DEFAULT_HEADERS = {
    "host": "api.investing.com",
    "domain-id": "id",
    "referer": "https://investing.com",
    "origin": "https://investing.com",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Pydantic Models
class HistoricalDataRequest(BaseModel):
    """Model for historical data request parameters"""
    code: str = Field(..., description="Stock code or ID (e.g., 29049 for BBRI)")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    time_frame: str = Field(default="Daily", description="Time frame (Daily, Weekly, Monthly)")
    
    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values:
            start = datetime.strptime(values['start_date'], '%Y-%m-%d')
            end = datetime.strptime(v, '%Y-%m-%d')
            if end < start:
                raise ValueError('End date must be after start date')
            if (end - start).days > 365:
                raise ValueError('Date range cannot exceed 365 days')
        return v

class SearchRequest(BaseModel):
    """Model for search request parameters"""
    query: str = Field(..., min_length=1, max_length=50, description="Search query for stock symbol")

class StockInfo(BaseModel):
    """Model for stock information"""
    code: str
    symbol: str
    name: str
    flag: str
    exchange: str

class APIResponse(BaseModel):
    """Standard API response model"""
    success: bool
    data: Optional[Union[Dict, List]] = None
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)

# Utility Functions
@lru_cache(maxsize=128)
def get_cached_search_result(symbol: str) -> Dict:
    """Cache search results to reduce API calls"""
    return _search_symbol(symbol)

def _search_symbol(symbol: str) -> Dict:
    """Internal search function"""
    url = f"{BASE_URL}/search/v2/search?q={symbol}"
    
    try:
        response = requests.get(url, impersonate="chrome", headers=DEFAULT_HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Search API error for symbol {symbol}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"External API error: {str(e)}"
        )

def _fetch_historical_data(code: str, start_date: str, end_date: str, time_frame: str = "Daily") -> Dict:
    """Internal function to fetch historical data"""
    url = f"{BASE_URL}/financialdata/historical/{code}"
    params = {
        "start-date": start_date,
        "end-date": end_date,
        "time-frame": time_frame,
        "add-missing-rows": "false"
    }
    
    try:
        response = requests.get(url, params=params, impersonate="chrome", headers=DEFAULT_HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Validate response data
        if not isinstance(data, dict) or 'data' not in data:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid response format from external API"
            )
        
        return data
    except requests.RequestException as e:
        logger.error(f"Historical data API error for code {code}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"External API error: {str(e)}"
        )

def extract_indonesia_stocks(search_response: Dict) -> List[StockInfo]:
    """Extract Indonesian stock information from search response"""
    stocks = []
    quotes = search_response.get("quotes", [])
    
    for quote in quotes:
        if quote.get("flag") == "Indonesia":
            try:
                stock = StockInfo(
                    code=quote.get("id", ""),
                    symbol=quote.get("symbol", ""),
                    name=quote.get("name", ""),
                    flag=quote.get("flag", ""),
                    exchange=quote.get("exchange", "")
                )
                stocks.append(stock)
            except Exception as e:
                logger.warning(f"Error parsing stock data: {e}")
                continue
    
    return stocks

def get_primary_stock_code(search_response: Dict) -> Optional[str]:
    """Get the primary stock code from search response (first Indonesian stock)"""
    for quote in search_response.get("quotes", []):
        if quote.get("flag") == "Indonesia":
            return quote.get("id")
    return None

# API Endpoints
@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint with API information"""
    return APIResponse(
        success=True,
        message="IDX Signal Scraping API - Ready to serve stock data",
        data={
            "version": "1.0.0",
            "endpoints": [
                "/historical - Get historical stock data",
                "/search - Search for stock symbols",
                "/stock-info - Get stock code and symbol information",
                "/health - Health check endpoint"
            ]
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/historical", response_model=APIResponse)
async def get_historical_data(
    code: str = Query(..., description="Stock code or ID (e.g., 29049 for BBRI)"),
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    time_frame: str = Query(default="Daily", description="Time frame: Daily, Weekly, Monthly")
):
    """
    Get historical stock data for a specific stock code.
    
    Parameters:
    - code: Stock ID from Investing.com (e.g., 29049 for BBRI)
    - start_date: Start date in YYYY-MM-DD format
    - end_date: End date in YYYY-MM-DD format  
    - time_frame: Data frequency (Daily, Weekly, Monthly)
    
    Returns:
    - Historical OHLCV data for the specified period
    """
    try:
        # Validate request
        request_data = HistoricalDataRequest(
            code=code,
            start_date=start_date,
            end_date=end_date,
            time_frame=time_frame
        )
        
        # Fetch data
        data = _fetch_historical_data(
            request_data.code,
            request_data.start_date,
            request_data.end_date,
            request_data.time_frame
        )
        
        return APIResponse(
            success=True,
            data=data,
            message=f"Historical data retrieved for code {code}"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in get_historical_data: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@app.get("/search", response_model=APIResponse)
async def search_stocks(
    q: str = Query(..., min_length=1, max_length=50, description="Search query for stock symbol")
):
    """
    Search for stock symbols and get basic information.
    
    Parameters:
    - q: Search query (stock symbol, name, or keyword)
    
    Returns:
    - List of matching stocks with their information
    """
    try:
        # Validate request
        search_request = SearchRequest(query=q)
        
        # Search for stocks
        search_response = get_cached_search_result(search_request.query.upper())
        
        # Extract Indonesian stocks
        indonesia_stocks = extract_indonesia_stocks(search_response)
        
        return APIResponse(
            success=True,
            data={
                "query": search_request.query,
                "total_results": len(indonesia_stocks),
                "stocks": [stock.dict() for stock in indonesia_stocks]
            },
            message=f"Found {len(indonesia_stocks)} Indonesian stocks matching '{q}'"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in search_stocks: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@app.get("/stock-info", response_model=APIResponse)
async def get_stock_info(
    symbol: str = Query(..., description="Stock symbol to get code and information")
):
    """
    Get stock code and detailed information for a given symbol.
    
    Parameters:
    - symbol: Stock symbol (e.g., BBRI, TLKM, GOTO)
    
    Returns:
    - Stock code, symbol, and detailed information
    """
    try:
        # Search for the symbol
        search_response = get_cached_search_result(symbol.upper())
        
        # Get primary stock code
        primary_code = get_primary_stock_code(search_response)
        
        if not primary_code:
            return APIResponse(
                success=False,
                message=f"No Indonesian stock found for symbol '{symbol}'"
            )
        
        # Extract all Indonesian stocks for additional info
        indonesia_stocks = extract_indonesia_stocks(search_response)
        primary_stock = next((stock for stock in indonesia_stocks if stock.code == primary_code), None)
        
        return APIResponse(
            success=True,
            data={
                "primary_code": primary_code,
                "symbol": symbol.upper(),
                "stock_info": primary_stock.dict() if primary_stock else None,
                "all_matches": [stock.dict() for stock in indonesia_stocks]
            },
            message=f"Stock information retrieved for symbol '{symbol}'"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in get_stock_info: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@app.get("/bulk-historical")
async def get_bulk_historical_data(
    codes: str = Query(..., description="Comma-separated stock codes (e.g., 29049,1034)"),
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    time_frame: str = Query(default="Daily", description="Time frame: Daily, Weekly, Monthly")
):
    """
    Get historical data for multiple stocks in a single request.
    
    Parameters:
    - codes: Comma-separated list of stock codes
    - start_date: Start date in YYYY-MM-DD format
    - end_date: End date in YYYY-MM-DD format
    - time_frame: Data frequency
    
    Returns:
    - Historical data for all requested stocks
    """
    try:
        code_list = [code.strip() for code in codes.split(",") if code.strip()]
        
        if len(code_list) > 20:  # Limit bulk requests
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 20 stocks per bulk request"
            )
        
        results = {}
        errors = {}
        
        for code in code_list:
            try:
                data = _fetch_historical_data(code, start_date, end_date, time_frame)
                results[code] = data
            except Exception as e:
                errors[code] = str(e)
                logger.warning(f"Failed to fetch data for code {code}: {e}")
        
        return APIResponse(
            success=True,
            data={
                "successful": results,
                "errors": errors,
                "summary": {
                    "total_requested": len(code_list),
                    "successful": len(results),
                    "failed": len(errors)
                }
            },
            message=f"Bulk historical data request completed: {len(results)}/{len(code_list)} successful"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in get_bulk_historical_data: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse(
            success=False,
            message=exc.detail,
            timestamp=datetime.now()
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=APIResponse(
            success=False,
            message="Internal server error occurred",
            timestamp=datetime.now()
        ).dict()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 
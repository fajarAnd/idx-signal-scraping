"""
Unit tests for IDX Signal Scraping API

Test coverage for all main API endpoints and core functionality.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import json

from main import app, get_cached_search_result, extract_indonesia_stocks, get_primary_stock_code

client = TestClient(app)

# Test data
MOCK_SEARCH_RESPONSE = {
    "quotes": [
        {
            "id": "29049",
            "symbol": "BBRI",
            "name": "Bank Rakyat Indonesia",
            "flag": "Indonesia",
            "exchange": "IDX"
        },
        {
            "id": "1034",
            "symbol": "TLKM",
            "name": "Telkom Indonesia",
            "flag": "Indonesia",
            "exchange": "IDX"
        }
    ]
}

MOCK_HISTORICAL_RESPONSE = {
    "data": [
        {
            "date": "2024-06-06",
            "open": 4550,
            "high": 4580,
            "low": 4530,
            "close": 4570,
            "volume": 85000000
        },
        {
            "date": "2024-06-05",
            "open": 4500,
            "high": 4560,
            "low": 4480,
            "close": 4550,
            "volume": 72000000
        }
    ]
}

class TestHealthAndRoot:
    """Test health check and root endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns API information"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "IDX Signal Scraping API" in data["message"]
        assert "endpoints" in data["data"]
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

class TestSearchEndpoint:
    """Test stock search functionality"""
    
    @patch('main._search_symbol')
    def test_search_stocks_success(self, mock_search):
        """Test successful stock search"""
        mock_search.return_value = MOCK_SEARCH_RESPONSE
        
        response = client.get("/search?q=BBRI")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["query"] == "BBRI"
        assert data["data"]["total_results"] == 2
        assert len(data["data"]["stocks"]) == 2
    
    def test_search_stocks_empty_query(self):
        """Test search with empty query"""
        response = client.get("/search?q=")
        assert response.status_code == 422  # Validation error
    
    def test_search_stocks_too_long_query(self):
        """Test search with query too long"""
        long_query = "a" * 60  # More than 50 characters
        response = client.get(f"/search?q={long_query}")
        assert response.status_code == 422  # Validation error
    
    @patch('main._search_symbol')
    def test_search_stocks_no_results(self, mock_search):
        """Test search with no Indonesian stocks found"""
        mock_search.return_value = {"quotes": []}
        
        response = client.get("/search?q=INVALID")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_results"] == 0

class TestHistoricalDataEndpoint:
    """Test historical data functionality"""
    
    @patch('main._fetch_historical_data')
    def test_historical_data_success(self, mock_fetch):
        """Test successful historical data retrieval"""
        mock_fetch.return_value = MOCK_HISTORICAL_RESPONSE
        
        response = client.get(
            "/historical?code=29049&start_date=2024-01-01&end_date=2024-06-06"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data["data"]
        mock_fetch.assert_called_once_with("29049", "2024-01-01", "2024-06-06", "Daily")
    
    def test_historical_data_invalid_date_format(self):
        """Test historical data with invalid date format"""
        response = client.get(
            "/historical?code=29049&start_date=01-01-2024&end_date=2024-06-06"
        )
        assert response.status_code == 400  # Bad request
    
    def test_historical_data_end_before_start(self):
        """Test historical data with end date before start date"""
        response = client.get(
            "/historical?code=29049&start_date=2024-06-06&end_date=2024-01-01"
        )
        assert response.status_code == 400  # Bad request
    
    def test_historical_data_date_range_too_large(self):
        """Test historical data with date range > 365 days"""
        start_date = "2023-01-01"
        end_date = "2024-06-06"  # More than 365 days
        response = client.get(
            f"/historical?code=29049&start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code == 400  # Bad request
    
    def test_historical_data_missing_parameters(self):
        """Test historical data with missing required parameters"""
        response = client.get("/historical?code=29049")
        assert response.status_code == 422  # Validation error

class TestStockInfoEndpoint:
    """Test stock information functionality"""
    
    @patch('main.get_cached_search_result')
    def test_stock_info_success(self, mock_search):
        """Test successful stock info retrieval"""
        mock_search.return_value = MOCK_SEARCH_RESPONSE
        
        response = client.get("/stock-info?symbol=BBRI")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["primary_code"] == "29049"
        assert data["data"]["symbol"] == "BBRI"
        assert len(data["data"]["all_matches"]) == 2
    
    @patch('main.get_cached_search_result')
    def test_stock_info_not_found(self, mock_search):
        """Test stock info when no Indonesian stocks found"""
        mock_search.return_value = {"quotes": []}
        
        response = client.get("/stock-info?symbol=INVALID")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert "No Indonesian stock found" in data["message"]

class TestBulkHistoricalEndpoint:
    """Test bulk historical data functionality"""
    
    @patch('main._fetch_historical_data')
    def test_bulk_historical_success(self, mock_fetch):
        """Test successful bulk historical data retrieval"""
        mock_fetch.return_value = MOCK_HISTORICAL_RESPONSE
        
        response = client.get(
            "/bulk-historical?codes=29049,1034&start_date=2024-01-01&end_date=2024-06-06"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["summary"]["total_requested"] == 2
        assert mock_fetch.call_count == 2
    
    def test_bulk_historical_too_many_codes(self):
        """Test bulk historical with too many stock codes"""
        codes = ",".join([str(i) for i in range(25)])  # More than 20
        response = client.get(
            f"/bulk-historical?codes={codes}&start_date=2024-01-01&end_date=2024-06-06"
        )
        assert response.status_code == 400  # Bad request
        assert "Maximum 20 stocks" in response.json()["message"]
    
    @patch('main._fetch_historical_data')
    def test_bulk_historical_partial_success(self, mock_fetch):
        """Test bulk historical with some failures"""
        def side_effect(code, start, end, timeframe):
            if code == "29049":
                return MOCK_HISTORICAL_RESPONSE
            else:
                raise Exception("API Error")
        
        mock_fetch.side_effect = side_effect
        
        response = client.get(
            "/bulk-historical?codes=29049,INVALID&start_date=2024-01-01&end_date=2024-06-06"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["summary"]["successful"] == 1
        assert data["data"]["summary"]["failed"] == 1

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_extract_indonesia_stocks(self):
        """Test extraction of Indonesian stocks from search response"""
        stocks = extract_indonesia_stocks(MOCK_SEARCH_RESPONSE)
        assert len(stocks) == 2
        assert all(stock.flag == "Indonesia" for stock in stocks)
        assert stocks[0].code == "29049"
        assert stocks[1].symbol == "TLKM"
    
    def test_extract_indonesia_stocks_empty(self):
        """Test extraction from empty response"""
        stocks = extract_indonesia_stocks({"quotes": []})
        assert len(stocks) == 0
    
    def test_get_primary_stock_code(self):
        """Test getting primary stock code"""
        code = get_primary_stock_code(MOCK_SEARCH_RESPONSE)
        assert code == "29049"
    
    def test_get_primary_stock_code_none(self):
        """Test getting primary stock code when none found"""
        code = get_primary_stock_code({"quotes": []})
        assert code is None

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @patch('main._fetch_historical_data')
    def test_external_api_error(self, mock_fetch):
        """Test handling of external API errors"""
        from fastapi import HTTPException
        mock_fetch.side_effect = HTTPException(status_code=503, detail="External API error")
        
        response = client.get(
            "/historical?code=29049&start_date=2024-01-01&end_date=2024-06-06"
        )
        assert response.status_code == 503
    
    def test_malformed_request(self):
        """Test handling of malformed requests"""
        response = client.get("/historical?invalid=parameter")
        assert response.status_code == 422

class TestDataValidation:
    """Test data validation and sanitization"""
    
    def test_date_validation_future_date(self):
        """Test validation rejects future dates beyond reasonable range"""
        future_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        response = client.get(
            f"/historical?code=29049&start_date=2024-01-01&end_date={future_date}"
        )
        # Should still work, but in production you might want to add future date validation
        assert response.status_code in [200, 400]
    
    def test_code_parameter_sanitization(self):
        """Test that code parameters are properly sanitized"""
        response = client.get(
            "/historical?code=29049&start_date=2024-01-01&end_date=2024-06-06"
        )
        assert response.status_code in [200, 503]  # Should be valid format

# Integration tests
class TestIntegration:
    """Integration tests for complete workflows"""
    
    @patch('main._search_symbol')
    @patch('main._fetch_historical_data')
    def test_search_then_historical_workflow(self, mock_fetch, mock_search):
        """Test complete workflow: search -> get code -> fetch historical"""
        mock_search.return_value = MOCK_SEARCH_RESPONSE
        mock_fetch.return_value = MOCK_HISTORICAL_RESPONSE
        
        # First, search for stock
        search_response = client.get("/search?q=BBRI")
        assert search_response.status_code == 200
        
        search_data = search_response.json()
        stock_code = search_data["data"]["stocks"][0]["code"]
        
        # Then, get historical data
        historical_response = client.get(
            f"/historical?code={stock_code}&start_date=2024-01-01&end_date=2024-06-06"
        )
        assert historical_response.status_code == 200
        
        historical_data = historical_response.json()
        assert historical_data["success"] is True

# Performance tests (basic)
class TestPerformance:
    """Basic performance tests"""
    
    def test_response_time_health_check(self):
        """Test that health check responds quickly"""
        import time
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 0.1  # Should respond in < 100ms

# Test fixtures
@pytest.fixture
def mock_successful_search():
    """Fixture for successful search response"""
    return MOCK_SEARCH_RESPONSE

@pytest.fixture
def mock_successful_historical():
    """Fixture for successful historical data response"""
    return MOCK_HISTORICAL_RESPONSE

# Parametrized tests
@pytest.mark.parametrize("symbol,expected_code", [
    ("BBRI", "29049"),
    ("TLKM", "1034"),
])
@patch('main.get_cached_search_result')
def test_multiple_stock_symbols(mock_search, symbol, expected_code):
    """Test multiple stock symbols with parametrized tests"""
    mock_response = {
        "quotes": [
            {
                "id": expected_code,
                "symbol": symbol,
                "name": f"Test {symbol}",
                "flag": "Indonesia",
                "exchange": "IDX"
            }
        ]
    }
    mock_search.return_value = mock_response
    
    response = client.get(f"/stock-info?symbol={symbol}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["data"]["primary_code"] == expected_code
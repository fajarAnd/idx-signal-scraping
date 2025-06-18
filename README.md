# IDX Signal Scraping API

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


## 📊 Tentang Proyek

Proyek ini merupakan bagian dari ekosistem **IDX Signal V2**, sistem rekomendasi trading saham berbasis analisis teknikal yang menggunakan:

- **Support/Resistance** (Pivot Points)
- **Simple Moving Average** (SMA-50)
- **Relative Strength Index** (RSI)
- **Volume Spike Analysis**
- **Risk/Reward Analysis** (Expectancy)

### 🎯 Tujuan

1. **Data Provider**: Menyediakan data historis saham IDX untuk analisis teknikal
2. **Automation Support**: Mendukung workflow otomatis N8N (Scheduler_Signal_IDX.json)
3. **Trading Journal**: Integrasi dengan sistem pencatatan trading untuk evaluasi performa
4. **Scalability**: API yang dapat menangani multiple requests untuk berbagai saham

## 🏗️ Arsitektur Sistem

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   N8N Workflow  │───▶│  IDX Signal API  │───▶│ Investing.com   │
│ (Scheduler)     │    │  (FastAPI)       │    │ API             │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       
         ▼                       ▼                       
┌─────────────────┐    ┌──────────────────┐              
│ Google Sheets   │    │ Postgress        │              
│ (Signal Results)│    │                  │              
└─────────────────┘    └──────────────────┘              
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip atau poetry untuk dependency management

### Installation

1. **Clone repository**
   ```bash
   git clone https://github.com/your-username/idx-signal-scraping.git
   cd idx-signal-scraping
   ```

2. **Setup virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # atau
   .venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Alternative Docs: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

## 📖 API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. 🔍 Search Stocks
```http
GET /search?q={symbol}
```

**Parameters:**
- `q` (string): Stock symbol atau keyword pencarian

**Example:**
```bash
curl "http://localhost:8000/search?q=BBRI"
```


#### 2. 📈 Historical Data
```http
GET /historical?code={code}&start_date={start}&end_date={end}
```

**Parameters:**
- `code` (string): Stock code dari Investing.com (contoh: 29049)
- `start_date` (string): Tanggal mulai (YYYY-MM-DD)
- `end_date` (string): Tanggal akhir (YYYY-MM-DD)
- `time_frame` (string): Daily, Weekly, Monthly (default: Daily)

**Example:**
```bash
curl "http://localhost:8000/historical?code=29049&start_date=2024-01-01&end_date=2024-06-06"
```



## ⚙️ Integration dengan IDX Signal V2

### N8N Workflow Integration

API ini dirancang untuk terintegrasi dengan N8N workflow (`Scheduler_Signal_IDX.json`):

1. **Scheduled Trigger**: Menjalankan analisis setiap minggu
2. **Data Fetching**: Mengambil data historis dari API ini
3. **Technical Analysis**: Menjalankan algoritma confluence scoring
4. **Signal Generation**: Menghasilkan rekomendasi trading
5. **Data Logging**: Menyimpan hasil ke Google Sheets

### Parameter Konfigurasi N8N

```json
{
  "intervalMonth": 4,
  "modalTersedia": 3300000,
  "scoreGreaterThan": 1,
  "MaxLoss": 200000
}
```


## 📁 Project Structure

```
idx-signal-scraping/
├── main.py                    # FastAPI application
├── requirements.txt           # Python dependencies
├── README.md                 # Documentation
├── .gitignore               # Git ignore rules
├── settings.json            # VS Code settings
├── tests/                   # Test files
│   ├── test_main.py         # API tests
│   └── test_utils.py        # Utility tests
├── config/                  # Configuration files
│   └── settings.py          # Application settings

```

## 🧪 Testing

### Unit Tests
```bash
pytest tests/ -v
```

### API Testing
```bash
# Test search endpoint
curl "http://localhost:8000/search?q=BBRI"

# Test historical data
curl "http://localhost:8000/historical?code=29049&start_date=2024-01-01&end_date=2024-06-06"

# Test health check
curl "http://localhost:8000/health"
```


## 🔧 Configuration

### Application Settings

```python
# config/settings.py
class Settings:
    API_TITLE = "IDX Signal Scraping API"
    API_VERSION = "1.0.0"
    RATE_LIMIT = 100  # requests per minute
    CACHE_TTL = 300   # 5 minutes
    MAX_BULK_STOCKS = 20
    MAX_DATE_RANGE = 365  # days
```

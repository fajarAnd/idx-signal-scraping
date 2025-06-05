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

### Algoritma Confluence Scoring

Sistem menggunakan 4+ indikator teknikal:

1. **Trend Analysis** (Close > SMA-50)
2. **RSI Oversold** (RSI < 40)
3. **Volume Spike** (Volume > 1.3x SMA-20)
4. **Support Cluster** (≥2 pivot low dalam ±1.5%)
5. **Empirical Bonus** (winRate > 65% & totalTrades ≥ 10)

### Action Recommendations

| Backtest Win Rate | Confluence Score | Rekomendasi |
|-------------------|------------------|-------------|
| ≥ 65%             | ≥ 3              | ✅ Sinyal kuat, entry penuh |
| 55% - 65%         | 2 - 3            | ⚠️ Entry sebagian atau tunggu konfirmasi |
| < 55%             | < 2              | ❌ Hindari atau watchlist saja |

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

### Load Testing
```bash
# Using Apache Bench
ab -n 100 -c 10 "http://localhost:8000/search?q=BBRI"
```



## 📊 Trading Journal Integration

API mendukung sistem Trading Journal untuk:

1. **Signal Tracking**: Mencatat setiap signal yang dihasilkan
2. **Performance Analysis**: Evaluasi akurasi prediksi
3. **Risk Management**: Monitoring exposure dan drawdown
4. **Historical Review**: Analisis performance jangka panjang

### Excel Integration

Trading Journal (Excel) mencakup:
- **Signal Log**: Record semua signal dengan timestamp
- **Performance Metrics**: Win rate, profit/loss, expectancy
- **Risk Analysis**: Drawdown analysis, position sizing
- **Market Analysis**: Sector performance, market conditions

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

### Rate Limiting

- Default: 100 requests per minute per IP
- Bulk endpoints: Lower limits
- Authentication: Higher limits for registered users

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add tests for new features
- Update documentation
- Use type hints
- Add logging for important operations

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check `/docs` endpoint
- **Issues**: Create GitHub issue
- **Email**: support@idxsignal.com
- **Discord**: [IDX Signal Community](https://discord.gg/idxsignal)

## 🔄 Changelog

### v1.0.0 (2025-06-06)
- Initial release
- Basic stock search and historical data
- N8N workflow integration
- Comprehensive error handling
- Bulk data endpoints
- Trading journal integration

### Planned Features

- [ ] Authentication & API keys
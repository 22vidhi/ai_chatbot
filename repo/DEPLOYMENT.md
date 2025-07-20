# Deployment Guide - Smart Invoice AI System

## ?? Quick Start

### Option 1: Local Development (Recommended for testing)

1. **Clone/Download the project to D:\repo**
2. **Install Python 3.8+** if not already installed
3. **Run the startup script:**
   - Windows: Double-click `start.bat`
   - Linux/Mac: `chmod +x start.sh && ./start.sh`
4. **Open browser:** http://localhost:8501

### Option 2: Manual Setup

```bash
# Navigate to project directory
cd D:\repo

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

## ?? Cloud Deployment

### Streamlit Cloud (Free)

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo>
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud:**
   - Go to https://share.streamlit.io/
   - Connect your GitHub account
   - Select your repository
   - Choose `app.py` as the main file
   - Click "Deploy"

3. **Your app will be available at:**
   `https://share.streamlit.io/[username]/[repo-name]/main/app.py`

### Hugging Face Spaces (Free)

1. **Create a new Space:**
   - Go to https://huggingface.co/spaces
   - Click "Create new Space"
   - Choose "Streamlit" as the SDK

2. **Upload files:**
   - Upload all project files
   - Ensure `app.py` is in the root directory
   - Hugging Face will automatically detect `requirements.txt`

3. **Your app will be available at:**
   `https://huggingface.co/spaces/[username]/[space-name]`

### Railway (Free tier available)

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Deploy:**
   ```bash
   railway login
   railway init
   railway up
   ```

### Heroku

1. **Create Procfile:**
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

2. **Deploy:**
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

## ?? Docker Deployment

### Build and Run Locally

```bash
# Build the image
docker build -t smart-invoice-ai .

# Run the container
docker run -p 8501:8501 smart-invoice-ai
```

### Docker Compose

Create `docker-compose.yml`:
```yaml
version: "3.8"
services:
  app:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./database:/app/database
      - ./models:/app/models
```

Run with:
```bash
docker-compose up
```

## ?? Configuration

### Environment Variables

Create `.env` file:
```
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_THEME_BASE=light
OCR_LANGUAGE=eng
CONFIDENCE_THRESHOLD=0.7
```

### Custom Configuration

Edit `config.yaml` to customize:
- OCR settings
- Field extraction patterns
- UI preferences
- Performance settings

## ?? Production Considerations

### Performance Optimization

1. **Enable caching:**
   ```python
   @st.cache_data
   def expensive_function():
       # Your code here
   ```

2. **Use session state for large objects:**
   ```python
   if "model" not in st.session_state:
       st.session_state.model = load_model()
   ```

### Security

1. **File upload limits:**
   - Max file size: 10MB (configurable)
   - Allowed extensions: PDF, PNG, JPG, CSV, TXT
   - File validation enabled

2. **Database security:**
   - SQLite with proper permissions
   - Input sanitization
   - SQL injection protection

### Monitoring

1. **Health checks:**
   - Built-in Streamlit health endpoint: `/_stcore/health`
   - Custom health check in Dockerfile

2. **Logging:**
   - Application logs in `logs/app.log`
   - Error tracking and reporting
   - Performance metrics

## ?? Troubleshooting

### Common Issues

1. **Import errors:**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

2. **Tesseract not found:**
   - Windows: Install from https://github.com/UB-Mannheim/tesseract/wiki
   - Linux: `sudo apt-get install tesseract-ocr`
   - Mac: `brew install tesseract`

3. **Port already in use:**
   ```bash
   streamlit run app.py --server.port 8502
   ```

4. **Memory issues:**
   - Reduce batch size in config
   - Enable garbage collection
   - Use smaller models

### Debug Mode

Enable debug mode in `config.yaml`:
```yaml
app:
  debug: true
```

Or set environment variable:
```bash
export STREAMLIT_DEBUG=true
```

## ?? Performance Benchmarks

### Expected Performance

- **Processing time:** 2-5 seconds per invoice
- **Memory usage:** ~200MB base + ~50MB per concurrent user
- **Accuracy:** 85%+ for standard invoice formats
- **Throughput:** 100+ invoices per batch

### Scaling

For high-volume processing:
1. Use Docker with multiple replicas
2. Implement queue-based processing
3. Consider GPU acceleration for OCR
4. Use external database (PostgreSQL)

## ?? Updates and Maintenance

### Updating the Application

1. **Pull latest changes:**
   ```bash
   git pull origin main
   ```

2. **Update dependencies:**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

3. **Restart the application**

### Database Maintenance

1. **Backup database:**
   ```bash
   cp database/invoice_system.db database/backup_$(date +%Y%m%d).db
   ```

2. **Clean old data:**
   - Use the admin interface
   - Or run cleanup scripts

### Model Updates

1. **Retrain models** with new data
2. **Version control** for model files
3. **A/B testing** for model performance

---

**Need help?** Create an issue in the GitHub repository or check the troubleshooting section.


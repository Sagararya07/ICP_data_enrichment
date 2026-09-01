import os
import subprocess
import pandas as pd
from io import BytesIO
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load env vars for DB
load_dotenv()

from database.db_operations import db_ops

app = FastAPI(title="Lumora Enrichment Web")

# Serve static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup():
    # Initialize DB pool for status queries
    await db_ops.connect()
    app.state.pool = db_ops.pool

@app.on_event("shutdown")
async def shutdown():
    await db_ops.close()

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)):
    is_csv = file.filename.endswith('.csv')
    is_excel = file.filename.endswith('.xlsx') or file.filename.endswith('.xls')
    
    if not (is_csv or is_excel):
        raise HTTPException(status_code=400, detail="Only CSV or Excel (.xlsx) files are allowed.")
    
    # Read the uploaded file into pandas
    contents = await file.read()
    try:
        if is_csv:
            df = pd.read_csv(BytesIO(contents))
        else:
            df = pd.read_excel(BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid file format: {str(e)}")

    # We want to smartly map columns if they uploaded a raw export
    column_mapping = {
        'Company Name': 'company_name',
        'Website': 'website',
        'Email': 'email',
        'Corporate Phone': 'phone',
        '# Employees': 'employees',
        'Annual Revenue': 'revenue',
        'City': 'location',
        'Company Linkedin Url': 'social_media'
    }
    
    # Rename matching columns
    df = df.rename(columns=column_mapping)
    
    # Ensure required columns exist
    if 'company_name' not in df.columns or 'website' not in df.columns:
        raise HTTPException(
            status_code=400, 
            detail="CSV must contain at least 'company_name' and 'website' columns."
        )

    # Clean data: drop empty websites and drop duplicates
    df = df.dropna(subset=['website'])
    df = df.drop_duplicates(subset=['website'])

    # Save to a temporary file
    os.makedirs('data', exist_ok=True)
    temp_path = 'data/web_upload.csv'
    df.to_csv(temp_path, index=False)

    # Call the existing load_csv script to insert into DB
    result = subprocess.run(['python', 'scripts/load_csv.py', temp_path], capture_output=True, text=True)
    
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Database insertion failed: {result.stderr}")

    return {"message": f"Successfully loaded {len(df)} unique companies into the database!"}

@app.post("/api/enrich")
async def start_enrichment(background_tasks: BackgroundTasks):
    # Run the enrichment engine as a background process so the request doesn't block
    def run_engine():
        subprocess.run(['python', 'scripts/run_enrichment.py'])

    background_tasks.add_task(run_engine)
    return {"message": "Enrichment engine started."}

@app.get("/api/status")
async def get_status():
    if not app.state.pool:
        raise HTTPException(status_code=500, detail="Database not connected.")
    
    stats = await db_ops.get_processing_stats()
    return stats

@app.get("/api/export")
async def export_csv(fit_status: str = None):
    if not app.state.pool:
        raise HTTPException(status_code=500, detail="Database not connected.")
    
    leads = await db_ops.get_enriched_leads(fit_status)
    if not leads:
        raise HTTPException(status_code=404, detail="No enriched leads found.")
        
    df = pd.DataFrame(leads)
    
    # Save to memory buffer
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    filename = f"lumora_leads_{fit_status.lower().replace(' ', '_')}.csv" if fit_status else "lumora_leads_all.csv"
    
    # Write to a temp file and return FileResponse to make downloading easier in FastAPI
    os.makedirs('data', exist_ok=True)
    temp_path = f"data/{filename}"
    df.to_csv(temp_path, index=False)
    
    return FileResponse(temp_path, media_type="text/csv", filename=filename)

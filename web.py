import os
import asyncio
import pandas as pd
from io import BytesIO
from scripts.load_csv import load as load_csv_data
from main import EnrichmentEngine
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, FileResponse
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
    os.makedirs('/tmp', exist_ok=True)
    temp_path = '/tmp/web_upload.csv'
    df.to_csv(temp_path, index=False)

    # Call the imported load function directly to insert into DB
    try:
        await load_csv_data(temp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database insertion failed: {str(e)}")

    return {"message": f"Successfully loaded {len(df)} unique companies into the database!"}

async def run_enrichment_task():
    engine = EnrichmentEngine()
    await engine.run()

@app.post("/api/enrich")
async def start_enrichment(background_tasks: BackgroundTasks):
    # Run the enrichment engine as a background process so the request doesn't block
    background_tasks.add_task(run_enrichment_task)
    return {"message": "Enrichment engine started."}

@app.get("/api/status")
async def get_status():
    if not app.state.pool:
        error_msg = db_ops.last_error or "Unknown database error"
        raise HTTPException(status_code=500, detail=f"Database not connected. Error: {error_msg}")
    
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
    
    from io import StringIO
    
    # Save to memory buffer
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    filename = f"lumora_leads_{fit_status.lower().replace(' ', '_')}.csv" if fit_status and fit_status != 'All' else "lumora_leads_all.csv"
    
    return Response(
        content=csv_buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

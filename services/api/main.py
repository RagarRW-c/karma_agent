from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import os

from .db import check_db_connection
from services.api.routers.products import router as products_router
from services.api.routers.shops import router as shops_router
from services.api.routers.shop_products import router as shop_products_router
from services.api.routers.analytics import router as analytics_router
from services.api.routers.ai_agent import router as ai_agent_router


app = FastAPI(
    title="Cat Food Price Agent API",
    version="0.3.0",
    description="🤖 AI-Powered autonomous cat food price monitoring with Claude API.",
)


class HealthResponse(BaseModel):
    status: str
    services: List[str]
    ai_agent: str


class DBHealthResponse(BaseModel):
    status: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    ai_configured = "configured" if os.getenv("ANTHROPIC_API_KEY") else "not_configured"
    
    return HealthResponse(
        status="ok",
        services=["api", "scraper", "celery", "ai-agent"],
        ai_agent=ai_configured
    )


@app.get("/db-health", response_model=DBHealthResponse)
async def db_health_check():
    """Database health check"""
    ok = check_db_connection()
    return DBHealthResponse(status="ok" if ok else "error")


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard HTML"""
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    
    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r", encoding="utf-8") as f:
            return f.read()
    
    # Fallback if dashboard.html doesn't exist
    ai_status = "✅ Configured" if os.getenv("ANTHROPIC_API_KEY") else "❌ Not Configured"
    
    return f"""
    <html>
        <head>
            <title>🤖 Karma Agent - AI Edition</title>
            <style>
                body {{ 
                    font-family: Arial; 
                    text-align: center; 
                    padding: 50px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }}
                .container {{
                    background: white;
                    color: #333;
                    padding: 40px;
                    border-radius: 20px;
                    max-width: 800px;
                    margin: 0 auto;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                }}
                h1 {{ color: #667eea; }}
                a {{
                    display: inline-block;
                    margin: 10px;
                    padding: 15px 30px;
                    background: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 10px;
                    font-weight: bold;
                }}
                a:hover {{ background: #764ba2; }}
                .status {{ 
                    padding: 20px; 
                    background: #f0f0f0; 
                    border-radius: 10px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Karma Agent - AI Edition</h1>
                <p style="font-size: 1.2em;">Autonomous cat food price monitoring with Claude AI</p>
                
                <div class="status">
                    <h3>🎯 AI Agent Status</h3>
                    <p>{ai_status}</p>
                </div>
                
                <hr style="margin: 30px 0;">
                
                <h2>📚 Available Endpoints:</h2>
                <div>
                    <a href="/docs">📖 API Documentation (Swagger)</a>
                    <a href="/health">🏥 Health Check</a>
                </div>
                
                <h3 style="margin-top: 30px;">🤖 AI Agent Features:</h3>
                <div>
                    <a href="/docs#/ai-agent/autonomous_search_ai_agent_search_post">🔍 Autonomous Search</a>
                    <a href="/docs#/ai-agent/auto_add_product_ai_agent_auto_add_post">🚀 Auto-Add Product</a>
                    <a href="/ai-agent/status">✓ Agent Status</a>
                </div>
                
                <h3 style="margin-top: 30px;">📊 Analytics:</h3>
                <div>
                    <a href="/analytics/current-prices">💰 Current Prices</a>
                    <a href="/analytics/best-deals">🔥 Best Deals</a>
                </div>
                
                <p style="margin-top: 40px; color: #666;">
                    Dashboard HTML not installed. Copy dashboard.html to services/api/
                </p>
            </div>
        </body>
    </html>
    """


# Register routers
app.include_router(products_router)
app.include_router(shops_router)
app.include_router(shop_products_router)
app.include_router(analytics_router)
app.include_router(ai_agent_router)  # 🤖 NEW: AI Agent router

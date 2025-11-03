# main.py
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import crud
from database import connect_to_mongo, close_mongo_connection

app = FastAPI(title="Balatro Joker Arena", description="Compare jokers with ELO")

# Add CORS middleware to allow external image loading
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates
templates = Jinja2Templates(directory="templates")

# Mount static files (for CSS/JS if needed)
# app.mount("/static", StaticFiles(directory="static"), name="static")


# Setup templates
templates = Jinja2Templates(directory="templates")

# Mount static files (for CSS/JS if needed)
# app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    # The connection function will raise an exception if it fails
    print("Application startup completed successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()


@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """Homepage with card comparison interface"""
    try:
        card_count = await crud.get_card_count()
        if card_count < 2:
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "message": "Not enough cards in database. Please add at least 2 cards."}
            )

        card1, card2 = await crud.get_random_card_pair()
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "card1": card1, "card2": card2}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compare")
async def compare_cards(winner_id: str = Form(...), loser_id: str = Form(...)):
    """Handle card comparison submission"""
    try:
        comparison = await crud.update_card_ratings(winner_id, loser_id)
        return {"success": True, "message": "Comparison recorded successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard(request: Request):
    """Leaderboard page showing top-rated cards"""
    try:
        cards = await crud.get_leaderboard()
        return templates.TemplateResponse(
            "leaderboard.html",
            {"request": request, "cards": cards}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cards")
async def get_cards():
    """API endpoint to get all cards"""
    try:
        cards = await crud.get_all_cards()
        return {"cards": cards}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cards")
async def create_card(name: str = Form(...), image_url: str = Form(...), description: str = Form("")):
    """API endpoint to create a new card"""
    try:
        card = await crud.create_card(name, image_url, description or "No description available")
        return {"success": True, "card_id": str(card.id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/leaderboard")
async def api_leaderboard(limit: int = 20):
    """API endpoint for leaderboard data"""
    try:
        cards = await crud.get_leaderboard(limit=limit)
        return {"cards": cards}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

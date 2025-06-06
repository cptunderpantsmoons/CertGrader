"""
PokéCertify FastAPI Backend

Main API implementation for card upload, verification, trading, and collection retrieval.

Author: PokéCertify Team
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import uuid
import base64
import logging
try:
    import modal  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    modal = None
from datetime import datetime
import os

# Import shared config if available
try:
    from src.shared.config import API_URL, DB_PATH, MODAL_GRADER_STUB, MODAL_GRADER_OBJ
except ImportError:
    API_URL = os.getenv("POKECERTIFY_API_URL", "http://localhost:8000")
    DB_PATH = os.getenv("POKECERTIFY_DB_PATH", "pokecertify.db")
    MODAL_GRADER_STUB = os.getenv("MODAL_GRADER_STUB", "card-grader")
    MODAL_GRADER_OBJ = os.getenv("MODAL_GRADER_OBJ", "CardGrader")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PokéCertify API")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict this!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Modal client using the updated API. Lookups may fail in offline
# environments (e.g. during unit tests) so fall back to a dummy object that is
# easily patchable.
try:  # pragma: no cover - external dependency
    if modal is None:
        raise RuntimeError("Modal SDK not available")
    stub = modal.App.lookup(MODAL_GRADER_STUB)
    grader = modal.Function.lookup(MODAL_GRADER_STUB, "grade_card")
except Exception as exc:  # fallback for tests
    logger.warning("Modal lookup failed: %s", exc)

    class _DummyGrader:
        async def remote(self, *_args, **_kwargs):
            raise RuntimeError("Modal not available")

    grader = _DummyGrader()

def get_db_connection():
    """Create a new SQLite database connection."""
    try:
        db_path = os.getenv("POKECERTIFY_DB_PATH", DB_PATH)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection failed")

@app.post("/upload")
async def upload_card(
    file: UploadFile = File(...),
    card_name: str = Form(""),
    card_info: str = Form(""),
    owner: str = Form(""),
):
    """
    Upload a card image, grade it, and store the result.
    """
    try:
        # Validate inputs
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        if not all([card_name, owner]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Read and encode image
        image_bytes = await file.read()
        image_b64 = f"data:image/{file.content_type.split('/')[-1]};base64,{base64.b64encode(image_bytes).decode('utf-8')}"
        
        # Grade the image using Modal
        grading_result = await grader.remote(image_b64)
        if grading_result["status"] != "success":
            raise HTTPException(status_code=500, detail=f"Grading failed: {grading_result['error_message']}")
        
        # Generate unique card ID
        card_id = str(uuid.uuid4())
        
        # Store in database
        conn = get_db_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO cards (id, owner, card_name, card_info, grade, estimated_value, image_path, date_added)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        card_id,
                        owner,
                        card_name,
                        card_info,
                        grading_result["grade"],
                        None,  # Estimated value (for future TCG API integration)
                        image_b64,  # Store base64 for previews
                        datetime.utcnow().isoformat()
                    )
                )
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Card ID already exists")
        finally:
            conn.close()
        
        logger.info(f"Card uploaded: {card_id}, Grade: {grading_result['grade']}")
        return {
            "card_id": card_id,
            "grade": grading_result["grade"],
            "confidence": grading_result["confidence"],
            "card_name": card_name,
            "card_info": card_info,
            "owner": owner,
            "date_added": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/card/{card_id}")
async def get_card(card_id: str):
    """Retrieve card details by ID for verification."""
    try:
        conn = get_db_connection()
        try:
            card = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
            if not card:
                raise HTTPException(status_code=404, detail="Card not found")
            
            return {
                "card_id": card["id"],
                "owner": card["owner"],
                "card_name": card["card_name"],
                "card_info": card["card_info"],
                "grade": card["grade"],
                "estimated_value": card["estimated_value"],
                "image_path": card["image_path"],
                "date_added": card["date_added"]
            }
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving card: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")

@app.post("/trade")
async def trade_card(card_id: str = Form(""), to_owner: str = Form("")):
    """
    Transfer card ownership and log the trade.
    """
    try:
        if not to_owner:
            raise HTTPException(status_code=400, detail="Missing to_owner")
        
        conn = get_db_connection()
        try:
            # Verify card exists and get current owner
            card = conn.execute("SELECT owner FROM cards WHERE id = ?", (card_id,)).fetchone()
            if not card:
                raise HTTPException(status_code=404, detail="Card not found")
            
            # Update card owner
            with conn:
                conn.execute(
                    "UPDATE cards SET owner = ? WHERE id = ?",
                    (to_owner, card_id)
                )
                # Log the trade
                conn.execute(
                    """
                    INSERT INTO trades (card_id, from_owner, to_owner, trade_date)
                    VALUES (?, ?, ?, ?)
                    """,
                    (card_id, card["owner"], to_owner, datetime.utcnow().isoformat())
                )
            
            logger.info(f"Card {card_id} traded from {card['owner']} to {to_owner}")
            return {
                "card_id": card_id,
                "from_owner": card["owner"],
                "to_owner": to_owner,
                "trade_date": datetime.utcnow().isoformat()
            }
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing trade: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Trade failed: {str(e)}")

@app.get("/collection/{owner}")
async def get_collection(owner: str):
    """
    Retrieve all cards owned by a user.
    """
    try:
        conn = get_db_connection()
        try:
            cards = conn.execute("SELECT * FROM cards WHERE owner = ?", (owner,)).fetchall()
            return [
                {
                    "card_id": card["id"],
                    "card_name": card["card_name"],
                    "card_info": card["card_info"],
                    "grade": card["grade"],
                    "image_path": card["image_path"],
                    "owner": card["owner"],
                    "date_added": card["date_added"]
                } for card in cards
            ]
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving collection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Collection retrieval failed: {str(e)}")
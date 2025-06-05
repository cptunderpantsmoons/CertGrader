"""
PokéCertify Shared Configuration

Centralizes configuration for API URLs, DB paths, Modal, and NFT settings.
All components should import from this module for consistency.

Author: PokéCertify Team
"""

import os

# Backend API URL (used by frontend and other services)
API_URL = os.getenv("POKECERTIFY_API_URL", "http://localhost:8000")

# Database path (used by backend/db/utils.py and FastAPI)
DB_PATH = os.getenv("POKECERTIFY_DB_PATH", "pokecertify.db")

# Modal Labs configuration
MODAL_GRADER_STUB = os.getenv("MODAL_GRADER_STUB", "card-grader")
MODAL_GRADER_OBJ = os.getenv("MODAL_GRADER_OBJ", "CardGrader")

# NFT/Polygon/Alchemy configuration
ALCHEMY_URL = os.getenv("ALCHEMY_URL", "https://polygon-mumbai.g.alchemy.com/v2/YOUR_API_KEY")
NFT_CONTRACT_ADDRESS = os.getenv("NFT_CONTRACT_ADDRESS", "YOUR_CONTRACT_ADDRESS")
NFT_MINTER_PRIVATE_KEY = os.getenv("NFT_MINTER_PRIVATE_KEY", "YOUR_PRIVATE_KEY")
NFT_CONTRACT_ABI_PATH = os.getenv("NFT_CONTRACT_ABI_PATH", "contract_abi.json")
"""
PokéCertify NFT Minter

This module provides a function to mint NFTs for graded cards on the Polygon testnet using Web3.py and Alchemy.

Author: PokéCertify Team
"""

import os
import json
import logging
from web3 import Web3

# Load configuration from environment or shared config
ALCHEMY_URL = os.getenv("ALCHEMY_URL", "https://polygon-mumbai.g.alchemy.com/v2/YOUR_API_KEY")
CONTRACT_ADDRESS = os.getenv("NFT_CONTRACT_ADDRESS", "YOUR_CONTRACT_ADDRESS")
PRIVATE_KEY = os.getenv("NFT_MINTER_PRIVATE_KEY", "YOUR_PRIVATE_KEY")
CONTRACT_ABI_PATH = os.getenv("NFT_CONTRACT_ABI_PATH", "contract_abi.json")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pokecertify.nft")

def load_contract_abi():
    """Load contract ABI from file."""
    with open(CONTRACT_ABI_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def mint_nft(card_id: str, owner: str):
    """
    Mint an NFT for a graded card on Polygon testnet.

    Args:
        card_id: Unique card ID (string)
        owner: Owner's wallet address (string)
    Returns:
        dict: Transaction hash or error
    """
    try:
        w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))
        if not w3.is_connected():
            raise Exception("Failed to connect to Polygon testnet")

        contract_abi = load_contract_abi()
        contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=contract_abi)
        account = w3.eth.account.from_key(PRIVATE_KEY)

        # Build transaction
        nonce = w3.eth.get_transaction_count(account.address)
        tx = contract.functions.mintNFT(owner, card_id).build_transaction({
            "from": account.address,
            "nonce": nonce,
            "gas": 200000,
            "gasPrice": w3.to_wei("20", "gwei")
        })

        # Sign and send transaction
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        logger.info(f"NFT minted for card {card_id}: {tx_hash.hex()}")
        return {"tx_hash": tx_hash.hex(), "status": "success"}

    except Exception as e:
        logger.error(f"Error minting NFT: {str(e)}")
        return {"status": "error", "error_message": str(e)}

if __name__ == "__main__":
    # Example usage
    import sys
    if len(sys.argv) != 3:
        print("Usage: python nft_minter.py <card_id> <owner_wallet_address>")
    else:
        result = mint_nft(sys.argv[1], sys.argv[2])
        print(result)
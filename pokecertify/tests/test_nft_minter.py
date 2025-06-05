import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/nft")))
from src.nft import nft_minter

class DummyContractFunction:
    def __init__(self):
        self.called = False
        self.args = None
    def build_transaction(self, tx_args):
        self.called = True
        self.args = tx_args
        return {"tx": "dummy_tx"}

class DummyContract:
    def __init__(self):
        self.functions = self
        self.mintNFT_func = DummyContractFunction()
    def mintNFT(self, owner, card_id):
        self.mintNFT_func.args = (owner, card_id)
        return self.mintNFT_func

class DummyWeb3:
    def __init__(self, connected=True):
        self._connected = connected
        self.eth = self
        self.account = self
        self._nonce = 42
        self._signed = False
        self._sent = False
    def is_connected(self):
        return self._connected
    def contract(self, address, abi):
        return DummyContract()
    def get_transaction_count(self, address):
        return self._nonce
    def sign_transaction(self, tx, private_key):
        self._signed = True
        return type("SignedTx", (), {"rawTransaction": b"dummy_raw_tx"})
    def send_raw_transaction(self, raw_tx):
        self._sent = True
        class DummyHash:
            def hex(self):
                return "0xdeadbeef"
        return DummyHash()
    def to_wei(self, value, unit):
        return 20000000000

@pytest.fixture
def patch_web3(monkeypatch):
    dummy_w3 = DummyWeb3()
    monkeypatch.setattr(nft_minter, "w3", dummy_w3)
    monkeypatch.setattr(nft_minter, "CONTRACT_ABI", [])
    monkeypatch.setattr(nft_minter, "CONTRACT_ADDRESS", "0x123")
    monkeypatch.setattr(nft_minter, "PRIVATE_KEY", "dummy")
    monkeypatch.setattr(nft_minter, "ACCOUNT", type("Account", (), {"address": "0xabc"})())
    return dummy_w3

def test_mint_nft_success(patch_web3):
    result = nft_minter.mint_nft("card-uuid", "0xowner")
    assert result["status"] == "success"
    assert result["tx_hash"] == "0xdeadbeef"

def test_mint_nft_not_connected(monkeypatch):
    dummy_w3 = DummyWeb3(connected=False)
    monkeypatch.setattr(nft_minter, "w3", dummy_w3)
    monkeypatch.setattr(nft_minter, "CONTRACT_ABI", [])
    monkeypatch.setattr(nft_minter, "CONTRACT_ADDRESS", "0x123")
    monkeypatch.setattr(nft_minter, "PRIVATE_KEY", "dummy")
    monkeypatch.setattr(nft_minter, "ACCOUNT", type("Account", (), {"address": "0xabc"})())
    result = nft_minter.mint_nft("card-uuid", "0xowner")
    assert result["status"] == "error"
    assert "Failed to connect" in result["error_message"]

def test_mint_nft_contract_error(monkeypatch):
    class FailingWeb3(DummyWeb3):
        def contract(self, address, abi):
            raise Exception("Contract error")
    dummy_w3 = FailingWeb3()
    monkeypatch.setattr(nft_minter, "w3", dummy_w3)
    monkeypatch.setattr(nft_minter, "CONTRACT_ABI", [])
    monkeypatch.setattr(nft_minter, "CONTRACT_ADDRESS", "0x123")
    monkeypatch.setattr(nft_minter, "PRIVATE_KEY", "dummy")
    monkeypatch.setattr(nft_minter, "ACCOUNT", type("Account", (), {"address": "0xabc"})())
    result = nft_minter.mint_nft("card-uuid", "0xowner")
    assert result["status"] == "error"
    assert "Contract error" in result["error_message"]
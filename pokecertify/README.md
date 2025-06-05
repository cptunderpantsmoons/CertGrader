# PokéCertify

**AI-powered Pokémon card grading, certification, and trading platform.**

---

## Features

- **AI Grading:** Upload card images for instant grading using a ResNet-50 model (Modal Labs GPU inference).
- **Digital Certification:** Generate PDF certificates with QR codes for card authenticity and grade verification.
- **Ownership & Trading:** Track card ownership, transfer cards, and maintain a trade history.
- **NFT Minting (Optional):** Mint graded cards as NFTs on Polygon testnet (Web3/Alchemy integration).
- **Modern UI:** Gradio-based frontend for uploads, verification, trading, and collection management.
- **Robust API:** FastAPI backend with async endpoints and SQLite (MVP) or PostgreSQL (production).
- **Extensive Testing:** Pytest-based suite for backend, Modal, NFT, and integration tests.
- **Interactive Management:** CLI script for test runs and environment initialisation.

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/your-org/pokecertify.git
cd pokecertify
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2. Initialise Environment

```bash
python scripts/manage.py
# Choose "2. Initialise environment only"
```

This will set up the database and check Modal model readiness.

### 3. Run the Backend API

```bash
uvicorn src/backend/api/main:app --reload
```

### 4. Run the Gradio Frontend

```bash
python src/frontend/app.py
```

### 5. Run Tests

```bash
python scripts/manage.py
# Choose "1. Run all tests"
```

---

## API Reference

### Base URL

```
http://localhost:8000
```

### Endpoints

#### `POST /upload`

Upload a card image for grading and storage.

- **Request:** `multipart/form-data`
    - `file`: Image file (required)
    - `card_name`: Card name (required)
    - `card_info`: Card info (optional)
    - `owner`: Owner identifier (required)
- **Response:** JSON
    - `card_id`, `grade`, `confidence`, `card_name`, `card_info`, `owner`, `date_added`

#### `GET /card/{card_id}`

Retrieve card details by ID.

- **Response:** JSON
    - `card_id`, `owner`, `card_name`, `card_info`, `grade`, `estimated_value`, `image_path`, `date_added`

#### `POST /trade`

Transfer card ownership and log the trade.

- **Request:** `application/json`
    - `card_id`: Card ID (required)
    - `to_owner`: New owner identifier (required)
- **Response:** JSON
    - `card_id`, `from_owner`, `to_owner`, `trade_date`

#### `GET /collection/{owner}`

Get all cards owned by a user.

- **Response:** JSON array of cards

---

## Advanced Deployment

### Docker Compose

A `docker-compose.yml` is provided for local multi-service setup.

```bash
docker-compose up --build
```

- **Backend:** Exposed on port 8000
- **Frontend:** Exposed on port 7860 (Gradio)
- **Database:** SQLite (default) or configure for PostgreSQL

### Production

- **Database:** Migrate to PostgreSQL for concurrency and reliability.
- **Secrets:** Use environment variables or a secrets manager for sensitive data.
- **ASGI Server:** Use Gunicorn/Uvicorn with multiple workers.
- **Reverse Proxy:** Use Nginx or Caddy for SSL and routing.
- **Modal:** Deploy grader with `modal deploy src/backend/modal_grader/modal_grader.py`.
- **Monitoring:** Integrate with Prometheus/Grafana or similar for metrics.

### Modal Model Training

To train or retrain the grading model:

```bash
python src/backend/modal_grader/train_modal_model.py --data_dir ./data/cards --output card_grader_model.pth
```

- Expects `train/` and `val/` subdirectories with class folders.
- For Modal Labs, use `modal run src/backend/modal_grader/train_modal_model.py`.

---

## Developer Guide

### Project Structure

```
pokecertify/
├── src/
│   ├── backend/
│   │   ├── api/           # FastAPI backend
│   │   ├── db/            # DB schema, utils
│   │   └── modal_grader/  # Modal AI grading & training
│   ├── frontend/          # Gradio UI
│   ├── nft/               # NFT minting logic
│   └── shared/            # Shared config/utilities
├── tests/                 # Pytest test suite
├── scripts/               # Init, deploy, manage scripts
├── Dockerfile.*           # Docker support
├── docker-compose.yml
├── requirements.txt
├── README.md
└── .env.example
```

### Environment Variables

Copy `.env.example` to `.env` and fill in required values for DB, Modal, Alchemy, etc.

### Testing

- All core modules are covered by tests in `tests/`.
- Use `python scripts/manage.py` for interactive test running.
- Integration tests require the backend to be running.

### Linting & Formatting

- Use `black`, `flake8`, and `isort` for code style.
- Run `black .` and `flake8 .` before PRs.

### Adding Features

- Fork and clone the repo.
- Create a feature branch.
- Add tests for new features.
- Submit a PR with a clear description.

### Modal Model

- Update `src/backend/modal_grader/train_modal_model.py` for new grading classes or architectures.
- Deploy new weights to Modal as needed.

### NFT Minting

- Configure `src/nft/nft_minter.py` with your contract address, ABI, and Alchemy API key.
- Mint NFTs for graded cards via backend or UI (optional).

---

## License

MIT License. See [LICENSE](LICENSE).

---

## Acknowledgements

- [Modal Labs](https://modal.com/) for serverless GPU inference.
- [Gradio](https://gradio.app/) for rapid UI prototyping.
- [Web3.py](https://web3py.readthedocs.io/) for blockchain integration.

---

## Contact

For issues, open a GitHub issue or contact the maintainers.
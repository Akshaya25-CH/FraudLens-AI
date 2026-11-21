
import sys
from pathlib import Path
from typing import Optional

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib

from backend.url_scanner import analyze_url_structure
from backend.upi_scanner import analyze_payment_fraud


app = FastAPI(
    title="FraudLens AI",
    description="Machine Learning Based Financial Scam, URL Phishing & UPI Fraud Detection",
    version="2.2.0"
)


# CORS middleware
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load the SMS model when its artifact is available.
# Public source releases may exclude model weights pending licensing review.
MODEL_PATH = BASE_DIR / "models" / "sms_model.joblib"

model = None

if MODEL_PATH.is_file():
    try:
        model = joblib.load(MODEL_PATH)
        print("SMS detection model loaded successfully.")
    except Exception as exc:
        print(f"WARNING: SMS model could not be loaded: {exc}")
else:
    print(
        "WARNING: SMS model unavailable. "
        "URL and UPI scanners remain available."
    )


# Request models
class ScanRequest(BaseModel):
    message: str


class UrlScanRequest(BaseModel):
    url: str


class PaymentScanRequest(BaseModel):
    message: str = ""
    upi_id: Optional[str] = None


# Home endpoint
@app.get("/")
def home():
    return {
        "message": "FraudLens AI Backend is running!",
        "modules": [
            (
                "SMS Fraud Detection (ML: TF-IDF + Logistic Regression)"
                if model is not None
                else "SMS Fraud Detection (Model artifact unavailable)"
            ),
            "URL Phishing Scanner (Structural & Lexical Heuristic Analysis)",
            "UPI & Payment Fraud Detection (Heuristic Rule-Based Engine)"
        ],
        "version": "2.2.0"
    }


# Health endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "modules": {
            "sms_scanner": (
                "TF-IDF + Logistic Regression"
                if model is not None
                else "Unavailable - model artifact not installed"
            ),
            "url_scanner": "Structural Heuristic Rule-Based Engine",
            "payment_scanner": "UPI & Payment Fraud Heuristic Engine"
        },
        "version": "2.2.0"
    }


# ---------------------------------------------------------------------------
# SMS Fraud Detection Endpoint
# ---------------------------------------------------------------------------
@app.post("/scan")
def scan_message(request: ScanRequest):
    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )

    if model is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "SMS scanning is unavailable because the model "
                "artifact is not installed."
            )
        )

    prediction = int(model.predict([message])[0])
    probabilities = model.predict_proba([message])[0]

    fraud_index = list(model.classes_).index(1)
    fraud_score = round(
        float(probabilities[fraud_index]) * 100, 2
    )

    if prediction == 1:
        risk_level = "POTENTIAL_FRAUD"
        explanation = (
            "The message exhibits language patterns and keywords strongly correlated "
            "with financial scam or phishing attempts."
        )
        recommendation = (
            "Be cautious. Do not share OTPs, PINs or passwords. "
            "Verify through official channels."
        )
    else:
        risk_level = "NO_FRAUD_PATTERN_DETECTED"
        explanation = (
            "The model did not identify strong fraud patterns in the text. "
            "However, always remain vigilant with unverified communications."
        )
        recommendation = (
            "The model did not identify a strong fraud pattern. "
            "This does not guarantee the message is safe."
        )

    return {
        "prediction": prediction,
        "risk_level": risk_level,
        "model_score": fraud_score,
        "explanation": explanation,
        "reasons": [explanation],
        "recommendation": recommendation
    }


# ---------------------------------------------------------------------------
# URL Phishing Scanner Endpoint
# ---------------------------------------------------------------------------
@app.post("/scan-url")
def scan_url(request: UrlScanRequest):
    raw_url = request.url.strip()

    if not raw_url:
        raise HTTPException(
            status_code=400,
            detail="URL cannot be empty"
        )

    analysis_result = analyze_url_structure(raw_url)
    return analysis_result


# ---------------------------------------------------------------------------
# UPI & Payment Fraud Detection Endpoint
# ---------------------------------------------------------------------------
@app.post("/scan-payment")
def scan_payment(request: PaymentScanRequest):
    msg = (request.message or "").strip()
    vpa = (request.upi_id or "").strip() if request.upi_id else None

    if not msg and not vpa:
        raise HTTPException(
            status_code=400,
            detail=(
                "Please provide payment message text or a UPI ID "
                "to analyze."
            )
        )

    analysis_result = analyze_payment_fraud(msg, vpa)
    return analysis_result


# Run the application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )

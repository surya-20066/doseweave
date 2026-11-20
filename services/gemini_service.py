"""
DoseWeave - Multimodal Gemini AI Service
Provides vision-based prescription OCR parsing, educational summarization,
and interactive patient Q&A.
Strictly scoped for educational comprehension and text understanding — not numerical risk prediction.
"""

import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List
from PIL import Image
from utils.logging_config import logger

load_dotenv()

GEMINI_MODEL_NAME = "gemini-3.6-flash"

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

PRESCRIPTION_SYSTEM_PROMPT = """
You are DoseWeave, an educational clinical prescription assistant.
Carefully inspect the uploaded prescription image.
Extract only the information that is clearly legible on the prescription.

Provide your response in the following structured clinical format:

### 1. 📋 INFORMATION EXTRACTED FROM PRESCRIPTION
- **Patient Details (if visible):**
- **Prescriber / Clinic Details (if visible):**
- **Date (if visible):**

**Identified Medications:**
For each identified medication:
- **Medicine Name:**
- **Generic / Active Ingredient (if legible):**
- **Strength (e.g. 500mg, 10mg):**
- **Prescribed Dosage:**
- **Frequency (e.g. Once daily, BID):**
- **Duration:**
- **Special Instructions (e.g. Take with food):**

### 2. 📚 GENERAL EDUCATIONAL INFORMATION
For each clearly identified medicine above, explain in plain, neutral language:
- **General Clinical Purpose:**
- **Typical Common Side Effects:**
- **Standard Precautions:**

### 3. ⚠️ INFORMATION REQUIRING VERIFICATION
Explicitly list any abbreviations, ambiguous handwriting, dosage uncertainties, or unclear drug names that must be confirmed with a licensed pharmacist or prescribing physician.

### 4. 🩺 SAFETY DISCLAIMER
State clearly that this analysis is an educational AI transcription aid and does not constitute medical advice or a verified clinical prescription audit.
"""

QA_SYSTEM_PROMPT = """
You are DoseWeave, an educational healthcare assistant helping a patient understand their uploaded prescription image.
Answer the user's specific inquiry using only the legible content from the prescription and well-established clinical pharmacology reference facts.

IMPORTANT SAFETY GUARDRAILS:
- Do not make clinical diagnoses.
- Do not prescribe new drugs or alter existing dosages.
- Do not instruct patients to abruptly stop medications without medical guidance.
- If text is ambiguous, explicitly state that pharmacist verification is required.
- Maintain a reassuring, objective, professional tone.
"""

class GeminiService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self.model = None
        self.configuration_error = None
        self._initialize_model()

    def set_api_key(self, api_key: str):
        self.api_key = api_key
        self._initialize_model()

    def _initialize_model(self):
        self.configuration_error = None
        if not GENAI_AVAILABLE or not self.api_key:
            self.model = None
            return
        if self.api_key.startswith(("ya29.", "1//")):
            self.model = None
            self.configuration_error = (
                "GOOGLE_API_KEY contains an OAuth token. Use a Gemini API key from "
                "https://aistudio.google.com/apikey instead."
            )
            logger.error(self.configuration_error)
            return
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(GEMINI_MODEL_NAME)
            logger.info(f"Initialized Gemini vision model: {GEMINI_MODEL_NAME}.")
        except Exception as e:
            logger.error(f"Could not initialize {GEMINI_MODEL_NAME}: {e}")
            self.model = None

    def is_available(self) -> bool:
        return self.model is not None

    def analyze_prescription(self, image: Image.Image) -> Optional[str]:
        """Runs multimodal image parsing on uploaded prescription image."""
        if not self.is_available():
            if self.configuration_error:
                return f"Error processing prescription image: {self.configuration_error}"
            logger.error("Gemini API is not configured or available.")
            return None
        try:
            response = self.model.generate_content([PRESCRIPTION_SYSTEM_PROMPT, image])
            return response.text
        except Exception as e:
            logger.error(f"Error during Gemini prescription analysis: {e}")
            return f"Error processing prescription image: {str(e)}"

    def answer_prescription_question(self, image: Image.Image, question: str) -> Optional[str]:
        """Answers contextual questions about the scanned prescription."""
        if not self.is_available():
            return None
        try:
            prompt = f"{QA_SYSTEM_PROMPT}\n\nPatient Question: {question}\n\nPlease provide a clear, concise educational explanation."
            response = self.model.generate_content([prompt, image])
            return response.text
        except Exception as e:
            logger.error(f"Error answering prescription question: {e}")
            return f"Error retrieving answer: {str(e)}"

# Singleton instance
gemini_service = GeminiService()

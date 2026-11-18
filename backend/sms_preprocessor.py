"""
FraudLens AI — Multilingual SMS Preprocessor
============================================
A scikit-learn-compatible transformer for multilingual Indian SMS normalization.
Handles English, Hinglish, and Devanagari Hindi with context-preserving entity placeholders.
"""

import re
import unicodedata
from typing import Any, Iterable, List, Union
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class MultilingualSMSPreprocessor(BaseEstimator, TransformerMixin):
    """
    Scikit-learn compatible transformer for multilingual SMS text normalization.

    Features:
    - NFC Unicode normalization preserving Devanagari matras, halants, and conjuncts.
    - Entity normalization to privacy-safe semantic tokens ([PHONE], [URL], [AMOUNT], etc.).
    - Strict regex execution ordering preventing partial or destructive overwrites.
    - Idempotent and safe against missing/null inputs.
    """

    # Recommended token pattern for downstream TfidfVectorizer.
    # Preserves bracketed entity tokens like [phone], [url], [amount] as atomic features,
    # and extracts Devanagari words without treating danda (। / ॥) as word letters.
    TOKEN_PATTERN = r"(?u)\[[a-zA-Z_]+\]|[\u0901-\u0963\u0966-\u097F\w]{2,}"

    def __init__(
        self,
        normalize_unicode: bool = True,
        normalize_entities: bool = True,
    ):
        self.normalize_unicode = normalize_unicode
        self.normalize_entities = normalize_entities
        self._compile_regexes()

    def _compile_regexes(self):
        """Compiles regex patterns in strict order of execution."""
        # 1. URLs
        self._url_pattern = re.compile(
            r'https?://[^\s<>"]+|www\.[^\s<>"]+',
            re.IGNORECASE
        )

        # 2. Toll-Free numbers (8 to 11 digits starting with 1800 or 1860, contiguous or separated by spaces/hyphens)
        self._tollfree_pattern = re.compile(
            r'(?<!\d)(?:1800|1860)(?:[-\s]\d{2,4}[-\s]\d{3,4}|[-\s]\d{2}[-\s]\d{2}[-\s]\d{2}|[-\s]?\d{4}|[-\s]?\d{6,8})(?!\d)'
        )

        # 3. Monetary amounts (Prefix or suffix in English/Devanagari, e.g., Rs 1,450, INR 500, रु 500, 850 रुपये)
        self._amount_pattern = re.compile(
            r'(?:(?:\b(?:रुपये|रु|Rs\.?|INR|₹)\s*[\d,]+(?:\.\d{1,2})?)|'
            r'(?:\b[\d,]+(?:\.\d{1,2})?\s*(?:रुपये|रु|rupees|Rs\.?|\/-)))(?!\w)',
            re.IGNORECASE
        )

        # 4. Masked Card Identifiers (preserves preceding context 'Credit Card', 'Debit Card', 'कार्ड')
        self._card_pattern = re.compile(
            r'(\b(?:Credit\s+Card|Debit\s+Card|Card|कार्ड)\s+(?:ending\s*(?:with\s*)?)?)(?:XX|\*+)?\d{4,}\b',
            re.IGNORECASE
        )

        # 5. Masked Account Identifiers (preserves preceding context 'A/C', 'Account', 'खाता')
        self._account_pattern = re.compile(
            r'(\b(?:A/C|A/c|a/c|account|acct|खाता)\s+(?:ending\s*(?:with\s*)?)?)(?:XX|\*+)?\d{3,}\b',
            re.IGNORECASE
        )

        # 6. Standalone masked account numbers like XX5821 or ****4821
        self._generic_masked_acc = re.compile(
            r'\b(?:XX|\*{2,})\d{3,}\b',
            re.IGNORECASE
        )

        # 7. Indian Vehicle Registration Plates (e.g. DL04CQ9102, MH02DE4819, HR-26-BQ-8192)
        self._vehicle_pattern = re.compile(
            r'\b[A-Z]{2}[-\s]?\d{2}[-\s]?[A-Z]{1,3}[-\s]?\d{4}\b'
        )

        # 8. Mobile Phone Numbers (10 digits starting with 6-9, optional +91, 91, or 0 prefix)
        self._phone_pattern = re.compile(
            r'(?<!\d)(?:\+91[-\s]?|91[-\s]?|0)?[6-9]\d{9}(?!\d)'
        )

        # 9. Devanagari sentence terminators (danda and double danda)
        self._danda_pattern = re.compile(r'[।॥]')

        # 10. Whitespace cleanup
        self._whitespace_pattern = re.compile(r'\s+')

    def clean_single(self, text: Any) -> str:
        """Normalizes a single text string."""
        if text is None:
            return ""

        # Handle pandas NA or float nan
        if isinstance(text, float) and np.isnan(text):
            return ""

        if not isinstance(text, str):
            text = str(text)

        text = text.strip()
        if not text:
            return ""

        # 1. Unicode NFC Normalization
        if self.normalize_unicode:
            text = unicodedata.normalize('NFC', text)

        # 2. Devanagari Punctuation separation
        text = self._danda_pattern.sub(' ', text)

        # 3. Entity Normalization (Strict Order)
        if self.normalize_entities:
            # 3a. URLs -> [URL]
            text = self._url_pattern.sub('[URL]', text)

            # 3b. Toll-Free numbers -> [TOLLFREE]
            text = self._tollfree_pattern.sub('[TOLLFREE]', text)

            # 3c. Monetary amounts -> [AMOUNT]
            text = self._amount_pattern.sub('[AMOUNT]', text)

            # 3d. Masked card identifiers -> [CARD]
            text = self._card_pattern.sub(r'\1[CARD]', text)

            # 3e. Masked account identifiers -> [ACCOUNT]
            text = self._account_pattern.sub(r'\1[ACCOUNT]', text)

            # 3f. Standalone masked tokens -> [ACCOUNT]
            text = self._generic_masked_acc.sub('[ACCOUNT]', text)

            # 3g. Vehicle plates -> [VEHICLE]
            text = self._vehicle_pattern.sub('[VEHICLE]', text)

            # 3h. Mobile numbers -> [PHONE]
            text = self._phone_pattern.sub('[PHONE]', text)

        # 4. Collapse whitespace
        text = self._whitespace_pattern.sub(' ', text).strip()
        return text

    def fit(self, X: Any, y: Any = None):
        """Fit method (stateless, returns self)."""
        return self

    def transform(self, X: Union[str, Iterable[Any]]) -> List[str]:
        """
        Transforms an input string, list, numpy array, or pandas Series of texts.

        Returns:
            List[str]: Cleaned, normalized strings.
        """
        # If single string passed directly
        if isinstance(X, str):
            return [self.clean_single(X)]

        # Handle iterables (Series, ndarray, list)
        if isinstance(X, (pd.Series, np.ndarray, list, tuple)):
            return [self.clean_single(item) for item in X]

        # Generic fallback
        return [self.clean_single(item) for item in X]

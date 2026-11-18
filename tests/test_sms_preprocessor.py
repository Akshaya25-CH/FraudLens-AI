import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from sms_preprocessor import MultilingualSMSPreprocessor


class TestSMSPreprocessorNormalization(unittest.TestCase):
    """Tests entity normalization and regex execution ordering."""

    def setUp(self):
        self.prep = MultilingualSMSPreprocessor()

    def test_url_normalization(self):
        msg = "Update KYC at https://sbi-portal.test/update or www.icici-login.test immediately."
        res = self.prep.clean_single(msg)
        self.assertIn("[URL]", res)
        self.assertNotIn("https://", res)
        self.assertNotIn("www.", res)
        self.assertEqual("Update KYC at [URL] or [URL] immediately.", res)

    def test_phone_normalization(self):
        msg = "Contact nodal officer at 9876543210 or +91 9123456789."
        res = self.prep.clean_single(msg)
        self.assertEqual("Contact nodal officer at [PHONE] or [PHONE].", res)

    def test_tollfree_normalization(self):
        # Retain existing contiguous toll-free test
        msg = "Call customer care at 1800112211 or 18002008 for dispute."
        res = self.prep.clean_single(msg)
        self.assertEqual("Call customer care at [TOLLFREE] or [TOLLFREE] for dispute.", res)

        # Regression tests for grouped and separated toll-free formats
        cases = [
            ("1800 11 2211", "[TOLLFREE]"),
            ("1800 2008", "[TOLLFREE]"),
            ("1860 123 4567", "[TOLLFREE]"),
            ("1800-11-2211", "[TOLLFREE]"),
            ("Call us on 1800 11 2211 for help", "Call us on [TOLLFREE] for help")
        ]
        for original, expected in cases:
            cleaned = self.prep.clean_single(original)
            self.assertEqual(expected, cleaned)

    def test_monetary_amount_normalization(self):
        cases = [
            ("debited by Rs 1,450.00 on 15-Nov", "debited by [AMOUNT] on 15-Nov"),
            ("paid INR 500 at Store", "paid [AMOUNT] at Store"),
            ("बकाया बिल रु 1,150 जमा करें", "बकाया बिल [AMOUNT] जमा करें"),
            ("850.00 रुपये से डेबिट हुआ", "[AMOUNT] से डेबिट हुआ"),
            ("Total fare 250 rupees paid", "Total fare [AMOUNT] paid")
        ]
        for original, expected in cases:
            res = self.prep.clean_single(original)
            self.assertEqual(expected, res)

    def test_masked_account_and_card_normalization(self):
        msg1 = "A/C ending with 4821 has been debited."
        res1 = self.prep.clean_single(msg1)
        self.assertEqual("A/C ending with [ACCOUNT] has been debited.", res1)

        msg2 = "Credit Card XX4019 spent at Netflix."
        res2 = self.prep.clean_single(msg2)
        self.assertEqual("Credit Card [CARD] spent at Netflix.", res2)

        msg3 = "Aapka khata XX9012 hold par hai."
        res3 = self.prep.clean_single(msg3)
        self.assertEqual("Aapka khata [ACCOUNT] hold par hai.", res3)

    def test_vehicle_plate_normalization(self):
        msg = "Challan registered for vehicle DL04CQ9102 and MH02DE4819."
        res = self.prep.clean_single(msg)
        self.assertEqual("Challan registered for vehicle [VEHICLE] and [VEHICLE].", res)

    def test_context_words_preservation(self):
        msg = "Dear customer, your A/C ending 4821 debited by Rs 1,200. Call 1800112211 if not you."
        res = self.prep.clean_single(msg)
        self.assertIn("Dear customer", res)
        self.assertIn("A/C ending [ACCOUNT]", res)
        self.assertIn("debited by [AMOUNT]", res)
        self.assertIn("Call [TOLLFREE] if not you", res)


class TestUnicodeAndDevanagariPreservation(unittest.TestCase):
    """Tests Devanagari Hindi and NFC Unicode handling."""

    def setUp(self):
        self.prep = MultilingualSMSPreprocessor()

    def test_devanagari_phrases(self):
        phrases = [
            ("आपका बैंक खाता XX5821 ब्लॉक होगा।", "आपका बैंक खाता [ACCOUNT] ब्लॉक होगा"),
            ("विद्युत आपूर्ति शाखा: बिल जमा करें।", "विद्युत आपूर्ति शाखा: बिल जमा करें"),
            ("कृपया तुरंत संपर्क करें।", "कृपया तुरंत संपर्क करें"),
        ]
        for inp, expected_prefix in phrases:
            res = self.prep.clean_single(inp)
            self.assertIn(expected_prefix, res)
            self.assertTrue(any('\u0900' <= char <= '\u097F' for char in res))

    def test_hinglish_phrases(self):
        cases = [
            ("aapka khata turant block hoga", "aapka khata turant block hoga"),
            ("UPI PIN enter karein to receive money", "UPI PIN enter karein to receive money"),
        ]
        for inp, expected in cases:
            res = self.prep.clean_single(inp)
            self.assertIn(expected, res)


class TestEdgeCasesAndSafety(unittest.TestCase):
    """Tests safety, idempotency, and boundary conditions."""

    def setUp(self):
        self.prep = MultilingualSMSPreprocessor()

    def test_missing_and_empty_inputs(self):
        self.assertEqual(self.prep.clean_single(None), "")
        self.assertEqual(self.prep.clean_single(""), "")
        self.assertEqual(self.prep.clean_single("   "), "")
        self.assertEqual(self.prep.clean_single(float('nan')), "")

    def test_idempotency(self):
        msg = "Call 9876543210 or visit https://sbi.test for Rs 500 on A/C XX4821."
        first_pass = self.prep.clean_single(msg)
        second_pass = self.prep.clean_single(first_pass)
        third_pass = self.prep.clean_single(second_pass)

        self.assertEqual(first_pass, "Call [PHONE] or visit [URL] for [AMOUNT] on A/C [ACCOUNT].")
        self.assertEqual(first_pass, second_pass)
        self.assertEqual(second_pass, third_pass)

    def test_iterable_inputs(self):
        inputs_list = ["Call 9876543210", "Visit https://bank.test"]
        res_list = self.prep.transform(inputs_list)
        self.assertEqual(res_list, ["Call [PHONE]", "Visit [URL]"])

        inputs_series = pd.Series(["A/C XX1234", "Rs 500"])
        res_series = self.prep.transform(inputs_series)
        self.assertEqual(res_series, ["A/C [ACCOUNT]", "[AMOUNT]"])


class TestScikitLearnCompatibilityAndTokenization(unittest.TestCase):
    """Tests scikit-learn Pipeline integration and token pattern vocabulary verification."""

    def test_pipeline_integration_and_features(self):
        corpus = [
            "Call [PHONE] at [URL] for [AMOUNT] on [ACCOUNT].",
            "आपका बैंक खाता तुरंत ब्लॉक किया जाएगा।",
            "विद्युत आपूर्ति शाखा: बकाया बिल जमा करें।",
            "कृपया तुरंत संपर्क करें।",
            "aapka khata turant block hoga.",
            "UPI PIN enter karein to receive payment."
        ]

        pipe = Pipeline([
            ("preprocessor", MultilingualSMSPreprocessor()),
            ("tfidf", TfidfVectorizer(
                token_pattern=MultilingualSMSPreprocessor.TOKEN_PATTERN,
                lowercase=True
            ))
        ])

        X = pipe.fit_transform(corpus)
        vocab = list(pipe.named_steps["tfidf"].get_feature_names_out())

        # 1. Non-zero feature matrix
        self.assertEqual(X.shape[0], len(corpus))
        self.assertGreater(X.nnz, 0)

        # 2. Required entity placeholders
        self.assertIn("[phone]", vocab)
        self.assertIn("[url]", vocab)
        self.assertIn("[amount]", vocab)
        self.assertIn("[account]", vocab)

        # 3. Required Devanagari vocabulary
        self.assertIn("आपका", vocab)
        self.assertIn("बैंक", vocab)
        self.assertIn("खाता", vocab)
        self.assertIn("विद्युत", vocab)
        self.assertIn("आपूर्ति", vocab)
        self.assertIn("कृपया", vocab)
        self.assertIn("तुरंत", vocab)
        self.assertIn("संपर्क", vocab)
        self.assertIn("करें", vocab)

        # 4. Required Hinglish vocabulary
        self.assertIn("aapka", vocab)
        self.assertIn("khata", vocab)
        self.assertIn("turant", vocab)
        self.assertIn("block", vocab)
        self.assertIn("hoga", vocab)
        self.assertIn("upi", vocab)
        self.assertIn("pin", vocab)
        self.assertIn("enter", vocab)
        self.assertIn("karein", vocab)


if __name__ == "__main__":
    unittest.main()

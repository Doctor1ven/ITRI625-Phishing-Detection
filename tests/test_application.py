"""Integration checks against trained artifacts, including notebook/API parity."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

import numpy as np
from fastapi.testclient import TestClient

from api.main import create_app
from desktop.app import request_prediction
from src.inference import PhishingDetector

ROOT = Path(__file__).resolve().parents[1]


class ApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.detector = PhishingDetector()
        cls.reference = json.loads((ROOT / 'reports/inference_reference.json').read_text())

    def test_notebook_artifact_prediction_parity(self):
        for row in self.reference:
            result = self.detector.predict(row['text'])
            self.assertAlmostEqual(result['phishing_probability'], row['p_phishing'], places=6)
            self.assertEqual(result['prediction'], 'phishing' if row['p_phishing'] >= 0.5 else 'legitimate')
            self.assertAlmostEqual(result['confidence'], max(row['p_phishing'], 1-row['p_phishing']), places=6)

    def test_explanation_matches_independent_token_removal(self):
        text = self.reference[0]['text']
        result = self.detector.predict(text)
        tokens = self.detector.word_analyser(text)
        self.assertGreater(len(result['indicators']), 0)
        for item in result['indicators']:
            altered = ' '.join(token for token in tokens if token != item['term'])
            p = self.detector.pipeline.predict_proba([altered])[0, 1]
            self.assertAlmostEqual(item['probability_drop'], result['phishing_probability']-p, places=6)
        np.testing.assert_allclose(self.detector.vectorizer.transform([text]).toarray(),
                                   self.detector.vectorizer.transform([' '.join(tokens)]).toarray())

    def test_no_known_vocabulary_warning(self):
        self.assertIsNotNone(self.detector.predict('zzzzunknownqqqq')['warning'])
        self.assertIsNotNone(self.detector.predict('!!!')['warning'])

    def test_api_valid_and_invalid_inputs(self):
        with TestClient(create_app()) as client:
            self.assertEqual(client.get('/health').status_code, 200)
            detector_id = id(client.app.state.detector)
            for row in self.reference:
                response = client.post('/predict', json={'text': row['text']})
                self.assertEqual(response.status_code, 200)
                self.assertAlmostEqual(response.json()['phishing_probability'], row['p_phishing'], places=6)
            self.assertEqual(id(client.app.state.detector), detector_id)
            for payload in [{}, {'text': ''}, {'text': ' \n\t'}, {'text': None}, {'text': 4}, {'text': 'x'*100001}]:
                self.assertEqual(client.post('/predict', json=payload).status_code, 422)
            self.assertEqual(client.post('/predict', json={'text': 'meeting report', 'explain': False}).json()['indicators'], [])
            with patch.object(client.app.state.detector, 'predict', side_effect=RuntimeError('internal error')):
                response = client.post('/predict', json={'text': 'hello world'})
                self.assertEqual(response.status_code, 500)
                self.assertNotIn('internal error', response.text)

    def test_missing_model_is_reported(self):
        with tempfile.TemporaryDirectory() as directory, TestClient(create_app(directory)) as client:
            self.assertEqual(client.get('/health').status_code, 503)
            self.assertFalse(client.get('/health').json()['model_loaded'])
            self.assertEqual(client.post('/predict', json={'text': 'hello world'}).status_code, 503)

    def test_desktop_malformed_response(self):
        for payload in [[], {'prediction': 'phishing', 'confidence': 0.9}]:
            response = Mock()
            response.json.return_value = payload
            with patch('desktop.app.requests.post', return_value=response):
                with self.assertRaisesRegex(RuntimeError, 'invalid response'):
                    request_prediction('hello world')

    def test_desktop_network_errors(self):
        import requests
        for error, expected in [(requests.ConnectionError(), 'API unavailable'), (requests.Timeout(), 'timed out')]:
            with patch('desktop.app.requests.post', side_effect=error):
                with self.assertRaisesRegex(RuntimeError, expected):
                    request_prediction('hello world')


if __name__ == '__main__':
    unittest.main(verbosity=2)

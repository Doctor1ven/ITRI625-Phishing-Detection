"""Load the notebook's exact Pipeline and provide reusable inference and XAI."""
from pathlib import Path
import json
import math

import joblib
import sklearn
from sklearn.pipeline import Pipeline

DEFAULT_MODEL_DIR = Path(__file__).resolve().parents[1] / 'models'
MAX_TEXT_LENGTH = 100_000


class PhishingDetector:
    def __init__(self, model_dir=DEFAULT_MODEL_DIR):
        model_dir = Path(model_dir)
        self.metadata = json.loads((model_dir / 'model_metadata.json').read_text())
        if self.metadata['sklearn_version'] != sklearn.__version__:
            raise RuntimeError('Model scikit-learn version differs; install requirements-lock.txt or retrain.')
        self.pipeline = joblib.load(model_dir / 'phishing_pipeline.joblib')
        if not isinstance(self.pipeline, Pipeline):
            raise ValueError('Expected a saved inference Pipeline.')
        self.vectorizer = self.pipeline.named_steps['tfidf']
        self.classifier = self.pipeline.named_steps['classifier']
        if list(self.classifier.classes_) != [0, 1]:
            raise ValueError('Unexpected classifier class ordering.')
        self.labels = self.metadata['label_mapping']
        if self.labels != {'0': 'Legitimate', '1': 'Phishing'}:
            raise ValueError('Unexpected label mapping.')
        self.threshold = float(self.metadata['threshold'])
        if not 0 < self.threshold < 1:
            raise ValueError('Invalid classification threshold.')
        self.features = self.vectorizer.get_feature_names_out()
        # Reconstruct unigram tokenisation for removal; saved analyser also emits bigrams.
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.word_analyser = TfidfVectorizer(
            lowercase=self.vectorizer.lowercase,
            strip_accents=self.vectorizer.strip_accents,
            token_pattern=self.vectorizer.token_pattern,
        ).build_analyzer()
        self.pipeline.predict_proba(['startup validation message'])

    def explain(self, text, probability, x, limit=5):
        """Probability change after removing a candidate unigram, as in the notebook."""
        candidates = sorted(
            [(self.features[i], float(v)) for i, v in zip(x.indices, x.data)
             if ' ' not in self.features[i]],
            key=lambda item: (-item[1], item[0]),
        )[:20]
        if not candidates:
            return []
        tokens = self.word_analyser(text)
        altered = [' '.join(token for token in tokens if token != term) for term, _ in candidates]
        changed = self.pipeline.predict_proba(altered)[:, 1]
        rows = [{'term': str(term), 'probability_drop': probability - float(p)}
                for (term, _), p in zip(candidates, changed)]
        return sorted(rows, key=lambda row: (-abs(row['probability_drop']), row['term']))[:limit]

    def predict(self, text, explain=True):
        if not isinstance(text, str) or not text.strip():
            raise ValueError('Enter a non-empty email message.')
        if len(text) > MAX_TEXT_LENGTH:
            raise ValueError(f'Message must contain at most {MAX_TEXT_LENGTH:,} characters.')
        # No custom cleaning: the saved vectorizer defines all model input processing.
        x = self.vectorizer.transform([text]).tocsr()
        p = float(self.classifier.predict_proba(x)[0, 1])
        if not math.isfinite(p) or not 0 <= p <= 1:
            raise RuntimeError('Model returned an invalid probability.')
        predicted_class = int(p >= self.threshold)
        warning = None
        if x.nnz == 0:
            warning = 'No known vocabulary was found; this result is driven by the model intercept/bias and is unreliable.'
        return {
            'prediction': self.labels[str(predicted_class)].lower(),
            'confidence': p if predicted_class else 1 - p,
            'phishing_probability': p,
            'model': self.metadata['selected_model'],
            'indicators': self.explain(text, p, x) if explain else [],
            'warning': warning,
        }

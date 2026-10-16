# ITRI625 Phishing Email Detection

A Python cybersecurity ML project with a fully executed Jupyter notebook, TF-IDF Logistic Regression baseline, small neural network with patience-based early stopping, FastAPI inference, and a Tkinter desktop client.

**Start with `notebooks/phishing_detection.ipynb`.** All important model code, explanations, metrics, and Matplotlib figures are inside the notebook. It is independent of the application modules. `THEORY_NOTES.md` follows assignment sections 3.1–3.4; `RUBRIC_CHECKLIST.md` maps verified evidence to marks.

## Dataset and problem

The supplied `../archive.zip` contains seven CSVs. We use only `data/raw/phishing_email.csv`: 82,486 rows, columns `text_combined` (text) and `label` (0 = Legitimate, 1 = Phishing). Raw classes: 39,595 legitimate / 42,891 phishing, approximately balanced. The notebook retains 82,051 rows after documented cleaning and creates 57,435 / 12,308 / 12,308 stratified training / validation / test sets with seed 42.

[Assignment-linked dataset](https://www.kaggle.com/datasets/naserabdullahalam/phishing-email-dataset). See `data/README.md` and `reports/INITIAL_INSPECTION.md` for provenance, all archive members, inspection findings, label evidence, and limitations. The archive and extracted raw data are unchanged. Positive labels include spam; a model prediction is neither proof of phishing nor a safety guarantee. The combined CSV's upstream preprocessing is not supplied.

## Project structure

```text
ITRI625-Phishing-Detection/
├── notebooks/phishing_detection.ipynb  # Executed primary ML deliverable
├── data/raw/phishing_email.csv         # Original bytes; ignored by Git
├── src/inference.py                    # Saved Pipeline inference and XAI
├── api/main.py                         # FastAPI /health and /predict
├── desktop/app.py                      # Tkinter HTTP client
├── models/                             # Models plus JSON metadata
├── figures/                            # Copies of inline notebook figures
├── reports/                            # Metrics, split manifest, audits, QA
├── tests/test_application.py           # API/artifact/error-handling tests
├── scripts/verify_desktop.py           # Real Tkinter + live HTTP smoke check
├── start_project.command               # One-command macOS launcher
├── requirements.txt                   # Direct dependencies, pinned
├── requirements-lock.txt              # Full tested environment
├── THEORY_NOTES.md
└── RUBRIC_CHECKLIST.md
```

## Installation and Jupyter setup (macOS/Linux)

Open **this repository folder** in VS Code. From its terminal:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m ipykernel install --user --name itri625-phishing --display-name "ITRI625 Phishing"
```

The existing `.venv` is already installed and the kernel registered on this machine; just activate it. The tested environment uses Python 3.13.3 on Apple Silicon. `requirements.txt` lists direct packages; the lock file records the complete environment. On a different platform, if the full lock cannot resolve, use `python -m pip install -r requirements.txt`, then rerun the notebook and application checks. TensorFlow, PyTorch, SHAP and LIME are not needed. Tkinter is part of the Python installation on this Mac; it is not installed by pip.

## Run the notebook

1. Confirm `data/raw/phishing_email.csv` exists. On a fresh clone, extract that member from the original archive into `data/raw/`; the raw dataset is intentionally outside Git. The notebook verifies its expected hash from `reports/data_integrity.json`.
2. Open `notebooks/phishing_detection.ipynb` in VS Code.
3. Select **ITRI625 Phishing** (or this repository's `.venv` interpreter).
4. Choose **Restart Kernel → Run All**, wait for completion, and save the notebook with outputs.

Alternatively:

```bash
jupyter notebook notebooks/phishing_detection.ipynb
# Noninteractive full execution and saving:
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1800 notebooks/phishing_detection.ipynb
```

The notebook has been repeatedly executed successfully with unchanged modelling choices and saved outputs, including during the final submission audit. Its test set is evaluated only after selection, once per complete execution. Do not tune after observing test results. Rerunning regenerates logs and model artifacts for the same fixed experiment.

## Model summary and actual results

TF-IDF uses 10,000 unigram/bigram features fitted only on training data. Baseline: Logistic Regression. Neural model: Dense(32, ReLU) → Dense(1, sigmoid), trained with Adam. The explicit loop requests 30 epochs, uses validation-loss patience 3, stops at epoch 11, and restores epoch 8. All six metrics are logged for training and validation every epoch. The selected model is **Neural MLP**, chosen by validation F1 (recall/AUC tie-breakers), with fixed threshold 0.5.

| Model / split | Accuracy | Precision | Recall | F1 | ROC AUC | Log loss |
|---|---:|---:|---:|---:|---:|---:|
| Logistic Regression (validation) | 0.98627 | 0.98376 | 0.99004 | 0.98689 | 0.99866 | 0.06801 |
| Neural MLP (validation) | 0.98928 | 0.98897 | 0.99051 | 0.98974 | 0.99931 | 0.03135 |
| Neural MLP (test) | 0.99001 | 0.98990 | 0.99097 | 0.99043 | 0.99912 | 0.03183 |

Final test confusion matrix: TN=5817, FP=65, FN=58, TP=6368. These are corpus-specific results; contemporary, campaign-disjoint evaluation remains future work. Global baseline coefficient plots and local selected-model token-removal explanations are included. Probabilities are uncalibrated model estimates.

## Run FastAPI

### One-command macOS startup

From Finder, double-click `start_project.command`. If macOS opens it in a text editor, right-click it, choose **Open With → Terminal**, or run it from a VS Code terminal:

```bash
./start_project.command
```

The script locates the project directory automatically, starts FastAPI, waits for a successful health check, and opens the Tkinter application. Closing the desktop window also stops the API.

### Start each component manually

From the repository root, with `.venv` active:

```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Visit http://127.0.0.1:8000/docs for interactive API documentation.

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"text":"Your account has been suspended. Click here to verify."}'
```

The response contains `prediction` (`phishing` or `legitimate`), predicted-class `confidence`, `phishing_probability`, `model`, local `indicators`, and an optional `warning`. Indicator values are the decrease in P(Phishing) when a word is removed; positive values support the phishing score. Use `"explain": false` to skip local explanations. Input must be nonblank text with at most 100,000 characters.

The API loads `models/phishing_pipeline.joblib` and `models/model_metadata.json` once at startup. It returns 503 when the model is unavailable, 422 for invalid input, and 500 for prediction errors. Unknown vocabulary triggers a warning. Full email contents are not deliberately logged by application code. API/server logs are local and excluded from Git. This is a local demonstration service, without production authentication or load-testing claims.

## Run Tkinter

Keep FastAPI running. In a **second terminal**, from the repository root:

```bash
source .venv/bin/activate
python -m desktop.app
```

Paste a subject/message, click **Analyse Email**, inspect the prediction, confidence and indicators, then use **Clear** to reset. Network calls run in a worker thread so the UI stays responsive. The GUI uses HTTP only and never loads the model directly.

For an alternate local port:

```bash
PHISHING_API_URL=http://127.0.0.1:8765 python -m desktop.app
```

## Verification

```bash
python -m unittest discover -s tests -v
python -m pip check
# With FastAPI running at the URL below; opens a real desktop window:
PHISHING_API_URL=http://127.0.0.1:8000 python -m scripts.verify_desktop
```

Tests compare inference/API probabilities with notebook-exported references, validate token-removal explanations, test missing models, empty/oversized input, unknown vocabulary, prediction failure, and desktop network/malformed-response handling. `reports/desktop_verification.json` records the live Tkinter → HTTP → model flow and GUI reset/unavailable-API checks; `reports/desktop_preview.png` shows the inspected layout.

## Troubleshooting

- **Kernel missing:** rerun the ipykernel registration command and select it in VS Code. Installing the VS Code extension alone does not install Python packages.
- **Module not found:** activate `.venv`; use `python -m ...` from the repository root.
- **Dataset missing/hash mismatch:** restore the exact supplied `phishing_email.csv`. Investigate a different dataset version before changing the integrity record.
- **Model unavailable (503):** run the notebook to completion; confirm Pipeline and metadata exist. Restart FastAPI after regenerating models because it loads them only at startup. `PHISHING_MODEL_DIR` can point to another trusted model directory.
- **Version mismatch:** install the tested lock or regenerate artifacts with the current environment. Joblib compatibility across scikit-learn versions is not assumed.
- **Tkinter unavailable:** use a Python distribution including Tcl/Tk. On Linux, install your distribution's matching Tk package and run in a graphical desktop session.
- **API unavailable:** start FastAPI separately and check the URL/port. The verification script defaults to port 8765; the normal app defaults to 8000.
- **Empty/unfamiliar text:** blank text is rejected. Punctuation-only or entirely unseen terms produce a warning; a bias-driven probability is not useful evidence.
- **High scores seem unrealistic:** read the corpus limitations and validation errors before drawing deployment conclusions.
- **TestClient deprecation notice:** the installed Starlette version warns about future migration from httpx; the pinned test environment passes today. This warning is not a test failure.

## Source control and submission

`.gitignore` excludes `.venv`, editor settings, caches, secrets, temporary logs, raw CSVs, and binary model files. The dataset and models remain present locally and may be needed for submission; they were not deleted. Notebook outputs, figures, JSON metadata and metric CSVs remain eligible for version control. A fresh clone must restore the raw dataset and rerun the notebook to recreate models. Check dataset redistribution permissions before sharing it.

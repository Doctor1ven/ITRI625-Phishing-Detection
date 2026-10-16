# ITRI625 rubric audit

Source: supplied `../ITRI625_Project_ML fin.pdf`, sections 2–4. Status means the listed implementation/evidence was checked, not a guarantee of lecturer-awarded marks. Verification details are in `reports/verification.json`. Model results are in the executed notebook and `reports/results.json`.

| Requirement | Marks | Evidence | Status | Notes |
|---|---:|---|---|---|
| 2.1 Model development | 20 | Notebook §§1–13; saved baseline, neural MLP and selected Pipeline | COMPLETE | Real supplied data; full workflow visible in notebook; both models trained and evaluated on validation. Neural MLP selected by declared validation rule. |
| 2.2 Dataset divided into train, validation, testing | 5 | Notebook §9; reports/split_manifest.csv | COMPLETE | 57,435 / 12,308 / 12,308; stratified seed 42; disjoint token-equivalent texts; vocabulary fitted only on training. |
| 2.3 Evaluation metric logging | 15 | Notebook §§10,12–13,17; reports/training_history.csv | COMPLETE | Each neural epoch logs full train/validation accuracy, precision, recall, F1, ROC AUC and predictive log loss. Optimiser loss separate. Baseline metrics and final selected test metrics displayed. |
| 2.4 Matplotlib metric graphs | 15 | Notebook §§6,10,14,16–17; figures/ | COMPLETE | Seven embedded figures, including class distribution, lengths, loss, accuracy, confusion matrices, ROC, PR and coefficient plots. Figures have titles and axis labels; curve legends show five-decimal AUC/AP. |
| 2.5 API and desktop application | 15 | api/main.py; desktop/app.py; src/inference.py; reports/desktop_verification.json; reports/desktop_preview.png | COMPLETE | Live Tkinter → local HTTP FastAPI → model round trip verified. Prediction/confidence/XAI displayed; blank, clear, unavailable API, input limits, missing model and inference failures checked. Seven automated integration tests pass. |
| 2.6 Patience / early stopping | 5 | Notebook §12; reports/training_history.csv; reports/results.json | COMPLETE | Explicit val-loss patience=3; 30 requested epochs, 11 trained, epoch 8 restored. Best validation loss 0.03134898. Trigger and restored predictions verified. |
| 2.7 Additional features: XAI | 10 bonus | Notebook §16; src/inference.py; API indicators; desktop indicators | COMPLETE | Global baseline coefficients plus local selected-model token removal. Perturbation probabilities independently checked; limitations documented. Hosting not attempted. Bonus award is lecturer's decision. |
| 3.1 Model scenario | 3 | THEORY_NOTES.md §3.1; notebook §§1–3 | COMPLETE | Explains phishing, cybersecurity use, false-negative consequences, and spam/phishing proxy labels. |
| 3.2 Model architecture | 10 | THEORY_NOTES.md §3.2; notebook §§8,10–12,16 | COMPLETE | TF-IDF, linear baseline, 32-unit ReLU neural layer, sigmoid output, 320,065 parameters, Adam, loss, regularisation, patience and inference architecture explained. |
| 3.3 Model result analysis | 10 | THEORY_NOTES.md §3.3; notebook §§13–17,20 | COMPLETE | Uses real validation/test metrics, confusion counts, loss/overfitting interpretation, ROC/PR, false positives/negatives, error excerpts and deployment limitations. |
| 3.4 Real-world use with academic references | 7 | THEORY_NOTES.md §3.4 | COMPLETE | Structured draft covers intrusion detection, threat classification, anomaly detection, risk assessment, data quality, drift, false positives and attacker adaptation. Three academic references verified against publisher/proceedings records; proposed uses distinguished from implemented work. |
| Notebook code and visible outputs | -10 if missing | notebooks/phishing_detection.ipynb; reports/verification.json | COMPLETE | Notebook schema valid; all 15 code cells executed in order, zero errors, seven embedded PNGs. Repeated full execution, including the final audit, passed; the notebook is saved with outputs. ML code is not a wrapper around application modules. |
| Source control used throughout project | -10 if poor | Existing .git; .gitignore; README source-control section | PARTIAL | Repository metadata preserved, but no commits existed and no commits/pushes were made. README suggests four logical commits. User must review/commit and continue meaningful source control; this audit cannot claim a development history. |

## Additional requested delivery checks

| Requirement | Marks | Evidence | Status | Notes |
|---|---:|---|---|---|
| Inspect real dataset without modification | Included above | reports/INITIAL_INSPECTION.md; reports/data_integrity.json; data/README.md | COMPLETE | All seven CSVs inspected read-only. Combined CSV shape/columns/labels/duplicates/balance inspected. Archive and extracted CSV hashes unchanged. |
| Justified cleaning and data quality | Included above | Notebook §§5–7; reports/cleaning_audit.csv | COMPLETE | 82,486 → 82,051 rows; every removal counted. One blank, one token-empty, 433 token-equivalent duplicates; zero conflicting groups/invalid labels. |
| Environment and kernel | Setup | .venv; requirements.txt; requirements-lock.txt; .vscode/settings.json | COMPLETE | Python 3.13.3 environment created, ITRI625 Phishing kernel registered, pip check passes. Tkinter available. |
| Validation-only selection and final test | Included above | Notebook §§13,17; reports/results.json | COMPLETE | Selection frozen before test. One aggregate test prediction pass per fixed run; no modelling changes after test inspection. Repeated identical execution is not a new independent test. |
| Error analysis and examples | Included above | Notebook §§15,18; reports/validation_errors.json | COMPLETE | Three real validation false positives and three false negatives; bounded excerpts, hypothesis-based discussion; manual examples clearly separated from dataset examples. |
| Saved artifacts and inference consistency | Included above | models/; src/inference.py; tests/test_application.py | COMPLETE | Selected Pipeline reload and API probabilities match notebook reference predictions; mapping/version/threshold validated. |
| README and theory notes | Documentation | README.md; THEORY_NOTES.md | COMPLETE | Installation, kernel, notebook/API/desktop launch, dataset details, results, limitations, tests and troubleshooting included. |
| Production or externally validated readiness | Not required | Limitations in README/theory/notebook | NOT STARTED | No hosting, external/temporal/campaign-disjoint validation, calibrated risk model, attachment analysis, or production readiness claim. |

## Marks discrepancy in the supplied specification

The assignment states 70 practical + 30 theory = 100. The five practical rows before early stopping already sum to 70; adding the separately printed 5-mark early-stopping row produces 75, plus a 10-mark bonus row. This checklist preserves the printed values and the stated 100% cap. It does not silently recalculate the official grading scheme.

## Submission actions remaining

Review and commit the work using your own Git identity, then continue meaningful version control. Read and adapt the theory draft to your own explanation and required citation style. Keep the real dataset and generated models in the local submission package if required: their exclusion from Git does not remove them from disk. Check the lecturer's submission format and dataset redistribution terms before publishing. No external publishing, email, or Git push has occurred.

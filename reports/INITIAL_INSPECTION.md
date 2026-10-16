# Workspace inspection

Assignment read: `../ITRI625_Project_ML fin.pdf` (four pages). Original workspace contained only archive.zip and this empty Git repository. No existing code, requirements, notebook or virtual environment was present. Python 3.13.3 and Tk 8.6 were installed; the VS Code Jupyter extension was installed, but no Jupyter CLI/kernel was available before setup. Git main had no commits. Existing repository metadata was retained.

## Archive inspection (read without modifying the archive)

| CSV | Rows | Columns | Label 0 | Label 1 | Exact duplicate rows |
|---|---:|---:|---:|---:|---:|
| CEAS_08.csv | 39154 | 7 | 17312 | 21842 | 0 |
| Enron.csv | 29767 | 3 | 15791 | 13976 | 0 |
| Ling.csv | 2859 | 3 | 2401 | 458 | 0 |
| Nazario.csv | 1565 | 7 | 0 | 1565 | 0 |
| Nigerian_Fraud.csv | 3332 | 7 | 0 | 3332 | 0 |
| SpamAssasin.csv | 5809 | 7 | 4091 | 1718 | 0 |
| phishing_email.csv | 82486 | 2 | 39595 | 42891 | 408 |

Use the combined phishing_email.csv alone. Columns: text_combined (text) and label (integer 0/1). One empty text; no missing labels. Raw class balance: 48.002% legitimate / 51.998% phishing. Exact duplicates: 408. Case/whitespace-normalised duplicate texts: 408, with no conflicting labels. The notebook also checks token-equivalent duplicates under the actual vectorizer's analyser before splitting.

No local label dictionary is included. Mapping is supported by inspecting labels in the constituent corpora: positive-only fraud and Nazario files contain 1; ordinary Enron correspondence contains 0. The assignment-linked data card describes spam/phishing versus legitimate. The combined dataset conflates spam and phishing and already has upstream text processing; document this limitation.

Plan: environment → fully visible notebook workflow → executed outputs and saved models → shared inference → API → desktop integration → documentation and rubric verification. Use train/validation/test with seed 42; TF-IDF logistic regression and a small scikit-learn MLP neural network with an explicit validation-loss patience loop. Scikit-learn supports sparse TF-IDF input, keeping CPU requirements manageable without a separate deep-learning framework.

Marks anomaly: practical rows before early stopping already sum to the stated 70. Preserve the printed 5 early-stopping and 10 bonus marks, and the stated overall cap of 100, rather than silently changing the rubric.

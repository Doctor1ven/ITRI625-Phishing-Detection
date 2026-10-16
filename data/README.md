# Dataset provenance

Source linked by the assignment: https://www.kaggle.com/datasets/naserabdullahalam/phishing-email-dataset

The supplied `../archive.zip` contains CEAS_08.csv, Enron.csv, Ling.csv, Nazario.csv, Nigerian_Fraud.csv, SpamAssasin.csv and phishing_email.csv. Only phishing_email.csv is used for modelling. Do not concatenate the source CSVs with the combined CSV: they may overlap.

The CSV is extracted byte-for-byte into data/raw; neither archive nor original CSV is edited. The combined CSV contains 82,486 rows and two columns: text_combined and label. The observed target values are 0 and 1. Positive-only Nazario and Nigerian_Fraud source files have label 1; legitimate Enron correspondence has label 0. This supports 0 = Legitimate, 1 = Phishing. The source description conflates spam with phishing: positive labels are a broad spam/phishing proxy, not independently verified malicious intent. The archive supplies no separate label dictionary or preprocessing script.

The text is already processed in the supplied combined CSV. Its upstream preprocessing cannot be fully reconstructed. Our saved vectorizer applies the same explicit tokenisation to training and API inputs, but arbitrary raw email may differ from the dataset distribution. Source/campaign/time identifiers are absent from the combined CSV, limiting external-validity checks.

Raw CSV and generated model binaries are excluded from Git due to size. Keep them locally for the submission; the notebook regenerates models. To reproduce on another machine, obtain the assignment dataset and extract phishing_email.csv into data/raw. Do not commit or redistribute the dataset without checking its source licence.

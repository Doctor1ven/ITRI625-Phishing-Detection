# ITRI625 theory analysis

This draft follows the assignment's exact 3.1–3.4 structure. Numerical results come from the executed `notebooks/phishing_detection.ipynb` and `reports/results.json`. Phishing is the positive class throughout.

## 3.1 Model Scenario

Phishing is a social-engineering attack in which an attacker pretends to be a trusted person or organisation to obtain sensitive information or induce a harmful action. Email messages may imitate account alerts, payment requests, or routine business correspondence. A victim may disclose a password, transfer funds, or open a harmful link or attachment.

This project classifies message text as Phishing or Legitimate. It can support a security analyst by prioritising messages for review and highlighting influential words. The desktop app sends the user's text to a local FastAPI endpoint, which applies the trained Pipeline and returns a prediction, estimated probability, and local indicators. A false negative can leave credential theft or fraud undetected; a false positive can interrupt legitimate work.

The supplied combined corpus has 82,486 rows, including 39,595 label-0 and 42,891 label-1 examples. The label mapping is supported by inspection of the constituent corpora. Positive labels include spam as well as phishing, so the project predicts a broad dataset proxy rather than independently confirmed malicious intent. The original archive and raw CSV were preserved and hashed. Data provenance and limitations are documented in `data/README.md`.

## 3.2 Model Architecture

### Preprocessing and dataset preparation

Input is `text_combined`; target is integer `label` (0 = Legitimate, 1 = Phishing). One blank message, one message without usable tokens, and 433 token-equivalent duplicate rows were removed, leaving 82,051. No conflicting labels were found for token-equivalent text. The original CSV has 408 exact duplicate rows; the larger token-equivalence count includes case, punctuation, and accent variants. Cleaning removes no unusual labels because all observed labels are valid. No class resampling is needed because the classes are approximately balanced.

A fixed seed of 42 gives a stratified split of 57,435 training, 12,308 validation, and 12,308 test messages. Duplicate keys are disjoint across all three splits. TF-IDF is fitted only on training text. The vocabulary and inverse-document-frequency values are then held fixed for validation, test, and API inference. Removing exact/token-equivalent duplicates limits a clear leakage route, but related campaigns or source-specific wording may still span splits.

TF-IDF uses lowercasing, Unicode accent stripping, word tokens of at least two characters, word unigrams and bigrams, minimum document frequency 2, sublinear term frequency, and at most 10,000 features. Sublinear term frequency uses 1 + log(count) for positive counts; inverse document frequency downweights terms occurring in many training messages, and each feature vector is L2-normalised. The combined CSV already contains processed text whose upstream transformation is not provided. We cannot claim that its original processing has been reconstructed for arbitrary raw email.

### Baseline: Logistic Regression

The baseline learns a weighted sum of TF-IDF inputs plus an intercept and applies a sigmoid to estimate P(Phishing). It uses L2 regularisation with C=1, the LBFGS solver, and at most 1,000 solver iterations. The notebook checks convergence. This is a sensible text baseline because sparse term frequencies can be strongly associated with message classes. Coefficients provide a simple global explanation, though correlated features and dataset origin affect their interpretation.

### Main neural network

The main network is a scikit-learn MLP with 10,000 inputs, one dense hidden layer of 32 ReLU units, and one sigmoid output. It has 320,065 trainable weights and biases: 10,000×32 + 32 + 32×1 + 1. ReLU computes max(0,z), enabling nonlinear combinations of word features. Sigmoid maps the output logit to a value between zero and one. Binary cross-entropy penalises confident wrong predictions. Adam updates weights in minibatches of 256 with learning rate 0.001 and L2 alpha=0.0001. This compact sparse-input architecture is practical on CPU; it does not use embeddings, dropout, or recurrent layers and cannot model long-range word order. The implementation is a neural network even though it does not require TensorFlow or PyTorch. See the [official MLP documentation](https://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPClassifier.html).

The explicit notebook loop calls partial_fit once per epoch, computes full training and validation metrics, and monitors validation log loss. Patience is 3; up to 30 epochs are requested. A lower validation loss saves a full checkpoint and resets the wait counter. Three consecutive non-improving epochs stop training. The best checkpoint is restored, rather than using the last epoch. Early stopping is regularisation through validation monitoring; it does not make the test set available for tuning.

### Model selection and explanations

The predeclared rule selects highest validation F1, then recall and ROC AUC; an exact tie favours the simpler baseline. Threshold 0.5 remains fixed. Neural MLP won using validation results. The selected fitted vectorizer/classifier Pipeline is the sole inference artifact required by the API. Model metadata fixes label names and threshold; the API loads it once during startup.

For bonus XAI, baseline coefficients are plotted globally. For the selected model, local token removal measures how P(Phishing) changes after removing a candidate word and re-vectorizing. Candidates are the top 20 TF-IDF unigrams in the message; the five largest absolute changes are shown. Positive changes mean the removed token supported the original phishing score. Removal changes bigrams and normalisation, so these values are sensitivity indicators, not additive or causal contributions. They explain the selected neural model directly rather than presenting baseline weights as neural explanations.

## 3.3 Model Result Analysis

### Measured performance

| Model / split | Accuracy | Precision | Recall | F1 | ROC AUC | Log loss |
|---|---:|---:|---:|---:|---:|---:|
| Logistic Regression (validation) | 0.98627 | 0.98376 | 0.99004 | 0.98689 | 0.99866 | 0.06801 |
| Neural MLP (validation) | 0.98928 | 0.98897 | 0.99051 | 0.98974 | 0.99931 | 0.03135 |
| Neural MLP (test) | 0.99001 | 0.98990 | 0.99097 | 0.99043 | 0.99912 | 0.03183 |

Test evaluation was performed only after selection, with a single selected-model prediction pass per fixed notebook execution. Plotting and metric calculations reuse those probabilities. The notebook was repeatedly executed to verify reproducibility, including during the final submission audit; architecture, split, stopping rule, selection rule, and threshold were not adjusted after test inspection. Repeated fixed execution is verification, not an independent new test experiment.

The neural model's validation F1 (0.98974) exceeded the baseline's (0.98689). Its test accuracy was 99.00%, precision 98.99%, recall 99.10%, and F1 99.04%. Accuracy measures all correct decisions. Precision measures the positive-label fraction among alerts; recall measures the fraction of phishing-labelled messages detected; F1 balances them. These numbers describe this approximately balanced corpus and the chosen threshold.

The final confusion matrix is:

| Actual / Predicted | Legitimate | Phishing |
|---|---:|---:|
| Legitimate | 5817 | 65 |
| Phishing | 58 | 6368 |

There were 58 false negatives among 6,426 positive-labelled messages: a 0.903% miss rate. Missing a real phishing attack can permit account compromise, so high accuracy alone is not sufficient. There were 65 false positives among 5,882 legitimate-labelled messages, a 1.105% false-positive rate. Operationally, those alerts consume analyst time and can disrupt users. Any future threshold adjustment should use new validation evidence and explicit error costs, not this test set.

The ROC AUC of 0.99912 indicates strong ranking on this split; it does not represent accuracy or perfect discrimination. The PR curve focuses on positive-class retrieval; average precision is 0.99916, compared with positive prevalence 52.21%. A lower real-world phishing prevalence can substantially reduce precision even if recall and false-positive rate appear similar. Log loss is 0.03183; it incorporates probability quality but does not establish calibration.

### Loss, early stopping, and overfitting

Training stopped after 11 of 30 epochs and restored epoch 8. Best validation loss was 0.03135; training loss at that checkpoint was 0.00905. The gap was 0.02230. Training loss continued falling after the best epoch while validation loss stopped improving and then rose. This is evidence of overfitting beginning in later epochs, which the patience loop curtailed. The logged prediction losses exclude the L2 penalty; optimiser loss is recorded separately in the CSV.

Class distribution, message lengths, baseline confusion matrix, training/validation loss and accuracy, selected validation and final test confusion matrices, ROC curves, PR curves, and coefficient plots are visible in the notebook and saved in `figures/`. ROC/PR legends show five decimal places to avoid rounding high scores to 1.00.

### Errors and effectiveness

Notebook section 15 and `reports/validation_errors.json` display three actual false positives and three false negatives, with excerpts capped at 450 characters. Possible explanations refer to visible vocabulary: commercial/account terms can cause false alarms, while ordinary correspondence wording can occur in positive-labelled text. These are hypotheses, not verified causes. Source artefacts, missing context, and inconsistent spam/phishing labels are other possible contributors.

The model is effective at reproducing labels within this experiment, but the near-99% scores do not establish readiness for a current real inbox. This dataset lacks source/time identifiers, includes already-processed messages, and mixes spam with phishing. Residual near-duplicates and source vocabulary may make random-split performance optimistic. There is no external test corpus, temporal evaluation, confidence interval, calibration study, attachment analysis, or attacker-evasion evaluation. The appropriate demonstrated use is a classroom screening prototype with human review.

## 3.4 Real-World Use of Models

### Intrusion detection and anomaly detection

ML can rank network events or host activity for investigation. A supervised intrusion detector learns from labelled benign and attack examples; an anomaly detector searches for deviation from an expected pattern. Unusual behaviour is not necessarily malicious, so alerts need context. CADE evaluates drift detection and explanation in malware classification and network intrusion detection, demonstrating the relevance of changing distributions to both applications [2]. This project detects message-label patterns; it has not implemented network intrusion or anomaly detection.

### Threat classification and risk assessment

Threat classifiers can assign labels to emails, malware, or other security observations. Their value depends on evaluation that reflects deployment conditions. TESSERACT shows how spatial and temporal experimental bias can inflate malware-classification results [1]. Applying that lesson here is an inference: a random split of a pooled email corpus should not be interpreted as evidence of performance on future campaigns. For risk assessment, the proposed role of this classifier is one signal for triage alongside asset importance, sender reputation, and incident context. Its uncalibrated probability is not itself a validated measure of business risk.

### Data quality and false positives

Missing text, duplicate campaigns, inconsistent labels, and historical source artefacts can distort training and evaluation. This project addresses measurable blanks and token-equivalent duplicates, but cannot reconstruct absent collection metadata. Representative deployment distributions matter [1]. A real inbox may have a much smaller positive prevalence than this dataset; then false alerts can form a large fraction of flagged messages. Pilot deployment should measure false positives per user and analyst workload, while retaining a process for reviewing missed attacks.

### Concept drift, model drift, and attacker adaptation

Concept drift concerns changes in the relationship between input and target; the survey by Gama et al. organises adaptation approaches and evaluation [3]. In cybersecurity, attackers and benign users change behaviour. CADE specifically investigates identifying and explaining drifting security samples [2]. A previously useful word pattern may therefore become unreliable. Here, “model drift” means observed model-performance degradation as operating conditions evolve; it should be diagnosed rather than assumed from changes in word counts alone. Monitoring should combine score/input statistics with newly reviewed labels, then evaluate retraining on fresh held-out data. This is a proposed deployment process, not a completed component.

### Deployment strengths and limitations

The demonstrated system has low CPU requirements, consistent saved preprocessing, a local API, usable desktop feedback, and local explanations. It can support a university demonstration and exploratory human review. A production system would also need representative recent evaluation, sender/link/attachment signals, access controls, privacy/retention policies, load testing, calibration, and monitoring. Probability estimates and token-removal indicators cannot guarantee safety or robustness against crafted inputs. The experimental-bias findings in [1] and drift examples in [2] support this cautious interpretation; they do not independently validate this model.

### Academic references

[1] Pendlebury, F., Pierazzi, F., Jordaney, R., Kinder, J., and Cavallaro, L. (2019). *TESSERACT: Eliminating Experimental Bias in Malware Classification across Space and Time*. 28th USENIX Security Symposium, pp. 729–746. https://www.usenix.org/conference/usenixsecurity19/presentation/pendlebury

[2] Yang, L., Guo, W., Hao, Q., Ciptadi, A., Ahmadzadeh, A., Xing, X., and Wang, G. (2021). *CADE: Detecting and Explaining Concept Drift Samples for Security Applications*. 30th USENIX Security Symposium, pp. 2327–2344. https://www.usenix.org/conference/usenixsecurity21/presentation/yang-limin

[3] Gama, J., Žliobaitė, I., Bifet, A., Pechenizkiy, M., and Bouchachia, A. (2014). *A survey on concept drift adaptation*. ACM Computing Surveys, 46(4), Article 44, pp. 1–37. https://doi.org/10.1145/2523813

The bibliographic details and supporting abstracts were checked against the publisher/proceedings pages. Adapt the citation style to your department's submission requirements.

## Phase 2: Modeling, Validation, and Deployment

### II.1 Model Development

In this phase, a machine learning model was developed to classify network traffic as benign or malicious using the curated dataset produced in Phase 1.

A baseline model was first established using a **Dummy Classifier** (most frequent strategy) to provide a reference point for performance evaluation. This baseline achieved an accuracy of approximately **80%**, reflecting the class imbalance in the dataset.

The primary model selected was a **Random Forest Classifier**, chosen for its ability to:

* handle tabular data effectively
* capture non-linear relationships
* provide robust performance with minimal preprocessing

The training pipeline was fully reproducible:

* fixed random seed (`random_state = 42`)
* explicit train/validation/test split
* parameterized model configuration
* MLflow logging for experiment tracking

---

### II.2 Model Validation

A structured validation strategy was implemented to ensure realistic and unbiased evaluation:

* Train / Validation / Test split was applied
* Stratified sampling was used to preserve class distribution
* Data leakage was avoided by ensuring strict separation between splits

The following evaluation metrics were used:

* Accuracy
* Precision
* Recall
* F1-score
* AUC (Area Under Curve)

Results:

* Baseline Accuracy: ~80%
* Final Model Accuracy: **98.24%**
* Final Model F1 Score: **95.58%**
* AUC Score: **~0.998**

The model significantly outperformed the baseline, demonstrating strong predictive capability.

---

### II.3 Model Versioning and Registration

The trained model was registered in the **Azure Machine Learning Model Registry**:

* Model Name: `intrusion-detection-model`
* Version: 1
* Linked Training Job: Azure ML experiment run
* Artifacts stored:

  * `model.pkl`
  * `feature_columns.pkl`

This ensures:

* traceability between data, code, and model
* reproducibility of results
* version control for future improvements

---

### II.4 Model Deployment

The trained model was deployed using **Azure Machine Learning Managed Online Endpoints** in real-time serving mode.

The deployment included:

* A scoring script (`score.py`) responsible for:

  * loading the trained model
  * ensuring correct feature ordering
  * processing incoming requests
* A custom inference environment (`inference_conda.yml`) defining all dependencies
* A managed online endpoint (`intrusion-endpoint-60302101`) exposing a REST API

The model was successfully deployed and made accessible through a **scoring URI**, enabling real-time predictions.

---

### II.5 Deployment Validation

The deployed endpoint was validated using HTTP POST requests with sample feature inputs.

The model returned valid predictions and probability scores:

* Prediction: 0 (Benign traffic)
* Probability: 0.067

This confirms:

* correct model loading
* correct feature handling
* consistency between offline and deployed predictions

The deployed system demonstrated reliable real-time inference behavior, aligning with expected model performance.

After validation, the deployment was **decommissioned** to optimize resource usage and avoid unnecessary cloud costs.

---

### Summary

This phase successfully completed the full machine learning lifecycle:

* Model development with baseline comparison
* Robust validation using multiple evaluation metrics
* Model versioning and registration in Azure ML
* Real-time deployment using managed endpoints
* Deployment validation through API testing

The system is fully reproducible, scalable, and aligned with real-world MLOps practices.

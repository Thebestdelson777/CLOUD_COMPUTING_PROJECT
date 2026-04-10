# Cloud-Based Machine Learning Pipeline for Network Intrusion Detection

## Anas Shoaib — 60104434 | Delson Fernandes — 60302101

---

## Project Overview

As organisations increasingly rely on cloud infrastructure, network security has become a critical concern. Modern networks face constant threats including denial-of-service attacks, port scanning, and unauthorised access. Traditional rule-based intrusion detection systems struggle to adapt to evolving attack patterns.

We built a cloud-native machine learning pipeline for binary intrusion detection using the CIC-IDS-2017 dataset and Azure Machine Learning as the execution platform. The pipeline spans two phases: a reproducible data foundation (Phase 1) and a full model development, validation, and deployment lifecycle (Phase 2).

**Hypothesis:** Statistical patterns in network traffic can reliably distinguish between benign and malicious activity, enabling automated detection with high precision and recall.

---

## Dataset

| Property | Detail |
|----------|--------|
| Name | CIC-IDS-2017 |
| Source | Canadian Institute for Cybersecurity, University of New Brunswick |
| Format | CSV (network flow features) |
| Classes | BENIGN (0) vs. Attack (1) |
| Total samples after cleaning | 2,827,876 |
| Class split | 80.3% benign / 19.7% attack |

---

## Azure Infrastructure

| Resource | Name |
|----------|------|
| Workspace | Amazon-Electronics-Lab-60104434 |
| Resource Group | rg-60104434 |
| Compute Instance | computeproject |
| Compute Cluster | computeclusterproject |

---

## Repository Structure

```
├── notebooks/
│   ├── eda_raw_data.ipynb          # Phase 1 — raw data exploration
│   ├── eda_processed.ipynb         # Phase 1 — EDA, feature selection, curated dataset
│   └── phase2_modeling.ipynb       # Phase 2 — full ML lifecycle notebook
├── scripts/
│   └── etl_pipeline.py             # Phase 1 — ETL pipeline
├── src/
│   ├── train.py                    # Phase 2 — Azure ML training script
│   ├── score.py                    # Phase 2 — inference scoring script
│   └── test_endpoint.py            # Phase 2 — endpoint validation
├── jobs/
│   ├── train_job.yml               # Azure ML training job definition
│   └── deployment.yml              # Azure ML deployment definition
├── env/
│   ├── conda.yml                   # Training environment
│   └── inference_conda.yml         # Inference environment
├── outputs/
│   ├── model.pkl                   # Serialised Random Forest classifier
│   ├── feature_columns.pkl         # Feature schema lock for inference
│   └── model_metadata.json         # Metrics, hyperparameters, and lineage
└── data_catalog.json               # Data schema, lineage, and zone definitions
```

---

## Phase 1 — Data Pipeline, ETL, and Feature Foundations

### II.1 Data Ingestion

We ingested raw CSV files from CIC-IDS-2017 using a **batch ingestion strategy**, appropriate for this static dataset. Files were uploaded to Azure Blob Storage under the `raw` zone, preserving the originals without modification. We chose batch over streaming because the dataset is historical and does not require real-time updates.

### II.2 ETL Process

We implemented an automated ETL pipeline (`scripts/etl_pipeline.py`) and executed it on Azure ML compute:

1. **Extract** — all raw CSV files loaded and merged into a single DataFrame
2. **Transform**:
   - Column names stripped of leading/trailing whitespace (CIC-IDS-2017 has a leading space in ` Label`)
   - Infinite values replaced with NaN (produced by zero-duration flow calculations)
   - Rows with NaN values dropped
   - Label binarised: `0` = BENIGN, `1` = Attack
3. **Load** — cleaned dataset saved to `processed/cleaned_data.csv`

We used `sorted(glob(...))` to guarantee deterministic file order across runs, ensuring reproducibility of the merged dataset.

### II.3 Data Cataloging and Governance

We adopted a three-layer storage architecture:

```
raw/               original, unmodified CSV files
processed/         cleaned and validated dataset (79 features + Label)
curated/           feature-selected dataset (15 features + Label)
```

Full schema definitions, data types, class distributions, and lineage are documented in `data_catalog.json`.

### II.4 Exploratory Analysis

We conducted EDA across two notebooks:

- **`eda_raw_data.ipynb`** — file schema consistency, column name inspection, numeric statistics, raw label distribution. We used `repr()` on column names to expose hidden whitespace characters in the CIC-IDS-2017 headers.
- **`eda_processed.ipynb`** — class imbalance analysis, duplicate handling, missing value verification, correlation heatmap, outlier assessment.

Key findings:
- Dataset is imbalanced (80/20 benign/attack) — addressed in Phase 2 via stratified splits
- Features are highly skewed with long tails, typical of network traffic data
- No missing values after ETL
- Duplicates retained as they represent legitimate repeated network flows

### II.5 Feature Extraction and Selection

We performed feature selection using the **ANOVA F-test** (`SelectKBest`, k=15). This method evaluates the statistical relationship between each feature and the binary target by comparing between-class and within-class variance. We chose ANOVA over wrapper methods because it scales efficiently to 2.8M rows without repeated model fitting.

**Selected features:**

| Feature | What it captures |
|---------|-----------------|
| Bwd Packet Length Max / Mean / Std | Backward traffic volume patterns |
| Flow IAT Max | Maximum inter-arrival time in the flow |
| Fwd IAT Std / Max | Forward direction timing variability |
| Max Packet Length | Largest single packet in the flow |
| Packet Length Mean / Std / Variance | Overall packet size distribution |
| Average Packet Size | Mean size across the full flow |
| Avg Bwd Segment Size | Backward segment characteristics |
| Idle Mean / Max / Min | Flow idle time behaviour |

The curated dataset (`curated/selected_features.csv`) contains these 15 features plus the binary label and is the input to Phase 2 training.

---

## Phase 2 — Modeling, Validation, and Deployment

### II.1 Model Development

We trained two models to establish a measurable performance baseline and a final production classifier.

**Baseline — DummyClassifier (most_frequent):**
Always predicts the majority class (Benign). Achieves ~80% accuracy purely from class distribution with zero ability to detect attacks. We included this to set a performance floor — any useful model must clearly beat it.

**Primary model — Random Forest Classifier:**
- `n_estimators=200` — stabilises variance without excessive memory cost on 2.8M rows
- `max_depth=12` — prevents overfitting while retaining sufficient depth for discrimination
- `random_state=42` — fully reproducible results across runs
- `n_jobs=-1` — parallelises tree building across all CPU cores

We chose Random Forest because it handles tabular data with mixed feature scales without normalisation, provides built-in feature importances for interpretability, and is robust to the class imbalance present in this dataset.

Training was executed as an **Azure ML job** on the compute instance, with the curated dataset registered as a data asset (`cic-ids-2017-curated`) in the workspace. Metrics were tracked via MLflow under experiment `intrusion_detection_phase2_experiment`.

### II.2 Model Validation

We used a three-way stratified split to avoid data leakage:

| Split | Proportion | Purpose |
|-------|-----------|---------|
| Train | 60% | Model fitting |
| Validation | 20% | Overfitting monitoring |
| Test | 20% | Held-out official result |

Stratification preserves the 80/20 class ratio in every split, preventing the model from seeing a skewed class distribution during evaluation.

**Test set results:**

| Metric | Baseline | Random Forest |
|--------|----------|---------------|
| Accuracy | 80.3% | 98.2% |
| Precision | 0.0% | 94.4% |
| Recall | 0.0% | 96.8% |
| F1 Score | 0.000 | 0.956 |
| AUC-ROC | — | 0.998 |

The Random Forest substantially outperforms the baseline across every metric. Our error analysis confirmed that false negatives (missed attacks) are rare and the train-to-test performance gap is minimal, indicating good generalisation rather than overfitting.

### II.3 Model Versioning and Registration

We registered the trained model in the **Azure ML Model Registry**:

- **Model name:** `intrusion-detection-model`
- **Artifacts stored:** `model.pkl`, `feature_columns.pkl`, `model_metadata.json`
- **Linked training job:** `intrusion_detection_phase2_experiment`
- **Tags:** dataset, feature set, training job ID

This ensures full traceability between the curated data version, training code, and the deployed model. `feature_columns.pkl` locks the inference feature schema, preventing silent column misalignment between training and serving.

### II.4 Deployment

We deployed the model as a **Managed Online Endpoint** on Azure ML for real-time inference:

- **Endpoint name:** `intrusion-endpoint-60104434`
- **Deployment name:** `blue` (100% traffic allocation)
- **Scoring script:** `src/score.py`
- **Instance type:** Standard_F2s_v2
- **Authentication:** key-based

The scoring script loads `model.pkl` and `feature_columns.pkl` on startup, aligns incoming request columns to the training schema, and returns predictions with class probabilities. We chose the blue/green deployment pattern so that future model versions can be introduced with incremental traffic shifting.

### II.5 Deployment Validation

We validated the deployed endpoint using `src/test_endpoint.py` with real samples drawn from the CIC-IDS-2017 test set:

- Single benign sample → prediction: 0 (Benign) — **PASS**
- Single attack sample → prediction: 1 (Attack) — **PASS**
- Batch request with mixed samples — **PASS**
- Response format validation (`predictions` + `probabilities` keys present, no `error` key) — **PASS**

We also performed an offline consistency check by reloading the serialised artifacts locally and confirming identical predictions to the in-memory model, verifying that `joblib` serialisation preserved the model faithfully.

After validation, we decommissioned the endpoint to avoid ongoing compute costs. The registered model remains available in the Azure ML workspace for future redeployment.

---

## Full Data Lineage

```
CIC-IDS-2017 raw CSVs (Azure Blob: raw/)
        |
        v
ETL Pipeline  (scripts/etl_pipeline.py)
        |
        v
Cleaned Dataset  (processed/cleaned_data.csv  —  79 features)
        |
        v
Feature Selection  (notebooks/eda_processed.ipynb  —  ANOVA F-test, k=15)
        |
        v
Curated Dataset  (curated/selected_features.csv  —  15 features)
        |
        v
Azure ML Training Job  (src/train.py  on  computeproject)
        |
        v
Registered Model  (intrusion-detection-model  —  Azure ML Registry)
        |
        v
Managed Online Endpoint  (intrusion-endpoint-60104434)  →  decommissioned post-validation
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Batch ingestion | Dataset is static; real-time streaming adds complexity with no benefit |
| Three-layer storage | Clear separation between raw, cleaned, and model-ready data |
| ANOVA F-test for selection | Fast, interpretable filter method suited for large tabular datasets |
| Random Forest | Handles non-linear relationships and mixed scales without preprocessing |
| Stratified splits | Preserves 80/20 class ratio across all partitions |
| Managed Online Endpoint | Simplest real-time serving option; no infrastructure management required |
| CPU compute only | Tabular data does not benefit from GPU acceleration |
| Endpoint decommissioned post-validation | Avoids ongoing cost; model stays registered for future use |
| `feature_columns.pkl` | Locks the feature schema so training/serving parity is enforced at load time |
| `random_state=42` everywhere | Ensures every split, model, and experiment is fully reproducible |

---

## Reproducibility

All steps are fully reproducible:
- `random_state=42` applied globally across all splits and model training
- Data assets registered with version numbers in Azure ML
- `feature_columns.pkl` locks the inference feature schema
- `data_catalog.json` documents exact transformations and class distributions
- `sorted(glob(...))` in ETL ensures deterministic file merge order

To reproduce the Phase 2 training job:
```bash
az ml job create --file jobs/train_job.yml \
  --workspace-name Amazon-Electronics-Lab-60104434 \
  --resource-group rg-60104434 \
  --subscription <your-subscription-id>
```

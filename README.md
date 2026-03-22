# Cloud-Based Machine Learning Pipeline for Network Intrusion Detection (Phase 1)
## Delson fernandes-60302101
## Anas shoaib-60104434
## Project Overview

As organizations increasingly rely on cloud infrastructure and online services, network security has become a critical concern. Modern networks are constantly exposed to threats such as denial-of-service attacks, port scanning, and unauthorized access. Traditional intrusion detection systems (IDS) often depend on predefined rules, which limits their ability to detect new or evolving attack patterns.

In this project, a machine learning-based Intrusion Detection System (IDS) is developed using a cloud-oriented data pipeline. The goal of Phase 1 is not to build the model itself, but to establish a **reliable and reproducible data foundation** that prepares network traffic data for future machine learning tasks.

---

## Dataset Description

* **Dataset**: CIC-IDS-2017 Intrusion Detection Dataset
* **Source**: Canadian Institute for Cybersecurity (University of New Brunswick)
* **Format**: CSV files (network flow features)

The dataset contains labeled network traffic flows representing both normal (benign) activity and multiple attack types such as DoS, brute-force attacks, and port scanning.

---

## Data Ingestion

The ingestion process follows a **batch ingestion strategy**, since the dataset is static and does not require real-time streaming.

* All raw CSV files were uploaded into Azure Blob Storage under the **`raw` container**.
* Data was initially staged on the Azure Machine Learning compute instance before being transferred to cloud storage.
* The original files were preserved without modification to ensure reproducibility and traceability.

### Storage Architecture

The dataset is organized into three logical layers:

```text
projectcloudcomputing
├── raw/        → original CSV files
├── processed/  → cleaned dataset
└── curated/    → feature-selected dataset
```

This layered design ensures clear separation between raw data, transformed data, and model-ready data.

---

## ETL Pipeline

An automated ETL (Extract, Transform, Load) pipeline was implemented using Python and executed on the Azure ML compute instance **`computeproject`**.

### Pipeline Steps

**1. Extraction**

* All CSV files were loaded from the raw data directory.
* Files were combined into a single dataset.

**2. Transformation**

* Column names were standardized by removing leading/trailing spaces.
* Infinite values were replaced with null values.
* Rows containing missing values were removed.
* The target column (`Label`) was converted into a binary format:

  * `0` → Benign traffic
  * `1` → Attack traffic

**3. Load**

* The cleaned dataset was saved as:

  * `processed/cleaned_data.csv`

This pipeline ensures that the data is clean, consistent, and ready for further analysis.

---

## Data Cataloging and Governance

A structured data organization approach was used to maintain clarity and traceability:

* **Raw Zone**: Stores original, unmodified data
* **Processed Zone**: Stores cleaned and validated data
* **Curated Zone**: Stores feature-engineered data for modeling

### Data Lineage

```text
Raw Data → ETL Pipeline → Processed Data → Feature Selection → Curated Data
```

This design allows every transformation step to be easily traced and reproduced.

---

## Exploratory Data Analysis (EDA)

A concise exploratory analysis was conducted on the processed dataset to evaluate data quality and readiness.

### Dataset Summary

* Total samples (after cleaning): **2,827,876**
* Number of features: **79**
* Target variable: **Label**

### Class Distribution

* Benign (0): **2,271,320 samples (80.32%)**
* Attack (1): **556,556 samples (19.68%)**

### Observations

* The dataset is **imbalanced**, with significantly more benign traffic than attack traffic.
* This imbalance is expected in real-world network data and will be addressed in Phase 2.
* The data contains a wide range of numerical values, representing different network behaviors.

---

## Feature Extraction and Selection

Feature selection was performed using a statistical method (**ANOVA F-test**) to identify the most relevant features.

### Selected Features

```text
Bwd Packet Length Max
Bwd Packet Length Mean
Bwd Packet Length Std
Flow IAT Max
Fwd IAT Std
Fwd IAT Max
Max Packet Length
Packet Length Mean
Packet Length Std
Packet Length Variance
Average Packet Size
Avg Bwd Segment Size
Idle Mean
Idle Max
Idle Min
```

### Justification

* These features capture important characteristics such as:

  * packet size distributions
  * flow timing behavior
  * traffic variability
* Reducing the number of features:

  * improves computational efficiency
  * reduces noise
  * helps models focus on meaningful patterns

The curated dataset was saved as:

```text
curated/selected_features.csv
```

---

## Azure Infrastructure

The pipeline was built and executed using Azure Machine Learning resources:


# Azure Machine Learning workspace was used - Amazon-Electronics-Lab-60302101
**rg-60302101**
* **Compute Instance**: `computeproject`
  Used for development, data processing, and ETL execution

* **Compute Cluster**: `computeclusterproject`
  Configured for scalable job execution and future pipeline automation

* **Storage Account**: `projectcloudcomputing`
  Used as the central data lake for all datasets

---

## Azure Deployment and Resource Optimization

The pipeline was executed within the Azure environment, and all datasets were successfully deployed to Azure Blob Storage.

* Raw, processed, and curated datasets are stored in the cloud
* The ETL process was executed on Azure compute resources
* The pipeline is designed to scale using the compute cluster

### Resource Optimization

* CPU-based compute was used, as the task involves tabular data processing
* GPU resources were avoided to reduce unnecessary cost
* The compute cluster was configured with a minimum node count of zero to prevent idle resource usage
* Batch processing was used for efficiency and simplicity

This ensures that the pipeline is both cost-efficient and scalable.

---

## Pipeline Overview

```text
Raw CSV Files (Azure Storage)
        ↓
ETL Pipeline (computeproject)
        ↓
Processed Dataset (cleaned_data.csv)
        ↓
Feature Selection
        ↓
Curated Dataset (selected_features.csv)
```

---

## Design Decisions and Scientific Rationale

Several key decisions were made during this phase:

* A **batch ingestion strategy** was chosen due to the static nature of the dataset
* A **layered data architecture** (raw, processed, curated) ensures reproducibility
* Feature selection was applied to reduce dimensionality and improve efficiency
* Azure ML was used to simulate a real-world cloud data pipeline

The approach aligns with the hypothesis that **statistical patterns in network traffic can distinguish between benign and malicious activity**.

---

## Conclusion

This phase successfully establishes a complete and reproducible data pipeline for a cloud-based intrusion detection system. The pipeline handles data ingestion, cleaning, transformation, analysis, and feature preparation in a structured and scalable manner.

The curated dataset produced in this phase will be used in Phase 2 for model development, validation, and deployment.

---

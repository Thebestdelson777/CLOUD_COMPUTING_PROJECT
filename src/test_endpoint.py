"""
Deployment validation script for the intrusion-detection-model endpoint.

Usage (run after endpoint is deployed):
    python src/test_endpoint.py --endpoint intrusion-endpoint-60104434 \
                                --subscription 86c2aaee-2c2c-4ba5-9650-714b68528e97 \
                                --resource-group rg-60104434 \
                                --workspace Amazon-Electronics-Lab-60104434

All arguments have defaults matching the project workspace so only
--subscription needs to be supplied.
"""

import argparse
import json
import sys

import requests
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential


# ---------------------------------------------------------------------------
# Sample payloads drawn directly from the CIC-IDS-2017 test set
# (random_state=42) to ensure the model sees realistic feature values.
# Using real samples avoids misclassification from synthetic out-of-distribution inputs.
# ---------------------------------------------------------------------------

BENIGN_SAMPLE = {
    "Bwd Packet Length Max": 66.0,
    "Bwd Packet Length Mean": 66.0,
    "Bwd Packet Length Std": 0.0,
    "Flow IAT Max": 200.0,
    "Fwd IAT Std": 0.0,
    "Fwd IAT Max": 3.0,
    "Max Packet Length": 66.0,
    "Packet Length Mean": 46.8,
    "Packet Length Std": 17.527,
    "Packet Length Variance": 307.2,
    "Average Packet Size": 58.5,
    "Avg Bwd Segment Size": 66.0,
    "Idle Mean": 0.0,
    "Idle Max": 0.0,
    "Idle Min": 0.0
}

ATTACK_SAMPLE = {
    "Bwd Packet Length Max": 6.0,
    "Bwd Packet Length Mean": 6.0,
    "Bwd Packet Length Std": 0.0,
    "Flow IAT Max": 60.0,
    "Fwd IAT Std": 0.0,
    "Fwd IAT Max": 0.0,
    "Max Packet Length": 6.0,
    "Packet Length Mean": 3.333,
    "Packet Length Std": 2.309,
    "Packet Length Variance": 5.333,
    "Average Packet Size": 5.0,
    "Avg Bwd Segment Size": 6.0,
    "Idle Mean": 0.0,
    "Idle Max": 0.0,
    "Idle Min": 0.0
}

# Note: ATTACK_SAMPLE has small packet sizes typical of port scanning / DoS attacks.
# The model learned this pattern from training data, not from packet payload size alone.


def get_ml_client(subscription_id, resource_group, workspace_name):
    """Create an Azure ML client using DefaultAzureCredential."""
    return MLClient(
        credential=DefaultAzureCredential(),
        subscription_id=subscription_id,
        resource_group_name=resource_group,
        workspace_name=workspace_name
    )


def get_endpoint_details(ml_client, endpoint_name):
    """Retrieve scoring URI and primary API key for the given endpoint."""
    endpoint = ml_client.online_endpoints.get(endpoint_name)
    keys = ml_client.online_endpoints.get_keys(endpoint_name)
    return endpoint.scoring_uri, keys.primary_key


def send_request(scoring_uri, api_key, records):
    """POST a list of records to the endpoint and return the parsed response."""
    payload = json.dumps({"data": records})
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.post(scoring_uri, data=payload, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def run_tests(scoring_uri, api_key):
    """
    Run functional validation tests against the deployed endpoint.
    Returns True if all tests pass, False otherwise.
    """
    all_passed = True

    print("\n" + "=" * 60)
    print("Deployment Validation Tests")
    print("=" * 60)

    # Test 1: single benign sample — expect prediction 0
    print("\nTest 1: Single benign sample")
    result = send_request(scoring_uri, api_key, [BENIGN_SAMPLE])
    pred = result.get("predictions", [None])[0]
    prob = result.get("probabilities", [None])[0]
    passed = (pred == 0)
    print(f"  Prediction  : {pred}  ({'Benign' if pred == 0 else 'Attack'})")
    if prob is not None:
        print(f"  Probability : {prob:.4f}")
    print(f"  Expected 0  : {'PASS' if passed else 'FAIL'}")
    all_passed = all_passed and passed

    # Test 2: single attack sample — expect prediction 1
    print("\nTest 2: Single attack sample")
    result = send_request(scoring_uri, api_key, [ATTACK_SAMPLE])
    pred = result.get("predictions", [None])[0]
    prob = result.get("probabilities", [None])[0]
    passed = (pred == 1)
    print(f"  Prediction  : {pred}  ({'Attack' if pred == 1 else 'Benign'})")
    if prob is not None:
        print(f"  Probability : {prob:.4f}")
    print(f"  Expected 1  : {'PASS' if passed else 'FAIL'}")
    all_passed = all_passed and passed

    # Test 3: batch request — 2 benign + 1 attack
    print("\nTest 3: Batch request (2 benign + 1 attack)")
    result = send_request(scoring_uri, api_key, [BENIGN_SAMPLE, BENIGN_SAMPLE, ATTACK_SAMPLE])
    preds = result.get("predictions", [])
    passed = (len(preds) == 3)
    print(f"  Predictions : {preds}")
    print(f"  Expected    : [0, 0, 1]")
    print(f"  Count check : {'PASS' if passed else 'FAIL'}")
    all_passed = all_passed and passed

    # Test 4: response format validation
    print("\nTest 4: Response format")
    result = send_request(scoring_uri, api_key, [BENIGN_SAMPLE])
    has_preds  = "predictions"   in result
    has_probs  = "probabilities" in result
    no_error   = "error"         not in result
    passed = has_preds and has_probs and no_error
    print(f"  Has 'predictions'   : {has_preds}")
    print(f"  Has 'probabilities' : {has_probs}")
    print(f"  No 'error' key      : {no_error}")
    print(f"  Format check        : {'PASS' if passed else 'FAIL'}")
    all_passed = all_passed and passed

    print("\n" + "=" * 60)
    print(f"Overall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 60)
    return all_passed


def main():
    parser = argparse.ArgumentParser(
        description="Validate the deployed intrusion detection endpoint"
    )
    parser.add_argument("--endpoint",       default="intrusion-endpoint-60104434")
    parser.add_argument("--subscription",   required=True, help="Azure subscription ID")
    parser.add_argument("--resource-group", default="rg-60104434")
    parser.add_argument("--workspace",      default="Amazon-Electronics-Lab-60104434")
    args = parser.parse_args()

    print(f"Connecting to workspace: {args.workspace}")
    ml_client = get_ml_client(args.subscription, args.resource_group, args.workspace)

    print(f"Fetching endpoint: {args.endpoint}")
    scoring_uri, api_key = get_endpoint_details(ml_client, args.endpoint)
    print(f"Scoring URI: {scoring_uri}")

    passed = run_tests(scoring_uri, api_key)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()

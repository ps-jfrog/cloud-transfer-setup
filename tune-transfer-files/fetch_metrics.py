import requests
import argparse
import os
import json
from datetime import datetime

def get_metrics(base_url, access_token, endpoint):
    url = f"{base_url}/{endpoint}"
    headers = {
        "Accept": "*/*",
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    return response.text

def save_metrics(metrics, filename):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{filename}_{timestamp}.txt"
    with open(output_file, 'w') as f:
        f.write(metrics)
    print(f"Metrics saved to {output_file}")

def parse_args():
    parser = argparse.ArgumentParser(description='Fetch JFrog Metrics')
    parser.add_argument('--base-url', '-u',
                      help='JFrog base URL (e.g., https://your-domain.jfrog.io)')
    parser.add_argument('--access-token', '-t',
                      help='JFrog Access Token')
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Priority: Command line args > Environment variables
    base_url = (args.base_url or 
                os.environ.get('JFROG_BASE_URL'))
    access_token = (args.access_token or 
                   os.environ.get('JFROG_ACCESS_TOKEN'))
    
    if not base_url or not access_token:
        raise ValueError("Base URL and Access Token must be provided via arguments or environment variables")
    
    # Remove trailing slash if present
    base_url = base_url.rstrip('/')
    
    # Fetch metrics from both endpoints
    try:
        print("Fetching Artifactory metrics...")
        artifactory_metrics = get_metrics(base_url, access_token, "artifactory/api/v1/metrics")
        save_metrics(artifactory_metrics, "artifactory_metrics")
        
        print("\nFetching Observability metrics...")
        observability_metrics = get_metrics(base_url, access_token, "observability/api/v1/metrics")
        save_metrics(observability_metrics, "observability_metrics")
        
        print("\nMetrics fetched successfully!")
    except Exception as e:
        print(f"Error fetching metrics: {e}")

if __name__ == "__main__":
    main() 
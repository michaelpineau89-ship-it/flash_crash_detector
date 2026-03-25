# 📉 Flash Crash Detector (Real-Time Stream Processing)

![Python Version](https://img.shields.io/badge/python-3.11-blue)
![GCP Service](https://img.shields.io/badge/service-Dataflow-orange)
![GCP Service](https://img.shields.io/badge/service-Cloud%20Functions-orange)
![License](https://img.shields.io/badge/license-MIT-green)

A real-time data engineering pipeline designed to detect "Flash Crash" anomalies in stock market data. This project leverages **Google Cloud Platform (GCP)** serverless technologies to ingest, process, and analyze financial data streams with sub-minute latency.

## 🏗️ Logical Architecture

This system uses a **Poller Pattern** for ingestion and a **Streaming Pipeline** for processing.

```mermaid
graph LR
    %% External & Local Edge Ingestion
    subgraph Edge ["Local Environment (Oshawa)"]
        direction TB
        Binance(("Binance Global\nWebSocket API"))
        Ingest["Python Ingestion Script\n(main.py)"]
        Binance -- "Raw JSON Trades" --> Ingest
    end

    %% CI/CD and Security Plane
    subgraph CICD ["Control Plane & Security"]
        direction TB
        GH["GitHub Actions\n(Workload Identity)"]
        AR["Artifact Registry\n(Container Scanning API)"]
        TF["Terraform\n(Infrastructure as Code)"]
        SA["Custom Service Account\n(Least Privilege IAM)"]

        GH -- "Builds & Pushes" --> AR
        GH -- "Deploys" --> TF
    end

    %% Google Cloud Data Plane
    subgraph GCP ["Google Cloud (us-central1)"]
        direction TB
        PS[["Cloud Pub/Sub\n(crypto-ticks)"]]
        
        subgraph Dataflow ["Cloud Dataflow (Streaming Engine)"]
            direction LR
            Read["ReadFromPubSub"]
            Parse["ParseJSON"]
            Window["WindowIntoMinutes\n(60s)"]
            Group["GroupByKey\n(Network Shuffle)"]
            Calc["CalculateStats\n(drop_pct)"]
            Write["WriteToBigQuery"]

            Read --> Parse --> Window --> Group --> Calc --> Write
        end
        
        BQ[("BigQuery\n(aggregated_stats table)")]
    end

    %% Cross-Boundary Connections
    Ingest -- "HTTPS / TLS\n(Encrypted Bytes)" --> PS
    PS --> Read
    Write --> BQ
    TF -. "Provisions Architecture" .-> GCP
    AR -. "Pulls Docker Template" .-> Dataflow
    SA -. "Secures Execution" .-> Dataflow

    %% Styling to make it look sharp
    classDef gcp fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000;
    classDef external fill:#f5f5f5,stroke:#9e9e9e,stroke-width:2px,color:#000;
    classDef cicd fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#000;
    classDef dataflow fill:#e8f5e9,stroke:#388e3c,stroke-width:2px,color:#000;
    
    class Edge,Binance,Ingest external;
    class GCP,PS,BQ gcp;
    class CICD,GH,AR,TF,SA cicd;
    class Dataflow,Read,Parse,Window,Group,Calc,Write dataflow;
```

## 🧩 System Components

### 1. The Ingestion Layer (`/src/ingestion`)
* **Service:** Cloud Functions (Gen 2) triggered by Cloud Scheduler.
* **Role:** Fetches real-time stock quotes from the **Alpha Vantage API** every 60 seconds and publishes the payload to a Pub/Sub topic.
* **Key Tech:** Python 3.11, `requests`, Google Pub/Sub Client.

### 2. The Processing Layer (`/src/pipeline`)
* **Service:** Cloud Dataflow (Apache Beam).
* **Role:** Subscribes to the data stream, groups data into fixed 1-minute windows, and calculates the percentage drop from the window's opening price to the current price.
* **Logic:** If a drop exceeds the defined threshold (e.g., 5%), the event is flagged as a "Crash" and routed to a high-priority BigQuery table.

## 🛠️ Local Development Setup

### Prerequisites
* **Python 3.11** (Required for Apache Beam compatibility)
* **Google Cloud SDK**
* Alpha Vantage API Key

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/michaelpineau89-ship-it/flash_crash_detector.git](https://github.com/michaelpineau89-ship-it/flash_crash_detector.git)
    cd flash_crash_detector
    ```

2.  **Create a Virtual Environment:**
    *Note: Ensure you use Python 3.11 to avoid build errors with Apache Beam.*
    ```bash
    python3.11 -m venv env
    source env/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Connectivity Test
Verify that your environment can reach the external stock API.
```bash
python3 src/verify_connectivity.py --api_key="YOUR_API_KEY"
```


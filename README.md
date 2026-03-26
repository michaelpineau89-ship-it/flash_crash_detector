# High-Frequency Crypto Ingestion & Analytics Pipeline

![Python Version](https://img.shields.io/badge/python-3.11-blue)
![GCP Service](https://img.shields.io/badge/service-Dataflow-orange)
![GCP Service](https://img.shields.io/badge/service-Cloud%20Functions-orange)
![License](https://img.shields.io/badge/license-MIT-green)



An enterprise-grade streaming data pipeline designed to process high-frequency cryptocurrency trades (BTC/USDT) with sub-second latency. This project demonstrates modern, cloud-native streaming patterns, infrastructure-as-code (IaC), and strict DevSecOps integrations.

## 🏗 Architecture Blueprint

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
## 🚀 Project Overview

This architecture captures live WebSocket ticks from the Binance global exchange, securely queues them in Google Cloud Pub/Sub, and leverages Apache Beam (Cloud Dataflow) to aggregate the raw data into 1-minute tumbling windows. The aggregated statistics—including volume, price action, and automated flash-crash detection—are continuously streamed into BigQuery for downstream analytics.

## 🛠 Core Technologies

* **Ingestion:** Python, `websocket-client`, Google Cloud Pub/Sub
* **Stream Processing:** Apache Beam, Google Cloud Dataflow (Streaming Engine)
* **Data Warehousing:** Google BigQuery
* **Infrastructure as Code (IaC):** Terraform
* **CI/CD & Security:** GitHub Actions, Workload Identity Federation (WIF), Artifact Registry (Container Scanning API)

## 🧠 Engineering Challenges Solved

Building a resilient streaming pipeline requires navigating complex distributed systems architectures. Key solutions implemented in this project include:

* **Stateful Edge Ingestion:** Bypassed the ephemeral, stateless nature of serverless containers (which aggressively throttle CPU and drop long-running WebSockets) by deploying a dedicated, persistent Python ingestion worker that handles automated reconnects and 451 geo-block routing.
* **Distributed Serialization Barriers:** Overcame Apache Beam's complex distributed memory model by implementing dynamic "inner imports" and `save_main_session` configurations, ensuring isolated Dataflow worker VMs could successfully hydrate and execute Python dependencies across the network.
* **Liquid Sharding & Firewall Optimization:** Eliminated the need to open internal TCP ports (`12345-12346`) on the VPC by enabling Dataflow Streaming Engine, offloading the heavy `GroupByKey` network shuffle to Google's managed backend while unlocking infinite worker scaling.

## 🔒 Security & Cost Optimization (Production Tiering)

While this repository demonstrates a highly scalable Proof-of-Concept, it is built with production-grade security and cost controls in mind:

* **Least Privilege IAM:** The Dataflow workers do not run as project editors. They operate under a strictly scoped custom Service Account with precise bindings (`dataflow.worker`, `pubsub.subscriber`, `bigquery.dataEditor`).
* **Automated Vulnerability Scanning:** Artifact Registry is configured with the Container Scanning API to automatically cross-reference new Docker pushes against global CVE databases before deployment.
* **Stateless Key Management:** Zero static JSON service account keys are stored or used. GitHub Actions securely authenticates to Google Cloud via OpenID Connect (OIDC) and Workload Identity Federation.
* **Cost Engineering:** The architecture can be adapted to utilize Preemptible/Spot VMs for the ingestion layer and BigQuery micro-batching to drastically reduce streaming insert costs without sacrificing data integrity.


---
**Architected by Mike** *Google Certified Data Engineer | 10+ Years IT Industry Experience* **Freelance Data Solutions**
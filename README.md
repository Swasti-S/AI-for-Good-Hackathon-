# 🏠 AI Home Inspection Intelligence
**AI-Assisted Autonomous Building Inspection System**

![Snowflake](https://img.shields.io/badge/Built%20With-Snowflake-29B5E8?logo=snowflake)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?logo=streamlit)
![Hackathon](https://img.shields.io/badge/Hackathon-AI%20For%20Good-blue)
![Status](https://img.shields.io/badge/Status-Prototype-green)

> **Turning messy inspection photos into life-saving safety scores.**
> An autonomous Snowflake-native pipeline that watches for defects 24/7, rates building safety in real-time, and empowers home buyers with transparent data.

---

## 🧐 The Problem
Home buyers and tenants in India often have little visibility into hidden issues in new or under-construction buildings—such as damp walls, exposed wiring, or structural cracks. These risks are often buried in scattered photos and unorganized inspection notes, leading to unsafe living conditions and zero accountability for developers.

## 💡 The Solution
**AI Home Inspection Intelligence** is a fully automated pipeline that runs entirely on the **Snowflake Data Cloud**:
1.  **Ingests** raw inspection images and notes into internal stages.
2.  **Auto-Detects** defects using **Snowflake Cortex AI**.
3.  **Calculates** a live "Safety Risk Score" for every property using Dynamic Tables.
4.  **Visualizes** risks on an interactive dashboard for buyers and regulators.

---

## 🏗️ Architecture & Process Flow

*Figure 1: Autonomous Event-Driven Process Flow*

<img width="1672" height="820" alt="image (4)" src="https://github.com/user-attachments/assets/053f913b-ba2d-4f49-b644-6c6572fabf48" />


### 🔄 Technical Workflow

#### **1. Ingestion & Event Detection (The Trigger)**
* **Data Source:** Inspectors upload raw images and text notes to a **Snowflake Internal Stage**.
* **Event Trigger:** **Snowflake Streams** monitor the stage for new files. The moment a file lands, the stream captures the change and triggers the downstream pipeline instantly.

#### **2. Autonomous Processing Layer (The Core)**
* **Orchestration:** **Serverless Tasks** are automatically executed when the stream detects new data.
* **AI Processing:**
    * **Vision:** The task calls **Cortex Vision (`AI_CLASSIFY`)** to scan pixel data and tag defects (e.g., "Crack", "Damp", "Wiring").
    
* **Result:** Structured data is written to the `PROCESSED_DEFECTS` table.

#### **3. Scoring Engine (The Logic)**
* **Transformation:** **Dynamic Tables** act as a continuous transformation engine. They aggregate the processed defects and apply a weighted scoring algorithm (e.g., *Wiring Issue = 10 pts, Paint Issue = 2 pts*).
* **Output:** A live `Risk Score` (0-100) is calculated for every room and property in near real-time.

#### **4. Semantic & Consumption Layer (The User)**
* **Semantic View:** A simplified data layer that maps complex tables to business terms for easier querying.
* **Natural Language Querying:** **Cortex Analyst** sits on top of the semantic view, allowing users to ask plain-text questions like *"Show me properties with high structural risk."*
* **Visualization:** A **Streamlit** dashboard displays the final Risk Scores and defect images.

---

## 🛠️ Tech Stack
* **Core Platform:** Snowflake Data Cloud
* **AI & ML:** Snowflake Cortex (`AI_CLASSIFY`, `AI_COMPLETE`, `Cortex Analyst`,`Cortex Agent`)
* **Automation:** Snowflake Streams & Serverless Tasks (Event-Driven Architecture)
* **Data Engineering:** Dynamic Tables (Real-time Risk Scoring), Directory Tables (Unstructured Data)
* **Frontend:** Streamlit in Snowflake (Python)


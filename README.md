# 🏠 Digital Inspector for India
**AI-Assisted Autonomous Building Inspection System**

![Snowflake](https://img.shields.io/badge/Built%20With-Snowflake-29B5E8?logo=snowflake)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?logo=streamlit)
![Hackathon](https://img.shields.io/badge/Hackathon-AI%20For%20Good-blue)
![Status](https://img.shields.io/badge/Status-Prototype-green)

> **Turning messy inspection photos into life-saving safety scores.**
> An autonomous Snowflake-native agent that watches for defects 24/7, rates building safety in real-time, and empowers home buyers with transparent data.

---

## 🧐 The Problem
Home buyers and tenants in India often have little visibility into hidden issues in new or under-construction buildings—such as damp walls, exposed wiring, or structural cracks. These risks are often buried in scattered photos and unorganized inspection notes, leading to unsafe living conditions and zero accountability for "slumlords."

## 💡 The Solution
**Digital Inspector** is a fully automated AI pipeline that runs entirely on the Snowflake Data Cloud:
1.  **Ingests** raw inspection images and notes into internal stages.
2.  **Auto-Detects** defects using **Snowflake Cortex AI** (Vision & NLP).
3.  **Calculates** a live "Safety Risk Score" for every property using Dynamic Tables.
4.  **Visualizes** risks on an interactive dashboard for buyers and regulators.

---

## 🏗️ Architecture & Process Flow
The system uses a multi-agent approach to separate automated processing from user interaction.


### 🔄 How It Works (The "Agents")

#### **🤖 Agent 1: The Autonomous Inspector (Backend)**
* **Trigger:** Watches a Snowflake Internal Stage for new file uploads using **Snowflake Streams**.
* **Action:** Triggers a **Serverless Task** (`auto_classify`) every minute.
* **Intelligence:**
    * **Vision:** Uses `AI_CLASSIFY` to tag images (e.g., "Crack", "Damp", "Wiring").
    * **NLP:** Uses `AI_SENTIMENT` to detect negative/critical tone in inspector notes.

#### **📊 Agent 2: The User Assistant (Frontend)**
* **Logic:** A **Dynamic Table** constantly re-calculates the `Risk Score` (0-100) based on weighted defects.
* **Interface:** A **Streamlit** dashboard allows users to select a property and see its status (CRITICAL / WARNING / PASS).
* **Q&A:** Integrated **Cortex Analyst** allows users to ask questions like *"Show me all damp rooms"* in plain English.

---

## 🛠️ Tech Stack
* **Platform:** Snowflake Data Cloud
* **AI & ML:** Snowflake Cortex (`AI_CLASSIFY`, `AI_SENTIMENT`, `Cortex Analyst`)
* **Orchestration:** Snowflake Streams & Tasks (Cron-based automation)
* **Data Engineering:** Dynamic Tables (Near real-time processing), Snowpark Python
* **Frontend:** Streamlit in Snowflake

---

## 🚀 Key Features

* **Zero-Touch Automation:** No manual "run" button needed. Upload a photo, and the risk score updates automatically.
* **Multi-Modal Analysis:** Combines visual data (images) and text data (notes) for a unified risk assessment.
* **Weighted Scoring Engine:** Prioritizes critical dangers (e.g., Exposed Wiring = 10 pts) over cosmetic issues (e.g., Peeling Paint = 2 pts).
* **Natural Language Search:** Chat with your inspection data to find specific evidence without writing SQL.

---

## 💻 Core Logic Snippets

### 1. Autonomous Classification Task
*Automatically tags new images and notes every minute.*

```sql
CREATE OR REPLACE TASK auto_classify
  WAREHOUSE = my_wh
  SCHEDULE = 'USING CRON * * * * * UTC'
AS
BEGIN
  -- Vision: Classify new images
  INSERT INTO image_defects (image_path, defect_type)
  SELECT image_path,
    AI_CLASSIFY('classify inspection defect', image_path, ['crack', 'damp', 'wiring', 'ok'])
  FROM image_metadata WHERE METADATA$IS_NEW;

  -- NLP: Analyze sentiment
  INSERT INTO text_inspection_issues (property_id, sentiment)
  SELECT property_id, AI_SENTIMENT(notes)
  FROM inspection_notes WHERE METADATA$IS_NEW;
END;

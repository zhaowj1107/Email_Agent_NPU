# Email Agent with NPU

## 📌 Brief Introduction

**Features:**
- 📬 **24/7 Email Monitoring**
- 📊 **Email Analysis & Categorization:**
  - **A (Archive - Low Priority):** Automatically archive.
  - **B (Reply - Medium Priority):** Auto-reply using LLM.
  - **M (Meeting/Important - High Priority):** Draft an email & send a WhatsApp notification.

**Platform:**
- Built for **Snapdragon X Elite**, designed to be **platform-agnostic** (performance may vary).

---

## 🖥️ Hardware

| Component | Specification |
|-----------|--------------|
| **Machine** | Dell Latitude 7455 |
| **Chip** | Snapdragon X Elite |
| **OS** | Windows 11 |
| **Memory** | 32 GB |

---

## 🛠️ Software

| Component | Specification |
|-----------|--------------|
| **Python Version** | 3.12.6 |
| **LLM Provider** | Qualcomm QNN (via AnythingLLM) |
| **LLM Model** | Llama 3.1 8B Chat (8K Context) |

### 🔧 Setup Instructions
1. Install and setup **AnythingLLM**.
2. Choose **Qualcomm QNN** as the LLM provider.
3. Select **Llama 3.1 8B Chat (8K Context)** as the model.
4. Create a workspace by clicking **"+ New Workspace"**.
5. Generate an API key:
   - Click **Settings** (bottom left panel).
   - Open **"Tools" > "Developer API"**.
   - Click **"Generate New API Key"**.

---

## ☁️ Google Cloud Services Integration

This project integrates **Google Calendar API** & **Gmail API** using **OAuth 2.0 authentication**.

### ✅ Prerequisites

#### 1️⃣ Create a Google Cloud Project
- Go to the [Google Cloud Console](https://console.cloud.google.com/).
- Log in with your Google account.
- Create a **new project**.
- Navigate to **API & Services > Library**.
- Enable **Google Calendar API** & **Gmail API**.

#### 2️⃣ Set Up OAuth 2.0 Authentication
- Go to **API & Services > Credentials**.
- Click **"Create Credentials" > "OAuth 2.0 Client ID"**.
- Configure application details & OAuth consent screen.
- Set up the redirect URI (local or production environment).
- Generate & download the **`credentials.json`** file.

### ⚠️ Important Notes
- Avoid credential conflicts by using separate token files:
  - `token_calendar.pickle` → **Google Calendar**.
  - `token_gmail.pickle` → **Gmail**.
- Ensure correct token file paths (they may exist in the root directory).

---

## 📦 Project Setup

### 1️⃣ Install Dependencies
Ensure Python 3.x is installed, then run:

```bash
pip install -r requirements.txt
```

---

This document provides a structured and easy-to-follow guide for setting up and running the Email Agent with NPU support.

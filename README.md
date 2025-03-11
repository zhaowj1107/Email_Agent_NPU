# Google Cloud Services Integration

This project integrates with **Google Calendar API** and **Gmail API** using **OAuth 2.0 authentication**. It allows you to access and interact with Google Calendar and Gmail data.

## Prerequisites

Before using Gmail and Google Calendar, you need to set up Google Cloud Services.

### 1. Create a Google Cloud Project
- Go to the [Google Cloud Console](https://console.cloud.google.com/).
- Log in with your Google account.
- Create a new project.
- In the left navigation pane, select **API & Services > Library**.
- Search for and enable the **Google Calendar API**.

### 2. Set Up OAuth 2.0 Authentication
- In the Google Cloud Console, go to **API & Services > Credentials**.
- Click on **Create Credentials** and select **OAuth 2.0 Client ID**.
- Configure your application details and select the correct OAuth consent screen.
- Set up the redirect URI (this can be your local callback URL or production environment URL).
- Generate and download the credentials file (`credentials.json`).

### Important Notes
- Be aware that there might be a conflict between the credentials files for Google Calendar API and Gmail API. To avoid conflicts, we use different filenames for the token files:
  - `token_calendar.pickle` for Google Calendar.
  - `token_gmail.pickle` for Gmail.
- Make sure to check the paths of the two pickle files. They may exist in the root directory rather than the project directory.

## Project Setup

### 1. Install Dependencies
Make sure you have Python 3.x installed and then install the required dependencies:

```bash
pip install -r requirements.txt
```

Chinese
----------------
在使用Gmail和Google Calendar前，需要使用Google Cloud Service
1. 创建一个 Google Cloud 项目
转到 Google Cloud Console，然后登录您的 Google 帐号。
创建一个新项目。
在左侧导航栏选择 API 和服务 > 库。
搜索并启用 Google Calendar API。

2. 设置 OAuth 2.0 认证
在 Google Cloud Console 中，进入 API 和服务 > 凭据。
点击 创建凭据，选择 OAuth 2.0 客户端 ID。
配置您的应用信息并选择正确的 OAuth 同意屏幕。
设置重定向 URI（可以是本地回调地址或生产环境的 URL）。
生成并下载 凭据文件（credentials.json）。

注意事项：请注意google Calendar API和gmail API的凭证存储文件(token.pickle)会存在冲突，在我们的项目中我们分别命名为token_calendar.pickle和token_gmail.pickle
同时请注意两个pickle文件的路径，两个文件可能存在于根目录而不是项目目录中。

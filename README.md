# LINE Photo & Note Uploader for Construction Sites

This application is a stateful service designed to streamline the process of collecting photos and notes from construction sites via the LINE Messaging API and automatically uploading them to organized folders in Google Drive.

## 🚀 Setup for Development 

To get the application running on your local machine, you need to set up configuration files and environment variables.

### 1. Configuration & Secret Files

This project requires three main JSON files for configuration and authentication. These files are sensitive and are listed in `.gitignore`, so they should **never** be committed to version control.

| Filename             | Description                                                                                                                                                                                            | How to Create                                                                                                                                                             |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `config.json`        | **[Required]** Manages application settings, including the mapping of secret codes to group names and the list of admin user IDs.                                                                        | Copy the template file: `cp config.json.template config.json`. Then, edit the file to add your own secret codes and admin LINE User IDs.                                    |
| `credentials.json`   | **[Required]** Contains the OAuth 2.0 Client ID and secret from Google Cloud. This is necessary for the application to ask for permission to access your Google Drive.                                    | Download this file from your project in the [Google Cloud Console](https://console.cloud.google.com/apis/credentials) under the "OAuth 2.0 Client IDs" section.               |
| `token.json`         | **[Auto-Generated]** Stores the access and refresh tokens that Google provides after you grant permission. The application uses this file to make authenticated API calls without asking you to log in every time. | This file is created automatically by running the `run_once_to_login.py` script after you have placed your `credentials.json` in the project root: `python run_once_to_login.py` |

### 2. Environment Variables

After setting up the JSON files, create the `.env` file to store other secrets.

1.  **Create the Environment File:**
    ```bash
    cp .env.example .env
    ```

2.  **Fill in the Variables:**
    Open the newly created `.env` file and fill in the values for each variable.

| Variable                    | Description                                                                                                                                                             | Example                               |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| `LINE_CHANNEL_ACCESS_TOKEN` | **[Required]** The long-lived channel access token for your LINE Messaging API. You can get this from the [LINE Developers Console](https://developers.line.biz/console/). | `YOUR_CHANNEL_ACCESS_TOKEN`           |
| `LINE_CHANNEL_SECRET`       | **[Required]** The channel secret for your LINE Messaging API, used to validate webhook signatures. Also found in the LINE Developers Console.                            | `YOUR_CHANNEL_SECRET`                 |
| `PARENT_FOLDER_ID`          | **[Optional]** The ID of the parent folder in Google Drive where all project folders will be created. If left empty, folders will be created in the root of "My Drive". | `1aBcDeFgHiJkLmNoPqRsTuVwXyZ-12345` |
| `SENTRY_DSN`                | **[Optional]** The Data Source Name (DSN) for Sentry.io integration, used for error tracking and performance monitoring.                                                | `https://xxxxxxxx@xxxx.ingest.sentry.io/xxxxxxx` |
| `REDIS_URL`                 | **[Optional]** The connection URL for your Redis instance. This is used for checking duplicate webhook events to prevent processing the same event multiple times.       | `redis://user:password@host:port`      |
# Strava Data Downloader

This project allows you to download your running and cycling data from Strava and save it locally as JSON for further analysis.

## 📌 Core Prerequisites

Before running this project, users must obtain **client_id** and **client_secret** from Strava.

To do this:
1. Log in to your [Strava account](https://www.strava.com/).
2. Navigate to **Settings → My API Application**.
3. Create a new API application.
4. Copy the generated **Client ID** and **Client Secret**.
5. Store them securely (e.g., in your `.env` file or system keyring).

These credentials are required for authenticating with the Strava API.

## 🚀 Usage

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/strava-downloader.git
   cd strava-downloader
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in `.env` file:
   ```env
   CLIENT_ID=your_client_id
   CLIENT_SECRET=your_client_secret
   ```

4. Run the script to download your activities:
   ```bash
   python main.py
   ```

Downloaded activities will be saved into the `runs.json` file in your project folder.

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

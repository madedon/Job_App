"""
Google Drive Upload Tool
Uploads files to Google Drive using OAuth credentials.

Usage: python tools/gdrive_upload.py <file_path> [folder_name]

Note: When running inside Claude Code, prefer using the built-in
Google Drive MCP connector (mcp__claude_ai_Google_Drive__*) instead
of this script for seamless authentication.
"""

import os, sys
from pathlib import Path

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:
    print("ERROR: Google API libraries not installed.")
    print("Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    exit(1)

PROJECT_ROOT = Path(__file__).parent.parent
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/drive",
]
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token_drive.json"


def authenticate():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        if not creds or not creds.valid:
            if not CREDENTIALS_FILE.exists():
                print(f"ERROR: {CREDENTIALS_FILE} not found.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def find_or_create_folder(service, folder_name):
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, spaces="drive", fields="files(id, name)").execute()
    folders = results.get("files", [])
    if folders:
        return folders[0]["id"]
    metadata = {"name": folder_name, "mimeType": "application/vnd.google-apps.folder"}
    folder = service.files().create(body=metadata, fields="id").execute()
    print(f"  Created folder: {folder_name}")
    return folder["id"]


def upload_file(service, file_path, folder_id=None):
    file_path = Path(file_path)
    metadata = {"name": file_path.name}
    if folder_id:
        metadata["parents"] = [folder_id]
    ext = file_path.suffix.lower()
    mime_types = {
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain", ".json": "application/json", ".csv": "text/csv",
    }
    mime = mime_types.get(ext, "application/octet-stream")
    media = MediaFileUpload(str(file_path), mimetype=mime, resumable=True)
    if folder_id:
        query = f"name='{file_path.name}' and '{folder_id}' in parents and trashed=false"
        existing = service.files().list(q=query, spaces="drive", fields="files(id)").execute()
        if existing.get("files"):
            file_id = existing["files"][0]["id"]
            service.files().update(fileId=file_id, media_body=media).execute()
            print(f"  Updated existing file: {file_path.name}")
            return file_id
    file = service.files().create(body=metadata, media_body=media, fields="id,webViewLink").execute()
    return file.get("id")


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/gdrive_upload.py <file_path> [folder_name]")
        sys.exit(1)
    file_path = sys.argv[1]
    folder_name = sys.argv[2] if len(sys.argv) > 2 else "Job Search Tracker"
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)
    print(f"Uploading: {file_path}")
    print(f"To folder: {folder_name}")
    creds = authenticate()
    if not creds:
        sys.exit(1)
    service = build("drive", "v3", credentials=creds)
    folder_id = find_or_create_folder(service, folder_name)
    file_id = upload_file(service, file_path, folder_id)
    file_info = service.files().get(fileId=file_id, fields="webViewLink").execute()
    link = file_info.get("webViewLink", "")
    print(f"\nUpload complete!")
    print(f"File ID: {file_id}")
    print(f"View: {link}")


if __name__ == "__main__":
    main()

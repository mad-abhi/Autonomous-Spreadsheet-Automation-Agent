import os
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_google_credentials():
    """
    Resolves credentials using Service Account (preferred) or OAuth2 user login fallback.
    """
    # 1. Check for Service Account Key
    if os.path.exists("service_account.json"):
        return Credentials.from_service_account_file("service_account.json", scopes=SCOPES)

    # 2. OAuth2 Desktop Client flow
    creds = None
    if os.path.exists("token.json"):
        creds = UserCredentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif os.path.exists("credentials.json"):
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token_file:
                token_file.write(creds.to_json())
        else:
            raise FileNotFoundError(
                "Neither 'service_account.json' nor 'credentials.json' was found in the project root."
            )
    return creds


def upload_to_google_sheets(title: str, data: list[dict]) -> str:
    """
    Creates and styles a new Google Sheet, populating it with tabular records.
    Returns the live URL of the created sheet.
    """
    creds = get_google_credentials()
    sheets_service = build("sheets", "v4", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    # 1. Create Spreadsheet
    spreadsheet_body = {"properties": {"title": title}}
    spreadsheet = sheets_service.spreadsheets().create(
        body=spreadsheet_body, 
        fields="spreadsheetId,spreadsheetUrl"
    ).execute()
    sheet_id = spreadsheet.get("spreadsheetId")
    sheet_url = spreadsheet.get("spreadsheetUrl")

    if not data:
        return sheet_url

    headers = list(data[0].keys())
    display_headers = [str(h).replace("_", " ").title() for h in headers]
    rows = [display_headers] + [[row.get(h, "") for h in headers] for row in data]

    # 2. Append Data Values
    sheets_service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range="Sheet1!A1",
        valueInputOption="USER_ENTERED",
        body={"values": rows}
    ).execute()

    # 3. Apply Professional Styling (Navy Header + White Bold Text + Auto-Resize)
    requests = [
        # Style Header Row
        {
            "repeatCell": {
                "range": {
                    "sheetId": 0,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": len(headers)
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.0, "green": 0.2, "blue": 0.4},  # Deep Navy
                        "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True, "fontSize": 10},
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        },
        # Auto-fit Column Widths
        {
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": 0,
                    "dimension": "COLUMNS",
                    "startIndex": 0,
                    "endIndex": len(headers)
                }
            }
        }
    ]

    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": requests}
    ).execute()

    # 4. Make Sheet publicly accessible with link (Viewer/Editor)
    try:
        drive_service.permissions().create(
            fileId=sheet_id,
            body={"type": "anyone", "role": "writer"}
        ).execute()
    except Exception:
        # Ignore permission failures (e.g. strict organizational GSuite policies)
        pass

    return sheet_url
# Mamourart Transport Automation — Email Integration V3 / Real Mailbox V1

This version continues V2 and connects the ingestion layer to a real mailbox safely.

## What is implemented

- `missions.csv` remains the mission source of truth; existing missions are preserved.
- Real IMAP mailbox access uses SSL/TLS and opens the mailbox in **read-only** mode.
- Messages are fetched with `BODY.PEEK[]` and stable IMAP UIDs.
- Only configured senders/domains are accepted.
- Duplicate mission references are ignored.
- Processed email IDs are tracked locally.
- A mailbox secret is never written to project files.
- The dashboard can prompt for the secret with masked input and pass it only to the import subprocess.
- Outlook/Microsoft 365 password-only IMAP is blocked because OAuth2/Modern Authentication is required.

## Provider presets

- Gmail: `imap.gmail.com:993`. For this temporary MVP, use an app password only when Google allows it for the account; OAuth is preferred long term.
- OVH MX Plan Europe: `imap.mail.ovh.net:993`.
- Infomaniak: `mail.infomaniak.com:993`.
- Outlook/Microsoft 365: OAuth2 remains a dedicated next step.
- Custom: enter the provider IMAP hostname and port.

## Installation into the current project

Copy the V3 files into the existing project folder, keeping your existing business data files if they are newer.

Then run:

```bat
python -m unittest -v test_email_integration.py
python apply_dashboard_patch.py
```

The patcher creates `app.py.before-email-v3.bak` before modifying the dashboard.

## Configure the real mailbox

```bat
python real_mailbox.py setup
```

Enter the provider, mailbox address, and at least one authorized client sender or domain. No mailbox password is saved.

## Safe connection test

```bat
python real_mailbox.py test
```

The secret is typed locally with hidden input. The connection is read-only and nothing is imported.

## First real import

Either use:

```bat
python real_mailbox.py import
```

or launch:

```bat
python app.py
```

and click **Import Emails**. When a real mailbox is configured, the dashboard asks for the secret with masked input, imports only authorized valid messages, and refreshes the mission table.

After reviewing a new mission, click **Run Automation** to propose a driver. Approval/rejection stays human-controlled.

## Data safety

The package's `missions.csv` contains only the five existing project missions TR-3001 to TR-3005. `TEST-001` is stored only in `samples/` and is never automatically imported.

# Zindi Submission Automation Bot

# **Co‑author:** Nighat Shabbir

<aside>
🧭

**Legend — Official Icons**

- Zindi: 🏆
- Jira (Atlassian): 📋
- SharePoint: 📁
- Bitbucket: 🧑‍💻

</aside>
<aside>
🌐

**EXTERNAL SYSTEMS**

</aside>

╔══════════════════════════════════════════════════════════════════════╗

║        ZINDI AUTOMATION SUBMISSION BOT — MACRO ARCHITECTURE           ║

╚══════════════════════════════════════════════════════════════════════╝

---

## 🌐 **EXTERNAL SYSTEMS LAYER**

```
┌─────────────────────────────────────────────────────────────┐
│EXTERNAL SYSTEMS                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
│  │   Zindi API   │   │   Jira API   │   │ SharePoint   │   │
│  │    🏆        │   │    📋        │   │    📁        │   │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘   │
│         │                  │                  │           │
│         └──────────────────┴──────────────────┘           │
│                                                             │
└─────────────────────────────────────────────────────────────┘

```

---

<aside>
🕹️

**ROBOCORP CONTROL ROOM (Orchestration Layer)**

</aside>

```
┌─────────────────────────────────────────────────────────────┐
│                ROBOCORP CONTROL ROOM                        │
│          (Scheduling • Secrets • Logs)                      │
└─────────────────────────────────────────────────────────────┘

```

---

<aside>
🏁

**ENTRY POINT**

</aside>

```
┌─────────────────────────────────────────────────────────────┐
│                         task.py                             │
│  • Initialize automation setup                              │
│  • Setup logging& directories                              │
│  •Create Jira issue                                        │
│  •Start workflow                                           │
└─────────────────────────────────────────────────────────────┘

```

---

<aside>
🛠️

**WORKFLOW ORCHESTRATOR**

</aside>

```
┌─────────────────────────────────────────────────────────────┐
│                   WORKFLOW ORCHESTRATOR                     │
│                   workflow.py                               │
│                                                             │
│  • Authenticate Zindiuser                                  │
│  •Prepare submission workflow                              │
│  • Coordinate file checks& uploads                         │
│  •Trigger report generation                                │
└─────────────────────────────────────────────────────────────┘

```

---

<aside>
🤖

**AUTOMATION / PROCESS LAYER**

</aside>

```
┌─────────────────────────────────────────────────────────────┐
│                 PROCESS PREPARATION LAYER                   │
│                 process.py                                  │
│                                                             │
│  •Fetchopen competitions                                  │
│  •Create competition directories                           │
│  •Normalize competition names                              │
│  • Validate submission files                                │
│  •Check daily submission limits                            │
└─────────────────────────────────────────────────────────────┘

```

---

<aside>
🗂️

**DATA & CONFIGURATION LAYER**

</aside>

```
┌─────────────────────────────────────────────────────────────┐
│                 DATA &CONFIGURATION                        │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Config.py                                             │  │
│  │ • Paths & directories                                 │  │
│  │ •User inputs                                         │  │
│  │ • Feature toggles                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Credentials (Bitwarden / Vault)                       │  │
│  │ • Zindi username &password                           │  │
│  │ • Jira credentials                                    │  │
│  │ • SharePoint credentials                              │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Output & Reports                                      │  │
│  │ • Submission reports (.csv)                           │  │
│  │ • Logs                                                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

```

---

## 🔄 **PROCESS FLOW — MACRO LEVEL**

<aside>
🔄

**End‑to‑End Workflow Execution**

</aside>

```
Initialize Automation
        │
        ▼
Load Config & Credentials
        │
        ▼
Loginto Zindi Platform
        │
        ▼
FetchOpen Competitions
        │
        ▼
Create Competition Folders
        │
        ▼
Check Submission Files
        │
        ├─Validate filenameformat
        ├─Move filesto correct folders
        │
        ▼
Filter Competitions
        │
        ├─Open competitionsonly
        ├─ Submissionlimit available
        │
        ▼
Upload Submissionsto Zindi
        │
        ▼
Generate Submission Report
        │
        ▼
Send Report via Gmail
        │
        ├─If size <25MB → Gmail
        └─Else → SharePoint
        │
        ▼
Update Jira Issue (Success / Failure)
        │
        ▼
END

```

---

## ⚠️ **ERROR HANDLING FLOW**

<aside>
🚨

**Exception Management**

</aside>

```
SubmissionFilesNotPresentFolder
IncorrectSubmissionFilesNames
SelectedCompetitionListEmpty
FileSizeTooLargeToSendThroughGmail
UnexpectedExceptions
        │
        ▼
LogError
        │
        ▼
UpdateJiraIssue
        │
        ▼
FailGracefully/Continue(ifallowed)

```

---

## 📊 **KEY METRICS**

<aside>
📈

**Operational KPIs**

</aside>

- Multiple competitions processed per run
- Automatic folder creation per competition
- 100% validation before submission
- Zero manual uploads
- Full Jira traceability
- Gmail + SharePoint fallback reporting
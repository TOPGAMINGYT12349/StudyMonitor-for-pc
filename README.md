# 🧠 StudyMonitor for PC — JARVIS Guardian

### Your Personal Study Companion | Focus Better. Study Smarter. Stay Productive.

StudyMonitor is a Windows desktop productivity application designed to help students maintain focus, reduce distractions, and build better study habits. It aims to make study sessions more productive through focus monitoring, alerts, audio features, and a personalized desktop experience.

Built for students who want to take control of their screen time and create a more disciplined study environment.

---

## 📌 Table of Contents

- [About the Project](#-about-the-project)
- [Features](#-features)
- [Privacy and Data Security](#-privacy-and-data-security)
- [System Requirements](#-system-requirements)
- [Download](#-download)
- [Installation Guide](#-installation-guide)
- [How to Run](#-how-to-run)
- [Troubleshooting](#-troubleshooting)
- [Recommended Usage](#-recommended-usage)
- [Limitations](#-limitations)
- [Disclaimer](#-disclaimer)
- [Developer](#-developer)

---

## 🚀 About the Project

Studying on a PC can be challenging when games, social media, entertainment, and other applications compete for your attention.

StudyMonitor is designed to help you stay aware of your study habits and return your attention to your work when distractions occur.

The project focuses on making a personal study assistant for Windows, with a desktop-based experience and configurable productivity features.

Whether you are preparing for school examinations, working on assignments, learning programming, or studying independently, StudyMonitor aims to support a more focused workflow.

### 🎯 Project Goals

- Encourage consistent study habits.
- Help users recognize and reduce distractions.
- Make study sessions more structured.
- Provide helpful alerts during study time.
- Keep personal study information on the user's device where supported by the application.
- Create a convenient desktop tool for students.

---

## ✨ Features

### 🎯 Focus and Productivity

- Designed to support focused study sessions.
- Helps users maintain awareness of distractions.
- Provides a productivity-oriented desktop experience.
- Supports a more structured study routine.

### 🔔 Alerts and Audio

- Audio-based alerts where configured.
- Support for custom audio files included with the application.
- Designed to remind users to return to their studies when necessary.

### 🖥️ Windows Desktop Application

- Designed for Windows PCs.
- Includes a Windows executable named `StudyMonitor.exe`.
- Distributed as a compressed ZIP package.
- Uses a folder-based application structure after extraction.

### ⚙️ Customization

Some behaviour may depend on the included configuration, audio files, and application version.

Please refer to the actual application settings and bundled files to determine which features are available in your build.

---

## 🔒 Privacy and Data Security

Privacy is an important consideration for a desktop application that may interact with a user's study environment.

### Local-First Approach

StudyMonitor is intended to be used as a desktop application on your own Windows PC.

Local storage means that information is stored on your device rather than in an online account or cloud database.

**Important privacy note:** The exact storage and network behaviour depends on the application's implementation. The absence of cloud storage alone does not prove that an application never transmits data over the internet.

### Privacy Principles

- **Personal device:** Run the application on your own PC.
- **Local files:** Application files and any locally stored logs remain on your computer unless you choose to share them or another process accesses them.
- **No cloud-storage claim without verification:** Cloud storage and network communication must be checked in the source code before making stronger privacy claims.
- **Responsible monitoring:** If webcam, microphone, or application-activity monitoring is enabled, understand what is accessed and when.
- **User awareness:** Review the permissions and behaviour of the application before use.

### Does StudyMonitor Upload My Data?

This repository does not make a verified guarantee that every component operates entirely offline.

To establish whether the application sends any data externally, its source code, third-party libraries, network connections, and runtime behaviour must be inspected.

### Webcam and Microphone Privacy

If a version of StudyMonitor uses a webcam or microphone for monitoring or voice interaction:

- Grant access only when necessary.
- Make sure monitoring is active only when intended.
- Avoid recording or monitoring other people without their knowledge and consent.
- Do not share private logs or recordings publicly.

### Security Recommendation

Download the application only from a source you trust. Keep your Windows installation updated and review security warnings before running downloaded executables.

---

## 💻 System Requirements

### Operating System

- Windows 10 or Windows 11, subject to compatibility with the included build.

### Required Files

- The downloaded StudyMonitor ZIP archive.
- A ZIP extraction utility such as Windows Extract All, 7-Zip, or WinRAR.
- All supporting files and folders included in the extracted package.

### Python Requirement

Python may be required if the application uses a Python interpreter or depends on external Python packages at runtime.

If the executable is fully packaged with its required Python runtime and dependencies, a separate Python installation may not be necessary.

If you need Python, download it from the official website:

https://www.python.org/downloads/

When installing Python for development or source-code execution, select **Add Python to PATH** when available.

---

## 📥 Download

Download the ZIP package from the repository or its Releases section.

**Package name:**

`StudyMonitor_JARVIS_Guardian_Audio_Fix_v6.zip`

After downloading, extract the archive before attempting to launch the application.

For easier distribution, check the repository's **Releases** section for the latest version and any release-specific instructions.

---

## 🛠️ Installation Guide

Follow these steps to install and launch StudyMonitor on Windows.

### Step 1 — Download the ZIP

Download:

`StudyMonitor_JARVIS_Guardian_Audio_Fix_v6.zip`

Save it to a location with sufficient free disk space.

### Step 2 — Extract the Archive

Right-click the ZIP file and select:

**Extract All...**

Alternatively, use 7-Zip or WinRAR.

Wait until the extraction process finishes. Do not run the executable directly from inside the compressed archive.

### Step 3 — Install Python if Required

If your build requires a separately installed Python runtime, download Python from:

https://www.python.org/downloads/

Install the version compatible with the application and its dependencies.

If the packaged executable is self-contained, you may be able to skip this step.

### Step 4 — Open the Extracted Folder

Navigate to the extracted project folder.

Follow this folder path:

`dist` → `StudyMonitor` → `StudyMonitor.exe`

### Step 5 — Launch the Application

Double-click:

`StudyMonitor.exe`

Wait for the application to start.

Keep the extracted application folder intact. Do not move the executable away from supporting files unless the application is confirmed to be self-contained.

### Step 6 — If the Application Does Not Start

See the troubleshooting section below for possible solutions.

---

## ▶️ How to Run

1. Download the ZIP archive.
2. Extract the complete archive.
3. Open the extracted project folder.
4. Open `dist`.
5. Open the `StudyMonitor` folder.
6. Double-click `StudyMonitor.exe`.
7. Follow any on-screen instructions provided by the application.

For the best experience, close unnecessary distracting applications before starting a study session.

---

## 🧰 Troubleshooting

### Application Does Not Open

- Confirm that extraction completed successfully.
- Verify that `StudyMonitor.exe` exists in the expected directory.
- Check that the supporting files have not been deleted.
- Check Windows Security or antivirus notifications to determine whether a file was quarantined.
- Only restore or allow a file if you trust its source and have verified it is safe.

### Python-Related Errors

If an error mentions Python, a missing module, or a missing runtime:

- Verify whether the build requires a separate Python installation.
- Check the Python version required by the project.
- Review `requirements.txt` if you intend to run the source code.
- Install dependencies only from trusted sources.

### Audio Is Not Working

- Check the Windows volume level.
- Confirm that the correct audio output device is selected.
- Verify that the bundled audio files have been extracted.
- Check application settings, if available.
- Ensure that Windows or another application is not muting the output.

### Missing Files

Do not delete files from the extracted folder unless you know they are unnecessary.

Some files may be required for the executable to start or for audio and other features to work.

### Windows Security Warning

Windows may display a warning when running an executable that is not widely recognized or digitally signed.

Do not bypass the warning automatically. Verify the source and inspect the file before deciding whether to run it.

---

## 📚 Recommended Usage

For a more productive study session:

1. Choose a clear study goal.
2. Keep only the applications needed for your work open.
3. Start StudyMonitor if its monitoring features are appropriate for your session.
4. Respond to reminders by returning your attention to the task.
5. Take reasonable breaks between study sessions.
6. Review your progress and adjust your study routine.

StudyMonitor is a productivity aid, not a replacement for personal discipline or a well-planned study schedule.

---

## ⚠️ Limitations

- Compatibility may vary across Windows systems.
- Some features may depend on local configuration and supporting files.
- Behaviour may differ between packaged builds.
- Python may be required for some execution or development workflows.
- Privacy and offline operation have not been independently certified.
- No application can guarantee the complete elimination of distractions.

---

## ⚖️ Disclaimer

StudyMonitor is provided as a personal productivity project.

The application is supplied on an as-is basis, without a guarantee that every feature will work on every Windows PC.

Users are responsible for checking the software's source, permissions, and security implications before running it.

Do not use monitoring functionality to observe other people without appropriate knowledge and consent.

---

## 👨‍💻 Developer

**Created by: NO NEED**

Project: StudyMonitor for PC — JARVIS Guardian

A project focused on helping students improve concentration and build better study habits.

If you find the project useful, consider starring the repository ⭐

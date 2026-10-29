# Study Monitor for Windows 11

A local-first Windows 11 study helper with a dark dashboard, webcam-based approximate alertness/head-direction estimates, configurable distracting-app warnings, custom MP3 audio, XP/levels/streaks, and local study-event analytics.

## What it does

- Starts and pauses a focus session with a live timer.
- Uses the webcam and MediaPipe Face Mesh to estimate prolonged eye closure, rough head droop, face absence, and horizontal head-turn/looking-away signals.
- Checks the foreground Windows process every ~1.8 seconds.
- Warns for process names in your **Distracting apps** list and for foreground apps not included in your **Allowed apps** list.
- Lets you edit allowed and distracting app names in the dashboard.
- Saves app lists under `%APPDATA%\StudyMonitor\settings.txt`; stores XP/streak data in `stats.json` and event history in `events.csv`.
- Awards 5 XP per active session minute, tracks levels and daily streaks, and provides a weekly event-activity chart plus recent event log in **View study analytics**.
- Uses the bundled custom MP3 for distraction warnings; the first visit warns, and a later separate visit can close the listed process if enabled.
- Processes webcam frames locally. It does not record or save video.

## Important limitations

- Drowsiness detection is approximate. Lighting, glasses, camera angle, face position, and natural blinking can cause false positives or missed detections. It is not a medical device.
- The app alerts for explicitly listed distracting processes and for any foreground process not on the allowlist. Add every app you want to use for studying to **Allowed apps**. If you allow a browser such as `chrome.exe`, individual websites/tabs inside it cannot be distinguished by this version.
- Browser tabs cannot reliably be distinguished by process name. For more precise website blocking, use a separate browser extension or DNS/hosts-based solution.
- The webcam must be available and not already exclusively occupied by another app.
- A packaged build is not signed. Windows SmartScreen may show an unrecognized-app warning.
- The app can close process names explicitly listed as distracting on the second separate visit if enabled. This may lose unsaved work. It does not record video or upload camera data.

## Recommended build environment

Use **Windows 11 x64 and Python 3.11 x64**. This avoids compatibility surprises with the pinned computer-vision dependencies.

1. Install Python 3.11 x64 from https://www.python.org/downloads/release/python-3119/
2. During setup, enable **Add python.exe to PATH**.
3. Extract this project folder to a simple path, such as `C:\\StudyMonitor`.
4. Double-click `build_exe.bat`.
5. When it finishes, run `dist\\StudyMonitor\\StudyMonitor.exe` (keep the whole `dist\\StudyMonitor` folder together).

The build script installs dependencies in a project-local virtual environment. The initial install needs an internet connection. Running the app after building does not require internet access for its core features.

## First launch

1. Allow camera access if Windows asks: **Settings → Privacy & security → Camera → Let desktop apps access your camera**.
2. Click **Start session**.
3. Put your face in view with decent front lighting.
4. Add executable process names in the **Distracting apps** box. Common examples:
   - `discord.exe`
   - `steam.exe`
   - `epicgameslauncher.exe`
   - `spotify.exe`
   - `telegram.exe`
   - `RobloxPlayerBeta.exe`
5. Add apps you want to treat as study apps to **Allowed apps**. The allowed list is stored separately for your study setup; distraction actions are driven by the distracting-app list.
6. Use **Save settings** to persist your lists. Any foreground app not on the allowed list will trigger an alert; the distracting-app list can explicitly flag apps even if you accidentally add one to the allowed list.

## Troubleshooting

- **Camera unavailable:** close Camera/Teams/Zoom/other apps using the webcam; check Windows camera permissions; try launching the app again.
- **Missing module:** rerun `build_exe.bat`, or in a terminal run `py -3.11 -m pip install -r requirements.txt`.
- **Build errors:** ensure Python is 64-bit Python 3.11 and that `build_exe.bat` is run from the extracted project directory.
- **False drowsiness alerts:** increase the eye-closure threshold duration in `study_monitor.py` from `1.8` seconds to `2.5` or `3.0`.
- **No app alert:** open Task Manager → Details and check the actual executable name. Add that exact name to the distracting list.
- **Notifications not visible:** enable Windows notifications for desktop apps and check Do not disturb / Focus settings.

## Privacy

The webcam is used only while a session is running. Frames are analyzed in memory and are not written to disk. Process names are checked locally. Settings are stored locally. Analytics are local-only: event logs and XP/streak data stay on this PC. No video is saved or uploaded.

\n## Custom audio fix\n\nThis build plays only the supplied MP3; generated text-to-speech has been removed. The audio path uses PyInstaller's bundled resource directory. Click **Test sound** before starting a session. If playback fails, the app shows an error instead of silently substituting a generic beep. Rebuild with `build_exe.bat`.\n

## Audio Manager (new)

Open **♫ Audio Manager** in the dashboard to add supported `.mp3`, `.wav`, `.ogg`, or `.flac` files, test them, remove them, assign a sound to an event, and set playback volume. Files are copied into `%APPDATA%\StudyMonitor\audio`; assignments and volume are saved in `%APPDATA%\StudyMonitor\audio_settings.json`. You can add/replace audio after building the EXE without rebuilding it. The bundled meme MP3 is copied to the audio library on first launch. Drowsiness audio can be assigned separately. Event choices for session-complete, break, and motivation are prepared for future event triggers. Playback is capped at 100% inside the app; it cannot exceed Windows/device volume.


## JARVIS-style alerts and voice assistant (experimental)

- Distraction events cycle through the bundled meme audio files and show a topmost full-screen “PLEASE STUDY, SIR!” overlay. Press Esc or click the dismiss button to close it.
- The **JARVIS Voice Assistant** button listens for one command in Hindi or English. Speech recognition uses Google's online recognition service and therefore needs internet; the microphone and optional voice packages must work.
- Supported starter commands include “WhatsApp kholo”, “WhatsApp khol [chat name]”, “study session start”, “pause session”, and “type [text]”. Dictation pastes into the currently focused text field; it does not send messages automatically.
- The WhatsApp URI/search behavior depends on the installed WhatsApp version and UI. Always verify the selected chat and text before sending.
- A soft female voice is selected only if Windows has a compatible installed voice (for example Zira/Heera). Available voices vary by Windows language pack; install a Hindi/Indian English voice in Windows Settings > Time & language > Speech if needed.
- Camera analysis remains local. Voice recognition is online and is only started when you press the assistant button.
- This build's voice assistant is a starter command handler, not a general-purpose conversational AI. It does not support arbitrary apps or arbitrary natural-language actions yet.

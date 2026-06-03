<h1 align="center">📱 Android Automation Tool Box</h1>

<p align="center">
  <strong>A cross-platform graphical application for visual design and automation of actions on Android devices.</strong>
</p>
<p align="center">
If you find this tool helpful, please consider giving the repository a star 🌟!
</p>

<p align="center">
  <img src="https://img.shields.io/github/stars/Yangvarr/Android-Automation-Tool-Box?style=for-the-badge&color=2ea44f" alt="Stars">
  <img src="https://img.shields.io/github/forks/Yangvarr/Android-Automation-Tool-Box?style=for-the-badge&color=0969da" alt="Forks">
  <img src="https://img.shields.io/github/issues/Yangvarr/Android-Automation-Tool-Box?style=for-the-badge&color=d73a49" alt="Issues">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
</p>

---

## 🎯 Key Features

*   **⚡ Visual Builder** — Design complex scenarios (clicks, swipes, loops, and conditional transitions) without writing a single line of code.
*   **🐍 Python Script Generation** — Export your completed visual flows into clean, executable Python code.
*   **🖼️ Image Recognition** — Find and interact with UI elements on your screen using computer vision (OpenCV).
*   **🖥️ Cross-Platform** — Runs seamlessly on Windows, macOS, and Linux.

---

## 🖥️ Application Interface

<p align="center">
  <img width="2560" height="1080" alt="image" src="https://github.com/user-attachments/assets/59df5b1e-ebf9-4fff-a54f-cf0322eb161a" />
</p>

---

## ⚙️ Prerequisites

Before launching the tool, make sure your environment is configured:

1.  **ADB (Android Debug Bridge)** must be installed on your computer and added to your system's `PATH`.
2.  **Developer Options** and **USB Debugging** must be enabled on your target Android device.

---

## 📂 Project Structure

```text
├── app.py              # Main application entry point and user interface
├── funks.py            # Utility functions for direct ADB interaction
├── click_on_image.py   # OpenCV-based module for accurate template matching
├── theme.py            # UI styling and color themes
├── locales.py          # Multi-language and localization module
└── requirements.txt    # Project dependencies
```
## 🚀 Quick Start
1. Connect your device: Connect your Android phone via USB and ensure it is recognized by ADB (adb devices command in your terminal should list the device).
2. Create Actions: Use the graphical interface to add actions like clicks, swipes, or template matching via screenshots.
3. Configure Flow: Build loops, conditional checks, and structure your automation sequence.
4. Export: Run the scenario directly from the interface or export it as a Python script for independent use.
## Clone the Repository
```
git clone https://github.com/Yangvarr/Android-Automation-Tool-Box.git
cd Android-Automation-Tool-Box
```
## Set Up Virtual Environment & Dependencies
```
# Create a virtual environment
uv venv

# Activate the environment (Windows)
.venv\Scripts\activate

# Activate the environment (macOS/Linux)
source .venv/bin/activate

# Install dependencies quickly
uv pip install -r requirements.txt
```
## Run the Application
```
python app.py
```

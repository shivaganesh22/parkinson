# Django Project Setup Instructions

## Prerequisites

1. **Python 3.10.10** - Download from https://www.python.org/downloads/
   - During installation, make sure to check "Add Python to PATH"

2. **FFmpeg** ( but recommended for audio processing)
   - Download from https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
   - Extract the zip file
   - Add the `bin` folder to your system PATH:
     * Open System Properties → Environment Variables
     * Edit PATH and add the full path to the FFmpeg `bin` folder
     * Restart your terminal/command prompt

## Quick Setup

```cmd
# 1. Create virtual environment
py -3.10 -m venv env

# 2. Activate virtual environment
env\Scripts\activate.bat

# 3. Clone Git Repository
git clone https://github.com/shivaganesh22/parkinson

# 4. Install requirements
cd parkinson
pip install -r requirements.txt

# 5. Run Django server
python manage.py runserver
```

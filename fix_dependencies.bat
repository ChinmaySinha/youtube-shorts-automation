@echo off
echo ===============================================================
echo  This script will fix the Python dependencies for the project.
echo  It will uninstall the old 'moviepy' library and then
echo  install all the correct libraries from requirements.txt.
echo ===============================================================
echo.
echo Step 1: Uninstalling the old moviepy version...
pip uninstall -y moviepy
echo.
echo Step 2: Installing all required libraries from requirements.txt...
pip install -r requirements.txt
echo.
echo ===============================================================
echo  Dependency fix complete!
echo  You can now try running the main program again:
echo  python -m youtube_agent_system.main
echo ===============================================================
pause

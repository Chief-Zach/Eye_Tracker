Final project for HCI 2024

Uses a combination of pupil location, pupil ratios, idea of the general screen size, and some custom smoothing and 
detection functions to create an eye tracker with 3 modes:
- Calibration 
  - Press space while focussing on the bubbles on the edges of your screen
  - This will register the locations of the screen compared to your eye socket
- Freestyle
  - Blank screen with a cursor that follows your gaze. Made for testing.
- Target Practice
  - 20 bubbles spawn one after another on the screen
  - Blink when you are looking at the target to get the next target to appear

Python Version 3.9 was used. Library supports 3.12 with some changes to the requirements.txt file.

Gaze Tracking Library from [@antoinelame](https://github.com/antoinelame)
Changes:
- Calibration time increased to allow for changes in brightness before tracking eyes
- Modification to blink detection


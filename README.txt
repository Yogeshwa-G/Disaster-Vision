DISASTERVISION — PREMIUM BUILD
==============================

ABOUT
-----
DisasterVision is a local web project for exploring environmental change
through dated satellite images. The current dataset is stored in
satellite_data/GLACIER/<LOCATION>/.

RUN ON WINDOWS
--------------
1. Extract this ZIP.
2. Double-click run.bat.
3. Wait for the terminal window.
4. Open http://127.0.0.1:8107 in your browser.
5. Install dependencies first if needed: python -m pip install -r requirements.txt

The web client starts Server.py automatically on the internal analysis port
5537. Do not run multiple copies on the same ports at the same time.

WHAT CHANGED
------------
- Premium sage-green interface with clean white cards and a natural system font with a clearer visual hierarchy.
- Scroll-triggered section reveals replay whenever a section leaves and re-enters the viewport, with reduced-motion accessibility support.
- Interactive Earth retained; automatic rotation direction corrected, pointer dragging preserved, and zoom kept.
- About section and project contact email: disastervision@gmail.com.
- Latest dated image is selected automatically as the reference image.
- More explicit model labels: the displayed year is a modeled high-risk
  threshold year, not a guaranteed disaster date.
- Prediction rate is fitted through the latest observation's 0% baseline.
- Threshold dates beyond 2100 are marked outside the supported horizon.
- Location preview requests ignore stale responses when users switch quickly.
- Existing location folder names and image data are preserved.

HOW THE CALCULATION WORKS
-------------------------
1. Each historical image is compared pixel-by-pixel with the latest dated
   image. Images are resized to a common size before comparison.
2. A pixel counts as changed when the average absolute RGB channel difference
   is greater than 20. The reported percentage is the share of such pixels.
3. A non-negative linear annual rate is fitted through the latest image's
   0% change baseline. The future estimate is rate × years ahead, bounded
   between 0% and 100%.
4. The prototype labels <20% LOW, 20% to <40% MODERATE, and >=40% HIGH.
   It estimates 20% and 40% threshold years from the fitted rate when those
   dates fall within 1900–2100.

IMPORTANT LIMITATIONS
---------------------
This is an educational image-difference prototype, not a scientifically
validated natural-disaster prediction system. RGB differences can be affected
by lighting, season, cloud cover, image registration, resolution, and sensor
changes. A visual pixel-change percentage is not the same as glacier area,
ice volume, retreat speed, or disaster probability. Linear trends do not
capture nonlinear climate dynamics or abrupt events. Results should not be
used as official warnings or for safety-critical decisions. A robust
scientific model would need calibrated geospatial imagery, image alignment,
domain-specific measurements, uncertainty intervals, and independent
validation.

DATA LOCATIONS
--------------
The location selector is discovered from the actual folder names under
satellite_data/GLACIER/. Empty or unreadable locations are handled with an
informative error instead of fabricated results.

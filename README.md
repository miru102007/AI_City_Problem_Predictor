# AI City Problem Predictor — Render deployment package

This is a Python standard-library prototype that can be deployed as a Render Web Service.

## Included files
- `app.py` — web application, configured to bind to `0.0.0.0` and use Render's `PORT` environment variable.
- `requirements.txt` — no third-party dependencies are currently needed.
- `render.yaml` — basic Render service configuration.

## Deploy with GitHub + Render
1. Extract this ZIP.
2. Create a new GitHub repository (for example, `ai-city-problem-predictor`).
3. Upload the three files from this folder to the repository root and commit them.
4. In Render, choose **New + → Web Service**, connect the GitHub repository, and select the Free plan for a demo.
5. If Render asks for commands, use:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`
6. Click **Create Web Service** and wait for the deploy to finish. Use the `onrender.com` URL Render provides to share the app.

## Notes
- If you have a compatible `city_model.pkl` from your own project, place it in the same folder before upload. Without it, the application labels and uses demo scoring.
- This prototype uses in-memory assessment history, so history may reset after a restart/redeploy. Free services can sleep after inactivity and may take about a minute to start on the next visit.
- Predictions are prototype estimates. The dashboard creates suggested department alerts only; it does not send real SMS, phone calls, or external notifications.

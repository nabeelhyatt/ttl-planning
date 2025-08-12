# Deployment Instructions for Tabletop Library Planning Tools

## Prerequisites
- Git installed on your local machine
- A Heroku account (free tier is sufficient)
- Heroku CLI installed

## Deployment Steps

### 1. Initialize Git Repository (if not already done)
```bash
git init
git add .
git commit -m "Initial commit for TTL Planning Tools"
```

### 2. Create a Heroku App
```bash
heroku create your-app-name
# Replace 'your-app-name' with your desired app name
```

### 3. Deploy to Heroku
```bash
git push heroku main
# or if you're on master branch:
git push heroku master
```

### 4. Open Your App
```bash
heroku open
```

## Configuration

The app will automatically use:
- The PORT environment variable provided by Heroku
- Production mode (debug=False) by default

### Optional Environment Variables
You can set these using:
```bash
heroku config:set VARIABLE_NAME=value
```

- `FLASK_DEBUG`: Set to 'true' for debug mode (not recommended in production)
- `FLASK_ENV`: Set to 'production' (default) or 'development'

## Monitoring

### View Logs
```bash
heroku logs --tail
```

### Check App Status
```bash
heroku ps
```

## Updating the App

After making changes:
```bash
git add .
git commit -m "Description of changes"
git push heroku main
```

## Alternative Deployment Options

### Deploy to Railway
1. Install Railway CLI: `npm i -g @railway/cli`
2. Login: `railway login`
3. Initialize: `railway init`
4. Deploy: `railway up`

### Deploy to Render
1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn app:app`

### Deploy to Google Cloud Run
1. Install Google Cloud SDK
2. Build container: `gcloud builds submit --tag gcr.io/PROJECT-ID/ttl-planning`
3. Deploy: `gcloud run deploy --image gcr.io/PROJECT-ID/ttl-planning --platform managed`

## Notes
- The app includes a `config.json` file that stores configuration data
- All data is stored locally in the config file (no database required)
- The app runs on Flask with gunicorn as the production server
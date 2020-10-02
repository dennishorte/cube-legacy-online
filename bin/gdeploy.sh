gcloud builds submit --tag gcr.io/cube-legacy-online/cube-legacy-online
gcloud run deploy --platform managed --image gcr.io/cube-legacy-online/cube-legacy-online

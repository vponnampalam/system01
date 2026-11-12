# system01
testing ai code

## Publishing webserver messages to Pub/Sub

The webserver stores each accepted message in SQLite and publishes its text as
the Pub/Sub message data. Configure the Cloud Run service with the full topic
name in `PUBSUB_TOPIC`, such as
`projects/PROJECT_ID/topics/TOPIC_ID`.

Create a topic and grant the Cloud Run runtime service account permission to
publish:

```sh
gcloud pubsub topics create TOPIC_ID --project=PROJECT_ID
gcloud pubsub topics add-iam-policy-binding TOPIC_ID \
  --project=PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role=roles/pubsub.publisher
```

Set the topic name on the Cloud Run service:

```sh
gcloud run services update SERVICE_NAME \
  --region=REGION \
  --update-env-vars="PUBSUB_TOPIC=projects/PROJECT_ID/topics/TOPIC_ID"
```

After adding the Pub/Sub dependency, rebuild and deploy the webserver image.
The worker can continue posting to the webserver as before; successful
`POST /messages` responses include the Pub/Sub message ID.

# rss-spot-pod

Description: Use GKE Autopilot Spot Pods to perform analysis of RSS feeds, dump into BigQuery, then build a low-code search engine via Vertex AI Agent Builder.

This code base was used in the following blog: [Search engines made simple: A low-code approach with GKE and Vertex AI Agent Builder](https://cloud.google.com/blog/products/application-development/building-a-search-engine-with-gke-and-vertex-ai)

## Building the base image

To build the base image, use the following:

```
mkdir -p base/dist
cd base && tar -czvf dist/app.tar.gz app/*

podman build --platform linux/amd64 -t rss-spot-pod-base:latest base/
```

## Building the app image

```
mkdir -p spot-pod/dist
cd spot-pod && tar -czvf dist/app.tar.gz app/*

podman build --platform linux/amd64 -t rss-spot-pod:latest spot-pod/
```

## Preparing for deployment

Ensure that Workload Identity is turned on for your Autopilot cluster and the proper Kubernetes Service Accounts (KSAs) are bound to the proper identites (access to BigQuery, etc.)

The relevant parts of the deployment spec are listed here

```
apiVersion: apps/v1
kind: Deployment
...
spec:
    spec:
      serviceAccountName: vertex-autopilot-sa
      nodeSelector:
        iam.gke.io/gke-metadata-server-enabled: "true"
        cloud.google.com/gke-spot: "true"
      terminationGracePeriodSeconds: 25
      containers:
      - image: us-west1-docker.pkg.dev/vertex-ai-project-here/genai-spot-pod/genai-spot-pod@sha256:71ebe64f17355ac5cbf4823ea92da2b0c2923ce8628a26b0344f10c819b41e20
        env:
          - name: BQ_TABLE
            value: 'bigquery-project-here.genai_spot_pod.document-summaries'
          - name: PUBSUB_TOPIC
            value: 'genai-spot-pod-test-1'
          - name: PUBSUB_SUBSCRIBER
            value: 'genai-spot-pod-sub-1'
```

Ensure that `BQ_TABLE`, `PUBSUB_TOPIC`, and `PUBSUB_SUBSCRIBER` are properly defined.

Deploy the Horizontal Pod Autoscaler if desired.
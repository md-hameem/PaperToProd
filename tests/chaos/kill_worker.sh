#!/bin/bash
# tests/chaos/kill_worker.sh
# Chaos Engineering: Randomly kill the Celery worker process to verify job checkpoint resumption.

echo "Starting Chaos Experiment: Worker Node Failure"

WORKER_PID=$(ps aux | grep '[c]elery -A app.worker worker' | awk '{print $2}' | head -n 1)

if [ -z "$WORKER_PID" ]; then
  echo "No Celery worker found running. Please start the worker first."
  exit 1
fi

echo "Found worker PID: $WORKER_PID. Submitting a test job via API..."

API_URL=${API_URL:-"http://localhost:8000"}
AUTH_TOKEN=${AUTH_TOKEN:-"mock-token"}

JOB_ID=$(curl -s -X POST "$API_URL/jobs" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "x-workspace-id: 1" \
  -F "arxiv_id=2103.00020" | jq -r .id)

echo "Job $JOB_ID submitted. Waiting 10 seconds for it to start processing..."
sleep 10

echo "Executing SIGKILL on worker $WORKER_PID to simulate OOM / node failure..."
kill -9 $WORKER_PID

echo "Worker killed. Waiting 5 seconds to simulate orchestrator restarting the pod..."
sleep 5

echo "Restarting Celery worker..."
cd apps/api && celery -A app.worker worker --loglevel=info &
NEW_WORKER_PID=$!

echo "New worker started with PID $NEW_WORKER_PID. Polling job $JOB_ID to ensure it successfully resumes from checkpoint..."

for i in {1..20}; do
  STATUS=$(curl -s "$API_URL/jobs/$JOB_ID" -H "Authorization: Bearer $AUTH_TOKEN" | jq -r .status)
  echo "Job Status: $STATUS"

  if [ "$STATUS" == "completed" ]; then
    echo "Chaos Experiment PASSED: Job successfully completed despite worker crash!"
    kill $NEW_WORKER_PID
    exit 0
  fi
  sleep 5
done

echo "Chaos Experiment FAILED: Job did not complete within the timeout period."
kill $NEW_WORKER_PID
exit 1

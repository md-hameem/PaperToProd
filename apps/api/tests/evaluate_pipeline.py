import asyncio
import json
import time
from pathlib import Path

import httpx

# Config
API_BASE = "http://localhost:8000"
DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
REPORT_PATH = Path(__file__).parent / "validation_report.md"


async def evaluate_job(client, paper, token):
    print(f"\nEvaluating: {paper['title']}")
    start_time = time.time()

    # Submit Job
    response = await client.post(
        f"{API_BASE}/jobs",
        json={"arxiv_url": paper["paper_url"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    if response.status_code != 200:
        print(f"  [Error] Failed to submit job: {response.text}")
        return None

    job_id = response.json()["id"]
    print(f"  [Info] Job ID: {job_id}. Waiting for completion...")

    # Poll for completion
    while True:
        res = await client.get(
            f"{API_BASE}/jobs/{job_id}", headers={"Authorization": f"Bearer {token}"}
        )
        if res.status_code != 200:
            print("  [Error] Failed to fetch job status.")
            return None

        status = res.json()["status"]
        if status in ["completed", "failed", "error"]:
            job_data = res.json()
            break

        await asyncio.sleep(5)

    end_time = time.time()
    duration = end_time - start_time
    print(f"  [Info] Job finished with status: {status} in {duration:.1f}s")

    return job_data, duration


async def main():
    if not DATASET_PATH.exists():
        print("Dataset not found!")
        return

    with open(DATASET_PATH) as f:
        dataset = json.load(f)

    report_lines = ["# MVP Validation Report", f"**Papers Evaluated**: {len(dataset)}", ""]

    # Quick login to get a token (assuming test user exists or mock auth)
    # Since auth is mocked for MVP, we might just pass a dummy token if security.py allows it.
    token = "test-token-123"

    async with httpx.AsyncClient(timeout=300.0) as client:
        for paper in dataset:
            result = await evaluate_job(client, paper, token)
            if not result:
                report_lines.append(f"## {paper['title']} (❌ FAILED)")
                report_lines.append("Failed to execute pipeline.")
                continue

            job_data, duration = result
            status = job_data["status"]
            score = job_data.get("fidelity_score", "N/A")

            # Simple grading logic
            # Since we don't have real LLM grading built in this script, we just check completion status
            success_icon = "✅" if status == "completed" else "❌"

            report_lines.append(f"## {success_icon} {paper['title']}")
            report_lines.append(f"- **ArXiv**: {paper['paper_url']}")
            report_lines.append(f"- **Status**: {status}")
            report_lines.append(f"- **Time to Runnable**: {duration:.1f} seconds")
            report_lines.append(f"- **Fidelity Score**: {score}")
            report_lines.append("")

            if status == "completed":
                print(f"  [Success] Scored {score}")
            else:
                print(f"  [Failed] Reason: {job_data.get('error_reason', 'Unknown')}")

    # Write report
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\nDone! Report written to {REPORT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())

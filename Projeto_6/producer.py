import asyncio
import zmq
import zmq.asyncio
import random
import datetime


PORT = 5555
context = zmq.asyncio.Context()
socket = context.socket(zmq.PUB)
socket.bind(f"tcp://*:{PORT}")

SCENARIOS = [
    {
        "source": "AWS CloudTrail",
        "message": "S3 bucket made public",
    },
    {
        "source": "Kubernetes Audit Log",
        "message": "Privileged container started",
    },
    {
        "source": "Web Application Firewall",
        "message": "SQL injection attempt detected",
    },
    {
        "source": "CI/CD Pipeline",
        "message": "Vulnerable dependency detected",
    },
    {
        "source": "System Log",
        "message": "User login successful",
    },
    {
        "source": "Git Scanner",
        "message": "AWS access key found in commit history",
    },
]


async def generate_logs():
    while True:
        await asyncio.sleep(random.uniform(2, 5))
        scenario = random.choice(SCENARIOS)

        log_event = {
            "type": "LOG",
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "source": scenario["source"],
            "message": scenario["message"],
        }

        print(f"Publishing log from {scenario['source']}")
        await socket.send_json(log_event)


if __name__ == "__main__":
    print(f"Producer started. Publishing logs on port {PORT}...")
    try:
        asyncio.run(generate_logs())
    except KeyboardInterrupt:
        print("Producer stopped.")
import re

with open("app/main.py", "r") as f:
    content = f.read()

old_code = """
        try:
            async for event in workflow_result_async(
                resume_text=request.resume_text,
                job_description=request.job_description,
                full_name=request.full_name,
                email=request.email,
                phone=request.phone,
                linkedin_url=request.linkedin_url,
                github_url=request.github_url,
            ):
                if not isinstance(event, dict):
                    continue

                if event.get("event") == "workflow_error":
                    yield "data: " + json.dumps(event, default=str) + "\n\n"
                    return

                if event.get("event") == "workflow_state_ready":
                    final_state = dict(event.get("data", {}).get("state", {}))
                    continue

                yield "data: " + json.dumps(event, default=str) + "\n\n"
"""

new_code = """
        try:
            queue = asyncio.Queue()

            async def consume_workflow():
                try:
                    async for event in workflow_result_async(
                        resume_text=request.resume_text,
                        job_description=request.job_description,
                        full_name=request.full_name,
                        email=request.email,
                        phone=request.phone,
                        linkedin_url=request.linkedin_url,
                        github_url=request.github_url,
                    ):
                        await queue.put(("event", event))
                    await queue.put(("done", None))
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    await queue.put(("error", e))

            consumer_task = asyncio.create_task(consume_workflow())

            while True:
                try:
                    msg_type, msg_data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    
                    if msg_type == "done":
                        break
                    elif msg_type == "error":
                        raise msg_data
                        
                    event = msg_data
                    if not isinstance(event, dict):
                        continue

                    if event.get("event") == "workflow_error":
                        yield "data: " + json.dumps(event, default=str) + "\\n\\n"
                        consumer_task.cancel()
                        return

                    if event.get("event") == "workflow_state_ready":
                        final_state = dict(event.get("data", {}).get("state", {}))
                        continue

                    yield "data: " + json.dumps(event, default=str) + "\\n\\n"
                    
                except asyncio.TimeoutError:
                    # Keep-alive ping to prevent client/proxy from dropping the idle connection
                    yield 'data: {"event": "ping"}\\n\\n'
                    continue
"""

if old_code.strip() in content:
    print("Found exact match, patching...")
    content = content.replace(old_code.strip(), new_code.strip())
    with open("app/main.py", "w") as f:
        f.write(content)
else:
    print("Could not find exact match!")

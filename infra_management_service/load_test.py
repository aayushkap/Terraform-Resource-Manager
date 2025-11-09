import asyncio
import random
import aiohttp

URL = "http://127.0.0.1:8080/stress-cpu?n="
PARALLEL_REQUESTS = 5  # workers
REQUEST_GAP = 5  # wait after each request/worker

success_count = 0
failure_count = 0
stop_event = asyncio.Event()


async def fetch(session, i):
    global success_count, failure_count
    n = random.randint(30, 40)
    url = f"{URL}{n}"   
    try:
        async with session.get(url, timeout=30) as resp:
            text = await resp.text()
            print(f"[{i}] {url} -> {resp.status} | {text[:60]}")
            success_count += 1
    except Exception as e:
        print(f"[{i}] Error: {e}")
        failure_count += 1


async def worker(worker_id):
    async with aiohttp.ClientSession() as session:
        i = 0
        while not stop_event.is_set():
            await fetch(session, f"W{worker_id}-R{i}")
            i += 1
            await asyncio.sleep(random.randint(1, 3))


async def main():
    tasks = [asyncio.create_task(worker(wid)) for wid in range(PARALLEL_REQUESTS)]

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass
    finally:
        print(f"\nTotal Success: {success_count}")
        print(f"Total Failures: {failure_count}")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        stop_event.set()
        # cancel gracefully
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        print(f"\nTotal Success: {success_count}")
        print(f"Total Failures: {failure_count}")

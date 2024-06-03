"""
Locust load test definition.
To run this load test open a terminal and run:

    $ pip install locust
    $ export COOKIE=CHANGE_ME  # "session" cookie
    $ export SLEEP_DUR=4       # can be set optionally to override default
    $ locust                   # finds locustfile.py automatically

To get a session cookie, login in a browser with the network tab open.
Look for /api/ requests and find the "session" cookie in the request or response headers.

After locust starts, visit http://localhost:8089/ and set the host to the desired environment URL e.g. ezfeedback.engbert.me
"""

from locust import HttpUser, task
import os
import time

COOKIE = os.environ.get("COOKIE")
assert COOKIE, "COOKIE environment variable missing, see locustfile.py description"
SLEEP_DUR = int(os.environ.get("SLEEP_DUR", 3))
print(f"Using sleep duration of {SLEEP_DUR} seconds.\n")

BASIC_PATHS = (
    "/",
    "/api/v1/course/",
    "/api/v1/course/ca330704-bf1c-4371-a8d8-e7829ad57c1f/assignment/22b3f6fe-d844-4caa-9b80-12ed523d9cf6/status",
    "/api/v1/attempt/?assignment_id=22b3f6fe-d844-4caa-9b80-12ed523d9cf6&user_id=c7f170cc-8ac8-4698-899c-10e473bbe6d7",
)


class MyLoadTest(HttpUser):
    @task
    def basic_get_request_walk(self):
        for path in BASIC_PATHS:
            self.client.get("/api/v1/auth/me", cookies={"session": COOKIE})
            self.client.get(path, cookies={"session": COOKIE})
            time.sleep(SLEEP_DUR)

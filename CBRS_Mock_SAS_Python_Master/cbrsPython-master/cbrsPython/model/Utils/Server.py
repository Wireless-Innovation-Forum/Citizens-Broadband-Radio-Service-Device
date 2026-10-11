# Copyright 2026 CBSD Project Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Explicit Werkzeug server lifetime, including HTTP/1.1 and shutdown."""

from threading import Thread

from werkzeug.serving import WSGIRequestHandler, make_server


class HarnessRequestHandler(WSGIRequestHandler):
    protocol_version = "HTTP/1.1"


def run_server(app, host, port, context, on_start=None):
    server = make_server(
        host, port, app, threaded=True,
        request_handler=HarnessRequestHandler, ssl_context=context,
    )
    app.config["HARNESS_SERVER"] = server
    try:
        if on_start is not None:
            on_start()
        server.serve_forever()
    finally:
        app.config.pop("HARNESS_SERVER", None)
        server.server_close()


def stop_server(app):
    server = app.config.get("HARNESS_SERVER")
    if server is not None:
        # shutdown() must run outside the thread executing serve_forever().
        Thread(target=server.shutdown, daemon=True).start()

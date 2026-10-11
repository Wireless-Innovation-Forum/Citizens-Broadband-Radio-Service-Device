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

"""Mutual TLS settings for the WINNF TLS 1.2 test harness."""

import ssl
from pathlib import Path

from . import Consts as consts


def create_server_context(conf_file, base_dir):
    def configured_path(name):
        value = conf_file.getElementsByTagName(name)[0].firstChild.data.strip()
        return Path(base_dir) / value

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # Keep the protocol required by these historical WINNF test vectors.
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.maximum_version = ssl.TLSVersion.TLSv1_2
    context.verify_mode = ssl.CERT_REQUIRED
    context.set_ciphers(consts.WINNF_APPROVED_CIPHERS)
    context.load_verify_locations(cafile=configured_path("caCerts"))
    context.load_cert_chain(
        certfile=configured_path("pemFilePath"),
        keyfile=configured_path("keyFilePath"),
    )
    return context

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

"""Runtime regressions for Python 3 and current Flask/JWT/TLS APIs."""

from collections import OrderedDict
from datetime import datetime, timedelta, timezone
import importlib
import json
from pathlib import Path
import pkgutil
import ssl
import sys
import tempfile
from threading import Thread
import time
import unittest
from unittest.mock import Mock, patch
from urllib.error import URLError
from urllib.request import urlopen
from xml.dom import minidom

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
from flask import Flask, jsonify
import jwt

REPO = Path(__file__).resolve().parents[1]
HARNESS = REPO / "CBRS_Mock_SAS_Python_Master" / "cbrsPython-master"
sys.path.insert(0, str(HARNESS / "cbrsPython"))

from controllers.CLIUtils.CsvFileParser import CsvFileParser
from controllers.CLIUtils.TestDefinition import TestDefinition
from controllers.CLIHandler import CLIHandler
from controllers.ENodeBController import ENodeBController
from controllers import StartPowerMeas
from model.CBRSRequestHandler import CBRSRequestHandler
from model.Engine import MyEngine
from model import flaskServer
from model.Utils import JsonComparisonUtils, Consts
from model.Utils.Server import run_server, stop_server
from model.Utils.Tls import create_server_context


def issue_certificate(key, name, issuer_key=None, issuer=None, ca=False, client=False):
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)])
    now = datetime.now(timezone.utc)
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer.subject if issuer is not None else subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=ca, path_length=None), critical=True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(
            (issuer_key or key).public_key()
        ), critical=False)
        .add_extension(x509.KeyUsage(
            digital_signature=True, content_commitment=False, key_encipherment=not ca,
            data_encipherment=False, key_agreement=False,
            key_cert_sign=ca, crl_sign=ca, encipher_only=False, decipher_only=False,
        ), critical=True)
    )
    if not ca:
        builder = builder.add_extension(
            x509.ExtendedKeyUsage([
                ExtendedKeyUsageOID.CLIENT_AUTH if client else ExtendedKeyUsageOID.SERVER_AUTH
            ]), critical=False,
        )
        builder = builder.add_extension(
            x509.SubjectAlternativeName([x509.DNSName(name)]), critical=False
        )
    return builder.sign(issuer_key or key, hashes.SHA256())


def write_identity(directory, name, key, certificate):
    cert_path = directory / (name + ".pem")
    key_path = directory / (name + ".key")
    cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ))
    return cert_path, key_path


class PythonRuntimeTests(unittest.TestCase):
    def test_all_non_gui_modules_import_without_prompting(self):
        with patch("builtins.input", side_effect=AssertionError("Unexpected input on import")):
            for name in ("controllers", "model", "Loggers"):
                package = importlib.import_module(name)
                for module in pkgutil.walk_packages(package.__path__, name + "."):
                    if module.name != "controllers.gui":
                        importlib.import_module(module.name)

    def test_all_bundled_csv_scenarios_resolve_json_files(self):
        config = minidom.parse(str(HARNESS / "Configuration" / "conf.xml"))
        scenarios = list((HARNESS / "testFiles").glob("*.csv"))
        self.assertTrue(scenarios)
        for scenario in scenarios:
            with self.subTest(scenario=scenario.name):
                parser = CsvFileParser(str(scenario.with_suffix("")), config, HARNESS)
                definition = TestDefinition(parser.initializeTestDefinition(), parser.find_Number_Of_Cols())
                self.assertTrue(any(definition.jsonNamesOfSteps))

    def test_csv_preserves_empty_columns_and_crlf(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "step.json").write_text("{}", encoding="utf-8")
            (directory / "scenario.csv").write_bytes(b'\xef\xbb\xbffirst,second\r\n,step.json\r\n')
            config = minidom.parseString('<config><jsonsRepoPath>.</jsonsRepoPath></config>')
            parser = CsvFileParser(str(directory / "scenario"), config, directory)
            steps = parser.initializeTestDefinition()
            self.assertEqual(parser.find_Number_Of_Cols(), 2)
            self.assertEqual([(step.index, step.jsonOfStep) for step in steps], [(1, "step.json")])

    def test_prepend_uses_public_ordered_mapping_api(self):
        for mapping in (OrderedDict([("a", 1), ("b", 2)]), {"a": 1, "b": 2}):
            JsonComparisonUtils.ordered_dict_prepend(mapping, "b", 3)
            self.assertEqual(list(mapping), ["b", "a"])
            self.assertEqual(mapping["b"], 3)
            JsonComparisonUtils.ordered_dict_prepend(mapping, "c", 4)
            self.assertEqual(list(mapping), ["c", "b", "a"])

    def test_unordered_nested_json_lists(self):
        first = [{"value": 2}, {"value": 1}]
        self.assertTrue(JsonComparisonUtils.are_same(first, first[::-1], True)[0])

    def test_heartbeat_error_fixture_selects_one_response_from_multiple(self):
        handler = CBRSRequestHandler.__new__(CBRSRequestHandler)
        handler.dirPath = HARNESS
        handler.enviormentConfFile = minidom.parse(str(HARNESS / "Configuration" / "conf.xml"))
        handler.loggerHandler = Mock()
        handler.jsonSteps = ["HBT_Post_HB_Error_500.json"]
        handler.numberOfStep = 0
        handler.expectedRelBeforeDeragistration = False
        handler.isLastStepInCSV = False
        response = handler.process_response("registration", {})
        self.assertEqual(list(response), ["registrationResponse"])
        self.assertEqual(response["registrationResponse"][0]["response"]["responseCode"], 200)

    def test_power_input_uses_numeric_conversion_and_reprompts(self):
        logger = Mock()
        with patch("builtins.input", side_effect=["__import__('os')", "3549", "3550"]):
            self.assertEqual(StartPowerMeas.input_spectrumInfoLow(logger), 3550000000)
        with patch("builtins.input", side_effect=["0", "-10", "bad", "10"]):
            spectrum = StartPowerMeas.input_bandwidth_Carrier(3550000000, logger)
            self.assertEqual(spectrum, [{"lowFrequency": 3550000000, "highFrequency": 3560000000}])
        with patch("builtins.input", side_effect=["bad", "100", "20.5"]):
            self.assertEqual(StartPowerMeas.input_maxEirp(logger), 20.5)

    def test_power_shutdown_works_without_removed_werkzeug_callback(self):
        response = StartPowerMeas.app.test_client().get("/shutdown")
        self.assertEqual(response.status_code, 200)

    def test_worker_stop_event_does_not_hide_thread_join_method(self):
        config = minidom.parse(str(HARNESS / "Configuration" / "conf.xml"))
        worker = CLIHandler("test", config, HARNESS, Mock(), TestDefinition([], 0))
        worker.stop_Thread_Due_To_Exception()
        with patch("controllers.CLIHandler.start_another_test"), patch("controllers.CLIHandler.time.sleep"):
            worker.start()
            worker.join(timeout=2)
        self.assertFalse(worker.is_alive())

    def test_registration_grant_heartbeat_relinquishment_deregistration(self):
        config = minidom.parse(str(HARNESS / "Configuration" / "conf.xml"))
        parser = CsvFileParser(str(HARNESS / "testFiles" / "WINNF.FT.C.DRG.1"), config, HARNESS)
        definition = TestDefinition(parser.initializeTestDefinition(), parser.find_Number_Of_Cols())
        engine = MyEngine(definition, config, HARNESS, Mock())
        old_controller = flaskServer.enodeBController
        self.addCleanup(setattr, flaskServer, "enodeBController", old_controller)
        flaskServer.enodeBController = ENodeBController(engine)
        client = flaskServer.app.test_client()

        def request(endpoint, payload):
            response = client.post(
                '/' + Consts.WINNF_PROTOCOL_VERSION + '/' + endpoint,
                json={endpoint + "Request": [payload]}, follow_redirects=True,
            )
            self.assertEqual(response.status_code, 200, response.data)
            self.assertIsInstance(response.json, dict, response.data)
            result = response.json[endpoint + "Response"][0]
            self.assertEqual(result["response"]["responseCode"], 0)
            return result

        registration = request("registration", {
            "cbsdSerialNumber": "D823956047", "fccId": "TEST", "userId": "operator",
        })
        cbsd_id = registration["cbsdId"]
        request("spectrumInquiry", {
            "cbsdId": cbsd_id,
            "inquiredSpectrum": [{"lowFrequency": 3550000000, "highFrequency": 3560000000}],
        })
        grant = request("grant", {
            "cbsdId": cbsd_id, "operationParam": {
                "maxEirp": 20, "operationFrequencyRange": {
                    "lowFrequency": 3550000000, "highFrequency": 3560000000,
                },
            },
        })
        grant_id = grant["grantId"]
        request("heartbeat", {"cbsdId": cbsd_id, "grantId": grant_id, "operationState": "GRANTED"})
        request("heartbeat", {"cbsdId": cbsd_id, "grantId": grant_id, "operationState": "AUTHORIZED"})
        request("relinquishment", {"cbsdId": cbsd_id, "grantId": grant_id})
        request("deregistration", {"cbsdId": cbsd_id})
        self.assertFalse(engine.check_Validation_Error())


class CpiSignatureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.handler = CBRSRequestHandler.__new__(CBRSRequestHandler)
        self.handler.dirPath = self.directory
        self.handler.loggerHandler = Mock()
        self.handler.enviormentConfFile = minidom.parseString(
            '<config><cpiCert>cpi.pem</cpiCert><jsonsRepoPath>'
            + str(HARNESS / "jsonExpectedFolder") + '</jsonsRepoPath></config>'
        )
        self.payload = {
            "fccId": "TEST", "cbsdSerialNumber": "D823956047",
            "installationParam": {
                "latitude": 38, "longitude": -77, "height": 10, "heightType": "AGL",
                "indoorDeployment": False, "antennaGain": 0,
                "antennaAzimuth": 0, "antennaDowntilt": 0, "antennaBeamwidth": 360,
            },
            "professionalInstallerData": {
                "cpiId": "test-installer", "cpiName": "Installer",
                "installCertificationTime": "2026-10-11T00:00:00Z",
            },
        }

    def signature(self, key, algorithm, payload=None):
        cert = issue_certificate(key, "cpi")
        (self.directory / "cpi.pem").write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        token = jwt.encode(self.payload if payload is None else payload, key, algorithm=algorithm)
        return dict(zip(
            ("protectedHeader", "encodedCpiSignedData", "digitalSignature"), token.split('.')
        ))

    def test_rsa_and_ecdsa_signatures(self):
        for key, algorithm in (
            (rsa.generate_private_key(public_exponent=65537, key_size=2048), "RS256"),
            (ec.generate_private_key(ec.SECP256R1()), "ES256"),
        ):
            with self.subTest(algorithm=algorithm):
                self.assertTrue(self.handler.checkCpiSignedData(self.signature(key, algorithm), "B"))

    def test_tampered_signature_is_rejected(self):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        data = self.signature(key, "RS256")
        signature = data["digitalSignature"]
        data["digitalSignature"] = ('A' if signature[0] != 'A' else 'B') + signature[1:]
        self.assertFalse(self.handler.checkCpiSignedData(data, "B"))

    def test_unsigned_or_malformed_tokens_are_rejected(self):
        unsigned = jwt.encode(self.payload, None, algorithm="none")
        data = dict(zip(("protectedHeader", "encodedCpiSignedData", "digitalSignature"), unsigned.split('.')))
        for malformed in ({}, data, {"protectedHeader": "??", "encodedCpiSignedData": "x", "digitalSignature": "x"}):
            with self.subTest(data=malformed):
                self.assertFalse(self.handler.checkCpiSignedData(malformed, "B"))

    def test_valid_signature_with_invalid_schema_is_rejected(self):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.assertFalse(self.handler.checkCpiSignedData(self.signature(key, "RS256", {}), "B"))

    def test_category_a_optional_antenna_fields(self):
        for field in Consts.CPI_INSTALLPARAM_CATA_OPTIONAL:
            self.payload["installationParam"].pop(field)
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        signature = self.signature(key, "RS256")
        self.assertTrue(self.handler.checkCpiSignedData(signature, "A"))
        self.assertFalse(self.handler.checkCpiSignedData(signature, "B"))


class MutualTlsTests(unittest.TestCase):
    def test_fresh_mutual_tls_and_server_shutdown(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            ca = issue_certificate(ca_key, "test-ca", ca=True)
            (directory / "ca.pem").write_bytes(ca.public_bytes(serialization.Encoding.PEM))
            for name, client in (("localhost", False), ("client", True)):
                key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
                certificate = issue_certificate(key, name, ca_key, ca, client=client)
                write_identity(directory, name, key, certificate)
            config = minidom.parseString(
                '<config><caCerts>ca.pem</caCerts><pemFilePath>localhost.pem</pemFilePath>'
                '<keyFilePath>localhost.key</keyFilePath></config>'
            )
            context = create_server_context(config, directory)
            self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
            self.assertEqual(context.minimum_version, ssl.TLSVersion.TLSv1_2)
            self.assertEqual(context.maximum_version, ssl.TLSVersion.TLSv1_2)
            app = Flask(__name__)
            app.add_url_rule("/ping", view_func=lambda: jsonify(ok=True))
            thread = Thread(target=run_server, args=(app, "127.0.0.1", 0, context), daemon=True)
            thread.start()
            deadline = time.monotonic() + 5
            while "HARNESS_SERVER" not in app.config and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertIn("HARNESS_SERVER", app.config)
            url = 'https://localhost:' + str(app.config["HARNESS_SERVER"].server_port) + '/ping'
            client_context = ssl.create_default_context(cafile=directory / "ca.pem")
            client_context.minimum_version = ssl.TLSVersion.TLSv1_2
            try:
                with self.assertRaises((ssl.SSLError, URLError)):
                    urlopen(url, context=client_context, timeout=3)
                client_context.load_cert_chain(directory / "client.pem", directory / "client.key")
                with urlopen(url, context=client_context, timeout=3) as response:
                    self.assertEqual(json.load(response), {"ok": True})
            finally:
                stop_server(app)
                thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
            self.assertNotIn("HARNESS_SERVER", app.config)


if __name__ == "__main__":
    unittest.main()

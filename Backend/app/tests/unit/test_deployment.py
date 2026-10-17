"""Deployment checks that do not start containers or download models.

Run from the repository root with:
python3 -m unittest discover -s Backend/app/tests/unit -p test_deployment.py -v
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile


BACKEND = Path(__file__).resolve().parents[3]


class MedcatStartupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        self.models = self.root / "models"
        self.env = {
            **os.environ,
            "PATH": f"{self.bin_dir}{os.pathsep}{os.environ['PATH']}",
            "MODEL_DIR": str(self.models),
            "MOCK_ROOT": str(self.root),
        }
        self.stub("curl", """#!/bin/bash
set -e
while [ "$#" -gt 0 ]; do
    if [ "$1" = "--output" ]; then
        output="$2"
        shift
    fi
    shift
done
echo download >> "$MOCK_ROOT/downloads"
echo model > "$output"
if [ "${MOCK_DOWNLOAD_FAIL:-0}" = 1 ]; then exit 22; fi
if [ "${MOCK_DOWNLOAD_EMPTY:-0}" = 1 ]; then : > "$output"; fi
""")
        self.stub("unzip", """#!/bin/bash
set -e
if [ "${MOCK_UNZIP_FAIL:-0}" = 1 ]; then exit 9; fi
while [ "$#" -gt 0 ]; do
    if [ "$1" = "-d" ]; then
        mkdir -p "$2"
        echo metadata > "$2/config.json"
        exit 0
    fi
    shift
done
exit 1
""")
        (self.root / "start_service_production.sh").write_text(
            'echo ready > "$MOCK_ROOT/ready"\n'
        )

    def stub(self, name, contents):
        path = self.bin_dir / name
        path.write_text(contents)
        path.chmod(0o755)

    def start(self, **flags):
        return subprocess.run(
            ["bash", str(BACKEND / "medcat-init.sh")],
            cwd=self.root,
            env={**self.env, **flags},
            capture_output=True,
            text=True,
            timeout=15,
        )

    def test_downloads_models_and_reuses_cache_on_restart(self):
        result = self.start()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / "ready").exists())
        self.assertTrue((self.models / "mc_status/config.json").exists())
        self.assertEqual(len((self.root / "downloads").read_text().splitlines()), 3)
        result = self.start()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len((self.root / "downloads").read_text().splitlines()), 3)

    def test_failed_download_does_not_cache_partial_model(self):
        result = self.start(MOCK_DOWNLOAD_FAIL="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.models / "medmen.cdb").exists())
        self.assertFalse((self.root / "ready").exists())
        result = self.start()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_empty_download_does_not_start_service(self):
        result = self.start(MOCK_DOWNLOAD_EMPTY="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.models / "medmen.cdb").exists())
        self.assertFalse((self.root / "ready").exists())

    def test_failed_extraction_can_be_retried(self):
        result = self.start(MOCK_UNZIP_FAIL="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.models / "mc_status").exists())
        self.assertFalse((self.root / "ready").exists())
        result = self.start()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.models / "mc_status/config.json").exists())

    @unittest.skipUnless(shutil.which("unzip"), "unzip is required for the archive regression")
    def test_corrupt_cached_archive_is_removed_and_redownloaded(self):
        self.models.mkdir()
        (self.models / "medmen.cdb").write_text("cached concept database")
        (self.models / "vocab.dat").write_text("cached vocabulary")
        archive = self.models / "mc_status.zip"
        archive.write_bytes(b"corrupt archive returned by a previous download")
        staged = self.models / "mc_status.tmp"
        staged.mkdir()
        (staged / "partial-model").write_text("incomplete extraction")

        # Use the real unzip command so recovery depends on replacing the bytes.
        (self.bin_dir / "unzip").unlink()
        with zipfile.ZipFile(self.root / "source.zip", "w") as fresh:
            fresh.writestr("config.json", '{"model": "fresh"}')
        self.stub("curl", """#!/bin/bash
set -e
while [ "$#" -gt 0 ]; do
    if [ "$1" = "--output" ]; then
        output="$2"
        shift
    fi
    shift
done
echo download >> "$MOCK_ROOT/downloads"
cp "$MOCK_ROOT/source.zip" "$output"
""")

        result = self.start()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(archive.exists(), "Corrupt archives must not survive a failed extraction")
        self.assertFalse(staged.exists(), "Partial extraction files must be removed")
        self.assertFalse((self.models / "mc_status").exists())
        self.assertFalse((self.root / "ready").exists())
        self.assertFalse((self.root / "downloads").exists())

        result = self.start()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / "ready").exists())
        self.assertEqual(
            (self.models / "mc_status/config.json").read_text(), '{"model": "fresh"}'
        )
        self.assertFalse((self.models / "mc_status/partial-model").exists())
        self.assertFalse(archive.exists())
        self.assertFalse(staged.exists())
        self.assertEqual((self.root / "downloads").read_text().splitlines(), ["download"])
        self.assertEqual((self.models / "medmen.cdb").read_text(), "cached concept database")
        self.assertEqual((self.models / "vocab.dat").read_text(), "cached vocabulary")


@unittest.skipUnless(shutil.which("docker"), "Docker Compose CLI is required")
class ComposeConfigurationTests(unittest.TestCase):
    def check_ports(self, overrides, host, backend_port, frontend_port, medcat_port):
        env = os.environ.copy()
        for key in ("PUBLIC_HOST", "BACKEND_PORT", "FRONTEND_PORT", "MEDCAT_PORT"):
            env.pop(key, None)
        with tempfile.TemporaryDirectory() as temp:
            env_file = Path(temp) / ".env"
            env_file.write_text(
                (BACKEND / ".env.example").read_text() + "\n"
                + "\n".join(f"{key}={value}" for key, value in overrides.items())
            )
            result = subprocess.run(
                [
                    "docker", "compose", "--env-file", str(env_file),
                    "-f", str(BACKEND / "docker-compose.yml"),
                    "config", "--no-env-resolution", "--format", "json",
                ],
                env=env, capture_output=True, text=True, timeout=30,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        services = json.loads(result.stdout)["services"]
        for name, published, target in (
            ("fastapi-backend", backend_port, 8000),
            ("frontend", frontend_port, 3030),
            ("medcat-service", medcat_port, 5000),
        ):
            port = services[name]["ports"][0]
            self.assertEqual(port["published"], str(published))
            self.assertEqual(port["target"], target)
        frontend_env = services["frontend"]["environment"]
        self.assertEqual(frontend_env["REACT_APP_BACKEND_URL"], f"http://{host}:{backend_port}")
        self.assertEqual(frontend_env["REACT_APP_BACKEND_WS_URL"], f"ws://{host}:{backend_port}")
        self.assertEqual(
            services["fastapi-backend"]["environment"]["MEDCAT_URL"],
            "http://medcat-service:5000/api/process",
        )

    def test_default_ports(self):
        self.check_ports({}, "localhost", 8010, 3030, 5000)

    def test_empty_settings_use_default_ports(self):
        self.check_ports(
            {"PUBLIC_HOST": "", "BACKEND_PORT": "", "FRONTEND_PORT": "", "MEDCAT_PORT": ""},
            "localhost", 8010, 3030, 5000,
        )

    def test_custom_ports_update_browser_urls_and_preserve_internal_address(self):
        self.check_ports(
            {"PUBLIC_HOST": "192.0.2.10", "BACKEND_PORT": "18010",
             "FRONTEND_PORT": "13030", "MEDCAT_PORT": "15000"},
            "192.0.2.10", 18010, 13030, 15000,
        )


if __name__ == "__main__":
    unittest.main()

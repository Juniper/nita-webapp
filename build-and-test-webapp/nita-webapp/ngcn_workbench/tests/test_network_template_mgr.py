# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile


class NetworkTemplateManagerTests(unittest.TestCase):
    def test_create_preserves_template_variables_and_replaces_inventory(self):
        job_file = Path(__file__).resolve().parents[3] / "network_template_mgr.xml"
        command = ElementTree.parse(job_file).findtext("./builders/hudson.tasks.Shell/command")
        self.assertIsNotNone(command)
        start = command.index('echo "extracting to $dest_folder..."')
        end = command.index('#echo "overwriting project.yaml file..."', start)
        create_script = command[start:end]

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "template.zip"
            files = {
                "group_vars/all.yaml": "common: value\n",
                "group_vars/registry.yaml": "registry: value\n",
                "group_vars/nested/all.yaml": "nested: value\n",
                "host_vars/device.yaml": "host: value\n",
                "hosts": "old inventory\n",
            }
            with ZipFile(archive, "w") as archive_file:
                for name, contents in files.items():
                    archive_file.writestr(f"template/{name}", contents)

            dest = root / "template-network"
            env = os.environ | {
                "src": str(archive),
                "source_folder": str(root / "template"),
                "dest_folder": str(dest),
                "hosts": "[all]\ndevice",
            }
            subprocess.run(
                ["bash", "-e", "-c", create_script],
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )

            for name, contents in files.items():
                if name != "hosts":
                    self.assertEqual((dest / name).read_text(), contents)
            self.assertEqual((dest / "hosts").read_text(), "[all]\ndevice\n")


if __name__ == "__main__":
    unittest.main()

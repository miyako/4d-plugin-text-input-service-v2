"""Preservation evidence, valid both at intake and after a guarded source bump."""

import importlib.util
from pathlib import Path
import re
import stat
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
BASE = "2ba5d73a5b8a0ce0470a170886dc38639674440e"
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location(
    "contract_source", ROOT / ".github/scripts/source_version.py"
)
source = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(source)


def original(path):
    return subprocess.check_output(["git", "-C", str(ROOT), "show", f"{BASE}:{path}"])


class RepositoryContractTests(unittest.TestCase):
    def test_explicit_coordinated_header_supersedes_fallback_body_and_history(self):
        bump = original(".github/workflows/bump-version.yml").decode()
        header, body = bump.split("name: Bump version", 1)
        self.assertIn("MARKETING_VERSION/CURRENT_PROJECT_VERSION AND Info.plist", header)
        self.assertIn("CFBundleShortVersionString/CFBundleVersion", header)
        self.assertIn('KEY="MARKETING_VERSION"', body)
        self.assertIn('KEY="CURRENT_PROJECT_VERSION"', body)
        history = subprocess.check_output([
            "git", "-C", str(ROOT), "log", "--follow", "--format=%H %B",
            BASE, "--", ".github/workflows/bump-version.yml",
        ], text=True)
        self.assertIn("88bf44afc5fccc777ea751b4ea9565e717e59f9b", history)
        self.assertIn("Sync version fields", history)
        release = original(".github/workflows/release.yml").decode()
        self.assertIn("  push:\n    tags:\n      - 'v*.*.*'", release)
        self.assertIn("  workflow_dispatch:\n    inputs:\n      tag:", release)
        self.assertNotIn("pull_request:", release)
        self.assertNotIn("branches:", release)

    def test_source_has_only_authorized_version_token_changes(self):
        current = source.read(ROOT)
        self.assertEqual(source.SETTING_COUNT, 6)
        for path in source.SOURCE_PATHS:
            with self.subTest(path=path):
                before = original(path)
                if path == source.LOCALIZED:
                    expected = before.replace(
                        b'CFBundleShortVersionString = "3.0.1";',
                        f'CFBundleShortVersionString = "{current}";'.encode(),
                    ).replace(
                        b"Text Input Service version 3.0.1, Copyright 2023 miyako.",
                        f"Text Input Service version {current}, Copyright 2023 miyako.".encode(),
                    )
                    self.assertNotIn(b"\n", before)
                    self.assertIn(b"\r", before)
                elif path == source.PROJECT:
                    expected = before.replace(
                        b"MARKETING_VERSION = 3.0.5;",
                        f"MARKETING_VERSION = {current};".encode(),
                    ).replace(
                        b"CURRENT_PROJECT_VERSION = 3.0.3;",
                        f"CURRENT_PROJECT_VERSION = {current};".encode(),
                    )
                else:
                    expected = before.replace(b"3.0.5", current.encode())
                self.assertEqual((ROOT / path).read_bytes(), expected)
                self.assertEqual(stat.S_IMODE((ROOT / path).stat().st_mode), 0o644)
        self.assertNotIn(b"<key>CFBundleVersion</key>", (ROOT / source.PLIST).read_bytes())

    def test_all_unrelated_original_files_preserved(self):
        paths = subprocess.check_output([
            "git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", BASE,
        ], text=True).splitlines()
        allowed = {*map(str, source.SOURCE_PATHS), "README.md",
                   ".github/workflows/bump-version.yml", ".github/workflows/release.yml"}
        for name in paths:
            if name in allowed:
                continue
            with self.subTest(path=name):
                self.assertEqual((ROOT / name).read_bytes(), original(name))
                recorded = subprocess.check_output([
                    "git", "-C", str(ROOT), "ls-tree", BASE, "--", name,
                ], text=True).split()[0]
                self.assertEqual(stat.S_IMODE((ROOT / name).stat().st_mode),
                                 int(recorded, 8) & 0o777)

    def test_actual_macos_only_pipeline_signing_and_secret_names(self):
        before = original(".github/workflows/release.yml").decode()
        after = (ROOT / ".github/workflows/release.yml").read_text()

        def block(workflow, name):
            return workflow.split(f"      - name: {name}\n", 1)[1].split(
                "\n      - name:", 1
            )[0].rstrip()

        for name in ("import Developer ID certificate",
                     "store notarytool credentials", "codesign"):
            self.assertEqual(block(before, name), block(after, name))
        secrets = r"\$\{\{ secrets\.([A-Z_]+) \}\}"
        self.assertEqual(re.findall(secrets, before), re.findall(secrets, after))
        for required in (
            'ARCHS="arm64 x86_64"', "-configuration Default",
            "MACOS_DEPLOYMENT_TARGET: '10.13'", "ONLY_ACTIVE_ARCH=NO",
            'xcrun stapler staple "$DMG_PATH"',
            'ditto -c -k --keepParent "$BUNDLE_PATH" "$ZIP_PATH"',
            'hdiutil create -format UDBZ -volname "${{ env.PRODUCT_NAME }}" -srcfolder "$BUNDLE_PATH" "$DMG_PATH"',
        ):
            self.assertIn(required, before)
            self.assertIn(required, after)
        for prohibited in ("runs-on: windows-latest", "msbuild ", "build-windows:",
                           "CODE_SIGNING_ALLOWED=NO"):
            self.assertNotIn(prohibited, before)
            self.assertNotIn(prohibited, after)

    def test_copy_phase_destinations_and_untouched_windows_project(self):
        project = (ROOT / source.PROJECT).read_text()
        self.assertIn("path = English.lproj/InfoPlist.strings", project)
        self.assertIn("InfoPlist.strings in Resources", project)
        self.assertIn("dstSubfolderSpec = 7;", project)
        self.assertIn("constants.xlf in CopyFiles", project)
        self.assertIn("manifest.json in CopyFiles", project)
        self.assertIn('CONFIGURATION_BUILD_DIR = "$(BUILD_DIR)"', project)
        self.assertIn('SYMROOT = "$(SRCROOT)/test/Plugins"', project)
        self.assertIn('if test \\"$CONFIGURATION\\" == \'Deployment\'', project)
        windows = ROOT / "Text Input Service.vcxproj"
        self.assertEqual(windows.read_bytes(), original(windows.name))
        ns = {"m": "http://schemas.microsoft.com/developer/msbuild/2003"}
        xml = ET.fromstring(windows.read_bytes())
        self.assertEqual({element.text for element in xml.findall(".//m:PlatformToolset", ns)},
                         {"v140"})
        for element in xml.findall(".//m:OutDir", ns):
            suffix = "windows64\\" if "x64" in element.attrib["Condition"] else "windows\\"
            self.assertEqual(element.text,
                             "$(ProjectDir)test\\plugins\\$(ProjectName).bundle\\contents\\" + suffix)
        self.assertEqual({element.text for element in xml.findall(".//m:TargetExt", ns)},
                         {".4DX"})


if __name__ == "__main__":
    unittest.main()

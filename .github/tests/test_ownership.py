"""Unsigned synthetic host: actual dispatcher, all wrappers, complete pinned SDK."""

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(os.environ.get("OWNERSHIP_SOURCE_ROOT", ROOT)).resolve()
SDK = {
    "4DPluginAPI.c": "62f745e91d81ef2c3c901c656ea8e175d3b173e8",
    "4DPluginAPI.h": "528bf1d2552df08d6a8b1bc95011a9b72934ad5c",
    "4DPluginAPI.def": "5bbdb82fb724b6f8e307feb01d9f158b802de89d",
    "EntryPoints.h": "da428d5f6ca23b0a30371c7288a01d29aa3c466a",
    "Flags.h": "7a5a35539f27430a3fd9cb711d6b789051316471",
    "PrivateTypes.h": "a3098cb662cdbc43ba574fdef72a059c4c6d1cd4",
    "PublicTypes.h": "9ae20b001bff9128f690fff3e6c3f873b6238333",
}


@unittest.skipUnless(sys.platform == "darwin", "macOS synthetic host")
class OwnershipTests(unittest.TestCase):
    runs = 0
    passes = 0

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="service-ownership-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.binary = Path(cls.temp.name) / "ownership"
        api = SOURCE / "4D Plugin API"
        for name, expected in SDK.items():
            contents = (api / name).read_bytes()
            blob = hashlib.sha1(f"blob {len(contents)}\0".encode() + contents).hexdigest()
            if blob != expected:
                raise AssertionError(f"Re-audit changed SDK: {name}: {blob}")
        flags = ["-DOWNERSHIP_BASELINE_COPY"] if os.environ.get("OWNERSHIP_BASELINE_COPY") else []
        result = subprocess.run([
            "clang++", "-std=c++14", "-x", "objective-c++", "-fblocks",
            "-include", str(ROOT / ".github/tests/ownership_platform.h"),
            "-I", str(api), "-I", str(api / "Classes"), "-I", str(SOURCE / "support"),
            "-I", str(SOURCE), *flags,
            "-fsanitize=address,undefined", "-fno-sanitize=alignment",
            "-fno-omit-frame-pointer", "-g",
            "-Wno-deprecated-declarations", "-Wno-return-type-c-linkage",
            "-Wno-ignored-attributes", "-Wno-writable-strings",
            str(api / "4DPluginAPI.c"),
            *map(str, sorted((api / "Classes").glob("*.cpp"))),
            str(SOURCE / "support/4DPlugin-JSON.cpp"),
            str(SOURCE / "4DPlugin-Text-Input-Service.cpp"),
            str(ROOT / ".github/tests/ownership_host.mm"),
            "-framework", "Cocoa", "-framework", "Carbon", "-o", str(cls.binary),
        ], capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        imports = subprocess.check_output(["nm", "-u", str(cls.binary)], text=True)
        linked = {line.split()[-1] for line in imports.splitlines() if line.split()}
        allowed_classes = {
            "_OBJC_CLASS_$_NSObject", "_OBJC_CLASS_$_NSString", "_OBJC_CLASS_$_NSMutableString",
            "_OBJC_CLASS_$_NSArray", "_OBJC_CLASS_$_NSMutableArray",
            "_OBJC_CLASS_$_NSDictionary", "_OBJC_CLASS_$_NSMutableDictionary", "_OBJC_CLASS_$_NSData",
        }
        denied = {name for name in linked if name.startswith("_OBJC_CLASS_$_") and name not in allowed_classes}
        denied |= {name for name in linked if name.startswith((
            "_TIS", "_CGImage", "_CGContext", "_CFURL", "_AX", "_IO", "_dispatch_", "_NSAllRoman",
        ))}
        denied |= {
            "_system", "_popen", "_execve", "_posix_spawn", "_kill", "_NSApp",
            "_open", "_fopen", "_socket", "_connect", "_getenv",
        } & linked
        if denied:
            raise AssertionError(f"Real platform boundary linked: {denied}")

    @classmethod
    def tearDownClass(cls):
        print(f"LEAF runs={cls.runs} passed={cls.passes} failed={cls.runs - cls.passes}", file=sys.stderr)

    def case(self, name, text="ASCII", empty="allocated", kind="string"):
        type(self).runs += 1
        result = subprocess.run(
            [str(self.binary), name, text, empty, kind],
            env={**os.environ, "ASAN_OPTIONS": "detect_leaks=0", "UBSAN_OPTIONS": "halt_on_error=1"},
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            type(self).passes += 1
        self.assertEqual(result.returncode, 0, f"{name}/{text}/{empty}/{kind}: {result.stdout}{result.stderr}")
        self.assertIn("strings=0 pictures=0 handles=0 objects=0 collections=0", result.stdout)

    def test_setter_empty_owner_overwrite(self):
        for setter in ("set-narrow", "set-wide", "set-wchars"):
            for text in ("ASCII", "\u65e5", "\U0001f600", ""):
                for empty in ("allocated", "null"):
                    with self.subTest(setter=setter, text=text, empty=empty):
                        self.case(setter, text, empty)
        self.case("set-picture")

    def test_getter_success_owners_and_mismatches(self):
        for getter in ("get-a", "get-b", "get-n", "get-c"):
            for kind in ("string", "picture", "object", "collection", "boolean", "real"):
                for empty in ("allocated", "null"):
                    with self.subTest(getter=getter, kind=kind, empty=empty):
                        self.case(getter, "\u65e5\U0001f600", empty, kind)
            for empty in ("allocated", "null"):
                with self.subTest(getter=getter, empty=empty):
                    self.case(getter, "", empty)

    def test_failed_results_and_stringify(self):
        for text in ("ASCII", "\u65e5", "\U0001f600", ""):
            for empty in ("allocated", "null"):
                with self.subTest(text=text, empty=empty):
                    self.case("stringify", text, empty)
        for kind in ("picture", "object", "collection", "boolean", "real"):
            with self.subTest(kind=kind):
                self.case("stringify", kind=kind)
        for name in ("get-a", "get-b", "get-n", "get-c", "stringify"):
            for kind in ("error-poison", "error-kind0"):
                with self.subTest(name=name, kind=kind):
                    self.case(name, kind=kind)
        for kind in ("error-handle", "error-first-handle", "error-copy",
                     "copy-string", "copy-picture", "copy-collection", "copy-boolean", "copy-real"):
            with self.subTest(kind=kind):
                self.case("stringify", kind=kind)

    def test_dispatcher_wrappers_and_array_controls(self):
        for empty in ("allocated", "null"):
            for text in ("ASCII", "\u65e5", "\U0001f600", ""):
                for name in ("dispatch-1", "dispatch-2", "dispatch-3", "array", "wrappers"):
                    with self.subTest(name=name, text=text, empty=empty):
                        self.case(name, text, empty)
            for selector in (1, 2, 3):
                with self.subTest(selector=selector, empty=empty):
                    self.case(f"dispatch-{selector}", empty=empty, kind="no-source")
        for kind in ("no-metadata", "icon-ref", "image-failure"):
            with self.subTest(kind=kind):
                self.case("dispatch-3", kind=kind)
        for name in ("sdk-failures", "blob-allocation-failure", "values", "null-controls", "missing", "copy-traits"):
            with self.subTest(name=name):
                self.case(name)

    @unittest.skipUnless(os.environ.get("OWNERSHIP_BASELINE_COPY"), "baseline-only unsafe copies")
    def test_baseline_copy_sanitizer(self):
        for name in ("copy-array", "assign-array", "copy-blob", "assign-blob"):
            with self.subTest(name=name):
                self.case(name)


if __name__ == "__main__":
    unittest.main()

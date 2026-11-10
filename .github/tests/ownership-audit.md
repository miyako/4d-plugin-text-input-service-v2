# Native ownership audit

## Provenance and complete inventory

Baseline commit `737a4db89d4996c91c126c79859f3ff0f79da256`, tree
`40e9433da1bddc1f3b4190dbd4562e3416b40b69`.
Canonical guidance was read through the GitHub API from
`miyako/skills/4d-skills/skills/4dplugin/SKILL.md` at immutable
`e6b492fcb81e5e1a7f7db723594b420e63bf6eb9`.
Synthetic-boundary prior art was inspected at
`miyako/4d-plugin-text-input-context` commit
`0b259172a9552b5bdf67a8798c26ad030a7bab23`. Its results and SDK identities
are not substituted for this target's evidence.

The complete bundled SDK is compiled unchanged. The source says "rev : v14";
this is not a verified upstream SDK release identifier.

| SDK file under `4D Plugin API/` | Git blob |
|---|---|
| `4DPluginAPI.c` | `62f745e91d81ef2c3c901c656ea8e175d3b173e8` |
| `4DPluginAPI.h` | `528bf1d2552df08d6a8b1bc95011a9b72934ad5c` |
| `4DPluginAPI.def` | `5bbdb82fb724b6f8e307feb01d9f158b802de89d` |
| `EntryPoints.h` | `da428d5f6ca23b0a30371c7288a01d29aa3c466a` |
| `Flags.h` | `7a5a35539f27430a3fd9cb711d6b789051316471` |
| `PrivateTypes.h` | `a3098cb662cdbc43ba574fdef72a059c4c6d1cd4` |
| `PublicTypes.h` | `9ae20b001bff9128f690fff3e6c3f873b6238333` |

All tracked native translation units are the SDK, actual
`4DPlugin-Text-Input-Service.cpp` dispatcher, `support/4DPlugin-JSON.cpp`,
and four wrappers: `ARRAY_TEXT.cpp`, `C_TEXT.cpp`, `C_BLOB.cpp`,
`C_LONGINT.cpp`. Their headers, `Classes/C_TYPES.h`, dispatcher header,
JSON header and SDK entry/export declarations are included in the inventory.
There is no second SDK/platform implementation. `FourDPackex` forwards into
`PluginMain`, whose selectors are 1-3.

Xcode's actual Sources phase contains SDK + dispatcher + JSON + `C_TEXT`.
`ARRAY_TEXT`, `C_BLOB` and `C_LONGINT` are dormant project consumers but all
compile and execute in this harness. The legacy Windows vcxproj lists only
SDK and dispatcher, omitting the helper/wrapper translation units; the
dispatcher unconditionally imports Carbon and uses Objective-C. It is not
a working Windows-branch validation target. No Windows/native-4D ABI or
Windows crash reproduction is claimed.

| Baseline wrapper/helper under `4D Plugin API/Classes/` unless noted | Git blob |
|---|---|
| `ARRAY_TEXT.cpp` | `534855e0959020ce9a66cef08f8434799c174495` |
| `ARRAY_TEXT.h` | `cf8a458fc8519b824c726a59d346c44d4c26e845` |
| `C_TEXT.cpp` | `45ea6432dff52b681a5c6a7cea58ad5fc15df66b` |
| `C_TEXT.h` | `6967390757db569ffcd3cfea8696bf14045cc748` |
| `C_BLOB.cpp` | `27bea3172ce90e4da339991c9b318a71ea8609b2` |
| `C_BLOB.h` | `d181534e5a2e9bd46de492a040c1538ed81bf45a` |
| `C_LONGINT.cpp` | `005b83a4aec2c1466b8b219cb27ab845eb58de91` |
| `C_LONGINT.h` | `71e24df633aed7155cba1ffddc07d6a1dfc12fa9` |
| `C_TYPES.h` | `6c8d2571f36cb0080e8cd4ac1f0f4819b6d4c138` |
| `support/4DPlugin-JSON.cpp` | `b58bc6f65a87806b50dae16c8d73e64ce07d1298` |
| `support/4DPlugin-JSON.h` | `7c8021c52fd63bf2e03df7085fcf87adb279af3d` |

The manifest declares scalar text for selectors 1 and 2, a scalar text
return for 2, and a collection return for 3. No public text arrays are
declared, but the dormant array wrapper is still audited and tested.
Selector 3 internally constructs objects containing six possible text
properties plus a picture. JSON helpers include dormant scalar/collection
getters, setters and stringify. No callback string aliases are retained
asynchronously in the actual dispatcher.

`include/json/*.h` contains vendored JsonCpp declarations/inline C++ helpers,
not a second PA string implementation; no consumer includes them.
`a/libjsoncpp.a`, Windows JsonCpp libraries, packaged plugins, ZIP/DMG,
packaged manifests, and `test/` 4D database/project assets are prebuilt
artifacts, not replacement source. They are unchanged and not executed.

## Exact contracts and surgical changes

`PA_CreateVariable(eVK_Unistring/eVK_Picture)` allocates an initial empty
owner (SDK 3920-4060). `PA_SetStringVariable` (4254) and
`PA_SetPictureVariable` (4280) shallow-assign without clearing it.
All three JSON string setter overloads and the picture setter now initialize
Undefined before adopting the distinct incoming allocation. Their final
variable clear remains necessary. The engine property boundary copies
strings/retains references or pictures before that clear. This fixes the
production `INPUT_SOURCE_LIST` string/picture path without removing cleanup.
There is no second explicit dispose of that picture in the caller.

`PA_GetObjectProperty` (637) and `PA_GetCollectionElement` (587) explicitly
say their successful result must be cleared. The four JSON property getters
now capture `PA_GetLastError` immediately, before kind inspection or cleanup.
Successful scalar values are copied before clearing, including mismatches.
`ob_get_c` transfers a matching collection owner to its caller, and clears
only successful mismatches. Failed unspecified values are never inspected,
adopted or cleared. In particular, raw failed `fType == 0` can be normalized
to text by `UnifyVarKind` (1713); zero is not proof of an owned empty string.

`ob_stringify` now executes OB Copy through the actual SDK command boundary,
not `PA_DuplicateObject`, whose implementation extracts an object before its
caller can check the command error. Duplicate and stringify errors are
captured before kind inspection, adoption or synchronous argument cleanup.
Successful wrong-kind returns are cleared. The original object remains
borrowed; its independently owned copy is cleared after synchronous
stringify, while the independent successful result survives until copied.
Failure still leaves the caller's output unchanged, as the existing helper
did for wrong-kind results; no worker throw or new error channel is added.
The existing lack of caller-visible error reporting is an explicit gap:
cleanup can reset the thread-local SDK error, and these helper signatures
cannot promise to propagate it.

`PA_SetStringInArray` (4933) disposes the old element then transfers the
incoming allocation only for Unicode-array kind, non-null data,
`0 <= index <= count`, and a non-null descriptor. Index zero is accepted.
Rejected assignments retain caller ownership. `ARRAY_TEXT` already has no
post-transfer dispose, so this behavior is preserved. Its getter copies
borrowed content into independent C++ strings before any later mutation.
`C_TEXT` parameter/return paths use `PA_SetUnistring`, a content setter,
not the array transfer implementation; its existing noncopy restriction
is prior art. `C_LONGINT` owns no heap object.

`ARRAY_TEXT` and `C_BLOB` own raw allocated C++ objects and previously
implicitly copied those pointers. Named baseline probes `copy-array`,
`assign-array`, `copy-blob`, `assign-blob` each produce ASan heap-use-after-free.
Both classes now use the existing `C_TEXT` deleted-copy pattern.
Every actual consumer compiles with it. These are latent defects: no
production wrapper-copy invocation was found, and none is invented.
`CBytes` holds its vector by value and remains copyable.

There is no `CPicture`, pointer-reference constructor, or `createCopy` in
this target. `CBytes::setBytes` copies caller bytes into a vector and creates
no picture owner; it is not the picture-wrapper leak from another SDK.
No converter-returned byte count is passed to a UTF-16 wrapper here:
the actual wrappers/helpers use CF UTF-16 character counts on macOS and
MultiByteToWideChar unit counts on Windows, with byte capacities for buffers.
Windows conversion branches were inspected but not compiled or certified.
No SDK/ABI/header implementation is rewritten.

## Isolated regression evidence

```sh
PYTHONDONTWRITEBYTECODE=1 python3 .github/tests/test_ownership.py
```

The same final harness is used against a `git archive` export of the exact
baseline native files, selected using `OWNERSHIP_SOURCE_ROOT`. Set
`OWNERSHIP_BASELINE_COPY=1` only for four intentionally unsafe baseline
copy probes; fixed builds omit that code and assert noncopyable traits.
All four tracked wrapper translation units, the actual dispatcher and JSON
helper, and the complete unchanged SDK compile together under ASan/UBSan.

| Final harness group | Baseline leaves | Baseline failures | Fixed leaves | Fixed failures |
|---|---:|---:|---:|---:|
| Dispatcher, wrappers, arrays and controls | 55 | 12 | 55 | 0 |
| Setter empty-owner overwrite | 25 | 13 | 25 | 0 |
| Getter owners and mismatches | 56 | 34 | 56 | 0 |
| Failed results and stringify | 31 | 15 | 31 | 0 |
| Baseline-only unsafe copies | 4 | 4 | 0 | 0 |
| Total | 171 | 78 | 167 | 0 |

Baseline: 93 passing controls, 78 failures. Fixed: 167/167 pass.
Named failures include `dispatch-3` (production string/picture leaks),
`set-narrow/wide/wchars`, `set-picture`, `get-a/b/n/c`, `blob-allocation-failure`, failed and
wrong-kind `stringify` results, `copy-traits`, and the four named ASan probes.
ASCII, BMP, supplementary surrogate pairs and empty fixtures run with
allocated and null engine empties. Assertions check exact UTF-16 unit
length/content and termination, conversion round trips, replacement/churn,
borrowed-copy survival, resize/clear, rejected kind/index/data/descriptor,
missing/null inputs, collection handoffs, independent command returns,
successful type mismatches, and failed poisoned/raw-kind0 returns.
Each successful leaf requires zero live strings, pictures, handles, objects
and collections, and balanced synthetic image/URL owners after autorelease.

Final harness SHA-256:

| File in `.github/tests/` | SHA-256 |
|---|---|
| `ownership_host.mm` | `b6df110300a4da2f042a903841f4dc0cb75e6a85a82162d19721356738af1930` |
| `ownership_platform.h` | `1aac3d8e746ecf52486e8c65a222b25a233c752f03e9ba59b6699a93e2cba6b6` |
| `test_ownership.py` | `97d8f30a66a53dc5c6cc1985e8567c75d1a87da85ae767aa74992cdd26f5b745` |

Before any consumer compiles, a forced include redirects all TIS current,
ASCII, language, enumeration, selection and property APIs, NSImage, NSURL,
image destinations and SDK drawing/path boundaries to synthetic stubs.
Unexpected engine selectors and unsupported boundary operations terminate
the test. An `nm` import gate runs before dispatch and rejects real input,
image, drawing, URL, process, file and networking boundaries and unexpected
Objective-C platform classes. Only in-memory Foundation/CF operations are
used. No keyboard is enumerated or changed; no UI/context/IME activation,
input capture/injection, icon file read or private data access occurs.

## Limits and safety gates

This is a synthetic ownership model derived from SDK implementation,
comments and engine forwarding, not an actual 4D host, native ABI test,
Windows-branch compile or reproduction of a reported Windows crash.
Engine property copy/reference retention is an explicit shim assumption,
not a newly verified 4D engine implementation.
ASan leak detection is disabled on macOS; explicit allocation/reference
ledgers enforce owner balances. UBSan alignment is excluded because the
unchanged SDK's packed ABI records otherwise trip synthetic C++ accesses;
other enabled ASan/UBSan checks remain active.

Allocation/resize failures are not certified by successful cases. The
SDK's `PA_ResizeArray` can dispose shrinking elements before resizing and
update metadata despite failed growth; `ARRAY_TEXT::toParamAtIndex` has
no reliable transactional resize contract or error channel. Its null-handle
construction/failed growth paths remain deferred, not tested as safe.
`CBytes::toParamAtIndex` previously disposed the old handle before allocation,
leaving the old caller pointer stale if allocation failed. Its safe local
fix allocates/copies first and releases the old handle only on success.
The named `blob-allocation-failure` case fails on baseline and verifies the
fixed caller's exact pointer, original bytes/capacity, error predicate and
final owner balance. This does not certify SDK resize or handle-lock failure
safety. The `sdk-failures` control verifies only exact SDK error predicates
and model-preserved handle capacity, not wrapper OOM safety or native
engine behavior. SDK allocation/cleanup/error-preservation changes require
a separately agreed contract; no success-shaped fallback is introduced.

All workflows, both Python release/version scripts, the pre-push hook and
Xcode/Windows build phases were inspected before validation/push. Existing
Bump version and Build workflows are manual-only. Build signs, notarizes,
packages and publishes; Xcode's Deployment shell phase also signs/packages/
notarizes. None is invoked or changed. The new read-only unsigned workflow
runs only on relevant-path pushes to `main` and the exact audit branch,
never builds the project, uses secrets, creates artifacts/releases/tags,
or dispatches other workflows. Manifests, project files, version metadata,
packaged binaries and existing release automation remain unchanged.

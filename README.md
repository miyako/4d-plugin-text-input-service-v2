# 4d-plugin-text-input-service-v2
Commands to control the front-end text editor.

![version](https://img.shields.io/badge/version-19%2B-5682DF)
![platform](https://img.shields.io/static/v1?label=platform&message=mac-intel%20|%20mac-arm%20&color=blue)
[![license](https://img.shields.io/github/license/miyako/4d-plugin-text-input-service-v2)](LICENSE)
![downloads](https://img.shields.io/github/downloads/miyako/4d-plugin-text-input-service-v2/total)

<img width="733" alt="" src="https://github.com/miyako/4d-plugin-text-input-service-v2/assets/1725068/d0aff5a0-e753-423a-bcb4-4cc092003382">

The Text Input Service plugin lets a 4D application inspect and change the active macOS **keyboard input source** (a keyboard layout, an Input Method / IME, or a palette input source), driving Apple's Text Input Source Services (`TISCopyCurrentKeyboardInputSource`, `TISCreateInputSourceList`, `TISSelectInputSource`, etc., from `<Carbon/Carbon.h>`). Input source identifiers and enumerated results are plain `Text`; the enumerated list is a `Collection` of objects, one of which carries an `icon` as a `Picture` encoded as TIFF.

| Command | Returns | Purpose |
|---|---|---|
| [`INPUT SET SOURCE`](#input-set-source) | — | Switch the active keyboard input source |
| [`INPUT Get source`](#input-get-source) | Text | Read the identifier of a keyboard input source |
| [`INPUT Sources list`](#input-sources-list) | Collection | Enumerate installed, selectable input sources |

**Platforms:** macOS — verified against source (Carbon Text Input Source Services). Windows — **not verified**; see Requirements below.

---

## Requirements & platform notes

- **macOS only, as reviewed.** Every command in this file is implemented on top of Carbon's Text Input Source Services. No explicit minimum macOS version is asserted here — the reviewed source doesn't call any version-gated API, so no specific OS floor can be confidently stated from the code alone.
- **Windows behavior is unconfirmed.** The plugin's build produces a Windows `.4DX` as part of the same cross-platform bundle, but the source reviewed for this document contains only the Objective‑C/Carbon implementation. Whether these three commands exist, no-op, or behave differently on Windows was not established — test directly on Windows before relying on them there.
- **Both `INPUT SET SOURCE` and `INPUT Get source` take one mandatory `Text` parameter.** There is no optional/omittable form — pass `""` explicitly to get "current source" behavior.
- **`INPUT Sources list` takes no parameters.**
- **Failure is silent, not a 4D error.** If a requested source can't be resolved, `INPUT SET SOURCE` leaves the currently active source unchanged, and `INPUT Get source` returns `""`. Neither raises a 4D error. See [Error handling & troubleshooting](#error-handling--troubleshooting).
- **`INPUT Sources list` only reports currently *selectable* sources** (it calls `TISCreateInputSourceList` with `includeAllInstalled = false`) — input sources that are installed but currently disabled are not included in the result.

---

## INPUT SET SOURCE

**`INPUT SET SOURCE ( source )`**

### Syntax

```4d
INPUT SET SOURCE ( source : Text )
```

| Parameter | Type | Description |
|---|---|---|
| `source` | Text | Input source to activate — see accepted values below. |
| Result | — | No return value (this is a procedure). |

**Accepted values for `source`:**

| Value | Behavior |
|---|---|
| `""` | Selects the current **ASCII-capable** keyboard input source (a plain Latin layout, not an IME). |
| `"ASCII"` | Same as `""` — explicitly selects the ASCII-capable source. |
| An exact `inputSourceID` (e.g. `"com.apple.inputmethod.Kotoeri.RomajiTyping.Japanese"`) | Selects the source with that identifier, if it's currently selectable (same restricted set `INPUT Sources list` reports). |
| A language/locale code, BCP‑47 style (e.g. `"ja-JP"`, `"fr"`) | If no selectable source's `inputSourceID` matches the string exactly, the plugin falls back to asking macOS for the best input source for that language, and selects it. |

### Description

`INPUT SET SOURCE` changes the system's active keyboard input source — the same effect as the user picking a different layout/IME from the macOS input-source menu. The change is system-wide and takes effect for subsequent keystrokes, not retroactively.

Resolution order for anything other than `""`/`"ASCII"`: first, an exact match against the `inputSourceID` of every currently selectable source; if nothing matches, the plugin asks macOS to resolve `source` as a language code instead. That language-fallback path goes through an undocumented HIToolbox function — its exact matching rules aren't published by Apple, so it's worth treating as best-effort rather than a guaranteed mapping, and its behavior could change between macOS versions.

If macOS reports more than one installed source could satisfy a request, and at least one has already been used in the current session, the most-recently-used one is preferred.

If `source` can't be resolved at all, the command does nothing — no error, and the previously active input source stays active.

### Example

From the plugin's own test method (`TEST.4dm`):

```4d
INPUT SET SOURCE("")  //ASCII source
INPUT SET SOURCE("ASCII")  //also ASCII source

INPUT SET SOURCE("ja-JP")  //by language
INPUT SET SOURCE("com.apple.inputmethod.Kotoeri.RomajiTyping.Japanese")  //by identifier
```

Saving and restoring the source around a field that requires plain ASCII input:

```4d
$saved:=INPUT Get source("")
INPUT SET SOURCE("ASCII")

  // ... user types into a serial-number/password field ...

If ($saved#"")
    INPUT SET SOURCE($saved)
End if
```

---

## INPUT Get source

**`INPUT Get source ( source ) -> Text`**

### Syntax

```4d
INPUT Get source ( source : Text ) -> Text
```

| Parameter | Type | Description |
|---|---|---|
| `source` | Text | Which input source to report on — see accepted values below. |
| Result | Text | The resolved input source's `inputSourceID`, or `""` if nothing could be resolved. |

**Accepted values for `source`:**

| Value | Behavior |
|---|---|
| `""` | Returns the identifier of the **currently active** input source, of any kind (ASCII layout, IME, or palette) — **not** restricted to ASCII-capable sources. |
| `"ASCII"` | Returns the identifier of the current **ASCII-capable** input source. |
| A language/locale code, BCP‑47 style (e.g. `"ja-JP"`, `"fr"`) | Returns the identifier of the best-matching installed source for that language, via the same undocumented language-resolution path used by `INPUT SET SOURCE`'s fallback. |

`source` is **not** looked up as a raw `inputSourceID` by this command — only `""`, `"ASCII"`, and language codes are recognized. Passing an identifier such as `"com.apple.keylayout.US"` will not resolve and returns `""`.

### Description

Note the asymmetry with `INPUT SET SOURCE`: there, `""` forces the ASCII-capable source; here, `""` reports whatever is currently active, ASCII or not. Don't assume the two commands treat `""` the same way.

Use this command to capture the active source before temporarily switching it with `INPUT SET SOURCE`, or to look up the identifier macOS would select for a given language without actually switching to it.

### Example

From the plugin's own test method (`TEST.4dm`):

```4d
$currentSource:=INPUT Get source("")  //current input source

$japaneseSource:=INPUT Get source("ja-JP")
$source:=INPUT Get source("ja")
$americanSource:=INPUT Get source("en-US")
$source:=INPUT Get source("fr-CA")
$source:=INPUT Get source("fr")
$asciiSource:=INPUT Get source("ASCII")
```

Checking whether a switch actually took effect:

```4d
INPUT SET SOURCE("ja-JP")
If (INPUT Get source("")="com.apple.inputmethod.Kotoeri.RomajiTyping.Japanese")
    ALERT("Switched to Japanese input.")
End if
```

---

## INPUT Sources list

**`INPUT Sources list -> Collection`**

### Syntax

```4d
INPUT Sources list -> Collection
```

No parameters.

| — | Type | Description |
|---|---|---|
| Result | Collection | One object per currently selectable input source. |

**Object structure** (a field is present only if macOS supplies a non-empty value for it — check with `#Null` rather than assuming a field exists):

| Property | Type | Description |
|---|---|---|
| `category` | Text | Input source category, e.g. `"TISCategoryKeyboardInputSource"`, `"TISCategoryPaletteInputSource"`. |
| `name` | Text | Localized display name, e.g. `"Japanese"`, `"U.S."`. |
| `type` | Text | Input source type, e.g. `"TISTypeKeyboardLayout"`, `"TISTypeKeyboardInputMethodModeEnabled"`. |
| `inputSourceID` | Text | Unique identifier — the value to pass to `INPUT SET SOURCE`. |
| `bundleID` | Text | Bundle identifier of the owning input method, when applicable. |
| `inputModeID` | Text | Mode identifier, for input methods exposing several modes (e.g. Hiragana vs. Katakana within one IME). |
| `icon` | Picture | The source's icon, encoded as TIFF, when macOS can supply one. |

### Description

This reports the same restricted, currently-selectable set of sources noted in [Requirements & platform notes](#requirements--platform-notes) — sources that are installed but currently disabled are excluded.

Building this list loads and, where available, re-encodes an icon for every source it returns. Expect this call to take noticeably longer than a typical plugin command on a machine with many installed keyboard layouts and IMEs — call it once and cache the result rather than calling it repeatedly (e.g. in a loop or on every keystroke).

### Example

From the plugin's own test method (`TEST.4dm`):

```4d
$lists:=INPUT Sources list
```

Building parallel arrays of names and identifiers for a picker UI:

```4d
$sources:=INPUT Sources list
ARRAY TEXT($names;0)
ARRAY TEXT($identifiers;0)

For ($i;0;$sources.length-1)
    If ($sources[$i].name#Null)
        APPEND TO ARRAY($names;$sources[$i].name)
        APPEND TO ARRAY($identifiers;$sources[$i].inputSourceID)
    End if
End for
```

Dispatching on `category` to only list real keyboard sources (excluding palette sources):

```4d
$sources:=INPUT Sources list
For ($i;0;$sources.length-1)
    Case of
        : ($sources[$i].category="TISCategoryKeyboardInputSource")
            LOG EVENT(Into system log;$sources[$i].name+" — "+$sources[$i].inputSourceID)
        Else
            // palette or other category; skip
    End case
End for
```

---

## Error handling & troubleshooting

- **`INPUT SET SOURCE` fails silently on an unresolved source.** If the identifier or language code doesn't match any selectable source, the previously active source stays active and no 4D error is raised. Confirm success afterward with `INPUT Get source("")` if you need to know for certain.
- **`INPUT Get source` returns `""` on an unresolved source**, including when a raw `inputSourceID` is passed instead of a language code or `""`/`"ASCII"` — no 4D error is raised either way.
- **`""` means different things to the two commands.** For `INPUT SET SOURCE`, `""` forces the ASCII-capable source; for `INPUT Get source`, `""` reports whatever is currently active, of any kind. Don't assume symmetry between them.
- **`INPUT Sources list` omits fields it can't populate**, rather than setting them to `""`. This applies especially to `bundleID`, `inputModeID`, and `icon` — check a property with `#Null` before reading it.
- **Icon decoding can be slow.** `INPUT Sources list` loads and re-encodes an icon per source; expect it to take noticeably longer with many keyboard layouts/IMEs installed. Cache the result instead of calling it repeatedly.
- **Language-code matching relies on an undocumented system API**, both as `INPUT SET SOURCE`'s fallback and as `INPUT Get source`'s only path for non-`""`/non-`"ASCII"` input. Its exact behavior isn't published by Apple and could shift between macOS versions.
- **Windows behavior is unverified.** These commands were reviewed only against their macOS (Carbon) implementation — test directly on Windows before depending on them there.

---

## Quick reference

```4d
// Save current source, force ASCII for a field, restore afterward
$saved:=INPUT Get source("")
INPUT SET SOURCE("ASCII")
  // ...
INPUT SET SOURCE($saved)

// Switch by language, then verify
INPUT SET SOURCE("ja-JP")
$active:=INPUT Get source("")

// Enumerate selectable sources and switch to a specific one by name
$sources:=INPUT Sources list
For ($i;0;$sources.length-1)
    If ($sources[$i].name="Japanese")
        INPUT SET SOURCE($sources[$i].inputSourceID)
    End if
End for
```

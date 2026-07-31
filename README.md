# 4d-plugin-text-input-service-v2
Commands to control the front-end text editor.

![version](https://img.shields.io/badge/version-19%2B-5682DF)
![platform](https://img.shields.io/static/v1?label=platform&message=mac-intel%20|%20mac-arm%20&color=blue)
[![license](https://img.shields.io/github/license/miyako/4d-plugin-text-input-service-v2)](LICENSE)
![downloads](https://img.shields.io/github/downloads/miyako/4d-plugin-text-input-service-v2/total)

<img width="733" alt="" src="https://github.com/miyako/4d-plugin-text-input-service-v2/assets/1725068/d0aff5a0-e753-423a-bcb4-4cc092003382">

## Overview

The **Text Input Service** plugin lets a 4D application inspect and control the
**keyboard input source** (keyboard layout, Input Method / IME, or palette
input source) currently active on the machine. It wraps Apple's *Text Input
Source Services* (part of the Carbon framework) and exposes three 4D
commands:

| Command | Returns | Purpose |
|---|---|---|
| `INPUT SET SOURCE` | — | Switch the active keyboard input source |
| `INPUT Get source` | Text | Read the identifier of a keyboard input source |
| `INPUT Sources list` | Collection | Enumerate every input source installed on the machine |

**Platform:** macOS only. The plugin builds a Windows binary (`.4DX`) as part
of the same cross-platform `.bundle`, but the input-source APIs used here
(`TISCopyCurrentKeyboardInputSource`, `TISCreateInputSourceList`, etc.) are
macOS-specific (Carbon `HIToolbox`). Calling these commands on Windows is not
meaningful and should be guarded in your code with `Current system version`
or an equivalent platform check if your database also runs on Windows.

**Typical uses:**
- Force a text field into a specific language/layout before the user starts
  typing (e.g. force "ASCII" before a password or serial-number field).
- Detect which language/IME the user currently has active, to adapt UI or
  logging.
- Build a settings screen letting the user pick from all input sources
  installed on their Mac, complete with icon and display name.

---

## `INPUT SET SOURCE`

### Syntax

```4d
INPUT SET SOURCE ( source )
```

| Parameter | Type | Description |
|---|---|---|
| `source` | Text | Input source to activate. See **Accepted values** below. |

No return value.

### Accepted values for `source`

| Value | Behavior |
|---|---|
| `""` (empty string) | Selects the current **ASCII-capable** keyboard input source (i.e. a plain Latin keyboard layout, not an IME). |
| `"ASCII"` | Same as passing `""` — explicitly selects the ASCII-capable input source. |
| An **input source identifier** (e.g. `"com.apple.inputmethod.Kotoeri.RomajiTyping.Japanese"`, `"com.apple.keylayout.US"`) | Selects the source with that exact identifier, if one is currently installed. Identifiers can be obtained from `INPUT Sources list` (the `inputSourceID` field) or from `INPUT Get source`. |
| A **language/locale code**, BCP‑47 style (e.g. `"ja-JP"`, `"ja"`, `"fr-CA"`, `"en-US"`) | If no installed source has a matching `inputSourceID`, the plugin falls back to asking macOS for the best input source for that language, and selects it. |

### Description

`INPUT SET SOURCE` changes what the *system* considers the active keyboard
input source — the same effect as the user picking a different layout/IME
from the macOS menu-bar input-source picker. The change is system-wide (not
scoped to the 4D window), and only takes effect for subsequent keystrokes.

If more than one installed input source could satisfy the request (for
example several IMEs are installed for the same language) and at least one of
them has been used previously in the current session, macOS will prefer the
most recently used one.

If the requested source cannot be resolved at all, the command does nothing
— no error is raised, and the previously active input source stays active.

### Examples

```4d
// Force a plain ASCII keyboard layout — useful before a password field
INPUT SET SOURCE("")
```

```4d
// Equivalent, explicit form
INPUT SET SOURCE("ASCII")
```

```4d
// Switch by language/locale — macOS will pick a matching input source
INPUT SET SOURCE("ja-JP")
```

```4d
// Switch by exact input source identifier
// (identifiers can be discovered via INPUT Sources list)
INPUT SET SOURCE("com.apple.inputmethod.Kotoeri.RomajiTyping.Japanese")
```

```4d
// Typical usage pattern: force ASCII before a numeric/code entry field,
// then restore whatever the user had active before
$previousSource:=INPUT Get source("")
INPUT SET SOURCE("ASCII")
  // ... let the user type into a serial-number field ...
INPUT SET SOURCE($previousSource)
```

---

## `INPUT Get source`

### Syntax

```4d
$identifier:=INPUT Get source ( source )
```

| Parameter | Type | Description |
|---|---|---|
| `source` | Text | Which input source to report on. See **Accepted values** below. |

| Return value | Type | Description |
|---|---|---|
| `$identifier` | Text | The input source identifier (e.g. `"com.apple.keylayout.US"`), or an empty string if no matching source could be resolved. |

### Accepted values for `source`

| Value | Behavior |
|---|---|
| `""` (empty string) | Returns the identifier of the **currently active** keyboard input source (of any kind — ASCII layout, IME, or palette). |
| `"ASCII"` | Returns the identifier of the current **ASCII-capable** input source. |
| A **language/locale code**, BCP‑47 style (e.g. `"ja-JP"`, `"fr"`, `"en-US"`) | Returns the identifier of the best-matching installed input source for that language. |

> **Note:** unlike `INPUT SET SOURCE`, this command does **not** attempt to
> resolve a raw input source identifier passed as `source` — only language
> codes, `""`, and `"ASCII"` are recognized. Passing an identifier such as
> `"com.apple.keylayout.US"` as the parameter is not a supported use case and
> will typically return an empty string.

### Description

Use `INPUT Get source` to read back the identifier of an input source,
whether the currently-active one, the ASCII one, or the best match for a
given language. This is the command to call *before* using `INPUT SET
SOURCE`, if you need to remember and later restore the user's original input
source.

### Examples

```4d
// What's active right now?
$currentSource:=INPUT Get source("")
```

```4d
// What's the ASCII-capable source called on this machine?
$asciiSource:=INPUT Get source("ASCII")
```

```4d
// What identifier would macOS use for Japanese?
$japaneseSource:=INPUT Get source("ja-JP")
$source:=INPUT Get source("ja")            // more general form of the language code
```

```4d
// A few more language examples
$americanSource:=INPUT Get source("en-US")
$source:=INPUT Get source("fr-CA")
$source:=INPUT Get source("fr")
```

---

## `INPUT Sources list`

### Syntax

```4d
$sources:=INPUT Sources list
```

No parameters.

| Return value | Type | Description |
|---|---|---|
| `$sources` | Collection | One object per input source installed on the machine. |

### Object structure

Each element of the returned collection is an object with the following
(optional) fields — a field is present only if macOS reports a non-empty
value for it:

| Field | Type | Description |
|---|---|---|
| `category` | Text | Input source category, e.g. `"TISCategoryKeyboardInputSource"` or `"TISCategoryPaletteInputSource"`. |
| `name` | Text | Localized display name, e.g. `"Japanese"`, `"U.S."`, `"ABC"`. |
| `type` | Text | Input source type, e.g. `"TISTypeKeyboardLayout"`, `"TISTypeKeyboardInputMethodModeEnabled"`. |
| `inputSourceID` | Text | Unique identifier for the source — the value to pass to `INPUT SET SOURCE`. |
| `bundleID` | Text | Bundle identifier of the input method that owns this source, if applicable. |
| `inputModeID` | Text | Mode identifier, for input methods that expose several modes (e.g. Hiragana vs. Katakana within the same IME). |
| `icon` | Picture | The input source's icon, if macOS can supply one. |

### Description

`INPUT Sources list` enumerates every keyboard layout, IME, and palette input
source currently installed and enabled on the machine — the same set the
user sees in **System Settings > Keyboard > Input Sources**. It's the
natural way to build a picker UI, or to look up the exact `inputSourceID` to
pass to `INPUT SET SOURCE`.

> **Performance note:** this command loads and, where available, decodes an
> icon image for every installed input source. On a machine with many
> keyboard layouts and IMEs installed, expect this call to take noticeably
> longer than a typical plugin command — avoid calling it repeatedly in a
> loop or on every keystroke; call it once and cache the result.

### Examples

```4d
// Get every installed input source
$lists:=INPUT Sources list
```

```4d
// Build a simple list box of input source names, keeping a parallel
// array of identifiers to use with INPUT SET SOURCE
ARRAY TEXT($names;0)
ARRAY TEXT($identifiers;0)

For ($i;0;(INPUT Sources list).length-1)
    $entry:=(INPUT Sources list)[$i]
    If ($entry.name#Null)
        APPEND TO ARRAY($names;$entry.name)
        APPEND TO ARRAY($identifiers;$entry.inputSourceID)
    End if
End for
```

```4d
// Find and activate the input source whose name is "Japanese"
$sources:=INPUT Sources list
$pos:=0
$found:=False

For ($i;0;$sources.length-1)
    If ($sources[$i].name="Japanese")
        $found:=True
        $pos:=$i
    End if
End for

If ($found)
    INPUT SET SOURCE($sources[$pos].inputSourceID)
End if
```

```4d
// Show icons and names for every keyboard-category input source
$sources:=INPUT Sources list
For ($i;0;$sources.length-1)
    $entry:=$sources[$i]
    If ($entry.category="TISCategoryKeyboardInputSource")
        LOG EVENT(Into system log;$entry.name+" — "+$entry.inputSourceID)
    End if
End for
```

---

## Worked example: force ASCII input, then restore

A common pattern — combining all three commands — is to force plain ASCII
typing for a specific field (serial numbers, license keys, passwords),
without permanently changing what the user had active:

```4d
// --- On entry into the field ---
$savedSource:=INPUT Get source("")  // remember what's currently active
INPUT SET SOURCE("ASCII")           // force ASCII for this field

// --- ... user types into the field ... ---

// --- On exit from the field ---
If ($savedSource#"")
    INPUT SET SOURCE($savedSource)  // restore the original input source
End if
```

## Worked example: language-aware default

Pick an input source appropriate to the current 4D application language,
falling back to ASCII if nothing matches:

```4d
Case of
    : (Application language=Japanese)
        $target:=INPUT Get source("ja-JP")
    : (Application language=French)
        $target:=INPUT Get source("fr")
    Else
        $target:=""
End case

If ($target#"")
    INPUT SET SOURCE($target)
Else
    INPUT SET SOURCE("ASCII")
End if
```

*(`Application language` above is illustrative — substitute whatever
mechanism your database uses to know the user's preferred language.)*

---

## Summary table

| Command | Signature | Notes |
|---|---|---|
| `INPUT SET SOURCE` | `INPUT SET SOURCE ( source : Text )` | Accepts `""`, `"ASCII"`, an exact `inputSourceID`, or a language code. Silently does nothing if unresolved. |
| `INPUT Get source` | `INPUT Get source ( source : Text ) -> Text` | Accepts `""`, `"ASCII"`, or a language code only — **not** a raw identifier. Returns `""` if unresolved. |
| `INPUT Sources list` | `INPUT Sources list -> Collection` | No parameters. Can be slow with many installed sources — cache the result rather than calling repeatedly. |

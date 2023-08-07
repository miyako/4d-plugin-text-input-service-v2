# 4d-plugin-text-input-service-v2
Commands to control the front-end text editor.

![version](https://img.shields.io/badge/version-19%2B-5682DF)
![platform](https://img.shields.io/static/v1?label=platform&message=mac-intel%20|%20mac-arm%20&color=blue)
[![license](https://img.shields.io/github/license/miyako/4d-plugin-text-input-service-v2)](LICENSE)
![downloads](https://img.shields.io/github/downloads/miyako/4d-plugin-text-input-service-v2/total)

#### Syntax

```
INPUT SET SOURCE (source)
```

<div class="grid">
<div class="syntax-th cell cell--2">Parameter</div>
<div class="syntax-th cell cell--2">Type</div>
<div class="syntax-th cell cell--8">Description</div>
<div class="syntax-td cell cell--2">source</div>
<div class="syntax-td cell cell--2">TEXT</div>
<div class="syntax-td cell cell--8"></div>   
</div>

```
source:=INPUT Get source({identifier})
```

<div class="grid">
<div class="syntax-th cell cell--2">Parameter</div>
<div class="syntax-th cell cell--2">Type</div>
<div class="syntax-th cell cell--8">Description</div>
<div class="syntax-td cell cell--2">identifier</div>
<div class="syntax-td cell cell--2">TEXT</div>
<div class="syntax-td cell cell--8"></div>   
  <div class="syntax-td cell cell--2">source</div>
<div class="syntax-td cell cell--2">TEXT</div>
<div class="syntax-td cell cell--8"></div>   
</div>

* pass a [RFC 4647](https://www.ietf.org/rfc/rfc4647.txt) or [RFC 3066](https://www.ietf.org/rfc/rfc3066.txt) `identifier` to specify a language.

* pass an empty string to request the current input source.

* pass the string "ASCII" to request the current ascii capable keyboard input source.

//%attributes = {}
$lists:=INPUT Sources list

$currentSource:=INPUT Get source("")  //current input source

$japaneseSource:=INPUT Get source("ja-JP")
$source:=INPUT Get source("ja")
$americanSource:=INPUT Get source("en-US")
$source:=INPUT Get source("fr-CA")
$source:=INPUT Get source("fr")
$asciiSource:=INPUT Get source("ASCII")

INPUT SET SOURCE("")  //ASCII source
INPUT SET SOURCE("ASCII")  //also ASCII source

INPUT SET SOURCE("ja-JP")  //by language
INPUT SET SOURCE("com.apple.inputmethod.Kotoeri.RomajiTyping.Japanese")  //by identifier
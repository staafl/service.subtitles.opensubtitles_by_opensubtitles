OpenSubtitles.org by OpenSubtitles KODI add-on
==============================================
DUAL SUBTITLE VERSION
----

How to install this addon in KODI:
- Download https://github.com/staafl/service.subtitles.opensubtitles_by_opensubtitles/releases/download/python3/script.module.pysubs2.zip
https://github.com/staafl/service.subtitles.opensubtitles_by_opensubtitles/releases/download/python3-5.2.16/service.subtitles.opensubtitles_by_opensubtitles_by_staafl.zip
- Open KODI -> System -> Settings -> Add-ons -> Install from zip file
- Navigate to the file you downloaded (install script.module.pysubs2.zip first)

Use the add-in from the "Download Subtitles" menu in Kodi's player. Also don't forget to set your subtitle language preferences in Kodi's settings (Settings -> Player -> Language -> Languages to download subitles for), or you'll only get subtitles in English.

NB: this is a fork that adds dual subtitle support. It's a fork of https://github.com/moham96/service.subtitles.opensubtitles_by_opensubtitles, which adds dual subtitles to https://github.com/opensubtitles/service.subtitles.opensubtitles_by_opensubtitles, but this fork supports Python 3 (based on work from https://github.com/juokelis/service.subtitles.opensubtitles_by_opensubtitles with my own additions). I've also tweaked the UI to allow you to:

* choose which subtitle should appear on top.

* choose relative subtitle offset if one subtitle is off (if both subtitles are wrong, you can use this feature to align them, then adjust the combined subtitle using Kodi's built-in).

* select subtitles from local files.

All the following text is taken from the upstream repository verbatim.



Changelog

5.2.15
- Ported to python 3.0. The 30th anniversary of the Restoration of Independence of Lithuania

5.2.14
- New feature: Users are able to check for subtitles when Kodi is not playing, by using the manual search or by standing on an item and opening the subtitles search dialog (By key or by an external addon) | @burekas
- The external addon for the contextmenu can be downloaded from here: https://github.com/burekas7/context.subtitlesdialog.contextmenu

5.1.14
- Users are able to download subtitles as anonymous without authentication. Added localized descriptions, media files

5.0.14
- Fix for Portuguese (Brazil) broken by 42f6ec9, thx host505

5.0.13
- Fix for Greek subtitles, thx host505

5.0.12
- compare season and episode and display only matching results

5.0.11
- fix: search issues
- cosmetics
- add slash or backslash at the end of path (fix xbmcvfs.exists in Helix), thx Ondrej Bima

5.0.10
- fix: Don't unquote(urldecode) file_original_path as it breaks http file hashing, thx arnova

5.0.9
- fix hash large rars, Beam
- Support for preferred language sorting and fetch using IMDBID, Glenn Jennehed
- fix: hack to work around issue where Brazilian is not found as language in XBMC

5.0.8
- fix: extension is needed for downloaded files

5.0.7
- fix: Do not use unsafe file names, thx Cesar Canassa

5.0.6
- clean temp folder
- add login details to addon settings

5.0.5
- [fix] ascii UNICODE.decode
- [fix] manual search string unquoted
- cosmetics and code simplification

5.0.4
- manual search button support

5.0.3
- fix Portuguese (Brazil) and Greek

5.0.2
- icon.png and added logo.png for skin to use in window

5.0.1
- let skin control flag filetype

5.0.0
- move the service out of XBMC Subtitles

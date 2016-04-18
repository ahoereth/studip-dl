# StudipDL

Simple script to download all documents from a course on a [Stud.IP](http://studip.de/) installation.

   * Requires the studip installation to have the [rest.ip](https://github.com/studip/studip-rest.ip) plugin enabled.
   * Requires [7zip](http://www.7-zip.org/) (`7z` terminal command) in order to automatically unpack `*.rar` and `*.7z` files.

## Usage
Adjust the `APIBASE` variable to match your universities studip url, then run the script using

```
python3 studip.py
```

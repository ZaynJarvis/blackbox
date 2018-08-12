# Blackbox

Dropbox for Blackboard

## About

Blackbox is a command-line program that attempts to download all your files from Blackboard. It doesn't, however, sync your files automatically just like Dropbox does, but that feature is in the pipeline.

---

## How to Download & Install

Download your installer according to your system version. Double-click to install and choose a location which is convenient for you to access because all your downloads will be stored in that folder. You are recommended to install to your default Downloads folder.

### Downloads

| System        | Installer     | Zip  |
| ------------- | ------------- | ----- |
| Windows 64-bit | [Blackbox-1.0-amd64.msi][1] | [exe.macosx-10.9-x86_64-2.7.zip][3] |
| Windows 32-bit | [Blackbox-1.0-win32.msi][2] | [exe.win32-2.7.zip][4] |
| Mac 64-bit | - | [exe.win-amd64-2.7.zip][5] |

[1]:https://github.com/jarrettyeo/blackbox/raw/master/dist/Blackbox-1.0-amd64.msi
[2]: https://github.com/jarrettyeo/blackbox/raw/master/dist/Blackbox-1.0-win32.msi
[3]: https://github.com/jarrettyeo/blackbox/raw/master/build/exe.macosx-10.9-x86_64-2.7/exe.macosx-10.9-x86_64-2.7.zip
[4]: https://github.com/jarrettyeo/blackbox/raw/master/build/exe.win32-2.7/exe.win32-2.7.zip
[5]: https://github.com/jarrettyeo/blackbox/raw/master/build/exe.win-amd64-2.7/exe.win-amd64-2.7.zip

> Mac Users: When prompted to allow access to your keychain, click on "Always Allow".

> Windows Users: When prompted to allow the program through your firewall, tick "Private networks" and click on "Allow access".

## How to Use (Basic)

### Section 1 - Credentials Options

Here you can add, edit or remove your Blackboard credentials. Please note that your password will **not** show as you type. Use `RETURN` or `ENTER` to confirm your input.

### Section 2 - Reset Options

Here you can choose what to reset in Blackbox.

Key in `y` and hit `ENTER` when you are asked "Would you like to reset everything?".

### Section 3 - Download Options

Here you can choose whether you want to throttle your downloads in Blackbox.

Key in `y` and hit `ENTER` when you are asked "Would you like to throttle your downloads?".

### Section 4 - Execute Options

Here you can determine whether you want to throttle your downloads.

Key in `y` and hit `ENTER` when you are asked "Would you like to execute everything?".

---

## Main Features

1. Download all files by running the executable.

2. Throttle your downloads.

3. Selectively sync your folders and files.

## Other Features

1. Videos are not downloaded by default.

2. Your credentials are stored in a keyring on your local machine.

## Recommended Settings

1. Enable download-throttling
> Blackboard apparently imposes a throttle download limit on your account if you download a large number of files at one go. It is best to throttle your downloads. The recommended max throttle wait time is 10 seconds while the min throttle wait time is 3 seconds.

2. Install in your Downloads folder
> It is recommended that you install Blackbox in your Downloads folder for easy access.

## Future Extensions

1. Auto-sync

2. Define custom file extension blacklist

3. Define custom download location

---

## Limitations

There is no easy way to determine whether a file has been updated or not - a file must be re-downloaded to determine whether so. Blackbox supports either an indiscriminate (re-)download of all files or a download of new files.

## Disclaimer

The author accepts no responsibility for any damage done to your machine in your course of using this program.

BaiduPanFilesUpdates

=====

## Introduction

This is a python script automatically pulls and updates Baidu Pan sharing
files to desired locations.


## Setup Cookie and User-Agent

1. Login your Baidu Pan account, `https://pan.baidu.com/disk/main`.

2. Open DevTools in your browser (shortcut F12).

3. Click `Network` tab.

4. Refresh your page (shortcut F5), or open `https://pan.baidu.com/disk/main`.

5. Find `main` page, in Headers, you can find `Cookie` and `User-Agent`.

6. Paste the values of `Cookie` and `User-Agent` in a `config.ini` file as
   two lines.

## Sharing Links and Save Paths

Prepare a csv file, `links.csv`, admitting the following format:
```
https://pan.baidu.com/s/1-HHcM-uVl1kERWx5EKJDag, PASS, /Path/To/Save
https://pan.baidu.com/s/1EFCrmlh0rhnWy8pi9uhkyA, , /Another/Path
```

Currently, we only support standard sharing link format.


## Run Script

After `config.ini` and `links.csv` are well-prepared, please run the
following line to transfer and update the files in sharing links to
desired paths.

```
python baidupanupdate.py
```


## Acknowledgment

This repository is inspired by @hxz393/BaiduPanFilesTransfers.



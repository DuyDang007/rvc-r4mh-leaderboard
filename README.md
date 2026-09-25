# STRAVA CLUB ACTIVITY LEADERBOARD 

This tool can summary the reports from Strava activities and create the leaderboard.

## Google Chrome extension to get the reports

Strava Clubs Reports: https://chromewebstore.google.com/detail/strava-clubs-reports/lgflepkbehloedhbiajhlaecldnijpjd

## How to use this tool

1. Put all .csv data files into CSV folder

2. Run parser

```
$ python parser.py
```

3. Start http host server in ./web/ directory

```
$ cd web
$ python -m http.server 8000
```
 
4. In browser, open `localhost:8000`

---

## FAQ:

### 1. Error: UnicodeEncodeError: 'charmap' codec can't encode character '\u1ec5' in position 23: character maps to \<undefined\>

Fix: On Unix-like terminal:

```
export PYTHONUTF8=1
```

On Batch:

```
set PYTHONUTF8=1
```
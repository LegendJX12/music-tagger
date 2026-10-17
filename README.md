# music-tagger

A small tool that fixes the **title, artist, album, year and genre** inside your music files (MP3 / M4A) in bulk, using a spreadsheet (CSV).

It was built to clean up a library of 937 songs downloaded from YouTube-style sources. Their filenames were messy (`Song (Lyrics) ft. X.mp3`) and their tags were mostly empty.

## How it works (3 steps)

```
 music folder ──scan──▶ tags.csv ──(you / AI fill it in)──▶ tags.csv ──apply──▶ music folder
```

1. **scan**: reads every song in a folder and writes its current tags to a CSV file.
2. **fill in**: correct the CSV in Excel or Google Sheets, or give it to Claude or Gemini to research. Set `conf` to `unknown` for any row you want left alone.
3. **apply**: writes the CSV back into the files. By default it only *previews* the changes. It changes nothing until you add `--write`.

## CSV columns

| column | meaning |
|---|---|
| `file` | exact filename in the folder (don't edit) |
| `title`, `artist`, `album`, `genre` | new tag values. Empty means "leave the existing value" |
| `year` | original release year of the song |
| `conf` | `high` / `medium` / `low`. Use `unknown` or `skip` to leave the file untouched |
| `length_s` | song length in seconds (info only) |

The **Album Artist** is set automatically to the main artist. For example, `Logic feat. Khalid` gives `Logic`.

## Setup on Windows (one time)

1. Install Python from <https://www.python.org/downloads/>. Tick **"Add Python to PATH"** during install.
2. Download this repo: green **Code** button, then **Download ZIP**, then unzip it.
3. Open the unzipped folder. Click the address bar, type `cmd`, and press Enter. A black window opens in that folder.
4. Install the one dependency:
   ```
   pip install -r requirements.txt
   ```

## Use it

```
python musictag.py scan  "C:\Users\YOU\Desktop\music"  my_tags.csv
```
Open `my_tags.csv`, fix the rows, and save it as CSV (UTF-8). Then:

```
python musictag.py apply "C:\Users\YOU\Desktop\music"  my_tags.csv
```
This prints a preview of every change. If it looks right, run it again with `--write`:

```
python musictag.py apply "C:\Users\YOU\Desktop\music"  my_tags.csv --write --backup backup
```
`--backup backup` copies every original file into a `backup` folder first, so you can undo.

## Things it handles

- **Fake extensions**: some `.mp3` downloads are really MP4/AAC inside. The tool checks the real format and uses the matching tag type, so the file isn't corrupted.
- **Unicode filenames**: Chinese characters, `’`, `é`, `♪` and hidden non-breaking spaces all work.
- **No blanking**: an empty CSV cell never erases an existing tag.
- **Errors don't stop the run**: a bad file is reported at the end and the rest still get processed.

## Conventions used

- **Year** is the song's original release year, not the year of a later compilation.
- Featured artists are written as `Main Artist feat. A & B`.

## Tests

```
pip install pytest
python -m pytest tests
```
(needs `ffmpeg` installed to generate tiny test audio files)

## Ideas / not done yet

- Rename files to a clean `Artist - Title.mp3` pattern from the CSV
- Embed album cover art
- Sort into `Artist/Album/` folders

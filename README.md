# Curl Bible
## Author: Connor Ricotta
## TODO
- [X] Finish endpoints
- [X] Look into multi-verse queries not be escaped properly
- [X] logging
- [X] version selection user friendly
- [X] color output
- [ ] Limit multi-text output
### Bible Endpoints 
- [X] **Single Verse**
* - [X] bible.sh/John:3:15
* - [X] bible.sh/John/3/15
* - [X] bible.sh/?book=John&chapter=3&verse=15

- [X] **Range of Verses**
* - [X] bible.sh/John:3:15-20
* - [X] bible.sh/John/3/15-20
* - [X] bible.sh/?book=John&chapter=3&verse=15-20

- [ ] **Multiple Verses**
* - [ ] bible.sh/John:3:15,17,19:20
* - [ ] bible.sh/John/3/15,17,19:20
* - [ ] bible.sh/?book=John&chapter=3&verse=15,17,19:20
 
- [ ] **Entire Chapters**
* - [X] bible.sh/John:3
* - [X] bible.sh/John/3
* - [X] bible.sh/?book=John&verse=3

- [X] **Range of Chapters**
* bible.sh/John:3:15:John:4:27 ^ \
^ a maximum amount of 2500 characters are returned

- [ ] **Change version**
* - [X] bible.sh/John:3:15?version=YTL
* - [X] bible.sh/book=John&chapter=3&verse=15:20&version=YLT
### Supports the following versions
   - King James Version (KJV)
   - American Standard-ASV1901 (ASV)
   - Bible in Basic English (BBE)
   - World English Bible (WEB)
   - Young's Literal Translation (YLT)


## Append /json to any of these endpoints to get the following data
```json
{
    StartingBook:'StartingBook',
    StartingChapter: 'StartingChapter',
    StartingVerse: 'StartingVerse',
    EndingBook: 'EndingBook',
    EndingChapter: 'EndingChapter',
    EndingVerse: 'EndingVerse',
    BibleVersion: 'BibleVersion',
    Text: 'Text',
    FullQuery: 'Fully Query'
}
```
EndingBook, EndingChapter, and EndingVerse may return an empty string if a single verse is queried.

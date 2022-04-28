# Curl Bible
## Author: Connor Ricotta
### Bible Endpoints
**Single Verse**
* bible.sh/John:3:15
* bible.sh/John/3/15
* bible.sh/book=John&verse=3&verse=15

**Range of Verses**
* bible.sh/John:3:15-20
* bible.sh/John/3/15-20
* bible.sh/book=John&verse=3&verse=15-20

**Multiple Verses**
* bible.sh/John:3:15,17,19:20
* bible.sh/John/3/15,17,19:20
* bible.sh/book=John&verse=3&verse=15,17,19:20
 
**Entire Chapters**
* bible.sh/John:3
* bible.sh/John/3
* bible.sh/book=John&verse=3

**Range of Chapters**
* bible.sh/John:3:15:John:4:27 ^

^ a maximum amount of 2500 characters are returned

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

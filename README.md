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


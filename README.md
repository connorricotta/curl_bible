<h1 align="center">
Curl Bible 
</h1>
<p align="center">
  <a href="https://github.com/aws/mit-0">
    <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License">
  </a>
  <a href="https://pypi.org/project/autopep8/"> 
    <img src="https://img.shields.io/badge/code--style-autopep8-blue" alt="Code Style Autopep8">
  </a>
</p>

![Screenshot 1](https://cdn.discordapp.com/attachments/775917117290709042/981019274560823346/unknown.png "Our logo")

Read passages from the bible using curl (or any CLI HTTP tool)! All output to the terminal colored using [ANSI Escape Codes](https://en.wikipedia.org/wiki/ANSI_escape_code).

## Examples:
```sh
  $ curl bible.ricotta.dev/John:3:15&options=length=15,width=10

  $ curl bible.ricotta.dev/?book=John&chapter=3&verse=15-19

  $ curl "bible.ricotta.dev/John/3/15-19&version=YLT&options=text"
```


## Installation
1. Install [Docker-compose](https://docs.docker.com/compose/install/)
2. Run the configuration script to generate a random password for both the root and regular database users.
```sh
$ ./install.sh
```
3. Start up the program.
   *  The Docker Image for the backend server will have to be built when ran for the first time.
   *  The Database might take ~15 seconds to become ready for queries.
```sh
$ docker-compose up -d
```

## Query Options
### There are three endpoints that can be used to query the database:
1. Full Verse Query (/`Book`:`Chapter`:`Verse`)
```sh 
$ curl bible.ricotta.dev/John:3:15-20
```
2. Slash Query (/`Book`/`Chapter`/`Verse`)
```sh 
$ curl bible.ricotta.dev/John/3/15-20
```
3. Parameter Query (/?book=`Book`&chapter=`Chapter`&verse=`Verse`)
```sh 
$ curl "bible.ricotta.dev/?book=John&chapter=3&verse=15-20"
```
### These endpoints can be queried with the following formats.

| **Query Types**       | **Examples**                                       |
|-----------------------|----------------------------------------------------|
| **Single Verse**      | `curl bible.ricotta.dev/John:3:15`                        |
|                       | `curl bible.ricotta.dev/John/3/15`                        |
|                       | `curl bible.ricotta.dev/?book=John&chapter=3&verse=15`    |
| **Multiple Verses**   | `curl bible.ricotta.dev/John:3:15-20`                     |
|                       | `curl bible.ricotta.dev/John/3/15-20`                     |
|                       | `curl bible.ricotta.dev/?book=John&chapter=3&verse=15-20` |
| **Entire Chapters**   | `curl bible.ricotta.dev/John:3`                          |
|                       | `curl bible.ricotta.dev/John/3`                          |
|                       | `curl bible.ricotta.dev/?book=John&chapter=3 `            |

## Options
The length, width, and output color of the returned book can be controlled by appending `options=` or `o=` to the query. The full list of options are:
  1. `length` or `l`:
     * Set the number of columns in the returned book.
     * Default Value: **`20`**
  2. `width` or `w`:
     * The size of each row in the returned book.
     * Default Value: **`80`** 
  3. `text` or `t`:
     * Only return the text, not the book.
     * Default Value: **`False`**
  4. `no_color` or `nc`:
     * Return the book without any ANSI Escape Codes.
       Useful if the default command is causing display errors.
     * Default Value: **`False`** 
  5. `color` or `c`:
     * Include ANSI Escape Codes in the output.
     * Default Value: **`True`** 
  6. `version` or `v`:
     * Specify which translation of the bible to query from.
     * Default Value **`ASV`** ([American Standard Version](https://en.wikipedia.org/wiki/American_Standard_Version))
### Examples:
```sh
$ curl "bible.ricotta.dev/John/3/15-20?options=length=25,width=50,no_color,version=ASV"

$ curl "bible.ricotta.dev?book=John&chapter=3&o=l=26,w=75,t"
```
### These options can be displayed with the command
```sh
$ curl bible.ricotta.dev/help
```
### Versions
There are five translation/versions that can be queried by this program.
These versions are taken from https://github.com/scrollmapper/bible_databases
1. ASV ([American Standard Version](https://en.wikipedia.org/wiki/American_Standard_Version)) 
2. BBE ([Bible in Basic English](https://en.wikipedia.org/wiki/Bible_in_Basic_English))
3. KJV ([King James Version](https://en.wikipedia.org/wiki/King_James_Version))
4. WEB ([World English Bible](https://en.wikipedia.org/wiki/World_English_Bible))
5. YLT ([Young's Literal Translation](https://en.wikipedia.org/wiki/Young%27s_Literal_Translation))
#### Examples:
```sh
$ curl bible.ricotta.dev/John/3/15-20?version=ASV

$ curl "bible.ricotta.dev?book=John&chapter=3&v=ylt"
```
### These options can be displayed with the command
```sh
$ curl bible.ricotta.dev/versions
```
<!-- <details><summary><b>Show full endpoints</b></summary> -->
  
<!-- </details> -->


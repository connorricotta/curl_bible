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

Read passages from the bible using curl or HTTPie! All output to the terminal colored using [ANSI Escape Codes](https://en.wikipedia.org/wiki/ANSI_escape_code).

## Examples:

```sh
  $ curl "bible.ricotta.dev/John:3:15-19?options=length=35,width=50"

  $ curl "bible.ricotta.dev/?book=John&chapter=3&verse=15-19"

  $ curl "bible.ricotta.dev/John/3/15-19?version=YLT&text_only=True"
```

## Installation (Docker)

1. Install [Docker-compose](https://docs.docker.com/compose/install/)
2. Run the configuration script to generate a random password for both the root and regular database users.

```sh
$ ./install.sh
```

3. Start up the program.
   - The Docker Image for the backend server will have to be built when ran for the first time.
   - The Database might take ~15 seconds to become ready for queries.

```sh
$ docker-compose up -d
```

<details><summary><b>Show manual installation instructions</b></summary>

1. Ensure [Python3](https://www.python.org/downloads/), [pip](https://pip.pypa.io/en/stable/installation/), and [pipenv](https://pypi.org/project/pipenv/) are installed.
2. Change directory into the python directory and create a pipenv environment.

```sh
$ cd python
$ pipenv shell
```

3. Start up the backend server with this command (more options can be found [here](https://docs.gunicorn.org/en/stable/settings.html?highlight=logging#logging))

```sh
$ gunicorn --bind 0.0.0.0:10000 wsgi:app --log-level warning --error-logfile error.log --capture-output --log-config logging.conf
```

4. Ensure that [mariadb](https://www.digitalocean.com/community/tutorials/how-to-install-mariadb-on-ubuntu-20-04) is installed and you are able to connect to it.
5. Open up mariadb and enter the following commands
   > The words in {braces} should be replaced with different values

```sh
CREATE USER 'bibleman'@'localhost' IDENTIFIED BY '{newpassword}'
CREATE DATABASE IF NOT EXISTS bible;
GRANT ALL PRIVILEGES ON bible.* TO 'bibleman'@'localhost';
FLUSH PRIVILEGES;
exit;
```

6. Import the SQL dump into the bible database.

```sh
sudo mysql -u root -p bible < {path to directory}/curl_bible/sql/bible-mysql.sql
```

7. Modify python/.env to make sure MYSQL_PASSWORD and DB_PORT match your current configuration.

```sh
MYSQL_ROOT_USER=root
MYSQL_ROOT_PASSWORD={changeme123}
MYSQL_USER=bibleman
MYSQL_PASSWORD={changemealso}
MYSQL_DATABASE=bible
DB_HOST=bible_db
DB_PORT=3306
```

</details>

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
$ curl "bible.ricotta.dev?book=John&chapter=3&verse=15-20"
```

### These endpoints can be queried with the following formats.

| **Query Types**     | **Examples**                                                |
| ------------------- | ----------------------------------------------------------- |
| **Single Verse**    | `curl bible.ricotta.dev/John:3:15`                          |
|                     | `curl bible.ricotta.dev/John/3/15`                          |
|                     | `curl "bible.ricotta.dev/?book=John&chapter=3&verse=15"`    |
| **Multiple Verses** | `curl bible.ricotta.dev/John:3:15-20`                       |
|                     | `curl bible.ricotta.dev/John/3/15-20`                       |
|                     | `curl "bible.ricotta.dev/?book=John&chapter=3&verse=15-20"` |
| **Entire Chapters** | `curl bible.ricotta.dev/John:3`                             |
|                     | `curl bible.ricotta.dev/John/3`                             |
|                     | `curl "bible.ricotta.dev/?book=John&chapter=3"`             |

## Options

The length, width, and output color of the returned book can be controlled by appending `options=` or `o=` to the query. The full list of options are:

1. `length` or `l`:
   - Set the number of columns in the returned book.
   - Default Value: **`20`**
2. `width` or `w`:
   - The size of each row in the returned book.
   - Default Value: **`80`**
3. `text_only` or `t`:
   - Only return the text, not the book.
   - Default Value: **`False`**
4. `color_text` or `c`:
   - Include ANSI Escape Codes in the output.
   - Default Value: **`True`**
5. `verse_number` or `b`:
   - Display the associated verse numbers in superscript.
   - Default value: **`False`**
6. `version` or `v`:
   - Specify which translation of the bible to query from.
   - Default Value **`ASV`** ([American Standard Version](https://en.wikipedia.org/wiki/American_Standard_Version))

### Examples:

```sh
$ curl "bible.ricotta.dev/John/3/15-20?options=length=25,color_text=False,version=ASV"

$ curl "bible.ricotta.dev/John/3/15-20?length=25&color_text=False&version=ASV"

$ curl "bible.ricotta.dev/John/3/15-20?l=&w=50&c=False&v=ASV"
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

$ curl "bible.ricotta.dev?book=John&chapter=3&version=ylt"
```

### These options can be displayed with the command

```sh
$ curl bible.ricotta.dev/versions
```
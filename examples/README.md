# Example codes

Example codes using [Flask](http://flask.pocoo.org/)

## Getting started

### Setup hostname and API credentials in .env file

Rename .env.sample file to .env and input your hostname and LINE Pay API credentials

```
$ cp ./.env.sample ./.env
$ vi ./.env

HOST_NAME=xxxxx.ngrok.io
LINE_PAY_CHANNEL_ID=YOUR_LINE_PAY_CHANNEL_ID
LINE_PAY_CHANNEL_SECRET=YOUR_LINE_PAY_CHANNEL_SECRET
```

### Install dependencies

```
$ pip install -r requirements.txt
```

### Run

Run example code

```
$ python request-confirm-refund.py
```

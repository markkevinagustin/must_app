# How to install

### you can also try online using **you must have an account first**

https://www.gitpod.io/#https://github.com/markkevinagustin/must_app

after initialization
```console
pip install -r requirements.txt
cd ../
uvicorn must_app.main:app --reload
```

### clone repo

```console
git clone https://github.com/markkevinagustin/must_app.git
```

### Install requirements

```console
pip install -r requirements.txt
```

### Run the server

make sure you are outside must_app folder

```console
uvicorn must_app.main:app --reload
```

### How to use

update the database
```console
curl --location --request GET 'http://127.0.0.1:8000/update_db/'
```

get meeting suggestions for all

```console
curl --location --request POST 'http://127.0.0.1:8000/suggestion_all' \
--header 'Content-Type: application/json' \
--data-raw '{
    "user_ids": [
        "276908764613820584354290536660008166629",
        "319700813371232514617077620852703245241",
        "11661445264906887745347952589770178954",
        "177736372484123384037491644729334788901",
        "115067134195675490853540122833412221063",
        "208447093461762909213862253103625406414",
        "276908764613820584354290536660008166629",
        "177736372484123384037491644729334788901",
        "248086622848468681706182205280565990732",
        "279593614767550049255157755133888126135"
    ],
    "meeting_length": "120",
    "earliest_latest": [
        "1/31/2015 09:00:00 AM",
        "1/31/2015 04:00:00 PM"
    ],
    "office_hours": [
        "9",
        "18"
    ],
    "timezone": "Asia/Manila"
}'
```

get meeting suggestions individually


```console
curl --location --request POST 'http://127.0.0.1:8000/suggestion_individual' \
--header 'Content-Type: application/json' \
--data-raw '{
    "user_ids": [
        "276908764613820584354290536660008166629",
        "319700813371232514617077620852703245241",
        "11661445264906887745347952589770178954",
        "177736372484123384037491644729334788901",
        "115067134195675490853540122833412221063",
        "208447093461762909213862253103625406414",
        "276908764613820584354290536660008166629",
        "177736372484123384037491644729334788901",
        "248086622848468681706182205280565990732",
        "279593614767550049255157755133888126135"
    ],
    "meeting_length": "120",
    "earliest_latest": [
        "1/31/2015 09:00:00 AM",
        "1/31/2015 04:00:00 PM"
    ],
    "office_hours": [
        "9",
        "18"
    ],
    "timezone": "Asia/Manila"
}'
```

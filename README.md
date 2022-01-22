# How to install

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

get meeting suggestions

```console
curl --location --request POST 'http://127.0.0.1:8000/meetings' \
--header 'Content-Type: application/json' \
--data-raw '{
   "user_ids": ["276908764613820584354290536660008166629"],
   "meeting_length": "60",
   "earliest_latest": ["1/25/2015 10:00:00 AM", "1/25/2015 02:00:00 PM"],
   "office_hours": ["9", "18"],
   "timezone": "Asia/Manila"
}'
```
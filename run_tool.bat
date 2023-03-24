
SET PATH=C:\Python38\Scripts\;C:\Python38\;%PATH%

pip install -r requirements.txt

waitress-serve --host 127.0.0.1 flask_server:app
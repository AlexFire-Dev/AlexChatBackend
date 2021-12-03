_**AlexChatBackend**_
------------


### **_conf.env_**
`location - ./conf.env`


~~~~
PYTHONBUFFEERED=1

SECRET_KEY={{ Секретный ключ django  }}
DB_USER={{ Имя пользователя postgres }}
DB_PASSWORD={{ Пароль БД postgres }}
DB_HOST=db
DB_PORT=5432
DB_NAME={{ БД postgres }}
DEBUG=0
~~~~
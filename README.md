_**AlexChatBackend**_
------------


### **_conf.env_**
`location - ./conf.env`

### **_apns-key.p8_**
`location - ./apps/oauth/apple/apns-key.p8`


~~~~
PYTHONBUFFEERED=1

SECRET_KEY={{ Секретный ключ django  }}
DB_USER={{ Имя пользователя postgres }}
DB_PASSWORD={{ Пароль БД postgres }}
DB_HOST=db
DB_PORT=5432
DB_NAME={{ БД postgres }}
DEBUG=0

APNS_KEY_ID={{ ID ключа APNS }}
APNS_TEAM_ID={{ ID команды APPLE }}
APNS_TOPIC={{ Bundle ID }}
~~~~
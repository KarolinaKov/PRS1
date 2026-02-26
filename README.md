# Debug Backend (Django + DRF)

Backendová aplikace pro ovládání spotřebičů podle pokojů a zpracování plateb.

Projekt poskytuje:
- autorizační tok pro operace se spotřebiči založený na JWT/TOTP
<<<<<<< HEAD
- endpointy pro životní cyklus spotřebiče (`start` / `finish`)
- evidenci a účtování zůstatku pokojů
- ingest bankovních transakcí a dobíjení pokojů
=======
- logování cyklů spotřebičů
- komunikaci s endpointy ovládající cyklus spotřebiče (`start` / `finish`)
- evidenci a účtování zůstatku pokojů
- ingest bankovních transakcí a dobíjení pokojů To Do
>>>>>>> a4d79aee090beebb3854e1e9cee5bd5ac2407ea4
- persistenci v PostgreSQL a volitelný lokální setup přes Docker

---

## 1. Technologický stack

- Python 3.13
- Django 5.2
- Django REST Framework
- JWT (`PyJWT`, `djangorestframework_simplejwt`)
- PostgreSQL (`psycopg2-binary`)
- Celery + Redis (nakonfigurováno, zatím nepoužito)


Závislosti jsou uvedené v `pozadavky.txt`.

---

## 2. Struktura repozitáře

```text
.
├─ api/                    # REST API endpointy a serializéry
├─ appliance_module/       # Jádro domény: pokoje, spotřebiče, endpointy, běhy, auth služby
├─ bank_module/            # Platební modely a logika dobíjení pokojů
├─ debug/                  # Konfigurace Django projektu (settings, urls, celery init)
├─ manage.py
└─ pozadavky.txt           # Python závislosti
```

---

## 3. Přehled domény

### 3.1 `appliance_module`

Hlavní modely:
- `Room`: identifikátor pokoje (`key`) + celočíselný zůstatek (uložený v haléřích)
- `Endpoint`: metadata endpoint zařízení a měnitelná verze tokenu
- `Appliance`: katalog spotřebičů s `name` + `price_per_unit`
- `RoomTOTP`: TOTP secret pro konkrétní pokoj používaný pro ověření autorizace
- `RunsLog`: životní cyklus běhu spotřebiče (running/finished/aborted), počáteční/konečné jednotky/cena
- `EndpointApplianceStateRoom`: stav obsazenosti pro dvojici (`endpoint`, `appliance`)

Business služby:
- `AuthService`
  - vytváří krátkodobý challenge token
  - validuje TOTP kód a vrací access token
  - ověřuje JWT tokeny
- `ApplianceService`
  - `start(...)`: validuje stav, strhne zůstatek, založí run log, nastaví obsazenost
  - `finish(...)`: dokončí běh, vrátí rozdíl ceny (pokud je třeba), uvolní stav
- `ApplianceServiceFactory`
  - načte stav endpoint/spotřebič a vytvoří `ApplianceService`

### 3.2 `bank_module` Není doděláno

Modely:
- `ValidPayments`: známý klíč pokoje + částka + id transakce
- `InvalidPayments`: záznamy transakcí s neznámým/neplatným pokojem nebo měnou

Servisní funkce:
- `update_rooms_from_json(json_str)`
  - parsuje payload transakcí
  - deduplikuje ID transakcí proti oběma platebním tabulkám
  - aplikuje vklady do odpovídajících pokojů (atomická transakce)
  - ukládá validní/nevalidní platební záznamy

### 3.3 `api`

<<<<<<< HEAD
Obsahuje DRF APIView a serializéry, které vystavují autentizaci a operace se spotřebiči.
=======
Obsahuje DRF APIView a serializéry, které vystavují autentizaci a operace se endpointy.
>>>>>>> a4d79aee090beebb3854e1e9cee5bd5ac2407ea4

---

## 4. API endpointy

Základní cesta: `/api/`

### 4.1 `POST /api/auth/challenge/`

Vytvoří krátkodobý challenge token pro dvojici pokoj + endpoint.

Požadavek:
```json
{
  "room_num": 12345,
  "endpoint_id": 1
}
```

Odpověď `200`:
```json
{
  "token": "<challenge_jwt>"
}
```

---

### 4.2 `POST /api/auth/verify/`

Ověří challenge token a TOTP kód, potom vrátí access token + zůstatek + seznam spotřebičů.

Požadavek:
```json
{
  "token": "<challenge_jwt>",
  "auth_code": 123456
}
```

Odpověď `200`:
```json
{
  "token": "<access_jwt>",
  "balance": 100000,
  "appliances": [
    {"name": "washer", "value": 25}
  ]
}
```

---

### 4.3 `POST /api/appliance/start/`

Spustí běh spotřebiče a rezervuje prostředky.

Požadavek:
```json
{
  "token": "<access_jwt>",
  "appliance_name": "washer",
  "units": 300,
  "price": 20
}
```

Odpověď `201`:
```json
{
  "newbalance": 98000,
  "token": "<start_jwt>"
}
```

Poznámky:
- API interně násobí `price` hodnotou 100.

---

### 4.4 `POST /api/appliance/finish/`

Dokončí běh a aplikuje vrácení prostředků (pokud je konečná cena nižší než rezervovaná).

Požadavek:
```json
{
  "token": "<start_jwt>",
  "units": 250,
  "price": 15,
  "aborted": false
}
```

Odpověď `200`:
```json
{
  "status": "finished"
}
```

---

## 5. Konfigurace

Aktuální nastavení je v `debug/settings.py`.

Důležité hodnoty:
- `ALLOWED_HOSTS = ["localhost", "127.0.0.1"]`
- konfigurace PostgreSQL databáze ukazuje na `localhost:5432`
- `SIMPLE_JWT` používá hardcoded signing key a 5minutovou životnost access tokenu
- Celery broker/backend je nastaven na `redis://localhost:6379/0`
- časová zóna je `Europe/Prague`

### 5.1 Doporučený `.env` (pro Docker compose)

Vytvořte `.env` v kořeni projektu:

```env
SECRET_KEY=change-me
DEBUG=True
DJANGO_LOGLEVEL=info
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=debug_db
DATABASE_USERNAME=debug_dbuser
DATABASE_PASSWORD=debug_dbpassword
DATABASE_HOST=db
DATABASE_PORT=5432
```

> Poznámka: `debug/settings.py` aktuálně čte hodnoty DB přímo z hardcoded nastavení, ne z těchto proměnných prostředí.

---

## 6. Lokální vývojové prostředí (bez Dockeru)

1. Vytvořte a aktivujte virtuální prostředí.
2. Nainstalujte závislosti:

   ```bash
   pip install -r pozadavky.txt
   ```

3. Ujistěte se, že PostgreSQL běží a existuje databáze/uživatel:
   - DB: `debug_db`
   - uživatel: `debug_dbuser`
   - heslo: `debug_dbpassword`

4. Spusťte migrace:

   ```bash
   python manage.py migrate
   ```

5. Spusťte server:

   ```bash
   python manage.py runserver
   ```

6. Otevřete:
   - API root: `http://127.0.0.1:8000/api/`
   - admin: `http://127.0.0.1:8000/admin/`

---

## 7. Docker setup

Repozitář obsahuje:
- `compose.yaml`
- `Dockerfile`

### 7.1 Aktuální omezení

`Dockerfile` instaluje závislosti z `requirements.txt`, ale repozitář používá `pozadavky.txt`.

Aby Docker běžel správně, udělejte jednu z těchto možností:
- vytvořte `requirements.txt` jako kopii `pozadavky.txt`, nebo
- upravte `Dockerfile`, aby používal `pozadavky.txt`.

### 7.2 Spuštění přes Compose

```bash
docker compose up --build
```

Služby:
- `db`: PostgreSQL 17 na portu `5432`
- `django-web`: Django aplikace na portu `8000`

---

## 8. Typický běhový tok

1. Klient požádá o challenge token (`/auth/challenge/`).
2. Klient ověří challenge přes TOTP (`/auth/verify/`) a získá access token.
3. Klient spustí spotřebič (`/appliance/start/`) s rezervovanými jednotkami/cenou.
4. Backend strhne prostředky, vytvoří `RunsLog` a označí stav endpoint-spotřebič jako obsazený.
5. Klient dokončí běh spotřebiče (`/appliance/finish/`) s konečnými jednotkami/cenou.
6. Backend dokončí `RunsLog`, vrátí rozdíl ceny (pokud existuje) a uvolní stav.

---

## 9. Poznámky ke konvencím dat

- Zůstatek a platební částky jsou uložené jako celá čísla v haléřích.
- Cena z API se ve handlerech `start/finish` násobí 100.
- `Room.key` funguje jako identifikátor pokoje používaný v API i ingestu plateb (mapování `VS`).
- Obsazenost spotřebiče je modelovaná pro každou dvojici `(endpoint, appliance)`.

---

## 10. Známé problémy / nehotové části

<<<<<<< HEAD
1. `AuthService.encode(..., "start", ...)` aktuálně odkazuje na `units` bez definice této proměnné v daném scope metody.
2. `bank_module/data_getter.py` je prázdný, i když Celery schedule odkazuje na `bank_module.data_getter.fetch_data_from_api`.
3. `debug/celery.py` je prázdný, ale projekt importuje `debug.celery` v `debug/__init__.py`.
4. `Dockerfile` očekává `requirements.txt`, ale závislosti jsou v `pozadavky.txt`.
5. Secrets/keys jsou hardcoded v `debug/settings.py` a pro produkci by měly být přesunuty do proměnných prostředí.
=======
2. `bank_module/data_getter.py` je prázdný, i když Celery schedule odkazuje na `bank_module.data_getter.fetch_data_from_api`. zakomentovano
3. `debug/celery.py` je prázdný, ale projekt importuje `debug.celery` v `debug/__init__.py`. zakomentovano
4. `Dockerfile` očekává `requirements.txt`, ale závislosti jsou v `pozadavky.txt`. upravit/dockerfile neni soucasti finalniho reseni projektu
5. Secrets/keys jsou hardcoded v `debug/settings.py` a pro produkci by měly být přesunuty do proměnných prostředí. !!!!!!!!!!!!!!!!!!!
>>>>>>> a4d79aee090beebb3854e1e9cee5bd5ac2407ea4

---

## 11. Doporučené další kroky

- Přesunout všechny secrets a DB nastavení do konfigurace přes proměnné prostředí.
- Dokončit inicializaci Celery aplikace a implementovat plánovaný úkol pro načítání bankovních dat.
- Přidat automatizované testy pro auth flow API a životní cyklus spotřebiče.
- Přidat generování DRF schema/OpenAPI.
- Zpřesnit exception handling pomocí explicitních typů chyb a jednotné struktury odpovědí.

---

## 12. Užitečné příkazy

```bash
# Migrace
python manage.py makemigrations
python manage.py migrate

# Vytvoření admin uživatele
python manage.py createsuperuser

# Spuštění vývojového serveru
python manage.py runserver

# Spuštění testů
python manage.py test
```


<<<<<<< HEAD
## 13. Licence

V tomto repozitáři aktuálně není přítomen soubor s licencí.
=======
>>>>>>> a4d79aee090beebb3854e1e9cee5bd5ac2407ea4

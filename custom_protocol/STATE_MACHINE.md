# KVSP - Tilakoneen määrittely

## 1. Yleiskuvaus
KVSP (Key-Value State Protocol) on tilallinen sovelluskerroksen protokolla TCP:n yli (oletusportti 9099). Protokollassa asiakas tunnistautuu palvelimelle, minkä jälkeen se voi suorittaa avain-arvotietojen tallennus- ja hakutoimintoja.

---

## 2. Palvelimen tilakone (Server FSM)

```
      +-------------------------------------------+
      |                  LISTEN                   |
      +-------------------------------------------+
                            |
                     TCP-yhteys hyvaksytty
                            v
      +-------------------------------------------+
      |                WAIT_HELLO                 | <-----+
      +-------------------------------------------+       |
            |                               |             |
      Komento: HELLO                  Vaara komento       |
            v                               +-------------+
      +-------------------------------------------+
      |               AUTHENTICATED               | <-----+
      +-------------------------------------------+       |
            |                         |                   |
      SET / GET / DEL / COUNT         Komento: BYE        |
            |                         |                   |
            v                         v                   |
      +-------------------+     +---------------+         |
      |    PROCESSING     |     | DISCONNECTING |         |
      +-------------------+     +---------------+         |
            |                         |                   |
      Vastaus lahetetty               Socket suljettu     |
            +-------------------------)-------------------+
                                      v
                                +-----------+
                                |  CLOSED   |
                                +-----------+
```

### Palvelimen tilat:
- **LISTEN**: Palvelin kuuntelee tulevia TCP-yhteyksiä.
- **WAIT_HELLO**: Yhteys hyväksytty, alkutervehdys lähetetty (`200 KVSP/1.0 READY`). Odotetaan `HELLO <id>` -komentoa.
- **AUTHENTICATED**: Asiakas tunnistautunut, valmis ottamaan vastaan tietokomentoja.
- **PROCESSING**: Käsitellään tallennus- tai hakukomentoa (`SET`, `GET`, `DEL`, `COUNT`). Vastauksen jälkeen palataan tilaan `AUTHENTICATED`.
- **DISCONNECTING**: Vastaanotettu `BYE`. Palvelin vastaa `200 GOODBYE` ja sulkee yhteyden.
- **CLOSED**: Yhteys suljettu ja resurssit vapautettu.

---

## 3. Asiakkaan tilakone (Client FSM)

```
      +-------------------+
      |       INIT        |
      +-------------------+
                |
           connect()
                v
      +-------------------+
      |    CONNECTING     |
      +-------------------+
                |
           Yhteys auki
                v
      +-------------------+
      |     CONNECTED     | (Odotetaan 200 READY)
      +-------------------+
                |
           Laheta HELLO
                v
      +-------------------+
      |    HANDSHAKING    |
      +-------------------+
                |
           200 OK saatu
                v
      +-------------------+ <--------------------+
      |       READY       |                      |
      +-------------------+                      |
         |             |                         |
      Laheta cmd    Laheta BYE                   |
         v             v                         |
+------------------+ +---------------+           |
|  AWAITING_REPLY  | |  TERMINATING  |           |
+------------------+ +---------------+           |
         |                   |                   |
     Vastaus saatu       GOODBYE saatu           |
         +-------------------)-------------------+
                             v
                       +-----------+
                       |  CLOSED   |
                       +-----------+
```

---

## 4. Viestiesimerkit

- Tervehdys: `HELLO kayttaja1\r\n` -> `200 HELLO_OK welcome kayttaja1\r\n`
- Tallennus: `SET lampotila 21.5\r\n` -> `201 STORED lampotila\r\n`
- Haku: `GET lampotila\r\n` -> `200 VALUE lampotila 21.5\r\n`
- Poisto: `DEL lampotila\r\n` -> `200 DELETED lampotila\r\n`
- Lukumäärä: `COUNT\r\n` -> `200 COUNT 0\r\n`
- Lopetus: `BYE\r\n` -> `200 GOODBYE\r\n`

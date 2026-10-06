# TIES323 Sovellusprotokollat - Harjoitustehtävät

Vastaukset ja ratkaisut kurssin **TIES323 Sovellusprotokollat** harjoitustehtäviin (yhteensä 100 pistettä toteutuksista). Tuntikirjanpito löytyy tiedostosta `tuntikirjanpito.md`.

- **Tekijä:** Khondker Montasirzzaman
- **Kieli ja ympäristö:** Python 3 (standardikirjaston matalan tason socketit)

---

## Kurssin suoritussuunnitelma ja pistetaulukko

| Pisteitä | Tehtäväalue | Tila |
| :--- | :--- | :--- |
| **40 p** | **Sähköpostiprotokollat (mailProtocols)** (SMTP, POP3, IMAP + lisäominaisuudet) | Suoritettu |
| **30 p** | **Tiedonsiirtoprotokollat (file_transfer)** (FTP-asiakas + luotettava TFTP ja häviötestaus) | Suoritettu |
| **30 p** | **Omat ja standardiprotokollat (custom_protocol)** (Echo, Daytime, Finger + oma KVSP-tilakone) | Suoritettu |
| **YHT. 100 p** | **Sovellusprotokollien toteutukset (osa 1)** | **100 / 100 p** |

---

## Yliopiston vaatima tekoälyilmoitus (AI Disclaimer)
Yliopiston linjausten mukaisesti ilmoitetaan, että tekoälyä (kielimallia) on käytetty apuvälineenä koodin syntaksin tarkistamiseen, virheenkorjaukseen (debuggaukseen) sekä dokumentaation jäsentelyyn. Kaikki protokollalogiikat, tilakoneet, socket-kutsut ja testit on tarkistettu, ajettu ja todennettu itse toimiviksi kurssin tehtävänantojen mukaisesti.

---

## Protokollat ja komentojen selitykset

### 1. Sähköpostiprotokollat (mailProtocols/ - 40 pistettä)

Palvelin (`MailServer/main.py`) ajaa samanaikaisesti kolmea säiettä ja jakaa yhteisen postilaatikon (`inbox.py`).

#### SMTP-komennot (portti 2525):
- `HELO <domain>`: Asiakas esittäytyy palvelimelle ja avaa SMTP-istunnon.
- `MAIL FROM:<osoite>`: Määrittää viestin lähettäjän ja aloittaa sähköpostitapahtuman.
- `RCPT TO:<osoite>`: Määrittää viestin vastaanottajan (voidaan antaa useampia peräkkäin).
- `DATA`: Ilmoittaa palvelimelle viestisisällön alkamisesta. Palvelin vastaa tilakoodilla `354`, jonka jälkeen asiakas lähettää viestin otsikot ja tekstin. Siirto päätetään riviin `<CRLF>.<CRLF>`. Tämän jälkeen viesti tallentuu palvelimen postilaatikkoon.
- `RSET`: Nollaa nykyisen viestitapahtuman tilan sulkematta yhteyttä.
- `NOOP`: No-operation - tarkistaa, että yhteys on elossa (palauttaa `250 OK`).
- `QUIT`: Päättää SMTP-istunnon hallitusti ja sulkee yhteyden (`221 Bye`).

#### POP3-komennot (portti 1110):
- `USER <nimi>`: Käyttäjätunnuksen syöttäminen (siirtyminen AUTHORIZATION-tilaan).
- `PASS <salasana>`: Salasanan varmennus (siirtyminen TRANSACTION-tilaan).
- `STAT`: Palauttaa postilaatikon tilan: viestien kokonaismäärän ja koon tavuina (`+OK count size`).
- `LIST [n]`: Listaa kaikkien viestien numerot ja koot tai yksittäisen viestin tiedot.
- `RETR <n>`: Noutaa halutun viestin koko sisällön palvelimelta (päättyy pisteeseen omalla rivillään `.`).
- `DELE <n>`: Merkitsee viestin poistettavaksi palvelimelta.
- `RSET`: Peruuttaa kaikki istunnon aikana tehdyt poistomerkinnät.
- `QUIT`: Siirtyy UPDATE-tilaan, toteuttaa poistot ja sulkee yhteyden (`+OK Bye`).

#### IMAP-komennot (portti 1143):
- `CAPABILITY`: Kyselee palvelimen tukemat ominaisuudet ja laajennukset (`* CAPABILITY IMAP4rev1`).
- `LOGIN <user> <pass>`: Tunnistautuu palvelimelle.
- `SELECT <folder>`: Valitsee postikansion (esim. `INBOX`) ja palauttaa viestimäärän (`* n EXISTS`).
- `FETCH <id> (RFC822)`: Hakee valitun viestin tekstisisällön ja otsikot pituustiedon kera.
- `LOGOUT`: Sulkee IMAP-istunnon hallitusti.

#### Lisäominaisuudet (15p extra):
1. **Graafinen käyttöliittymä (5p)** (`extra/gui.py`): Tkinter-pohjainen sähköpostiohjelma viestien lähetykseen (SMTP) ja selaamiseen (POP3).
2. **SSL/TLS-tuki (5p)** (`extra/test_tls.py`): Testiohjelma salatun SSL/TLS-socketin muodostamiseen (esim. Gmail POP3s porttiin 995).
3. **Standardikirjastojen vertailu (5p)** (`extra/stdlib_test.py`): Testaa omaa palvelinta Pythonin virallisilla standardikirjastoilla (`smtplib`, `poplib`, `imaplib`), mikä todistaa yhteensopivuuden RFC-määritysten kanssa.

**Testaus:**
```bash
# Automaattinen testi:
python3 mailProtocols/test_mail_protocols.py

# Tai palvelin ja asiakkaat erikseen:
python3 mailProtocols/MailServer/main.py
python3 mailProtocols/SMTPclient/smtp_client.py
python3 mailProtocols/POP3client/pop3_client.py
python3 mailProtocols/IMAPclient/imap_client.py
```

---

### 2. Tiedonsiirtoprotokollat (file_transfer/ - 30 pistettä)

#### FTP-asiakas (`ftp_client.py`, 5p):
FTP käyttää erillistä kontrolliyhteyttä (portti 2121) ja passiivista datayhteyttä:
- `USER <nimi>` ja `PASS <salasana>`: Tunnistautuminen kontrolliyhteydellä.
- `PASV`: Pyytää palvelinta avaamaan passiivisen dataportin (IPv4). Palvelin vastaa muodossa `(h1,h2,h3,h4,p1,p2)`, josta asiakas laskee portin `p1 * 256 + p2` ja avaa erillisen datasocketin.
- `EPSV`: Extended Passive Mode (tukee myös IPv6:tta), palauttaa dataportin muodossa `(|||portti|)`.
- `LIST`: Pyytää hakemistolistauksen avatun datayhteyden kautta.
- `RETR <tiedosto>`: Lataa palvelimelta tiedoston sisällön datayhteyden läpi.
- `QUIT`: Sulkee FTP-istunnon.

#### TFTP-asiakas ja -palvelin (`tftp_client.py` & `tftp_server.py`, 15p):
Toteutettu UDP-pohjainen TFTP (RFC 1350) kaksisuuntaisella siirrolla:
- `RRQ (Opcode 1)`: Read Request – pyyntö ladata tiedosto palvelimelta asiakkaalle.
- `WRQ (Opcode 2)`: Write Request – pyyntö lähettää tiedosto palvelimelle. Palvelin vastaa lohkon 0 kuittauksella (`ACK 0`).
- `DATA (Opcode 3)`: Sisältää 2 tavun lohkonumeron ja enintään 512 tavua dataa. Viimeinen lohko tunnistetaan siitä, että sen pituus on alle 512 tavua.
- `ACK (Opcode 4)`: Sisältää vahvistettavan lohkon 2-tavuisen lohkonumeron.
- `ERROR (Opcode 5)`: Palauttaa virhekoodin ja virheilmoituksen.

#### TFTP-luotettavuus ja pakettihäviötesti (10p):
- **Lohkonumeroiden tarkistus:** Jokaisen saapuvan paketin lohkonumero tarkistetaan vastaamaan odotettua.
- **Datan uudelleenlähetys:** Jos kuittauksessa on väärä lohko, virheellinen opcode tai aikakatkaisu (timeout), DATA-paketti lähetetään uudelleen.
- **Kuittauksen uudelleenlähetys:** Jos datapaketti viivästyy tai duplikoituu, edellinen ACK lähetetään uudelleen.
- **Pakettihäviö ja toipuminen:** `network_impairment_proxy.py` pudottaa satunnaisesti 25 % paketeista. Testi ajaa siirron onnistuneesti loppuun ja tallentaa Wireshark-kaappauksen tiedostoon:
  `captures/tftp_packet_loss_recovery.pcap`

**Testaus:**
```bash
python3 file_transfer/test_file_transfer.py
```

---

### 3. Omat ja standardiprotokollat (custom_protocol/ - 30 pistettä)

#### Standardiprotokollat (15p = 3 x 5p):
- **RFC 862 Echo (5p)** (`rfc862_echo.py`): Portti 8007. Palauttaa kaiken vastaanottamansa datan sellaisenaan. Testattavissa Netcatilla: `nc 127.0.0.1 8007`.
- **RFC 867 Daytime (5p)** (`rfc867_daytime.py`): Portti 8013. Palauttaa nykyisen ajan ja päivämäärän tekstinä (UTC) ja sulkee yhteyden. Testattavissa: `nc 127.0.0.1 8013`.
- **RFC 1288 Finger (5p)** (`rfc1288_finger.py`): Portti 8079. Asiakas kysyy käyttäjätietoja lähettämällä nimen, ja palvelin palauttaa tilatiedot. Testattavissa: `finger @127.0.0.1 -p 8079`.

#### Oma protokolla: KVSP (Key-Value State Protocol, 15p):
TCP-pohjainen avain-arvo-tilakoneprotokolla (portti 9099). Yksityiskohtainen tilakaavio ja määrittely löytyy tiedostosta `STATE_MACHINE.md`.

**KVSP-komennot:**
- `HELLO <asiakas>`: Kättely, joka siirtää yhteyden `INIT`-tilasta `AUTHENTICATED`-tilaan.
- `SET <avain> <arvo>`: Tallentaa avaimelle arvon muistiin. Vastaus: `201 STORED <avain>`.
- `GET <avain>`: Hakee tallennetun arvon. Vastaus: `200 VALUE <avain> <arvo>` tai `404 NOT_FOUND`.
- `DEL <avain>`: Poistaa tallennetun avaimen. Vastaus: `200 DELETED <avain>` tai `404 NOT_FOUND`.
- `COUNT`: Palauttaa tallennettujen avainten määrän. Vastaus: `200 COUNT <määrä>`.
- `BYE`: Päättää istunnon ja siirtyy `CLOSED`-tilaan. Vastaus: `200 GOODBYE`.

**Testaus:**
```bash
python3 custom_protocol/test_custom_protocol.py
```

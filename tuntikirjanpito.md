# Tuntikirjanpito

Tässä tiedostossa pidetään kirjaa kurssille TIES323 Sovellusprotokollat käytetyistä työtunneista. Tunnit on jaoteltu aiheittain ja tehtäväkokonaisuuksittain. Yhteensä kurssin toteutusosaan käytetty 38,5 tuntia.

## META ja suunnittelu

Yleinen suunnittelu, kurssisivujen ja RFC-dokumenttien läpikäynti sekä ympäristön pystytys.

| PVM | Tunteja | Selite |
| --- | ------- | ------ |
| 28.9.2026 | 1.5h | Kurssisivuihin, pisteytykseen ja RFC-määrittelyihin tutustuminen. Päätetty toteuttaa sähköposti-, tiedonsiirto- ja omat protokollat (100p). |
| 29.9.2026 | 1.0h | Git-repositorion alustus, hakemistorakenteen luonti ja Python-socket-kehitysympäristön valmistelu. |

Yhteensä: 2,5 h

---

## 1. Sähköpostiprotokollat (mailProtocols, 40p)

SMTP-, POP3- ja IMAP-palvelimet ja -asiakkaat sekä yhteinen postilaatikko ja lisäominaisuudet.

| PVM | Tunteja | Selite |
| --- | ------- | ------ |
| 30.9.2026 | 3.0h | Jaetun postilaatikon (`inbox.py`) ja SMTP-palvelimen rungon koodaus. Komentojen `HELO`, `MAIL FROM`, `RCPT TO`, `DATA` ja `QUIT` tuki. |
| 1.10.2026 | 2.5h | SMTP-asiakkaan (`smtp_client.py`) toteutus ja viestien lähetystestaus palvelimelle. Monirivisen datan (`<CRLF>.<CRLF>`) käsittelyn korjaus. |
| 1.10.2026 | 3.0h | POP3-palvelimen ja -asiakkaan (`pop3_client.py`) toteutus (`USER`, `PASS`, `STAT`, `LIST`, `RETR`, `DELE`, `QUIT`). Viestien lukeminen postilaatikosta. |
| 2.10.2026 | 2.5h | IMAP4-palvelimen ja -asiakkaan (`imap_client.py`) toteutus (`CAPABILITY`, `LOGIN`, `SELECT`, `FETCH`, `LOGOUT`). |
| 2.10.2026 | 3.0h | Lisäominaisuuksien tekeminen: Tkinter-käyttöliittymä (`gui.py`), TLS/SSL-yhteystesti (`test_tls.py`) ja standardikirjastojen vertailutesti (`stdlib_test.py`). |

Yhteensä: 14,0 h

---

## 2. Tiedonsiirtoprotokollat (file_transfer, 30p)

FTP-asiakas sekä luotettava TFTP-asiakas ja -palvelin pakettihäviötestauksineen.

| PVM | Tunteja | Selite |
| --- | ------- | ------ |
| 3.10.2026 | 3.0h | FTP-asiakkaan (`ftp_client.py`) ohjelmointi. Erillisten kontrolli- ja datayhteyksien hallinta, `PASV`- ja `EPSV`-portin parsinta ja tiedoston lataus (`RETR`). |
| 3.10.2026 | 2.5h | TFTP UDP -palvelimen ja -asiakkaan perustoiminnallisuus (`RRQ` ja `WRQ`, 512 tavun lohkot ja `ACK`). |
| 4.10.2026 | 3.5h | TFTP-luotettavuusmekanismit: lohkonumeroiden validointi, virheellisten pakettien hylkäys ja uudelleenlähetys timeoutin jälkeen (sekä DATA- että ACK-paketeille). |
| 4.10.2026 | 2.5h | Pakettihäviöproxy (`network_impairment_proxy.py`) ja testaus 25 % UDP-häviöllä. Pcap-liikennekaappauksen tallennus ja tarkistus Wiresharkilla. |

Yhteensä: 11,5 h

---

## 3. Omat ja valmiit protokollat (custom_protocol, 30p)

Standardiprotokollat (Echo, Daytime, Finger) ja oma tilakoneprotokolla KVSP.

| PVM | Tunteja | Selite |
| --- | ------- | ------ |
| 5.10.2026 | 2.5h | RFC 862 Echo-, RFC 867 Daytime- ja RFC 1288 Finger -palvelimien ja -asiakkaiden toteutus ja testaus netcatilla. |
| 5.10.2026 | 4.0h | Oman avain-arvo-tilakoneprotokollan (KVSP) suunnittelu. Tilasiirtymien, komentojen ja virhetilojen määrittely sekä `STATE_MACHINE.md`:n kirjoittaminen. |
| 6.10.2026 | 4.0h | KVSP-palvelimen ja -asiakkaan tilakoneiden ohjelmointi, yhteydenhallinta, datan käsittely ja automaattitestin (`test_custom_protocol.py`) laadinta. |

Yhteensä: 10,5 h

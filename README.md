# Accenture Hackathon - Dagens Bedrift

Dette prosjektet inneholder data som skal brukes under Accenture Hackathon - Dagens Bedrift.

Hver tabell inneholder en beskrivelse av feltene, link til JSON og CSV.

## Introduksjon

VennSkaper er et morsomt og interaktivt spill som går ut på å svare på spørsmål og resulterer i at du får nye venner.

For å kunne spille VennSkaper må man først finne en av de 4 arkade-maskinene / boothene.

Deretter starter man spillet ved å identifisere seg, noe som gjøres ved å bruke din unike QR-kode fra appen "UKApp17", som kan lastes ned i fra Google Play Store eller iOS App Store, til å scanne i boothen.

Etter deltakeren har scannet sin QR-kode i arkade-maskinen / boothen, så starter spillet.

Selve spillet går så ut på å svare på 18 spørsmål.

Disse 18 spørsmålene er delt inn i 5 typer / deler:

* Dilemma(dilemma) - 4 spørsmål.
* Hot or not(hotOrNot) - 6 spørsmål.
* Har du noen gang(harDu) - 3 spørsmål.
* What to do?(tekst) - 4 spørsmål.
* Etisk(etisk) - 1 spørsmål.

Totalt finnes det 127 spørsmål som blir brukt, slik at deltakere vil få forskjellige spørsmål men fremdeles innen like typer / deler.

Deltakernes svar til disse spørsmålene blir så lagret, for å senere kunne brukes til å "matche" brukere opp mot hverandre basert på hvor likt de har svart.

Etter deltakeren har spilt VennSkaper, så kan han møte opp ved en "printer" som står i Lyche, Accenture sitt konseptlokale på Samfundet, for å få printet ut en markør.
Markøren plasserer deg i en gruppe med X-antall andre personer som du har svart likt med, og som vi derfor antar at du har noe til felles med :)

## Answers

Answers inneholder alle svar brukere har gitt på de spørsmålene han har blitt stilt i VennSkaper.

### Data

* [JSON](https://github.com/langz/dagensbedrift/blob/master/answers/answers.json)

### Felter



## Answers (Total)

Answers (Total) er en enkel fremstilling av alle data i fra Answers.

### Data

* [JSON](https://github.com/langz/dagensbedrift/blob/master/answers-total/answers-total.json)

### Felter

* questionID - En referanse til questionID for et spørsmål i Questions
* type - En referanse til type for et spørsmål i Questions
* c1 - Svaralternativ 1 (Rød) 
* c2 - Svaralternativ 2 (Blå)
* c3 - Svaralternativ 3 (Grønn) 
* timeout - Deltaker brukte for lang tid til å svare på spørsmålet

## Groups

### Data

* [JSON](https://github.com/langz/dagensbedrift/blob/master/groups/groups.json)

### Felter



## Groups (Total)

Groups (Total) er en enkel fremstilling av alle data i fra Groups.

### Data

* [JSON](https://github.com/langz/dagensbedrift/blob/master/groups-total/groups-total.json)

### Felter

## Questions

Questions inneholder alle spørsmålene som en deltaker kan få når han spiller VennSkaper.

### Data

* [JSON](https://github.com/langz/dagensbedrift/blob/master/questions/questions.json)

### Felter

* questionID - En unik id for hvert spørsmål
* type - Typer av spørsmål kan være: hotOrNot, etisk, dilemma, tekst, harDu, 
* group - En gruppe kan være?
* questionText - Spørsmålsteksten
* answer1 - Svaralternativ 1 (Rød)
* answer2 - Svaralternativ 2 (Blå)
* answer3 - Svaralternativ 3 (Grønn)
* image1 - Bilde som kun blir brukt for type hotOrNot.

## Scans

Scans inneholder data for hver gang en deltaker har fått printet ut sin markør i printeren.

### Data

* [JSON](https://github.com/langz/dagensbedrift/blob/master/scans/scans.json)

### Felter



## Scans (Total)

Scans (Total) er en enkel fremstilling av alle data i fra Scans.

### Data

* [JSON](https://github.com/langz/dagensbedrift/blob/master/scans-total/scans-total.json)

### Felter

* date - Dato da printer var tilgjengelig
* totalNumberOfScans - Antall brukere som har skannet
* numberOfMatchingGroupsCreated - Antall opprettede grupper
* numberOfRandomAssignments - Antall brukere som ble plassert i en tilfeldig gruppe
* location - Lokasjon på printer
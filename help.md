# Povinator3000 - Manuale Utente

Il codice sorgente di Povinator3000 si trova su 
[GitHub](https://github.com/dpdani/povinator3000).

## Preparazione al caricamento delle Presentazioni

Per permettere agli studenti di caricare le proprie presentazioni, è necessario 
preparare una cartella su Google Drive che ospiterà i file degli studenti.

### Struttura della Cartella Lauree

È necessario costruire la cartella in modo che contenga nel primo livello una 
cartella per ognuno dei Dipartimenti che parteciperanno alla sessione di laurea.
Al secondo livello, per ogni Dipartimento è necessario creare una sotto-cartella
per ogni Commissione di Laurea di tale Dipartimento.

Per esempio, si potrebbe ottenere una struttura simile alla seguente:

```
+ Lauree 2020-04-26
  + CIBIO
    + BCM 1
    + BCM 2
  + DISI
    + Commissione 1
    + Commissione 2
```

Suggerimento: nominare le cartelle con anno-mese-giorno permette di far 
coincidere l'ordine alfabetico con quello cronologico.

### Generazione del Form

Povinator3000 richiede che il Google Form che raccoglierà le presentazioni
sia costruito in un certo modo.
Al fine di produrlo correttamente, Povinator mette a disposizione una 
funzionalità di generazione di Google Form.

Dopo aver strutturato la cartella lauree come indicato nella sezione precedente,
navigare su Google Drive in tale cartella e copiare l'URL presente nella
barra di navigazione del proprio browser.

L'URL sarà simile a:
`https://drive.google.com/drive/u/0/folders/0BwwA4oUTeiV1TGRPeTVjaWRDY1E`.

Navigare ora su http://localhost:3000/form e incollare il link appena copiato
nella aposita casella e procedere.

### Completare la Generazione del Form

Per limitazioni delle API di Google, Povinator non è in grado di
compiere tutte le azioni che sono necessarie per finalizzare la costruzione
del Form.
Nella sezione successiva verranno mostrate tali azioni.

## Download delle Presentazioni

Una volta che viene chiuso il Form e gli studenti non hanno più la possibilità 
di caricare le proprie presentazioni, si può usare Povinator per procedere con
la routine di rinominazione, spostamento e download delle presentazioni.

### Pagina Principale

Per utilizzare Povinator, navigare con il proprio browser su
http://localhost:3000/presentations.

Quella che viene mostrata è la pagina iniziale di Povinator.
Da qui è possibile indicare l'URL della cartella di Google Drive su cui operare.

L'URL da inserire sarà simile a:
`https://drive.google.com/drive/u/0/folders/0BwwA4oUTeiV1TGRPeTVjaWRDY1E`.
In particolare, questo URL può essere trovato navigando su Google Drive nella 
cartella da utilizzare e copiando l'URL nella barra di navigazione del proprio
browser.

Nella stessa pagina è anche possibile selezionare l'opzione di scaricare nel
computer locale i file delle presentazioni che sono stati caricati dagli
studenti, una volta che Povinator li abbia rinominati e spostati nella cartella
corretta, all'interno di Drive.

Nota: eseguire più volte Povinator sugli stessi file non produrrà effetti
indesiderati.

### Fogli di Risposte

Una volta inserito l'URL e selezionate le opzioni desiderate, è possibile 
procedere alla schermata successiva, premendo il pulsante con la freccia.

In questa schermata è possibile selezionare quali file siano i fogli 
elettronici contenenti le risposte al Form presentato ai laureandi.

Povinator utilizzerà questi file per decidere come rinominare e spostare i file
all'interno dell'archivio Drive.

È necessario selezionare almeno un file perché Povinator riesca ad effettuare
le consuete operazioni. 
Nel caso non venga selezionato nulla, Povinator procederà senza effettuare 
nessuna operazione.

Povinator mette a disposizione dell'utente per la selezione _solo_ i file che
rispettano le caratteristiche adatte, ovvero

- il file deve essere un Google Spreadsheet;
- il nome del file deve terminare con "(Responses)" o "(Risposte)" i quali sono 
i suffissi che Google applica ai file di risposta dei Google Form.

Nel caso Povinator non riesca a trovare nessun file che rispetti queste 
caratteristiche, anziché mostrare la normale pagina di selezione, mostrerà una
schermata di errore.

### Pagina Finale

Dopo aver selezionato i Fogli di Risposta, Povinator procederà a rinominare e 
spostare i file caricati dagli studenti nelle cartelle corrette.

I file verranno rinominati con il nome e il cognome dello studente che li ha
caricati, così come lo studente avrà indicato compilando il Form.

In questa pagina, sarà possibile prendere visione di tutte le operazioni 
compiute da Povinator, in forma testuale.

In calce al corpo della pagina, Povinator mostrerà i percorsi in cui sono stati
scaricati i file e dove è stato creato l'archivio ZIP, se così era stato
richiesto nella pagina principale.

## Installazione

### Python

Come prima cosa assicurarsi che Python sia disponibile sul proprio sistema
in versione &ge; 3.6, preferibilmente 3.8 o superiore.

Per Windows è possibile scaricarlo da https://www.python.org/downloads/windows/.

Per Linux, consultare le modalità di installazione della propria distribuzione.
Inoltre, è assai probabile che sia già installato.
Si può verificare inserendo il comando da terminale:

```
$ python3
Python 3.8.2 (default, Feb 26 2020, 22:21:03) 
[GCC 9.2.1 20200130] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> 
``` 

Se l'esecuzione di tale comando restituisce un output simile a quello mostrato,
allora Python è stato installato con successo.

### Git

Successivamente, è necessario installare Git.

Per Windows: https://git-scm.com/download/win.

Nuovamente, per Linux consultare le modalità specifiche della propria
distribuzione.
Anche git è probabile che sia preinstallato.

Verificare la corretta installazione:

```
$ git --version
git version 2.25.2
```

### Povinator3000

Posizionandosi in una cartella che si intende usare come cartella di
installazione di Povinator, eseguire i seguenti comandi:

```
$ git clone https://github.com/dpdani/povinator3000.git
...
$ cd povinator3000
$ python3 -m venv venv
$ source venv/bin/activate  # on linux
$ venv\bin\activate.bat  # on windows
$ pip install -r requirements.txt
$ python -m povinator3000
``` 

Verificare la corretta installazione navigando su http://localhost:3000/.

Se sul browser viene mostrata la pagina di benvenuto di Povinator, allora
l'installazione è avvenuta con successo.


### Servizio Automatico

Povinator3000 all'avvio.

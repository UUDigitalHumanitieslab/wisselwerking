# Toewijzen wisselwerkingen

1. Download de resultaten als puntkomma-gescheiden CSV-bestand.
2. Werk eventueel capacities.csv bij. Het is ook mogelijk het bestand te verwijderen: het script zal dan bij een onbekende keuze vragen wat de capaciteit is, en een nieuw bestand opslaan.
3. Installeer Python 3 en draai vanuit een command line (powershell, bash, cmd):

```bash
python magic.py aanmeldformulier-wisselwerking.csv "/run/user/1000/gvfs/dav:host=webdav.uu.nl,ssl=true/Data/GW/Projecten/Wisselwerking OBP op reis/"
```

(dat laatste is de locatie van de voorgaande toewijzingen op de O-schijf)


## Statistieken

Genereer csv-bestanden (geanonimiseerd!) met informatie over deelname in het verleden:

```bash
python history.py "/run/user/1000/gvfs/dav:host=webdav.uu.nl,ssl=true/Data/GW/Projecten/Wisselwerking OBP op reis/"
```

Hint: zorg dat het huidige jaar al op de juiste plek staat zodat die worden meegenomen.

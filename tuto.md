# Tuto pour ajouter l'extraction d'une donnée au code

Le cas le plus défavorable est celui ou le topic n’est pas encore traité.
Prenons pour exemple, le topic “julienlebg”

## Modification à faire

- Dans **Data_recovery.py** :  
   - Dans **class Drix_data** : 
      ajouter le nom du topic dans la liste *self.list_topics*
      ```
      158    self.list_topics = ['/gps', ... , ‘/julienlebg’]
      ```


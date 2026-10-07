# Note de cadrage : un bonus de pointe est-il rentable, et peut-on le tester ?

**Destinataire** : responsable de la rémunération des riders (cas fictif).  **Périmètre** : courses Uber et Lyft de New York,
janvier-février 2026, échantillon de 30 %.

## La question

Un bonus de 1,50 $ par course en heure de pointe, en semaine, augmente-t-il assez le nombre de courses pour être rentable, et
sait-on le mesurer de façon fiable ?

## Ce qui a été construit

Une plateforme de données testée (12,2 M de courses réconciliées de la source aux agrégats), un simulateur de coût piloté par des
fichiers de règles, un plan d'expérience (alternance dans le temps sur toute la ville), une surveillance de la qualité des données et un
tableau de bord dont chaque chiffre est réconcilié avec la base.

## Ce que les données montrent

1. **Le bonus coûte cher.** Environ [5,76 M$] sur l'échantillon (+[2,33] % de la rémunération). La pointe pèse 55 % du coût du scénario combiné.
2. **Il doit faire beaucoup venir.** Avec une marge de 6,25 $ par course, le bonus rapporte plus qu'il ne coûte seulement si les
   courses augmentent d'au moins **31,6 %** (35,1 % le matin, 30,5 % le soir). À +5 % de courses, chaque course supplémentaire coûte
   31,50 $ de bonus.
3. **Le test a des limites chiffrées.** Avec 78 unités, l'expérience tranche de façon fiable si l'effet vrai est inférieur à environ
   10 % (abandon dans 92 % des cas) ou supérieur à environ 60 % (adoption dans 96,5 % des cas). Entre 20 % et 50 %, la réponse est
   « non concluant » dans au moins un tirage sur trois. **L'effet du bonus est simulé** : ce résultat valide la méthode, pas un effet réel.
4. **Les données ont des incidents.** 83 % des 35 087 courses signalées tiennent dans trois journées de la source ; la surveillance
   les retrouve sans fausse alerte sur la période.

## Recommandation

- Ne pas juger le bonus sur son seul coût ni sur une estimation isolée : exiger l'intervalle de confiance et comparer sa borne au seuil de 31,6 %.
- Pour un test réel : au moins 8 semaines hors jours exceptionnels, une règle d'exclusion fondée sur la météo et le calendrier fixée à l'avance,
  et une analyse principale qui ne change pas après avoir vu les résultats.
- Mettre en place la surveillance avant le test : un incident de source de quelques heures suffit à fausser des journées entières.

## Limites et risques

Effet simulé ; échantillon de 30 % ; coût statique (aucun comportement de chauffeur modélisé) ; marge approximative ; une seule station
météo ; 78 unités ; le nombre de courses mélange offre et demande.

## Décisions demandées

1. Valider le seuil de rentabilité et la marge à utiliser (la marge réelle de l'entreprise remplace mon approximation).
2. Choisir entre un test de 8 semaines et un plan plus court avec un effet minimal détectable plus grand.
3. Désigner qui acquitte les alertes de qualité des données.
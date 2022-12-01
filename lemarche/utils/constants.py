EMPTY_CHOICE = (("", ""),)

# KIND_PERSO = "PERSO"  # PERSON_TYPE_NATURAL / 1
# KIND_COMPANY = "COMPANY"  # PERSON_TYPE_LEGAL / 2 (not used)
USER_KIND_SIAE = "SIAE"  # PERSON_TYPE_INCLUSIVE / 4
USER_KIND_BUYER = "BUYER"  # PERSON_TYPE_CLASSIC / 3
USER_KIND_PARTNER = "PARTNER"  # PERSON_TYPE_PARTNER / 6
USER_KIND_ADMIN = "ADMIN"  # PERSON_TYPE_ADMIN/ 5

USER_KIND_CHOICES = (
    # (KIND_PERSO, "Utilisateur"),  # Une personne
    # (KIND_COMPANY, "Entreprise"),  # Une entreprise
    (USER_KIND_SIAE, "Structure"),  # Structure inclusive qui souhaite proposer ses offres
    (USER_KIND_BUYER, "Acheteur"),  # Un acheteur qui souhaite réaliser un achat inclusif
    (USER_KIND_PARTNER, "Partenaire"),  # Partenaire
)
USER_KIND_CHOICES_WITH_ADMIN = USER_KIND_CHOICES + ((USER_KIND_ADMIN, "Administrateur"),)  # Administrateur.trice

MARCHE_BENEFIT_TIME = "TIME"
MARCHE_BENEFIT_DISCOVER = "DISCOVER"
MARCHE_BENEFIT_MORE = "MORE"
MARCHE_BENEFIT_CLAUSE = "CLAUSE"
MARCHE_BENEFIT_SECURE = "SECURE"
MARCHE_BENEFIT_NONE = "NONE"
MARCHE_BENEFIT_CHOICES = (
    (MARCHE_BENEFIT_TIME, "Gagner du temps"),
    (MARCHE_BENEFIT_DISCOVER, "Découvrir de nouveaux prestataires inclusifs"),
    (MARCHE_BENEFIT_MORE, "Faire plus d'achats inclusifs"),
    (MARCHE_BENEFIT_CLAUSE, "Intégrer une clause sociale à un marché"),
    (MARCHE_BENEFIT_SECURE, "Sécuriser un marché réservé"),
    (MARCHE_BENEFIT_NONE, "Aucun"),
)

# how many scale is used for survey on signup
# nb of inculsive or handicap provider
HOW_MANY_SCALE_0 = "0"
HOW_MANY_SCALE_1 = "1"
HOW_MANY_SCALE_2 = "2"
HOW_MANY_SCALE_3 = "3"
HOW_MANY_SCALE_4 = "4"
HOW_MANY_SCALE_5 = "5"
HOW_MANY_SCALE_6 = "6"
HOW_MANY_SCALE_6 = "+6"

HOW_MANY_CHOICES = (
    (HOW_MANY_SCALE_0, "0"),
    (HOW_MANY_SCALE_1, "1"),
    (HOW_MANY_SCALE_2, "2"),
    (HOW_MANY_SCALE_3, "3"),
    (HOW_MANY_SCALE_4, "4"),
    (HOW_MANY_SCALE_5, "5"),
    (HOW_MANY_SCALE_6, "6"),
    (HOW_MANY_SCALE_6, "+ de 6"),
)

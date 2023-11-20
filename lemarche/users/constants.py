KIND_SIAE = "SIAE"  # Structure inclusive qui souhaite proposer ses offres
KIND_SIAE_DISPLAY = "Structure"
KIND_BUYER = "BUYER"  # Un acheteur qui souhaite réaliser un achat inclusif
KIND_BUYER_DISPLAY = "Acheteur"
KIND_PARTNER = "PARTNER"
KIND_PARTNER_DISPLAY = "Partenaire"
KIND_ADMIN = "ADMIN"
KIND_ADMIN_DISPLAY = "Administrateur"  # Administrateur.trice

KIND_CHOICES = (
    (KIND_SIAE, KIND_SIAE_DISPLAY),
    (KIND_BUYER, KIND_BUYER_DISPLAY),
    (KIND_PARTNER, KIND_PARTNER_DISPLAY),
)
KIND_CHOICES_WITH_ADMIN = KIND_CHOICES + ((KIND_ADMIN, KIND_ADMIN_DISPLAY),)

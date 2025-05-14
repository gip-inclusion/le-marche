from dataclasses import dataclass


@dataclass
class InclusivePotential:
    potential_siaes: int
    score_inclusif: int
    inclusif_interpretation: str


def get_score_inclusif(siaes_count):
    score_inclusif = 0
    inclusif_interpretation = ""
    match siaes_count:
        case _ if siaes_count >= 8:
            score_inclusif = 50
            inclusif_interpretation = "Offre suffisante et diversifiée"
        case _ if siaes_count >= 6:
            score_inclusif = 40
            inclusif_interpretation = "Offre existante mais concentrée"
        case _ if siaes_count >= 4:
            score_inclusif = 20
            inclusif_interpretation = "Offre limitée"
        case _ if siaes_count >= 1:
            score_inclusif = 10
            inclusif_interpretation = "Offre très réduite"
        case 0:
            score_inclusif = 0
            inclusif_interpretation = "Absence d’offre locale"

    return InclusivePotential(siaes_count, score_inclusif, inclusif_interpretation)

from dataclasses import dataclass

from lemarche.api.inclusive_potential.constants import (
    LIMIT_FOR_CLAUSE,
    LIMIT_FOR_ECO_DEPENDENCY,
    LIMIT_FOR_LOT,
    LIMIT_FOR_RESERVATION,
    PRESTA_TYPE_TO_SIAE_KINDS,
    RECOMMENDATIONS,
)
from lemarche.siaes.constants import KIND_HANDICAP_LIST, KIND_INSERTION_LIST
from lemarche.siaes.models import Siae


@dataclass
class PotentialData:
    potential_siaes: int
    insertion_siaes: int
    handicap_siaes: int
    local_siaes: int
    siaes_with_super_badge: int
    employees_insertion_average: int
    employees_permanent_average: int


def set_analysis_data(siaes, siaes_count, budget, analysis_data):
    # Get all valid CA values from siaes and calculate the average manually to avoid to many fat queries
    ca_values = [siae.ca or siae.api_entreprise_ca for siae in siaes if siae.ca or siae.api_entreprise_ca]
    if ca_values:
        analysis_data["ca_average"] = round(sum(ca_values) / len(ca_values))
        analysis_data["eco_dependency"] = round(budget / analysis_data["ca_average"] * 100)

    if siaes_count > LIMIT_FOR_RESERVATION:
        if "eco_dependency" in analysis_data and analysis_data["eco_dependency"] < LIMIT_FOR_ECO_DEPENDENCY:
            recommendation = RECOMMENDATIONS["reservation"].copy()
        else:
            recommendation = RECOMMENDATIONS["lot"].copy()
    elif siaes_count > LIMIT_FOR_LOT:
        recommendation = RECOMMENDATIONS["lot"].copy()
    elif siaes_count > LIMIT_FOR_CLAUSE:
        recommendation = RECOMMENDATIONS["clause"].copy()
    else:
        recommendation = RECOMMENDATIONS["aucun"].copy()

    # check if eco_dependency and ca_average exist as they are needed to format the explanation
    recommendation["explanation"] = (
        recommendation["explanation"].format(
            siaes_count=siaes_count,
            eco_dependency=analysis_data["eco_dependency"],
            ca_average=analysis_data["ca_average"],
        )
        if "eco_dependency" in analysis_data and "ca_average" in analysis_data
        else None
    )
    analysis_data["recommendation"] = recommendation


def get_allowed_kinds_for_presta_types(presta_types: list) -> set:
    """Returns the union of SIAE kinds matching the given list of presta_types."""
    allowed_kinds = set()
    for presta_type in presta_types:
        allowed_kinds.update(PRESTA_TYPE_TO_SIAE_KINDS.get(presta_type, []))
    return allowed_kinds


def get_inclusive_potential_data(
    sector: str, perimeter: str, budget: int, presta_types: list = None
) -> tuple[PotentialData, dict]:
    """
    Get the potential data for a given sector and perimeter.
    Budget is optional and is used to calculate the eco-dependency.
    presta_types is optional and filters results to the SIAE kinds matching the selected prestation types.
    """

    # Get all siaes with potential through activities
    siaes = Siae.objects.filter_with_potential_through_activities(sector, perimeter).with_is_local(perimeter)

    # Filter by SIAE kinds when presta_types filter is provided
    if presta_types:
        allowed_kinds = get_allowed_kinds_for_presta_types(presta_types)
        siaes = siaes.filter(kind__in=allowed_kinds)

    # Calculate the number of siaes by kind and the number of employees
    # Prefer to loop over siaes rather than using querysets to avoid lots of big queries
    siaes_count = 0
    insertion_siaes = 0
    handicap_siaes = 0
    local_siaes = 0
    siaes_with_super_badge = 0
    employees_insertion_count = 0
    employees_permanent_count = 0
    for siae in siaes:
        siaes_count += 1
        if siae.kind in KIND_INSERTION_LIST:
            insertion_siaes += 1
            employees_insertion_count += siae.c2_etp_count or 0
        elif siae.kind in KIND_HANDICAP_LIST:
            handicap_siaes += 1
            employees_insertion_count += siae.employees_insertion_count or 0

        if siae.is_local:
            local_siaes += 1

        siaes_with_super_badge += 1 if siae.super_badge else 0

        employees_permanent_count += siae.employees_permanent_count or 0

    analysis_data = {}
    if budget:
        set_analysis_data(siaes, siaes_count, budget, analysis_data)

    return (
        PotentialData(
            potential_siaes=siaes_count,
            insertion_siaes=insertion_siaes,
            handicap_siaes=handicap_siaes,
            local_siaes=local_siaes,
            siaes_with_super_badge=siaes_with_super_badge,
            employees_insertion_average=round(employees_insertion_count / siaes_count, 2) if siaes_count else 0,
            employees_permanent_average=round(employees_permanent_count / siaes_count, 2) if siaes_count else 0,
        ),
        analysis_data,
    )

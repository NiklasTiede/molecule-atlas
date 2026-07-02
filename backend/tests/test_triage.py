from app.chem.triage import calculate_triage_flags
from app.models.candidate import DescriptorSet


def test_triage_flags_have_no_violations_for_aspirin_like_descriptors() -> None:
    descriptors = DescriptorSet(
        molecular_weight=180.2,
        logp=1.2,
        tpsa=63.6,
        hbond_donors=1,
        hbond_acceptors=3,
        rotatable_bonds=2,
        ring_count=1,
        heavy_atom_count=13,
        fraction_csp3=0.1,
        murcko_scaffold="c1ccccc1",
    )

    flags = calculate_triage_flags(descriptors)

    assert flags.lipinski_violations == 0
    assert flags.veber_violations == 0

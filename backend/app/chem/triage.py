from app.models.candidate import DescriptorSet, TriageFlags


def calculate_triage_flags(descriptors: DescriptorSet) -> TriageFlags:
    lipinski_notes: list[str] = []
    if descriptors.molecular_weight > 500:
        lipinski_notes.append("Molecular weight is greater than 500.")
    if descriptors.logp > 5:
        lipinski_notes.append("LogP is greater than 5.")
    if descriptors.hbond_donors > 5:
        lipinski_notes.append("More than 5 hydrogen bond donors.")
    if descriptors.hbond_acceptors > 10:
        lipinski_notes.append("More than 10 hydrogen bond acceptors.")

    veber_notes: list[str] = []
    if descriptors.rotatable_bonds > 10:
        veber_notes.append("More than 10 rotatable bonds.")
    if descriptors.tpsa > 140:
        veber_notes.append("TPSA is greater than 140.")

    return TriageFlags(
        lipinski_violations=len(lipinski_notes),
        lipinski_notes=tuple(lipinski_notes),
        veber_violations=len(veber_notes),
        veber_notes=tuple(veber_notes),
    )

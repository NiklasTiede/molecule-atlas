from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, Lipinski, rdMolDescriptors
from rdkit.Chem.Scaffolds import MurckoScaffold

from app.models.candidate import DescriptorSet


def calculate_descriptors(mol: Chem.Mol) -> DescriptorSet:
    scaffold_mol = MurckoScaffold.GetScaffoldForMol(mol)
    scaffold = Chem.MolToSmiles(scaffold_mol, canonical=True) if scaffold_mol else None

    return DescriptorSet(
        molecular_weight=Descriptors.MolWt(mol),
        logp=Crippen.MolLogP(mol),
        tpsa=rdMolDescriptors.CalcTPSA(mol),
        hbond_donors=Lipinski.NumHDonors(mol),
        hbond_acceptors=Lipinski.NumHAcceptors(mol),
        rotatable_bonds=Lipinski.NumRotatableBonds(mol),
        ring_count=rdMolDescriptors.CalcNumRings(mol),
        heavy_atom_count=mol.GetNumHeavyAtoms(),
        fraction_csp3=rdMolDescriptors.CalcFractionCSP3(mol),
        murcko_scaffold=scaffold or None,
    )

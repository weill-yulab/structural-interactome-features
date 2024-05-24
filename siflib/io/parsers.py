from pathlib import Path
from typing import Dict
import warnings
import re


def parse_fasta(fasta_file: Path,
                uniprot_header=True,
                skip_metadata=False) -> Dict:
    """
    Parses a fasta file and produces a dictionary that maps the accession ID
    to the sequence and other metadata if available.

    Parameters
    ----------
    fasta_file : Path
        Path to the FASTA file
    uniprot_header : bool, default True
        If true, parses the Protein ID line using the following header as
        defined by UniProt. "UniqueIdentifier" will be used as the accession ID
        and all other elements will be added as metadata to each element

        if False, everything after ">" will be used as the accession ID, and
        the only metadata will be the sequence
    skip_metadata : bool, default False
        If true, only "sequence" will be included in the resulting dictionary.

    Returns
    -------
    Dict
        A dictionary with the following structure:
        {
            "accession_id": {
                "sequence": "...", # only this one is guaranteed to be included
                "db": "..."
                "EntryName": "..."
                ...
            }
        }
    """
    assert fasta_file.is_file()
    uniprot_re = None
    if uniprot_header:
        regex = (r"^>(?P<db>[a-zA-Z]+)\|(?P<UniqueIdentifier>\w+)\|"
                 r"(?P<EntryName>\w+)\s(?P<ProteinName>.*)\s"
                 r"OS=(?P<OrganismName>.*)\sOX=(?P<OrganismIdentifier>\w*)\s"
                 r"(?:GN=(?P<GeneName>.*)\s)?PE=(?P<ProteinExistence>.*)\s"
                 r"SV=(?P<SequenceVersion>\w+).*$")
        uniprot_re = re.compile(regex)

    sequences = {}
    metadata = {}
    curr_seq = ""
    curr_acc = ""
    with fasta_file.open() as f:
        for line in f:
            if line.startswith(">"):
                if curr_seq != "":
                    sequences[curr_acc] = {
                        "sequence": curr_seq
                    }
                    if not skip_metadata:
                        for m, v in metadata.items():
                            sequences[curr_acc][m] = v
                        metadata = {}
                    curr_seq = ""
                if uniprot_header:
                    match = uniprot_re.match(line)
                    if match:
                        metadata = match.groupdict()
                        curr_acc = metadata["UniqueIdentifier"]
                    else:
                        warnings.warn("Could not parse header, defaulting to"
                                      f"simple header for this entry {line}")
                        curr_acc = line[1:].split()[0]
                else:
                    curr_acc = line[1:].split()[0]
            else:
                curr_seq += line.strip()
    return sequences


def parse_cd_hit(cd_hit_file: Path) -> Dict:
    """
    Parses the output of rpsblast

    Parameters
    ----------
    cd_hit_file : Path
        Path to the output file produced by rpsblast

    Returns
    -------
    Dict
        A dictionary with the following structure:
        {
            "query acc.ver": [{
                "subject acc.ver": "..."
                "% identity": "...",
                "alignment length": "...",
                "mistmatches": "...",
                "gap opens": "...",
                "q. start": "...",
                "q. end": "...",
                "s. start": "...",
                "s. end": "...",
                "evalue": "...",
                "bit socre": "..."
            },
            ...],
            ...
        }
    """
    assert cd_hit_file.is_file()
    domains = {}
    with cd_hit_file.open() as f:
        for line in f:
            if line.startswith("#"):
                continue
            (qacc, sacc, pid, al, mism,
             gop, qs, qe, ss, se, ev, bs) = line.strip().split("\t")
            if qacc not in domains.keys():
                domains[qacc] = []
            domains[qacc].append({
                "subject acc.ver": sacc,
                "% identity": float(pid),
                "alignment length": int(al),
                "mistmatches": int(mism),
                "gap opens": int(gop),
                "q. start": int(qs),
                "q. end": int(qe),
                "s. start": int(ss),
                "s. end": int(se),
                "evalue": float(ev),
                "bit socre": float(bs)
            })
    return domains


def parse_ecod_domains(ecod_domains_file: Path) -> Dict:
    """
    Parses ECOD `domain.txt` files

    Parameters
    ----------
    cd_hit_file : Path
        Path to the ECOD `domain.txt` files

    Returns
    -------
    Dict
        A dictionary with the following structure:
        {
            "<PDB ID>_<PDB chain>": [{
                "uid": "...",
                "ecod_domain_id": "...",
                "manual_rep": "...",
                "t_id": "...",
                "pdb": "...",
                "chain": "...",
                "pdb_range": "...",
                "seqid_range": "...",
                "unp_acc": "...",
                "arch_name": "...",
                "x_name": "...",
                "h_name": "...",
                "t_name": "...",
                "f_name": "...",
                "asm_status": "...",
                "ligand": "...",
            },
            ...],
            ...
        }
    """
    assert ecod_domains_file.is_file()
    domains = {}
    with ecod_domains_file.open() as f:
        for line in f:
            if line.startswith("#"):
                continue
            (uid, ecod_domain_id, manual_rep, t_id, pdb, chain, pdb_range,
             seqid_range, unp_acc, arch_name,
             x_name, h_name, t_name, f_name,
             asm_status, ligand) = line.strip().split("\t")
            key = f"{pdb}_{chain}"
            if key not in domains.keys():
                domains[key] = []

            # pdbr_chain, pdbr_range = pdb_range.split(":")
            # pdbr_start, pdbr_end = pdbr_range.split("-")
            # seqidr_chain, seqidr_range = seqid_range.split(":")
            # seqidr_start, seqidr_end = seqidr_range.split("-")
            domains[key].append({
                "uid": uid,
                "ecod_domain_id": ecod_domain_id,
                "manual_rep": manual_rep,
                "t_id": t_id,
                "pdb": pdb,
                "chain": chain,
                "pdb_range": pdb_range,
                "seqid_range": seqid_range,
                "unp_acc": unp_acc,
                "arch_name": arch_name,
                "x_name": x_name,
                "h_name": h_name,
                "t_name": t_name,
                "f_name": f_name,
                "asm_status": asm_status,
                "ligand": ligand,
            })
    return domains

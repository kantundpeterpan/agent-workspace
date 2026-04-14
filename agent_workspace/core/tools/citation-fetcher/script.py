#!/usr/bin/env python3
"""
Citation Fetcher Tool
Fetches BibTeX (and other format) citations from DOI, arXiv ID, or PubMed ID.
"""

import re
from typing import Any, Dict, Optional


def _detect_type(identifier: str) -> str:
    """Detect identifier type: doi, arxiv, or pubmed."""
    identifier = identifier.strip()
    if re.match(r"^10\.\d{4,}/", identifier):
        return "doi"
    if re.match(r"^(arxiv:)?[\d]{4}\.\d{4,}(v\d+)?$", identifier, re.IGNORECASE):
        return "arxiv"
    if re.match(r"^(PMID:?)?\d{6,}$", identifier, re.IGNORECASE):
        return "pubmed"
    # Try DOI embedded in URL
    doi_match = re.search(r"10\.\d{4,}/\S+", identifier)
    if doi_match:
        return "doi"
    return "unknown"


def _fetch_doi_bibtex(doi: str) -> Dict[str, Any]:
    """Fetch BibTeX from doi.org content negotiation."""
    try:
        import urllib.request
        url = f"https://doi.org/{doi}"
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/x-bibtex"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            bibtex = resp.read().decode("utf-8")
        return {"status": "success", "citation": bibtex}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _fetch_arxiv_bibtex(arxiv_id: str) -> Dict[str, Any]:
    """Fetch metadata from arXiv API and build a BibTeX entry."""
    try:
        import urllib.request
        import xml.etree.ElementTree as ET

        clean_id = re.sub(r"^arxiv:", "", arxiv_id, flags=re.IGNORECASE)
        url = f"https://export.arxiv.org/abs/{clean_id}"
        api_url = f"https://export.arxiv.org/api/query?id_list={clean_id}"
        req = urllib.request.Request(api_url, headers={"User-Agent": "citation-fetcher/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            xml_data = resp.read().decode("utf-8")

        ns = {"atom": "http://www.w3.org/2005/Atom",
              "arxiv": "http://arxiv.org/schemas/atom"}
        root = ET.fromstring(xml_data)
        entry = root.find("atom:entry", ns)
        if entry is None:
            return {"status": "not_found", "message": "arXiv ID not found."}

        title = (entry.findtext("atom:title", "", ns) or "").strip().replace("\n", " ")
        authors = [
            a.findtext("atom:name", "", ns).strip()
            for a in entry.findall("atom:author", ns)
        ]
        year_raw = entry.findtext("atom:published", "", ns)
        year = year_raw[:4] if year_raw else "?????"
        doi_elem = entry.find("arxiv:doi", ns)
        doi_str = doi_elem.text.strip() if doi_elem is not None and doi_elem.text else ""

        cite_key = f"{authors[0].split()[-1]}{year}" if authors else f"arxiv{clean_id}"
        author_str = " and ".join(authors)

        bibtex = (
            f"@misc{{{cite_key},\n"
            f"  title   = {{{title}}},\n"
            f"  author  = {{{author_str}}},\n"
            f"  year    = {{{year}}},\n"
            f"  eprint  = {{{clean_id}}},\n"
            f"  archivePrefix = {{arXiv}},\n"
        )
        if doi_str:
            bibtex += f"  doi     = {{{doi_str}}},\n"
        bibtex += f"  url     = {{https://arxiv.org/abs/{clean_id}}}\n}}"

        return {
            "status": "success",
            "cite_key": cite_key,
            "citation": bibtex,
            "metadata": {
                "title": title,
                "authors": authors,
                "year": int(year) if year.isdigit() else None,
                "doi": doi_str,
            },
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _fetch_pubmed_bibtex(pmid: str) -> Dict[str, Any]:
    """Fetch metadata from NCBI E-utilities and build a BibTeX entry."""
    try:
        import urllib.request
        import xml.etree.ElementTree as ET

        clean_id = re.sub(r"^PMID:?", "", pmid, flags=re.IGNORECASE).strip()
        url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            f"?db=pubmed&id={clean_id}&rettype=xml&retmode=xml"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "citation-fetcher/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            xml_data = resp.read().decode("utf-8")

        root = ET.fromstring(xml_data)
        article = root.find(".//PubmedArticle")
        if article is None:
            return {"status": "not_found", "message": "PubMed ID not found."}

        title = article.findtext(".//ArticleTitle") or ""
        year = article.findtext(".//PubDate/Year") or "????"
        journal = article.findtext(".//Journal/Title") or ""
        volume = article.findtext(".//JournalIssue/Volume") or ""
        issue = article.findtext(".//JournalIssue/Issue") or ""
        pages = article.findtext(".//MedlinePgn") or ""
        doi_elem = article.find(".//ArticleId[@IdType='doi']")
        doi_str = doi_elem.text.strip() if doi_elem is not None else ""

        authors = []
        for author in article.findall(".//Author"):
            last = author.findtext("LastName") or ""
            fore = author.findtext("ForeName") or author.findtext("Initials") or ""
            if last:
                authors.append(f"{last}, {fore}".strip(", "))

        cite_key = f"{authors[0].split(',')[0]}{year}" if authors else f"pmid{clean_id}"
        author_str = " and ".join(authors)

        bibtex = (
            f"@article{{{cite_key},\n"
            f"  title   = {{{title}}},\n"
            f"  author  = {{{author_str}}},\n"
            f"  journal = {{{journal}}},\n"
            f"  year    = {{{year}}},\n"
        )
        if volume:
            bibtex += f"  volume  = {{{volume}}},\n"
        if issue:
            bibtex += f"  number  = {{{issue}}},\n"
        if pages:
            bibtex += f"  pages   = {{{pages}}},\n"
        if doi_str:
            bibtex += f"  doi     = {{{doi_str}}},\n"
        bibtex += f"  pmid    = {{{clean_id}}}\n}}"

        return {
            "status": "success",
            "cite_key": cite_key,
            "citation": bibtex,
            "metadata": {
                "title": title,
                "authors": authors,
                "year": int(year) if year.isdigit() else None,
                "journal": journal,
                "doi": doi_str,
            },
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def fetch(
    identifier: str,
    format: str = "bibtex",
    cite_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetch a citation by DOI, arXiv ID, or PubMed ID.

    Args:
        identifier: DOI, arXiv ID (e.g. 2103.00020), or PubMed ID (e.g. PMID:34385711).
        format: Output format — only 'bibtex' is currently supported via API.
        cite_key: Optional custom BibTeX cite key.

    Returns:
        dict with status, cite_key, citation string, and metadata.
    """
    id_type = _detect_type(identifier)

    if id_type == "doi":
        doi = re.search(r"10\.\d{4,}/\S+", identifier)
        doi_str = doi.group(0).rstrip(".") if doi else identifier.strip()
        result = _fetch_doi_bibtex(doi_str)
    elif id_type == "arxiv":
        result = _fetch_arxiv_bibtex(identifier)
    elif id_type == "pubmed":
        result = _fetch_pubmed_bibtex(identifier)
    else:
        return {
            "status": "error",
            "message": f"Could not detect identifier type for: '{identifier}'. "
                       "Expected a DOI (10.xxxx/...), arXiv ID (2103.00020), or PubMed ID (PMID:...).",
        }

    # Override cite_key if provided
    if cite_key and result.get("status") == "success" and result.get("citation"):
        old_key_match = re.match(r"@\w+\{([^,]+),", result["citation"])
        if old_key_match:
            result["citation"] = result["citation"].replace(
                old_key_match.group(1), cite_key, 1
            )
            result["cite_key"] = cite_key

    return result


if __name__ == "__main__":
    import fire
    fire.Fire(fetch)

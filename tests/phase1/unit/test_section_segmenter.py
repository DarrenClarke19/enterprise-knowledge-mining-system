from src.parsing.section_segmenter import segment_sections


def test_segment_standard_sections():
    text = """
    Item 1A. Risk Factors
    Risk text here.

    Item 3. Legal Proceedings
    Legal text here.

    Item 7. Management's Discussion and Analysis
    MD&A text here.

    Item 8. Financial Statements and Supplementary Data
    Financial text here.
    """

    sections = segment_sections("doc1", text)
    names = [s.normalized_section for s in sections]

    assert "item_1a_risk_factors" in names
    assert "item_3_legal_proceedings" in names
    assert "item_7_md&a" in names
    assert "item_8_financial_statements" in names
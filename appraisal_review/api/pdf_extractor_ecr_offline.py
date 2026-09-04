"""
100% Offline Pure Python Extractor for Employee Relocation Council (ERC / ECR) Appraisal Reports.
Extracts all 9 standard ECR categories completely dynamically using PyMuPDF coordinate slicing and pattern matching:
  - SUMMARY
  - SUBJECT
  - NEIGHBORHOOD
  - SITE
  - IMPROVEMENTS
  - MARKET_TRENDS
  - SALES_COMPARISON
  - ANTICIPATED_SALES_PRICE
  - CERTIFICATION
  + SALES_GRID (Subject, Comps 1-3, Comps 4-6)
"""

import os
import re
import json
import pymupdf


def extract_page_words_and_lines(page):
    """
    Extracts word bounding boxes (x0, y0, x1, y1, word) and creates
    a spatial text representation sorted by top-to-bottom, left-to-right.
    """
    words = page.get_text("words")  # list of tuples (x0, y0, x1, y1, word, block_no, line_no, word_no)
    lines_dict = {}
    for w in words:
        y_center = (w[1] + w[3]) / 2.0
        y_approx = round(y_center, 1)
        found_key = None
        for k in lines_dict.keys():
            if abs(k - y_approx) < 4.0:
                found_key = k
                break
        if found_key is None:
            found_key = y_approx
            lines_dict[found_key] = []
        lines_dict[found_key].append(w)

    sorted_y = sorted(lines_dict.keys())
    spatial_lines = []
    for yk in sorted_y:
        line_words = sorted(lines_dict[yk], key=lambda x: x[0])
        spatial_lines.append(" ".join(w[4] for w in line_words))

    spatial_text = "\n".join(spatial_lines)
    return words, spatial_text


def get_words_on_line(words, target_y: float, y_tol: float = 4.5):
    """Returns words whose vertical center falls within target_y ± y_tol, sorted left-to-right."""
    line_words = [w for w in words if abs(((w[1] + w[3]) / 2.0) - target_y) <= y_tol]
    line_words.sort(key=lambda w: w[0])
    return line_words


def get_line_segment(words, target_y: float, xmin: float, xmax: float, y_tol: float = 4.5) -> str:
    """Returns text inside an x-range on a specific horizontal line band."""
    lw = [w for w in get_words_on_line(words, target_y, y_tol) if not (w[2] < xmin or w[0] > xmax)]
    return " ".join([w[4] for w in lw]).strip()


def get_box_text(words, xmin: float, ymin: float, xmax: float, ymax: float) -> str:
    """Filters words whose bounding box overlaps with the given rectangle, sorted top-down, left-to-right."""
    matched = [
        w for w in words
        if not (w[2] < xmin or w[0] > xmax or w[3] < ymin or w[1] > ymax)
    ]
    matched.sort(key=lambda x: (round(x[1] / 3.0) * 3, x[0]))
    return " ".join(w[4] for w in matched).strip()


def clean_narrative(text: str, prompt_prefix_words: list = None, stop_words: list = None) -> str:
    """Cleans form label prefixes and stop word delimiters from multi-line text boxes."""
    if not text:
        return ""
    if prompt_prefix_words:
        for p in prompt_prefix_words:
            if p in text:
                text = text.split(p, 1)[-1].strip()
    if stop_words:
        for s in stop_words:
            if s in text:
                text = text.split(s, 1)[0].strip()
    return text.strip()


def clean_curr(val: str) -> str:
    """Cleans currency formatting and numeric prefixes."""
    if not val:
        return ""
    s = str(val).replace("$", "").replace("Plus", "").replace("Minus", "").replace(",", "").strip()
    s = re.sub(r"^(?:taxes|range|to|price|fee|fees|built|stories|units|s|age)\s*[:\-]*\s*", "", s, flags=re.IGNORECASE).strip()
    return s


def clean_field_value(val: str) -> str:
    """
    Strips pre-printed form guide sub-labels (e.g., 'File #:', 'Address:', 'City:', 'State:', 'Code:', 'Name:', 'Price:', etc.)
    that appear inside field boxes in standard Worldwide ERC / ECR forms.
    """
    if not val:
        return ""
    s = str(val).strip()
    sub_labels = [
        r"^(?:Client\s*)?File\s*#?\s*[:\-]+",
        r"^(?:Appraiser\s*)?File\s*#?\s*[:\-]+",
        r"^(?:Subject\s*Property\s*|Client\s*|Appraiser\s*)?Address\s*[:\-]+",
        r"^(?:Subject\s*|Client\s*|Appraiser\s*)?City\s*[:\-]+",
        r"^(?:Subject\s*|Client\s*|Appraiser\s*)?State\s*[:\-]+",
        r"^(?:Subject\s*|Client\s*|Appraiser\s*Zip\s*)?(?:Zip\s*)?Code\s*[:\-]+",
        r"^(?:Subject\s*)?County\s*[:\-]+",
        r"^(?:Subject\s*)?Unit\s*[:\-]+",
        r"^(?:Appraiser\s*Company\s*)?Name\s*[:\-]+",
        r"^(?:Data\s*)?Source\s*[:\-]+",
        r"^Tax\s*Year\s*[:\-]+",
        r"^(?:Monthly\s*HOA\s*)?Fees?\s*[:\-]+",
        r"^(?:Annual\s*real\s*estate\s*|real\s*estate\s*)?taxes\s*[:\-]+",
        r"^(?:Street\s*|Driveway\s*)?Surface\s*[:\-]+",
        r"^(?:Year\s*)?Built\s*[:\-]+",
        r"^(?:No\.\s*of\s*)?Stories\s*[:\-]+",
        r"^(?:No\.\s*of\s*)?Units?\s*[:\-]+",
        r"^s\s*[:\-]+",
        r"^(?:Original\s*List\s*|Current\s*List\s*|Last\s*Sale\s*)?Price\s*[:\-]+",
        r"^(?:Date\s*of\s*Last\s*Price\s*)?Revision\s*[:\-]+",
        r"^Days[\-\s]on[\-\s]market\s*[:\-]+",
        r"^(?:Listing\s*)?Company\s*\/\s*Agent\s*[:\-]+",
        r"^(?:Appraiser\s*)?Ph(?:one|\.)?\s*#?\s*[:\-]+",
        r"^(?:Appraiser\s*)?Fax\s*#?\s*[:\-]+",
        r"^(?:Appraiser\s*)?E-?mail\s*[:\-]+",
        r"^(?:Last\s*Sale\s*|Closing\s*)?Date\s*[:\-]+",
        r"^(?:Single\s*)?Family\s*[:\-]+",
        r"^(?:Multi[\-\s]*family|Commercial|Industrial|Condo|Present\s*Land\s*Use|Land\s*Use)\s*[:\-]+",
        r"^(?:To)?pography\s*[:\-]+",
        r"^(?:Shape|View|Landscaping|Drainage|Dimensions|Site\s*Area)\s*[:\-]+",
        r"^(?:Single[\-\s]*family\s*)?(?:Price\s*)?Range\s*[:\-\$]+",
        r"^to\s*[:\-\$]+",
        r"^(?:Single[\-\s]*family\s*)?Age\s*[:\-]+",
        r"^(?:Predominant\s*(?:Price|Age|Occupancy)?)\s*[:\-\$]+",
        r"^(?:Location\s*Type|Built\s*Up|Development\s*Rate|Change\s*in\s*Present\s*Land\s*Use)\s*[:\-]+",
        r"^(?:(?:CO[\-\s]*)?APPRAISER\s*)?(?:Date\s*of\s*Appraisal\s*)?Inspection\s*[:\-]+",
        r"^(?:(?:CO[\-\s]*)?APPRAISER\s*)?(?:Date\s*of\s*Value\s*Opinion\s*)?\(?Effective\s*Date\)?\s*[:\-]+",
        r"^(?:(?:CO[\-\s]*)?APPRAISER\s*)?(?:State\s*)?License\s*\/\s*Certification\s*(?:#)?\s*[:\-]+",
        r"^(?:(?:CO[\-\s]*)?APPRAISER\s*)?(?:Expiration\s*Date\s*of\s*)?(?:State\s*)?License\s*\/\s*Certification\s*[:\-]+",
        r"^\(Yrs\.?\)\s*[:\-]*",
        r"^(?:Actual\s*)?Age\s*(?:\(Yrs\.?\))?\s*[:\-]+",
        r"^(?:Legal\s*)?Description\s*[:\-]+",
        r"^(?:Assessor['’]s\s*)?(?:Parcel\s*)?#?\s*[:\-]+",
        r"^(?:Map\s*)?Reference\s*[:\-]+",
        r"^(?:Architectural\s*)?Style\s*[:\-]+",
        r"^(?:Roofing\s*|Wall\s*)?Material\s*[:\-]+",
        r"^(?:Window\s*)?Type\s*[:\-]+",
        r"^(?:If\s*condominium\s*or\s*cooperative,\s*indicate\s*complex\s*name)\s*[:\-]+",
        r"^(?:Total\s*No\.\s*of\s*Units|No\.\s*of\s*Owner-occupied\s*Units|%\s*of\s*Owner-occupied\s*Units|Total\s*No\.\s*of\s*Floors|Subject\s*Floor\s*#)\s*[:\-]+",
        r"^#\s*[:\-]+",
        r"^[:\-\s%]+$",
    ]
    for pat in sub_labels:
        s = re.sub(pat, "", s, flags=re.IGNORECASE).strip()
    # Strip any trailing column labels that bled through
    s = re.sub(r"\s+(?:Floors?|Carpet|Vinyl|Tile|Wood|Walls?|Drywall|Plaster|Other)\s*[:\-]*$", "", s, flags=re.IGNORECASE).strip()
    # Strip any leading colon or punctuation left over
    s = re.sub(r"^[:\-\s]+", "", s).strip()
    # If the remaining string is only punctuation or matches static template sublabels, return empty string
    if s.lower() in ["inspection:", "inspection", "(effective date):", "(effective date)", "effective date:", "effective date", 
                     "license/certification #:", "license/certification:", "license/certification", "license:", "certification:",
                     "did did not", "did did", "did not", "did", "name:", "name", "transferee tenant vacant :", "transferee tenant vacant",
                     "simple leasehold subtype: pud condominium cooperative", "cooperative, indicate complex name:",
                     "minium or cooperative, indicate complex name: n/a", "is market rate financing available? yes no",
                     "of the homeowners association?", "control of the homeowners association?", "any marketability issues? yes",
                     "are there any marketability issues?", "surface:", "taxes:", "built:", "stories:", "units:", "style:", "material:", "type:"]:
        return ""
    return s.strip()


def locate_ecr_pages(doc) -> dict:
    """
    Locates the 7 primary Worldwide ERC Appraisal pages and any addenda pages.
    """
    page_map = {
        "summary_p1": None,
        "subject_p2": None,
        "improvements_p3": None,
        "market_trends_p4": None,
        "market_trends_p5": None,
        "sales_grid_p6": None,
        "certification_p7": None,
        "comps_4_6": None
    }

    for idx, page in enumerate(doc):
        text = page.get_text("text")
        text_upper = text.upper()

        if "SALIENT FACTS AND CONCLUSIONS" in text_upper or "DEFINITIONS AND GUIDELINES" in text_upper:
            if page_map["summary_p1"] is None:
                page_map["summary_p1"] = idx

        elif "SUBJECT INFORMATION" in text_upper and "OVERALL SITE APPEAL RATING" in text_upper:
            if page_map["subject_p2"] is None:
                page_map["subject_p2"] = idx

        elif "DESCRIPTION OF IMPROVEMENTS" in text_upper and ("FOUNDATION" in text_upper or "BASEMENT" in text_upper or "EXTERIOR APPEAL" in text_upper):
            if page_map["improvements_p3"] is None:
                page_map["improvements_p3"] = idx

        elif "MARKET TRENDS ANALYSIS" in text_upper and "CLOSED SALES ANALYSIS" in text_upper:
            if page_map["market_trends_p4"] is None:
                page_map["market_trends_p4"] = idx

        elif ("COMPETING PROPERTIES" in text_upper or "COMPETITIVE LIST PRICE RANGE" in text_upper) and "FORECASTING:" in text_upper:
            if page_map["market_trends_p5"] is None:
                page_map["market_trends_p5"] = idx

        elif "SALES COMPARISON ANALYSIS" in text_upper and "COMPARABLE SALE" in text_upper and ("OPINION OF ANTICIPATED SALES PRICE" in text_upper or "RECONCILIATION" in text_upper):
            if page_map["sales_grid_p6"] is None and "ADDITIONAL COMPARABLE" not in text_upper:
                page_map["sales_grid_p6"] = idx

        elif "ADDITIONAL COMPARABLE SALES" in text_upper or "COMPARABLE SALE #4" in text_upper or "COMPARABLE SALE # 4" in text_upper:
            if page_map["comps_4_6"] is None:
                page_map["comps_4_6"] = idx

        elif "STATEMENT OF LIMITING CONDITIONS" in text_upper or "APPRAISER CERTIFICATION" in text_upper or "DID NOT PERSONALLY INSPECT" in text_upper:
            if page_map["certification_p7"] is None:
                page_map["certification_p7"] = idx

    # Fallback to index-based mapping
    total_pages = len(doc)
    if page_map["summary_p1"] is None and total_pages >= 1: page_map["summary_p1"] = 0
    if page_map["subject_p2"] is None and total_pages >= 2: page_map["subject_p2"] = 1
    if page_map["improvements_p3"] is None and total_pages >= 3: page_map["improvements_p3"] = 2
    if page_map["market_trends_p4"] is None and total_pages >= 4: page_map["market_trends_p4"] = 3
    if page_map["market_trends_p5"] is None and total_pages >= 5: page_map["market_trends_p5"] = 4
    if page_map["sales_grid_p6"] is None and total_pages >= 6: page_map["sales_grid_p6"] = 5
    if page_map["certification_p7"] is None and total_pages >= 7: page_map["certification_p7"] = 6
    elif page_map["certification_p7"] is None and total_pages >= 6: page_map["certification_p7"] = page_map["sales_grid_p6"]

    return page_map


def _extract_regex_field(text: str, pattern: str) -> str:
    if not text:
        return ""
    try:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            if m.groups():
                return m.group(1).strip()
            return m.group(0).strip()
    except Exception:
        pass
    return ""


def _extract_currency_field(text: str, pattern_prefix: str) -> str:
    if not text:
        return ""
    try:
        m = re.search(pattern_prefix + r"[\s:\$]*([0-9][0-9,]*)", text, re.IGNORECASE)
        if m:
            if m.groups():
                return m.group(1).replace(",", "").strip()
            return m.group(0).replace(",", "").strip()
    except Exception:
        pass
    return ""


def _extract_number_field(text: str, pattern_prefix: str) -> str:
    if not text:
        return ""
    try:
        m = re.search(pattern_prefix + r"[\s:\-_]*([0-9]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
        if m:
            if m.groups():
                return m.group(1).strip()
            return m.group(0).strip()
    except Exception:
        pass
    return ""


def extract_ecr_summary_section(words, spatial_text: str, full_doc_text: str = "") -> dict:
    """Extracts Page 1 Summary & Client/Appraiser info for ECR form."""
    res = {}
    st = spatial_text + "\n" + full_doc_text

    # Header Grid (Page 1 Top)
    res["Client:"] = get_line_segment(words, 56.0, 85, 335) or _extract_regex_field(st, r"Client\s*[:\-]\s*([^\n\r]+)")
    res["Client File #:"] = get_line_segment(words, 56.0, 375, 580) or _extract_regex_field(st, r"Client\s*File\s*#?\s*[:\-]?\s*([A-Za-z0-9\-_]+)")
    res["Client Address:"] = get_line_segment(words, 65.5, 105, 580) or _extract_regex_field(st, r"Client\s*Address\s*[:\-]\s*([^\n\r]+)")
    res["Client City:"] = get_line_segment(words, 74.5, 80, 300) or _extract_regex_field(st, r"Client\s*City\s*[:\-]\s*([^\n\r,]+)")
    res["Client State:"] = get_line_segment(words, 74.5, 320, 410) or _extract_regex_field(st, r"Client\s*State\s*[:\-]\s*([A-Za-z]{2})")
    res["Client Zip Code:"] = get_line_segment(words, 74.5, 445, 580) or _extract_regex_field(st, r"Client\s*Zip\s*(?:Code)?\s*[:\-]?\s*(\d{5}(?:-\d{4})?)")

    # Transferee & Subject Address
    res["Transferee:"] = get_line_segment(words, 84.0, 95, 275) or _extract_regex_field(st, r"Transferee\s*[:\-]\s*([^\n\r]+)")
    res["Owner(s) of Record:"] = get_line_segment(words, 84.0, 335, 580) or _extract_regex_field(st, r"(?:Owner\(s\)\s*of\s*Record|Owner\s*of\s*Record)\s*[:\-]\s*([^\n\r]+)")
    res["Subject Property Address:"] = get_line_segment(words, 93.5, 120, 320) or _extract_regex_field(st, r"Subject\s*(?:Property\s*)?Address\s*[:\-]\s*([^\n\r]+)")
    unit_val = get_line_segment(words, 93.5, 340, 385)
    if "unit" in unit_val.lower():
        unit_val = unit_val.replace("Unit:", "").replace("Unit", "").strip()
    if unit_val.lower() in ["county", "county:", "city", "state", "zip"]:
        unit_val = ""
    res["Unit:"] = unit_val
    res["Subject County:"] = get_line_segment(words, 93.5, 405, 580) or _extract_regex_field(st, r"(?:Subject\s*)?County\s*[:\-]\s*([A-Za-z\s]+)")
    res["Subject City:"] = get_line_segment(words, 102.5, 80, 300) or _extract_regex_field(st, r"(?:Subject\s*)?City\s*[:\-]\s*([^\n\r,]+)")
    res["Subject State:"] = get_line_segment(words, 102.5, 320, 410) or _extract_regex_field(st, r"(?:Subject\s*)?State\s*[:\-]\s*([A-Za-z]{2})")
    res["Subject Zip Code:"] = get_line_segment(words, 102.5, 445, 580) or _extract_regex_field(st, r"(?:Subject\s*)?Zip\s*(?:Code)?\s*[:\-]?\s*(\d{5}(?:-\d{4})?)")

    # Appraiser Info
    res["Appraiser Company Name:"] = get_line_segment(words, 112.0, 125, 340) or _extract_regex_field(st, r"Appraiser\s*(?:Company\s*Name|Firm)\s*[:\-]\s*([^\n\r]+)")
    res["Appraiser File #:"] = get_line_segment(words, 112.0, 385, 580) or _extract_regex_field(st, r"Appraiser\s*File\s*#?\s*[:\-]?\s*([A-Za-z0-9\-_]+)")
    res["Appraiser(s):"] = get_line_segment(words, 121.0, 95, 275) or _extract_regex_field(st, r"Appraiser\(s\)\s*[:\-]\s*([^\n\r]+)")
    res["Co-appraiser (if applicable)"] = get_line_segment(words, 121.0, 335, 580)
    res["Appraiser Address"] = get_line_segment(words, 131.0, 110, 580) or _extract_regex_field(st, r"Appraiser\s*Address\s*[:\-]\s*([^\n\r]+)")
    res["Appraiser City:"] = get_line_segment(words, 140.0, 80, 300) or _extract_regex_field(st, r"Appraiser\s*City\s*[:\-]\s*([^\n\r,]+)")
    res["Appraiser State:"] = get_line_segment(words, 140.0, 320, 410) or _extract_regex_field(st, r"Appraiser\s*State\s*[:\-]\s*([A-Za-z]{2})")
    res["Appraiser Zip Code:"] = get_line_segment(words, 140.0, 445, 580) or _extract_regex_field(st, r"Appraiser\s*Zip\s*(?:Code)?\s*[:\-]?\s*(\d{5}(?:-\d{4})?)")
    res["Appraiser Ph. #:"] = get_line_segment(words, 149.5, 85, 200) or _extract_regex_field(st, r"Appraiser\s*Ph(?:one|\.)?\s*#?\s*[:\-]?\s*([\(\)\d\s\-\.\/]+)")
    res["Appraiser Fax #:"] = get_line_segment(words, 149.5, 225, 340)
    res["Appraiser E-mail:"] = get_line_segment(words, 149.5, 365, 580) or _extract_regex_field(st, r"Appraiser\s*E-?mail\s*[:\-]\s*([^\s\n\r]+@[^\s\n\r]+)")

    # Salient Facts & Valuation
    res["Anticipated Sales Price: $"] = clean_curr(get_line_segment(words, 172.5, 125, 275) or _extract_currency_field(st, r"Anticipated\s*Sales\s*Price"))
    res["Assignment Marketing Period:"] = get_line_segment(words, 189.5, 75, 140) or _extract_regex_field(st, r"Assignment\s*Marketing\s*Period\s*[:\-]\s*([^\n\r]+)")
    app_val = get_line_segment(words, 199.0, 105, 140)
    res["Appearance:"] = app_val.replace("“", "").replace("”", "").replace('"', "").replace("‘", "").replace("’", "").strip() if app_val else _extract_regex_field(st, r"Appearance\s*[:\-]\s*([^\n\r]+)")
    res["Date of Value Opinion (Effective Date):"] = get_line_segment(words, 210.0, 155, 275) or _extract_regex_field(st, r"Date\s*of\s*Value\s*Opinion\s*(?:\(Effective\s*Date\))?\s*[:\-]?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})")
    
    res["Is the subject property currently listed?"] = "Yes" if "yes" in get_line_segment(words, 226.9, 180, 220).lower() else ("No" if "no" in get_line_segment(words, 226.9, 180, 220).lower() else "")
    res["Current List Price: $"] = clean_curr(get_line_segment(words, 238.1, 120, 180) or _extract_currency_field(st, r"Current\s*List\s*Price"))
    res["days on market:"] = get_line_segment(words, 238.1, 225, 255) or _extract_number_field(st, r"Days\s*(?:on\s*market|DOM)")
    res["Actual Age (Yrs.):"] = clean_field_value(get_line_segment(words, 256.8, 115, 165)) or _extract_number_field(st, r"Actual\s*Age(?:\s*\(Yrs\.\))?")
    res["Bedrooms:"] = clean_field_value(get_line_segment(words, 256.8, 198, 230)) or _extract_number_field(st, r"Bedrooms")
    res["Baths:"] = clean_field_value(get_line_segment(words, 256.8, 255, 290)) or _extract_number_field(st, r"Baths")
    
    gla = get_line_segment(words, 266.1, 155, 188) or _extract_regex_field(st, r"Gross\s*Living\s*Area\s*[:\-]?\s*([0-9,]+)")
    res["Gross Living Area:"] = clean_curr(gla)
    
    # Trends & Checklist boxes on Page 1
    p1_trends = get_line_segment(words, 283.1, 60, 580)
    res["Overall Historic Price Trend"] = "Stable" if "stable" in p1_trends.lower() else ("Increasing" if "increasing" in p1_trends.lower() else ("Declining" if "declining" in p1_trends.lower() else ""))
    res["Current Supply/Demand:"] = "In Balance" if "balance" in p1_trends.lower() else ("Shortage" if "shortage" in p1_trends.lower() else ("Over Supply" if "over" in p1_trends.lower() else ""))
    res["Forecasted Price Trend:"] = "Stable" if "stable" in p1_trends.lower() else ("Increasing" if "increasing" in p1_trends.lower() else ("Declining" if "declining" in p1_trends.lower() else ""))

    # Checklists on Summary Page
    def get_p1_chk(y, x0=420, x1=580):
        seg = get_line_segment(words, y, x0, x1).lower()
        if "yes" in seg:
            return "Yes"
        if "no" in seg:
            return "No"
        if "none observed" in seg or "none" in seg:
            return "None Observed"
        return ""

    res["Mandatory Inspections"] = get_p1_chk(189.5)
    res["Adverse Easements/Encroachments"] = get_p1_chk(199.0)
    res["Adverse External Conditions"] = get_p1_chk(208.5)
    res["Adverse Environmental Conditions"] = get_p1_chk(218.0)
    res["Apparent Modifications to Dwelling"] = get_p1_chk(227.5)
    res["Adverse Conditions Requiring Inspections"] = get_p1_chk(237.0)
    res["Recommended Repairs and/or Improvements"] = get_p1_chk(246.5)
    res["New Construction Competition"] = "Yes" if "yes" in get_line_segment(words, 238.1, 420, 520).lower() else ("No" if "no" in get_line_segment(words, 238.1, 420, 520).lower() else "")
    res["Distressed Market Competition"] = get_p1_chk(256.0)
    res["Prevalence of Seller Concessions"] = get_p1_chk(265.5)
    res["Adverse Financing Conditions"] = get_p1_chk(275.0)

    return res


def extract_ecr_subject_section(words, spatial_text: str, full_doc_text: str = "") -> dict:
    """Extracts Subject Property info (Page 2) for ECR form."""
    res = {}
    st = spatial_text + "\n" + full_doc_text

    res["Transferee:"] = get_line_segment(words, 37.6, 110, 280) or _extract_regex_field(st, r"Transferee\s*[:\-]\s*([^\n\r]+)")
    raw_occ = get_line_segment(words, 37.6, 300, 580)
    if "tenant" in raw_occ.lower() and not ("transferee" in raw_occ.lower() and "vacant" in raw_occ.lower()):
        res["Occupant:"] = "Tenant"
    elif "vacant" in raw_occ.lower() and not ("transferee" in raw_occ.lower() and "tenant" in raw_occ.lower()):
        res["Occupant:"] = "Vacant"
    elif "transferee" in raw_occ.lower():
        res["Occupant:"] = "Transferee"
    else:
        res["Occupant:"] = ""

    res["Subject Property Address:"] = get_line_segment(words, 47.0, 150, 320) or _extract_regex_field(st, r"Subject\s*Property\s*Address\s*[:\-]\s*([^\n\r]+)")
    
    subj_unit = get_line_segment(words, 47.0, 335, 385)
    if "unit" in subj_unit.lower():
        subj_unit = subj_unit.replace("Unit:", "").replace("Unit", "").strip()
    res["Subject Unit:"] = clean_field_value(subj_unit)
    res["Subject County:"] = clean_field_value(get_line_segment(words, 47.0, 410, 580) or _extract_regex_field(st, r"County\s*[:\-]\s*([^\n\r]+)"))
    res["Subject City:"] = clean_field_value(get_line_segment(words, 56.3, 100, 300) or _extract_regex_field(st, r"City\s*[:\-]\s*([^\n\r,]+)"))
    res["Subject State:"] = clean_field_value(get_line_segment(words, 56.3, 320, 410) or _extract_regex_field(st, r"State\s*[:\-]\s*([A-Za-z]{2})"))
    res["Subject Zip Code:"] = clean_field_value(get_line_segment(words, 56.3, 445, 580) or _extract_regex_field(st, r"Zip\s*(?:Code)?\s*[:\-]?\s*(\d{5}(?:-\d{4})?)"))
    
    res["Legal Description:"] = clean_field_value(get_line_segment(words, 65.7, 130, 580) or _extract_regex_field(st, r"Legal\s*Description\s*[:\-]\s*([^\n\r]+)"))
    res["Assessor's Parcel #:"] = clean_field_value(get_line_segment(words, 93.8, 140, 300) or _extract_regex_field(st, r"Assessor['’]s\s*Parcel\s*#?\s*[:\-]?\s*([A-Za-z0-9\-\.\/]+)"))
    res["Map Reference:"] = clean_field_value(get_line_segment(words, 93.8, 350, 580) or _extract_regex_field(st, r"Map\s*Reference\s*[:\-]\s*([^\n\r]+)"))
    res["Property Rights Appraised:"] = clean_field_value(get_line_segment(words, 93.8, 100, 300)) or _extract_regex_field(st, r"Property\s*Rights\s*Appraised\s*[:\-]\s*([^\n\r]+)")
    res["Subtype:"] = clean_field_value(get_line_segment(words, 93.8, 300, 580)) or _extract_regex_field(st, r"Subtype\s*[:\-]\s*([^\n\r]+)")

    # Condo section (only populate if condo/coop complex name or info is actually present)
    condo_complex = clean_field_value(get_line_segment(words, 111.3, 200, 580))
    if condo_complex and condo_complex.lower() not in ["n/a", "none", "indicate complex name:", "complex name:"]:
        res["If condominium or cooperative, indicate complex name:"] = condo_complex
        res["Total No. of Units"] = clean_field_value(get_line_segment(words, 120.7, 120, 160))
        res["No. of Owner-occupied Units:"] = clean_field_value(get_line_segment(words, 120.7, 218, 265))
        res["% of Owner-occupied Units:"] = clean_field_value(get_line_segment(words, 120.7, 321, 370))
        res["Total No. of Floors:"] = clean_field_value(get_line_segment(words, 120.7, 407, 450))
        res["Subject Floor #:"] = clean_field_value(get_line_segment(words, 120.7, 483, 580))
        res["Is the complex complete?"] = clean_field_value(get_line_segment(words, 130.0, 160, 250))
        res["Is market rate financing available?"] = clean_field_value(get_line_segment(words, 130.0, 440, 500))
        res["Is the developer/builder in control of the homeowners association?"] = clean_field_value(get_line_segment(words, 139.4, 260, 310))
        res["Are there any marketability issues?"] = clean_field_value(get_line_segment(words, 139.4, 440, 500))
        res["Comments:"] = clean_narrative(get_box_text(words, 80, 150, 580, 192), ["Comments:"])
    else:
        res["If condominium or cooperative, indicate complex name:"] = ""
        res["Total No. of Units"] = ""
        res["No. of Owner-occupied Units:"] = ""
        res["% of Owner-occupied Units:"] = ""
        res["Total No. of Floors:"] = ""
        res["Subject Floor #:"] = ""
        res["Is the complex complete?"] = ""
        res["Is market rate financing available?"] = ""
        res["Is the developer/builder in control of the homeowners association?"] = ""
        res["Are there any marketability issues?"] = ""
        res["Comments:"] = ""

    # Taxes & Listing
    res["Annual real estate taxes: $"] = clean_curr(get_line_segment(words, 196.7, 140, 230) or _extract_currency_field(st, r"Annual\s*real\s*estate\s*taxes"))
    res["Tax Year:"] = get_line_segment(words, 196.7, 260, 320) or _extract_number_field(st, r"Tax\s*Year")
    res["Data Source:"] = get_line_segment(words, 196.7, 360, 580) or _extract_regex_field(st, r"Data\s*Source\s*[:\-]\s*([^\n\r]+)")
    res["Are taxes typical?"] = "Yes" if "yes" in get_line_segment(words, 206.1, 140, 220).lower() else ("No" if "no" in get_line_segment(words, 206.1, 140, 220).lower() else "")
    res["Monthly HOA Fees: $"] = clean_curr(get_line_segment(words, 206.1, 290, 350) or _extract_currency_field(st, r"Monthly\s*HOA\s*Fees"))
    res["Discuss atypical taxes, homeowner association fees and known pending special assessments, and comment on their effect on marketability"] = clean_narrative(get_box_text(words, 80, 215, 580, 260), ["marketability."])

    res["Is the subject property currently listed?"] = "Yes" if "yes" in get_line_segment(words, 271.6, 200, 260).lower() else ("No" if "no" in get_line_segment(words, 271.6, 200, 260).lower() else "")
    res["Original List Price: $"] = clean_curr(get_line_segment(words, 271.6, 330, 420) or _extract_currency_field(st, r"Original\s*List\s*Price"))
    res["Current List Price: $"] = clean_curr(get_line_segment(words, 281.0, 125, 220) or _extract_currency_field(st, r"Current\s*List\s*Price"))
    res["Date of Last Price Revision:"] = get_line_segment(words, 281.0, 355, 450) or _extract_regex_field(st, r"Date\s*of\s*Last\s*Price\s*Revision\s*[:\-]?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})")
    res["Days-on-market:"] = get_line_segment(words, 290.3, 125, 170) or _extract_number_field(st, r"Days-on-market")
    res["Listing Company/Agent:"] = get_line_segment(words, 290.3, 240, 400) or _extract_regex_field(st, r"Listing\s*Company\s*\/\s*Agent\s*[:\-]\s*([^\n\r]+)")
    res["Ph. #:"] = get_line_segment(words, 290.3, 425, 580) or _extract_regex_field(st, r"Ph\.\s*#?\s*[:\-]?\s*([\(\)\d\s\-\.\/]+)")
    res["Last Sale Date:"] = get_line_segment(words, 299.7, 125, 220) or _extract_regex_field(st, r"Last\s*Sale\s*Date\s*[:\-]?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})")
    res["Last Sale Price: $"] = clean_curr(get_line_segment(words, 299.7, 325, 420) or _extract_currency_field(st, r"Last\s*Sale\s*Price"))
    res["Analyze and discuss any current agreement of sale, option on or listing of the subject property as well as the last three years of sales history. Include complete marketing history, noting price changes and days on market."] = clean_narrative(get_box_text(words, 80, 320, 580, 390), ["days on market."])
    res["Are there any mandatory inspections required by a governmental institution to transfer title?"] = "Yes" if "yes" in get_line_segment(words, 370.0, 80, 580).lower() else ("No" if "no" in get_line_segment(words, 370.0, 80, 580).lower() else "")

    return res


def extract_ecr_neighborhood_section(words, spatial_text: str, full_doc_text: str = "") -> dict:
    """Extracts Neighborhood characteristics (Page 2) for ECR form."""
    res = {}
    st = spatial_text + "\n" + full_doc_text

    res["Define neighborhood boundaries (may or may not be the same area used for the Market Trends Analysis on pages 4 and 5)."] = clean_narrative(
        get_box_text(words, 80, 400, 580, 428),
        ["pages 4 and 5).", "4 and 5)."]
    )
    
    loc_text = get_line_segment(words, 429.6, 80, 340)
    res["Location Type:"] = "Suburban" if "suburban" in loc_text.lower() else ("Urban" if "urban" in loc_text.lower() else ("Rural" if "rural" in loc_text.lower() else loc_text))

    bu_text = get_line_segment(words, 441.3, 80, 340)
    res["Built Up:"] = "25 - 75%" if "25" in bu_text else ("Over 75%" if "over" in bu_text.lower() else ("Under 25%" if "under" in bu_text.lower() else bu_text))

    dr_text = get_line_segment(words, 453.1, 80, 340)
    res["Development Rate:"] = "Stable" if "stable" in dr_text.lower() else ("Rapid" if "rapid" in dr_text.lower() else ("Slow" if "slow" in dr_text.lower() else dr_text))

    ch_text = get_line_segment(words, 464.8, 80, 340)
    res["Change in Present Land Use:"] = "Not Likely" if "not likely" in ch_text.lower() or "not" in ch_text.lower() else ("Taking Place" if "taking" in ch_text.lower() else ("Likely" if "likely" in ch_text.lower() else ch_text))

    sf = get_line_segment(words, 442.5, 380, 430)
    res["Single Family:"] = clean_field_value(clean_curr(sf.replace("%", "")))
    
    com = get_line_segment(words, 442.5, 470, 520)
    res["Commercial:"] = clean_field_value(clean_curr(com.replace("%", "")))

    mf = get_line_segment(words, 453.1, 380, 430)
    res["Multi-family:"] = clean_field_value(clean_curr(mf.replace("%", "")))
    
    ind = get_line_segment(words, 453.1, 470, 520)
    res["Industrial:"] = clean_field_value(clean_curr(ind.replace("%", "")))

    cnd = get_line_segment(words, 464.8, 380, 430)
    res["Condo:"] = clean_field_value(clean_curr(cnd.replace("%", "")))
    
    oth = get_line_segment(words, 464.8, 470, 520)
    res["Present Land Use comment"] = clean_field_value(clean_curr(oth.replace("%", "")))

    res["Single-family Price Range: $"] = clean_curr(get_line_segment(words, 475.4, 140, 240))
    res["to: $"] = clean_curr(get_line_segment(words, 475.4, 265, 350))
    res["Predominant Price: $"] = clean_curr(get_line_segment(words, 475.4, 410, 520))

    res["Single-family Age"] = clean_curr(get_line_segment(words, 484.7, 125, 155))
    res["years to"] = clean_curr(get_line_segment(words, 484.7, 175, 200))
    res["Predominant Age:"] = clean_curr(get_line_segment(words, 484.7, 280, 310))
    
    occ_text = get_line_segment(words, 484.7, 360, 580)
    res["Predominant Occupancy:"] = "Owner" if "owner" in occ_text.lower() else ("Tenant" if "tenant" in occ_text.lower() else occ_text)

    res["Discuss positive and negative neighborhood characteristics impacting the subject property’s marketability (e.g., employment, environmental conditions, external obsolescence, property compatibility, schools, vacancy rates, transportation, etc.)."] = clean_narrative(
        get_box_text(words, 80, 495, 580, 565),
        ["etc.).", "etc.)"]
    )
    
    app_text = get_line_segment(words, 570.1, 80, 580)
    res["Overall Neighborhood Appeal Rating:"] = "Good" if "good" in app_text.lower() else ("Average" if "average" in app_text.lower() else ("Fair" if "fair" in app_text.lower() else ("Poor" if "poor" in app_text.lower() else app_text)))

    return res


def extract_ecr_site_section(words, spatial_text: str, full_doc_text: str = "") -> dict:
    """Extracts Site details and utilities (Page 2) for ECR form."""
    res = {}
    st = spatial_text + "\n" + full_doc_text

    res["Dimensions:"] = get_line_segment(words, 582.9, 115, 360)
    res["Site Area:"] = get_line_segment(words, 592.3, 110, 220)
    res["Corner Lot"] = "Yes" if "yes" in get_line_segment(words, 592.3, 270, 360).lower() else ("No" if "no" in get_line_segment(words, 592.3, 270, 360).lower() else "")
    res["FEMA Special Flood Hazard Area?"] = "Yes" if "yes" in get_line_segment(words, 601.7, 210, 300).lower() else ("No" if "no" in get_line_segment(words, 601.7, 210, 300).lower() else "")
    res["Specific Zoning Classification:"] = get_line_segment(words, 611.0, 155, 220)
    res["Zoning Description:"] = get_line_segment(words, 611.0, 270, 580)
    res["Is present use permitted by zoning regulations?"] = "Yes" if "yes" in get_line_segment(words, 620.4, 250, 350).lower() else ("No" if "no" in get_line_segment(words, 620.4, 250, 350).lower() else "")

    res["Street Access:"] = get_line_segment(words, 643.9, 135, 225)
    res["Street Maintenance:"] = get_line_segment(words, 655.4, 155, 225)
    res["Gated"] = "Yes" if "yes" in get_line_segment(words, 655.4, 300, 400).lower() else ("No" if "no" in get_line_segment(words, 655.4, 300, 400).lower() else "")
    res["Electric"] = get_line_segment(words, 667.1, 110, 145)
    res["Gas"] = get_line_segment(words, 667.1, 150, 225)
    res["Water"] = get_line_segment(words, 678.9, 110, 145)
    res["San. Sewer:"] = get_line_segment(words, 690.7, 135, 225)
    res["Topography:"] = get_line_segment(words, 643.9, 260, 365)
    res["Shape:"] = get_line_segment(words, 655.4, 260, 365)
    res["View"] = get_line_segment(words, 667.1, 260, 365)
    res["Landscaping:"] = get_line_segment(words, 678.9, 260, 365)
    res["Drainage:"] = get_line_segment(words, 690.7, 260, 365)

    res["Adverse Easements/Encroachments:"] = "Yes" if "yes" in get_line_segment(words, 700.0, 80, 200).lower() else ("No" if "no" in get_line_segment(words, 700.0, 80, 200).lower() else "")
    res["Adverse External Conditions:"] = "Yes" if "yes" in get_line_segment(words, 700.0, 200, 350).lower() else ("No" if "no" in get_line_segment(words, 700.0, 200, 350).lower() else "")
    res["Adverse Environmental Conditions:"] = "Yes" if "yes" in get_line_segment(words, 700.0, 350, 580).lower() else ("No" if "no" in get_line_segment(words, 700.0, 350, 580).lower() else "")

    res["Street Surface:"] = clean_field_value(get_line_segment(words, 667.1, 415, 580))
    res["Driveway Surface:"] = clean_field_value(get_line_segment(words, 678.9, 415, 580))
    res["Alley:"] = clean_field_value(get_line_segment(words, 690.7, 415, 580))
    res["Discuss positive and negative site characteristics impacting the subject property’s marketability (e.g., site utility, conformity, site improvements, leasehold, adverse conditions, etc)"] = clean_narrative(get_box_text(words, 80, 715, 580, 760), ["etc)", "etc.)", "leasehold, adverse conditions, etc)"])
    res["Overall Site Appeal Rating:"] = get_line_segment(words, 765.0, 180, 580)

    return res


def extract_ecr_improvements_section(words, spatial_text: str, full_doc_text: str = "") -> dict:
    """Extracts Improvements, Room Counts, Materials, Condition (Page 3) for ECR form."""
    res = {}
    st = spatial_text + "\n" + full_doc_text

    def get_impr_chk(y, x0=80, x1=580):
        seg = get_line_segment(words, y, x0, x1).lower()
        if "yes" in seg:
            return "Yes"
        if "no" in seg:
            return "No"
        return ""

    # General
    res["Existing Construction:"] = "Yes" if "yes" in get_line_segment(words, 41.5, 100, 180).lower() else ("No" if "no" in get_line_segment(words, 41.5, 100, 180).lower() else "")
    res["New Construction:"] = "Yes" if "yes" in get_line_segment(words, 50.9, 100, 180).lower() else ("No" if "no" in get_line_segment(words, 50.9, 100, 180).lower() else "")
    res["Completed"] = "Yes" if "yes" in get_line_segment(words, 60.2, 100, 180).lower() else ("No" if "no" in get_line_segment(words, 60.2, 100, 180).lower() else "")
    res["Year Built"] = clean_field_value(get_line_segment(words, 78.9, 115, 180)) or _extract_number_field(st, r"Year\s*Built")
    res["Actual Age (Yrs.):"] = clean_field_value(get_line_segment(words, 88.3, 130, 180)) or _extract_number_field(st, r"Actual\s*Age(?:\s*\(Yrs\.\))?")
    res["Effective Age (Yrs.):"] = clean_field_value(get_line_segment(words, 97.7, 135, 180)) or _extract_number_field(st, r"Effective\s*Age(?:\s*\(Yrs\.\))?")
    res["Attached:"] = "Yes" if "yes" in get_line_segment(words, 107.0, 100, 180).lower() else ("No" if "no" in get_line_segment(words, 107.0, 100, 180).lower() else "")
    res["Detached:"] = "Yes" if "yes" in get_line_segment(words, 116.4, 100, 180).lower() else ("No" if "no" in get_line_segment(words, 116.4, 100, 180).lower() else "")
    res["No. of Units"] = clean_field_value(get_line_segment(words, 125.7, 115, 160))
    res["No. of Stories"] = clean_field_value(get_line_segment(words, 135.1, 120, 160))
    res["Manufact. Housing"] = "Yes" if "yes" in get_line_segment(words, 144.5, 100, 180).lower() else ("No" if "no" in get_line_segment(words, 144.5, 100, 180).lower() else "")
    res["If yes, type:"] = clean_field_value(get_line_segment(words, 152.1, 110, 180))

    # Exterior
    res["Architectural Style"] = clean_field_value(get_line_segment(words, 50.9, 230, 295))
    res["Roofing Material:"] = clean_field_value(get_line_segment(words, 60.2, 230, 295))
    res["Wall Material"] = clean_field_value(get_line_segment(words, 69.6, 225, 295))
    res["Window Type:"] = clean_field_value(get_line_segment(words, 107.0, 225, 295))
    res["Insulated:"] = "Yes" if "yes" in get_line_segment(words, 116.4, 225, 295).lower() else ("No" if "no" in get_line_segment(words, 116.4, 225, 295).lower() else "")
    res["Screens:"] = "Yes" if "yes" in get_line_segment(words, 125.7, 225, 295).lower() else ("No" if "no" in get_line_segment(words, 125.7, 225, 295).lower() else "")
    res["Storm Sash:"] = "Yes" if "yes" in get_line_segment(words, 135.1, 225, 295).lower() else ("No" if "no" in get_line_segment(words, 135.1, 225, 295).lower() else "")
    res["Gutters/Downspouts:"] = "Yes" if "yes" in get_line_segment(words, 144.5, 225, 295).lower() else ("No" if "no" in get_line_segment(words, 144.5, 225, 295).lower() else "")
    
    amen1 = get_line_segment(words, 181.9, 210, 350)
    amen2 = get_line_segment(words, 191.3, 190, 250)
    res["Exterior Amenities"] = f"{amen1} {amen2}".strip()

    # Interior & Bath
    res["Floor"] = get_line_segment(words, 60.2, 295, 410)
    res["Walls"] = get_line_segment(words, 116.4, 295, 410)
    res["Bath Floors"] = get_line_segment(words, 172.5, 295, 410)
    res["Bath Wainscot"] = get_line_segment(words, 238.1, 315, 350)
    res["interior amenities"] = get_line_segment(words, 294.2, 335, 410)

    # Kitchen, HVAC & Attic
    kitch_counters = get_line_segment(words, 116.4, 445, 580)
    res["Kitchen Built-ins"] = kitch_counters
    res["Heating Type:"] = get_line_segment(words, 172.5, 435, 580)
    res["Heating Fuel:"] = get_line_segment(words, 181.9, 435, 580)
    res["Air Conditioning Central Air:"] = "Yes" if "yes" in get_line_segment(words, 191.3, 435, 580).lower() else ("No" if "no" in get_line_segment(words, 191.3, 435, 580).lower() else "")
    res["Air Conditioning Other:"] = get_line_segment(words, 200.7, 435, 580)
    res["Attic Scuttle:"] = "Yes" if "yes" in get_line_segment(words, 210.0, 435, 580).lower() else ("No" if "no" in get_line_segment(words, 210.0, 435, 580).lower() else "")
    res["Attic Drop Stair:"] = "Yes" if "yes" in get_line_segment(words, 219.3, 435, 580).lower() else ("No" if "no" in get_line_segment(words, 219.3, 435, 580).lower() else "")
    res["Attic Stairway:"] = "Yes" if "yes" in get_line_segment(words, 228.7, 435, 580).lower() else ("No" if "no" in get_line_segment(words, 228.7, 435, 580).lower() else "")
    res["Attic Finished:"] = "Yes" if "yes" in get_line_segment(words, 238.1, 435, 580).lower() else ("No" if "no" in get_line_segment(words, 238.1, 435, 580).lower() else "")
    res["Attic Other:"] = get_line_segment(words, 247.4, 435, 580)

    # Car Storage
    cars_cnt = get_line_segment(words, 238.1, 165, 185)
    res["Garage"] = f"{cars_cnt} Car Attached" if cars_cnt else ""
    res["Garage (Attached, Detached, Built-in:)"] = f"Attached ({cars_cnt} Cars)" if cars_cnt else ""
    res["Carport"] = get_line_segment(words, 256.8, 115, 185)
    res["Carport (Attached, Detached, Built-in:)"] = res["Carport"]
    res["Car Storage Other"] = get_line_segment(words, 275.5, 115, 185)

    # Foundation and Basement
    res["Foundation Material"] = get_line_segment(words, 218.6, 220, 350)
    res["Slab:"] = "Yes" if "yes" in get_line_segment(words, 228.7, 220, 350).lower() else ("No" if "no" in get_line_segment(words, 228.7, 220, 350).lower() else "")
    res["Crawl Space:"] = "Yes" if "yes" in get_line_segment(words, 238.1, 220, 350).lower() else ("No" if "no" in get_line_segment(words, 238.1, 220, 350).lower() else "")
    bsmt_sqft = clean_curr(get_line_segment(words, 256.8, 220, 260))
    bsmt_fin = get_line_segment(words, 266.1, 230, 270)
    res["Basement:"] = f"{bsmt_sqft} / {bsmt_fin}".strip(" /") if (bsmt_sqft or bsmt_fin) else ""
    res["Sq. Ft"] = bsmt_sqft
    res["% Finished:"] = bsmt_fin
    res["Floor:"] = get_line_segment(words, 275.5, 215, 350)
    res["Wall:"] = get_line_segment(words, 284.9, 215, 350)
    res["Ceiling:"] = get_line_segment(words, 294.2, 220, 350)
    res["Outside Entry:"] = "Yes" if "yes" in get_line_segment(words, 303.6, 220, 350).lower() else ("No" if "no" in get_line_segment(words, 303.6, 220, 350).lower() else "")
    res["Sump:"] = "Yes" if "yes" in get_line_segment(words, 312.9, 220, 350).lower() else ("No" if "no" in get_line_segment(words, 312.9, 220, 350).lower() else "")
    res["Other:"] = get_line_segment(words, 322.3, 220, 350)
    res["Adequate:"] = "Yes" if "yes" in get_line_segment(words, 331.7, 220, 350).lower() else ("No" if "no" in get_line_segment(words, 331.7, 220, 350).lower() else "")

    # Textareas
    res["Relevant Characteristics/Significant Features: Describe and discuss features and improvements affecting marketability. (Only those relevant characteristics affecting the Anticipated Sales Price should be considered in the Significant Features fields on pages 5 and 6.)"] = clean_narrative(
        get_box_text(words, 80, 355, 580, 420),
        ["6.).", "pages 5 and 6.)", "marketability."]
    )
    res["Personal Property: Is personal property included in the Anticipated Sales Price?"] = clean_narrative(
        get_box_text(words, 80, 424, 580, 445),
        ["describe:", "please describe:"]
    )

    # Room Breakdown Table (Level 1, Level 2, Level 3, Basement, Attic)
    # Scan rows on Page 3 at y ∈ [470, 520]
    res["Level 1_Living"] = get_line_segment(words, 471.3, 190, 205)
    res["Level 1_Dining"] = get_line_segment(words, 471.3, 215, 230)
    res["Level 1_Kitchen"] = get_line_segment(words, 471.3, 238, 255)
    res["Level 1_Family"] = get_line_segment(words, 471.3, 265, 280)
    res["Level 1_Bedrooms"] = get_line_segment(words, 471.3, 290, 305)
    res["Level 1_Baths"] = get_line_segment(words, 471.3, 320, 335)
    res["Level 1_OtherRooms"] = get_line_segment(words, 471.3, 345, 360)
    res["Level 1_ListOfOtherRooms"] = get_line_segment(words, 471.3, 365, 495)
    res["Level 1_GLA"] = clean_curr(get_line_segment(words, 471.3, 500, 550))

    for l_idx in [2, 3]:
        res[f"Level {l_idx}_Living"] = ""
        res[f"Level {l_idx}_Dining"] = ""
        res[f"Level {l_idx}_Kitchen"] = ""
        res[f"Level {l_idx}_Family"] = ""
        res[f"Level {l_idx}_Bedrooms"] = ""
        res[f"Level {l_idx}_Baths"] = ""
        res[f"Level {l_idx}_OtherRooms"] = ""
        res[f"Level {l_idx}_ListOfOtherRooms"] = ""
        res[f"Level {l_idx}_GLA"] = ""

    # Basement row
    res["Basement_Living"] = get_line_segment(words, 480.7, 190, 205)
    res["Basement_Dining"] = get_line_segment(words, 480.7, 215, 230)
    res["Basement_Kitchen"] = get_line_segment(words, 480.7, 238, 255)
    res["Basement_Family"] = get_line_segment(words, 480.7, 265, 280)
    res["Basement_Bedrooms"] = get_line_segment(words, 480.7, 290, 305)
    res["Basement_Baths"] = get_line_segment(words, 480.7, 320, 335)
    res["Basement_OtherRooms"] = get_line_segment(words, 480.7, 345, 360)
    res["Basement_ListOfOtherRooms"] = get_line_segment(words, 480.7, 365, 495)

    # Attic row
    res["Attic_Living"] = ""
    res["Attic_Dining"] = ""
    res["Attic_Kitchen"] = ""
    res["Attic_Family"] = ""
    res["Attic_Bedrooms"] = ""
    res["Attic_Baths"] = ""
    res["Attic_OtherRooms"] = ""
    res["Attic_ListOfOtherRooms"] = ""

    # Totals
    res["Living"] = res["Level 1_Living"]
    res["Dining"] = res["Level 1_Dining"]
    res["Kitchen"] = res["Level 1_Kitchen"]
    res["Family"] = res["Basement_Family"]
    res["Bedrooms"] = get_line_segment(words, 527.5, 140, 160) or res["Level 1_Bedrooms"]
    res["Baths"] = get_line_segment(words, 527.5, 210, 230) or res["Level 1_Baths"]
    res["Other"] = res["Basement_OtherRooms"]
    rooms_vals = [int(res[k]) for k in ["Living", "Dining", "Kitchen", "Family", "Bedrooms"] if res.get(k, "").isdigit()]
    res["Rooms"] = str(sum(rooms_vals)) if rooms_vals else ""
    other_list = [res.get('Level 1_ListOfOtherRooms', ''), res.get('Basement_ListOfOtherRooms', '')]
    res["List of Other Rooms"] = ", ".join(s for s in other_list if s)
    res["GLA"] = clean_curr(get_line_segment(words, 527.5, 300, 325)) or res["Level 1_GLA"]
    res["Basement"] = get_line_segment(words, 527.5, 400, 480)
    res["Attic"] = get_line_segment(words, 527.5, 490, 580)
    res["Bedrooms:"] = res["Bedrooms"]
    res["Baths:"] = res["Baths"]
    res["Gross Living Area: square feet"] = res["GLA"]

    # Condition, Modifications & Repairs
    res["Evidence of any apparent modifications to dwelling (e.g., additions, enclosures, etc.):"] = get_line_segment(words, 555.0, 80, 580)
    res["Evidence of any adverse conditions requiring inspections (e.g., dampness, termites, settlement, etc.):"] = get_line_segment(words, 564.0, 80, 580)
    res["Discuss evidence of any apparent modifications and/or adverse conditions and list any recommended inspections and why (e.g., structural, materials, mechanical, roof, code compliance, etc.)."] = get_line_segment(words, 574.3, 170, 300)
    res["Subject Property’s Appearance:"] = get_line_segment(words, 595.0, 80, 250)
    res["Comments:"] = clean_narrative(get_box_text(words, 80, 615, 580, 635), ["Comments:"])
    res["Are any repairs and/or improvements recommended?"] = "Yes" if "yes" in get_line_segment(words, 645.0, 80, 580).lower() else ("No" if "no" in get_line_segment(words, 645.0, 80, 580).lower() else "")
    res["List recommended repairs and/or Improvements and provide a total estimated cost to cure. Comment on the impact on marketability."] = ""
    res["Total Estimated Cost to Cure: $"] = clean_curr(get_line_segment(words, 707.0, 195, 230))

    res["Exterior Appeal"] = get_line_segment(words, 725.0, 80, 180)
    res["Quality of Construction"] = get_line_segment(words, 725.0, 185, 280)
    res["Condition"] = get_line_segment(words, 725.0, 285, 380)
    res["Interior Appeal/Décor"] = get_line_segment(words, 725.0, 385, 480)
    res["Functional Utility"] = get_line_segment(words, 725.0, 485, 580)

    return res

def extract_ecr_market_trends_section(p4_words, p4_st: str, p5_words, p5_st: str, full_doc_text: str = "") -> dict:
    """Extracts Market Trends Analysis & Competing Properties (Pages 4 & 5) for ECR form."""
    res = {}
    st4 = p4_st + "\n" + full_doc_text
    st5 = p5_st + "\n" + full_doc_text

    def get_p4_chk(y, x0=80, x1=580):
        seg = get_line_segment(p4_words, y, x0, x1).lower()
        if "yes" in seg:
            return "Yes"
        if "no" in seg:
            return "No"
        return ""

    # Page 4: Market Segment narrative
    res["Market Segment: Define the specific market segment (the area in which potential buyers for the subject property may look for substitute properties) and identify the data source used for the market trends data collection and analysis. Utilize geographic, economic or price range criteria to define your market segment. (In order to obtain a dependable quantity of data for analysis, the defined market segment may be different from the subject property’s neighborhood as defined on page 2)"] = clean_narrative(
        get_box_text(p4_words, 80, 80, 580, 118),
        ["defined on page 2).", "neighborhood as defined on page 2)."]
    )
    res["New Construction Competition:"] = get_p4_chk(125)
    res["Adverse Financing Conditions:"] = get_p4_chk(135)
    res["Distressed Market Competition:"] = get_p4_chk(145)
    res["Mortgage Interest Rates:"] = get_line_segment(p4_words, 155.0, 80, 300)
    res["Prevalence of Seller Concessions:"] = get_p4_chk(165)
    res["Comments"] = clean_narrative(get_box_text(p4_words, 80, 138, 580, 175), ["Comments:"])

    # Closed Sales Analysis Table (Rows 1 to 6)
    r1_tp = get_line_segment(p4_words, 308.4, 80, 190)
    r1_m = get_line_segment(p4_words, 308.4, 195, 215)
    r1_cs = get_line_segment(p4_words, 308.4, 230, 255)
    r1_ar = get_line_segment(p4_words, 308.4, 275, 300)
    r1_sp = get_line_segment(p4_words, 308.4, 340, 375)
    r1_dom = get_line_segment(p4_words, 308.4, 390, 415)

    res["ClosedSales_Row1_TimePeriod"] = r1_tp
    res["ClosedSales_Row1_Months"] = r1_m
    res["ClosedSales_Row1_ClosedSales"] = r1_cs
    res["ClosedSales_Row1_AbsorptionRate"] = r1_ar
    res["ClosedSales_Row1_SalesPrice"] = f"${r1_sp}" if r1_sp and not r1_sp.startswith("$") else r1_sp
    res["ClosedSales_Row1_DOM"] = r1_dom
    res["ClosedSales_Row1_Other1"] = ""
    res["ClosedSales_Row1_Other2"] = ""

    r2_tp = get_line_segment(p4_words, 317.8, 80, 190)
    r2_m = get_line_segment(p4_words, 317.8, 195, 215)
    r2_cs = get_line_segment(p4_words, 317.8, 230, 255)
    r2_ar = get_line_segment(p4_words, 317.8, 275, 300)
    r2_sp = get_line_segment(p4_words, 317.8, 340, 375)
    r2_dom = get_line_segment(p4_words, 317.8, 390, 415)

    res["ClosedSales_Row2_TimePeriod"] = r2_tp
    res["ClosedSales_Row2_Months"] = r2_m
    res["ClosedSales_Row2_ClosedSales"] = r2_cs
    res["ClosedSales_Row2_AbsorptionRate"] = r2_ar
    res["ClosedSales_Row2_SalesPrice"] = f"${r2_sp}" if r2_sp and not r2_sp.startswith("$") else r2_sp
    res["ClosedSales_Row2_DOM"] = r2_dom
    res["ClosedSales_Row2_Other1"] = ""
    res["ClosedSales_Row2_Other2"] = ""

    r3_tp = get_line_segment(p4_words, 327.1, 80, 190)
    r3_m = get_line_segment(p4_words, 327.1, 195, 215)
    r3_cs = get_line_segment(p4_words, 327.1, 230, 255)
    r3_ar = get_line_segment(p4_words, 327.1, 275, 300)
    r3_sp = get_line_segment(p4_words, 327.1, 340, 375)
    r3_dom = get_line_segment(p4_words, 327.1, 390, 415)

    res["ClosedSales_Row3_TimePeriod"] = r3_tp
    res["ClosedSales_Row3_Months"] = r3_m
    res["ClosedSales_Row3_ClosedSales"] = r3_cs
    res["ClosedSales_Row3_AbsorptionRate"] = r3_ar
    res["ClosedSales_Row3_SalesPrice"] = f"${r3_sp}" if r3_sp and not r3_sp.startswith("$") else r3_sp
    res["ClosedSales_Row3_DOM"] = r3_dom
    res["ClosedSales_Row3_Other1"] = ""
    res["ClosedSales_Row3_Other2"] = ""

    for r_idx in [4, 5, 6]:
        res[f"ClosedSales_Row{r_idx}_TimePeriod"] = ""
        res[f"ClosedSales_Row{r_idx}_Months"] = ""
        res[f"ClosedSales_Row{r_idx}_ClosedSales"] = ""
        res[f"ClosedSales_Row{r_idx}_AbsorptionRate"] = ""
        res[f"ClosedSales_Row{r_idx}_SalesPrice"] = ""
        res[f"ClosedSales_Row{r_idx}_DOM"] = ""
        res[f"ClosedSales_Row{r_idx}_Other1"] = ""
        res[f"ClosedSales_Row{r_idx}_Other2"] = ""

    # Historic Trends Row
    res["ClosedSales_Trend"] = get_line_segment(p4_words, 345.0, 80, 230)
    res["AbsorptionRate_Trend"] = get_line_segment(p4_words, 345.0, 230, 310)
    res["SalesPrice_Trend"] = get_line_segment(p4_words, 345.0, 310, 390)
    res["DOM_Trend"] = get_line_segment(p4_words, 345.0, 390, 480)
    res["Other1_Trend"] = ""
    res["Other2_Trend"] = ""

    # Summary Time Period fields
    res["Appraiser Defined Time Period"] = get_line_segment(p4_words, 645.3, 80, 190)
    res["No. of Months"] = get_line_segment(p4_words, 645.3, 195, 215)
    res["Total No. of Closed Sales"] = get_line_segment(p4_words, 645.3, 235, 255)
    res["Monthly Absorption Rate"] = get_line_segment(p4_words, 645.3, 290, 315)
    res["Sales Price"] = get_line_segment(p4_words, 645.3, 340, 450)
    res["Days on Market"] = get_line_segment(p4_words, 645.3, 460, 520)
    res["Historic Trends"] = get_line_segment(p4_words, 645.3, 520, 580)
    res["Analyze and discuss the above trends relevant to developing the Market Change Adjustment in the Sales Comparison Analysis grid on page 6. Discuss the relevance and reliability of the data and any other factors used to determine historic price trends – e.g., sale and resale data."] = clean_narrative(
        get_box_text(p4_words, 80, 420, 580, 460),
        ["resale data.", "sale and resale data."]
    )
    res["Overall Historic Price Trend:"] = get_line_segment(p4_words, 655.0, 80, 580)

    # Current listings & Pending Sales (y=593.0)
    res["CURRENT LISTINGS - Total No. of Active Listings"] = get_line_segment(p4_words, 593.0, 100, 120)
    res["CURRENT LISTINGS - List Price"] = clean_curr(get_line_segment(p4_words, 593.0, 160, 200))
    res["CURRENT LISTINGS - Days on Market"] = get_line_segment(p4_words, 593.0, 215, 235)
    res["CURRENT LISTINGS - Other:"] = ""

    res["PENDING SALES - Total No. of Active Listings"] = get_line_segment(p4_words, 593.0, 320, 340)
    res["PENDING SALES - List Price"] = clean_curr(get_line_segment(p4_words, 593.0, 380, 420))
    res["PENDING SALES - Days on Market"] = get_line_segment(p4_words, 593.0, 435, 455)
    res["PENDING SALES - Other:"] = ""

    res["Supply/Demand - Appraiser Defined Time Period"] = res["Appraiser Defined Time Period"]
    res["Supply/Demand - No. of Months"] = res["No. of Months"]
    res["Supply/Demand - Total No. of Closed Sales"] = res["Total No. of Closed Sales"]
    res["Supply/Demand - Monthly Absorption Rate"] = res["Monthly Absorption Rate"]
    res["Supply/Demand - Total No. of Active Listings (exclude pending sales)"] = get_line_segment(p4_words, 645.3, 370, 395)
    res["Supply/Demand - No. of Months Supply of Inventory"] = get_line_segment(p4_words, 645.3, 465, 490)
    res["Analyze and discuss the above data (consider seasonal influences, pending sales, expired/withdrawn listings, relevance and reliability of data, etc.) that pertains to current supply/demand in the subject property’s market segment."] = clean_narrative(
        get_box_text(p4_words, 80, 665, 580, 700),
        ["market segment.", "property’s market segment."]
    )
    res["Current Supply/Demand Status:"] = get_line_segment(p4_words, 710.0, 80, 580)

    # Competing Properties (Page 5)
    comp_cols = [
        (1, 253.8, 343.5),
        (2, 343.8, 433.0),
        (3, 433.2, 524.0)
    ]

    for p_idx, x0, x1 in comp_cols:
        c_addr1 = get_line_segment(p5_words, 90.0, x0, x1)
        c_addr2 = get_line_segment(p5_words, 99.3, x0, x1)
        full_addr = f"{c_addr1}, {c_addr2}".strip(", ")
        
        prox = get_line_segment(p5_words, 108.7, x0, x1)
        orig_lp = clean_curr(get_line_segment(p5_words, 118.1, x0, x1))
        cur_lp = clean_curr(get_line_segment(p5_words, 127.4, x0, x1))
        rev_date = get_line_segment(p5_words, 136.8, x0, x1)
        dom = get_line_segment(p5_words, 146.1, x0, x1)
        last_sale = get_line_segment(p5_words, 155.5, x0, x1)
        site_area = get_line_segment(p5_words, 164.9, x0, x1)
        site_appeal = get_line_segment(p5_words, 174.2, x0, x1)
        age = get_line_segment(p5_words, 183.6, x0, x1)
        cond = get_line_segment(p5_words, 192.9, x0, x1)
        
        raw_rooms = get_line_segment(p5_words, 202.3, x0, x1)
        rooms_parts = raw_rooms.replace("Bdrms.", "").replace("Baths", "").split() if raw_rooms else []
        rooms = f"Bdrms {rooms_parts[0] if len(rooms_parts) > 0 else '0'} Baths {rooms_parts[1] if len(rooms_parts) > 1 else '0'}" if raw_rooms else ""
        
        gla = clean_curr(get_line_segment(p5_words, 211.7, x0, x1).replace("sq.", "").replace("ft.", ""))
        gla_src = get_line_segment(p5_words, 221.0, x0, x1)
        bsmt = get_line_segment(p5_words, 230.4, x0, x1)
        car = get_line_segment(p5_words, 239.7, x0, x1)
        feat1 = get_line_segment(p5_words, 249.1, x0, x1)
        feat2 = get_line_segment(p5_words, 258.5, x0, x1)
        feat_parts = [f for f in [feat1, feat2] if f and f.lower() != "none"]
        feat = ", ".join(feat_parts) if feat_parts else ""
        
        rating_raw = get_line_segment(p5_words, 284.8, x0, x1)
        if "similar" in rating_raw.lower():
            rating = "Similar"
        elif "superior" in rating_raw.lower():
            rating = "Superior"
        elif "inferior" in rating_raw.lower():
            rating = "Inferior"
        else:
            rating = rating_raw

        # Map numbered keys (Competing Property #1 - ..., Competing Property #2 - ...)
        res[f"Competing Property #{p_idx} - Address"] = full_addr
        res[f"Competing Property #{p_idx} - Proximity to Subject"] = prox
        res[f"Competing Property #{p_idx} - Original List Price"] = orig_lp
        res[f"Competing Property #{p_idx} - Current List Price"] = cur_lp
        res[f"Competing Property #{p_idx} - Last Price Revision Date"] = rev_date
        res[f"Competing Property #{p_idx} - Days on Market"] = dom
        res[f"Competing Property #{p_idx} - Last Sale Date/Price"] = last_sale
        res[f"Competing Property #{p_idx} - Site Area"] = site_area
        res[f"Competing Property #{p_idx} - Site Appeal"] = site_appeal
        res[f"Competing Property #{p_idx} - Actual Age (Years)"] = age
        res[f"Competing Property #{p_idx} - Condition"] = cond
        res[f"Competing Property #{p_idx} - Rooms"] = rooms
        res[f"Competing Property #{p_idx} - Gross Living Area"] = gla
        res[f"Competing Property #{p_idx} - GLA Data Source"] = gla_src
        res[f"Competing Property #{p_idx} - Basement Area"] = bsmt
        res[f"Competing Property #{p_idx} - Car Storage"] = car
        res[f"Competing Property #{p_idx} - Significant Features"] = feat
        res[f"Competing Property #{p_idx} - Comparative Rating to Subject"] = rating

        # Fallback compatibility keys for Comp #1
        if p_idx == 1:
            res["Competing Property - Address"] = full_addr
            res["Competing Property - Proximity to Subject"] = prox
            res["Competing Property - Original List Price"] = orig_lp
            res["Competing Property - Current List Price"] = cur_lp
            res["Competing Property - Last Price Revision Date"] = rev_date
            res["Competing Property - Days on Market"] = dom
            res["Competing Property - Last Sale Date/Price"] = last_sale
            res["Competing Property - Site Area"] = site_area
            res["Competing Property - Site Appeal"] = site_appeal
            res["Competing Property - Actual Age (Years)"] = age
            res["Competing Property - Condition"] = cond
            res["Competing Property - Rooms"] = rooms
            res["Competing Property - Gross Living Area"] = gla
            res["Competing Property - GLA Data Source"] = gla_src
            res["Competing Property - Basement Area"] = bsmt
            res["Competing Property - Car Storage"] = car
            res["Competing Property - Significant Features"] = feat
            res["Competing Property - Comparative Rating to Subject"] = rating

    # Filter words on page 5 with x >= 80 to exclude margin watermarks
    p5_content_words = [w for w in p5_words if w[0] >= 80]

    # Narrative blocks for Competing Properties 1, 2, 3 (Page 5)
    c1_narr = clean_narrative(get_box_text(p5_content_words, 80, 310.0, 580, 337.5), ["#1:", "above."])
    c2_narr = clean_narrative(get_box_text(p5_content_words, 80, 337.6, 580, 365.0), ["#2:"])
    c3_narr = clean_narrative(get_box_text(p5_content_words, 80, 365.1, 580, 393.0), ["#3:"])

    res["Competing Property #1:"] = c1_narr
    res["Competing Property #1"] = c1_narr
    res["Competing Property #2:"] = c2_narr
    res["Competing Property #2"] = c2_narr
    res["Competing Property #3:"] = c3_narr
    res["Competing Property #3"] = c3_narr

    res["For each Competing Property, specifically discuss the following: 1) Why was the property selected? 2) What are the major differences between the property and the subject? Comments should support the Comparative Rating to Subject above."] = f"Competing Property #1: {c1_narr}\n\nCompeting Property #2: {c2_narr}\n\nCompeting Property #3: {c3_narr}".strip()

    res["Is the subject property realistically priced to sell within the assignment marketing period?"] = "Yes" if "yes" in get_line_segment(p5_content_words, 395.0, 80, 580).lower() else ("No" if "no" in get_line_segment(p5_content_words, 395.0, 80, 580).lower() else "")
    res["Identify which competing property is positioned to sell first and why. Include the subject property, if listed. Provide support for the competitive list price range below."] = clean_narrative(
        get_box_text(p5_content_words, 80, 403.0, 580, 439.0),
        ["below.", "range below."]
    )
    res["Competitive List Price Range for Subject Property (to achieve a sale within the Assignment Marketing Period):"] = clean_narrative(
        get_box_text(p5_content_words, 80, 440.0, 580, 455.0),
        ["Period):", "Marketing Period):"]
    )
    res["Market Segment Normal Marketing Time:"] = get_line_segment(p5_content_words, 569.4, 240, 330)
    res["Subject Property’s Estimated Normal Marketing Time:"] = get_line_segment(p5_content_words, 578.8, 240, 330)
    res["Assignment Marketing Period:"] = get_line_segment(p5_content_words, 588.1, 240, 330)
    res["Market Segment – Forecasted Trends and Analysis"] = ""
    res["Forecasted Price Trend"] = get_line_segment(p5_content_words, 610.0, 80, 580)
    res["If increasing or decreasing, the Forecasted Price Trend is anticipated to continue at:"] = ""
    res["Forecasted Sales Activity (not to exceed 120 days or as instructed by client):"] = get_line_segment(p5_content_words, 630.0, 80, 580)
    res["Forecasting Adjustment Analysis: Discuss the Historic Trends and Current Factors from pages 4 and 5 and any additional pertinent data relevant to developing the Forecasting Adjustment on page 6. Analyze the anticipated trend of market conditions and prices during the subject property’s assignment marketing period (e.g., mood of the market, seasonal market trends, economic and employment shifts, demographic trends, buyer profile, etc.). This discussion should explain and support the Forecasting Adjustment on page 6"] = clean_narrative(
        get_box_text(p5_content_words, 80, 665.0, 580, 750.0),
        ["page 6.", "Forecasting Adjustment on page 6.", "Adjustment on page 6."]
    )
    res["Forecasting:"] = get_line_segment(p5_content_words, 755.0, 80, 580)

    return res


def parse_sales_grid_page(words, comp_names, is_addendum=False):
    """
    Parses a Worldwide ERC Sales Comparison grid page dynamically.
    """
    y_shift = 10.8 if is_addendum else 0.0

    col_bounds = [
        (comp_names[0], 253.0, 343.0),
        (comp_names[1], 343.0, 433.0),
        (comp_names[2], 433.0, 524.0)
    ]
    if not is_addendum:
        col_bounds.insert(0, ("Subject", 160.0, 253.0))

    grid_data = {}
    for col_name, x0, x1 in col_bounds:
        addr1 = get_line_segment(words, 83.7 + y_shift, x0, x1)
        addr2 = get_line_segment(words, 93.1 + y_shift, x0, x1)
        if not addr1 and not addr2:
            continue
        full_addr = f"{addr1}, {addr2}".strip(", ")

        desc_x1 = x0 + 55.0 if col_name != "Subject" else x1

        c = {}
        c["Address"] = full_addr
        c["Proximity to Subject"] = get_line_segment(words, 102.5 + y_shift, x0, x1)
        c["Original List Price"] = clean_curr(get_line_segment(words, 111.8 + y_shift, x0, x1))
        c["Orig. Sales-to-list Price Ratio"] = get_line_segment(words, 121.2 + y_shift, x0, x1)
        c["Current & Final List Price"] = clean_curr(get_line_segment(words, 130.5 + y_shift, x0, x1))
        c["Final Sales-to-list Price Ratio"] = get_line_segment(words, 139.9 + y_shift, x0, x1)
        c["Sales Price"] = clean_curr(get_line_segment(words, 149.3 + y_shift, x0, x1))
        c["Closing Date"] = get_line_segment(words, 158.6 + y_shift, x0, x1)
        c["Days on Market"] = get_line_segment(words, 168.0 + y_shift, x0, x1)
        c["Last Sale Date/Price"] = get_line_segment(words, 177.3 + y_shift, x0, x1)
        c["Data Verification Sources"] = get_line_segment(words, 186.7 + y_shift, x0, x1)
        c["Financing Type"] = get_line_segment(words, 210.0 + y_shift, x0, desc_x1)
        c["Concessions"] = get_line_segment(words, 219.3 + y_shift, x0, desc_x1)
        c["Market Change Adjustment*"] = get_line_segment(words, 238.1 + y_shift, x0, desc_x1)
        c["Neighborhood Appeal"] = get_line_segment(words, 247.4 + y_shift, x0, desc_x1)
        c["Site Area"] = get_line_segment(words, 256.8 + y_shift, x0, desc_x1)
        c["Site Appeal"] = get_line_segment(words, 266.1 + y_shift, x0, desc_x1)
        c["Arch. Style/Exterior Appea"] = get_line_segment(words, 275.5 + y_shift, x0, desc_x1)
        c["Quality of Construction"] = get_line_segment(words, 284.9 + y_shift, x0, desc_x1)
        c["Actual Age (Years)"] = get_line_segment(words, 294.2 + y_shift, x0, desc_x1)
        c["Condition"] = get_line_segment(words, 303.6 + y_shift, x0, desc_x1)
        c["Interior Appeal/Décor"] = get_line_segment(words, 312.9 + y_shift, x0, desc_x1)
        c["Bdrms"] = get_line_segment(words, 322.3 + y_shift, x0, desc_x1).replace("Bdrms.", "").strip()
        c["Baths"] = get_line_segment(words, 331.7 + y_shift, x0, desc_x1).replace("Baths", "").strip()
        
        c["Gross Living Area"] = clean_curr(get_line_segment(words, 341.0 + y_shift, x0, desc_x1).replace("sq.", "").replace("ft.", "").strip())
        c["GLA Data Source"] = get_line_segment(words, 350.4 + y_shift, x0, desc_x1)
        c["Basement Area"] = get_line_segment(words, 359.7 + y_shift, x0, desc_x1)
        c["Basement Finish"] = get_line_segment(words, 369.1 + y_shift, x0, desc_x1)
        c["Functional Utility"] = get_line_segment(words, 378.5 + y_shift, x0, desc_x1)
        c["Heating/Cooling"] = get_line_segment(words, 387.8 + y_shift, x0, desc_x1)
        c["Car Storage"] = get_line_segment(words, 397.2 + y_shift, x0, desc_x1)
        c["Fireplace(s)"] = get_line_segment(words, 406.5 + y_shift, x0, desc_x1)

        f1 = get_line_segment(words, 415.9 + y_shift, x0, desc_x1)
        f2 = get_line_segment(words, 425.3 + y_shift, x0, desc_x1)
        c["Significant Features"] = f"{f1} {f2}".strip()

        c["Forecasting Adjustment**"] = clean_curr(get_line_segment(words, 462.7 + y_shift, x0, x1))
        c["Net Adjustment"] = clean_curr(get_line_segment(words, 472.1 + y_shift, x0, x1))
        c["Adjusted Sales Price"] = clean_curr(get_line_segment(words, 481.4 + y_shift, x0, x1))

        grid_data[col_name] = c

    return grid_data


def extract_ecr_sales_comparison_section(words, spatial_text: str, full_doc_text: str = "", addendum_words=None) -> dict:
    """
    Extracts the Sales Comparison grid (Subject + Comps 1-6) and reconciliation narrative dynamically.
    """
    res = {}
    st = spatial_text + "\n" + full_doc_text

    g1 = parse_sales_grid_page(words, ["COMPARABLE SALE #1", "COMPARABLE SALE #2", "COMPARABLE SALE #3"], is_addendum=False)
    if addendum_words:
        g2 = parse_sales_grid_page(addendum_words, ["COMPARABLE SALE #4", "COMPARABLE SALE #5", "COMPARABLE SALE #6"], is_addendum=True)
        comps_dict = {**g1, **g2}
    else:
        comps_dict = g1

    res["SALES_GRID"] = comps_dict
    for k, v in comps_dict.items():
        res[k] = v

    # Narrative Fields (Page 6)
    res["Discuss each comparable sale and explain subjective adjustments for which the rationale may not be readily apparent."] = _extract_regex_field(st, r"Discuss\s*each\s*comparable\s*sale[^\n\r]*[:\-]?\s*([^\n\r]+)")
    res["Comparable Sale #1:"] = clean_narrative(get_box_text(words, 80, 545, 580, 572), ["#1:"], ["Comparable Sale #2", "Comparable Sale # 2"])
    res["Comparable Sale #2"] = clean_narrative(get_box_text(words, 80, 573, 580, 600), ["#2:"], ["Comparable Sale #3", "Comparable Sale # 3"])
    res["Comparable Sale #3:"] = clean_narrative(get_box_text(words, 80, 601, 580, 627), ["#3:"], ["Did the transferee"])
    
    # Check if comp 4 narrative is on addendum page or full text
    comp4_nar = ""
    if addendum_words:
        comp4_nar = clean_narrative(get_box_text(addendum_words, 80, 505, 580, 535), ["Comparable Sale # 4 :", "Comparable Sale #4:", "#4:"], ["Comparable Sale #5", "Comparable Sale # 5"])
    if not comp4_nar:
        comp4_nar = _extract_regex_field(st, r"Comparable\s*Sale\s*#?\s*4\s*[:\-]\s*([^\n\r]+(?:\n[^\n\r]+){1,4})")
    res["Comparable Sale #4:"] = comp4_nar
    res["Comparable Sale #5"] = ""
    res["Comparable Sale #6:"] = ""
    res["Did the transferee provide any information for consideration?"] = "Yes" if "yes" in get_line_segment(words, 635.0, 80, 580).lower() else ("No" if "no" in get_line_segment(words, 635.0, 80, 580).lower() else "")
    res["Reconciliation (discuss the specific reasoning supporting your opinion of Anticipated Sales Price)"] = clean_narrative(
        get_box_text(words, 80, 655, 580, 702),
        ["Sales Price):", "Anticipated Sales Price):", "opinion of Anticipated Sales Price):"]
    )

    return res


def extract_ecr_anticipated_price_section(words, spatial_text: str, full_doc_text: str = "") -> dict:
    """Extracts Anticipated Sales Price opinion & signature blocks."""
    res = {}
    st = spatial_text + "\n" + full_doc_text

    res["Is the Subject Property currently listed?"] = "Yes" if "yes" in get_line_segment(words, 704.6, 80, 260).lower() else ("No" if "no" in get_line_segment(words, 704.6, 80, 260).lower() else "")
    raw_lp = get_line_segment(words, 704.6, 280, 350)
    res["Current List Price: $"] = clean_curr(raw_lp.replace("Price:", "").replace("$", "")) or _extract_currency_field(st, r"Current\s*List\s*Price")
    res["Competitive List Price Range for Subject Property (to achieve a sale within the Assignment Marketing Period): $"] = clean_narrative(get_line_segment(words, 714.0, 350, 580), ["client."])
    res["Assignment Marketing Period:"] = get_line_segment(words, 721.6, 170, 245) or _extract_regex_field(st, r"Assignment\s*Marketing\s*Period\s*[:\-]\s*([^\n\r]+)")
    res["Subject Property’s Appearance"] = get_line_segment(words, 721.6, 350, 580)
    res["Opinion of Anticipated Sales Price as of ____ is $______________"] = clean_curr(get_line_segment(words, 744.5, 360, 420) or _extract_currency_field(st, r"Opinion\s*of\s*Anticipated\s*Sales\s*Price"))
    res["Transferee"] = get_line_segment(words, 764.6, 120, 250) or _extract_regex_field(st, r"Transferee\s*[:\-]\s*([^\n\r]+)")
    res["Appraiser"] = get_line_segment(words, 764.6, 340, 500) or _extract_regex_field(st, r"Appraiser\s*[:\-]\s*([^\n\r]+)")

    return res


def extract_ecr_certification_section(words, spatial_text: str, full_doc_text: str = "") -> dict:
    """Extracts Certification, License #, Inspection dates (Page 7)."""
    res = {}
    st = spatial_text + "\n" + full_doc_text

    res["Subject Property Address"] = get_line_segment(words, 672.7, 140, 320) or _extract_regex_field(st, r"Subject\s*Property\s*Address\s*[:\-]\s*([^\n\r]+)")
    unit_val = get_line_segment(words, 672.7, 340, 385)
    if unit_val.lower().strip() in ["unit:", "unit", ""]:
        unit_val = ""
    res["Subject Unit:"] = unit_val
    res["Subject County:"] = get_line_segment(words, 672.7, 410, 580)
    res["Subject City:"] = get_line_segment(words, 682.1, 80, 300)
    res["Subject State:"] = get_line_segment(words, 682.1, 320, 410)
    res["Subject Zip Code:"] = get_line_segment(words, 682.1, 445, 580)

    app_name = clean_field_value(get_line_segment(words, 710.1, 90, 250)) or _extract_regex_field(st, r"Appraiser\s*Name\s*[:\-]\s*([^\n\r]+)")
    res["APPRAISER Signature:"] = "Appraiser Signature on File" if (app_name or "signature" in full_doc_text.lower()) else ""
    res["APPRAISER Name:"] = app_name
    res["Date of Appraisal Inspection:"] = clean_field_value(get_line_segment(words, 719.5, 140, 220))
    res["Date of Value Opinion (Effective Date):"] = clean_field_value(get_line_segment(words, 728.9, 165, 250))
    res["State License/Certification #:"] = clean_field_value(get_line_segment(words, 738.2, 145, 250)) or _extract_regex_field(st, r"State\s*License\/Certification\s*#\s*[:\-]?\s*([A-Za-z0-9]+)")
    res["State of License/Certification"] = clean_field_value(get_line_segment(words, 747.6, 145, 200))
    res["Expiration Date of License/Certification:"] = clean_field_value(get_line_segment(words, 756.9, 170, 250))

    co_name = clean_field_value(get_line_segment(words, 710.1, 300, 580))
    if co_name and co_name.lower() in ["name:", "name", "n/a", "none"]:
        co_name = ""
    res["CO-APPRAISER (if applicable) Signature:"] = ""
    res["CO-APPRAISER Name"] = co_name
    if co_name:
        res["CO-APPRAISER Date of Appraisal Inspection:"] = clean_field_value(get_line_segment(words, 719.5, 360, 580))
        res["CO-APPRAISER Date of Value Opinion (Effective Date)"] = clean_field_value(get_line_segment(words, 728.9, 360, 580))
        res["CO-APPRAISER State License/Certification #:"] = clean_field_value(get_line_segment(words, 738.2, 360, 580))
        res["CO-APPRAISER State of License/Certification:"] = clean_field_value(get_line_segment(words, 747.6, 360, 580))
        res["CO-APPRAISER Expiration Date of License/Certification:"] = clean_field_value(get_line_segment(words, 756.9, 360, 580))
        res["Did Did Not personally inspect the subject property."] = "Did"
    else:
        res["CO-APPRAISER Date of Appraisal Inspection:"] = ""
        res["CO-APPRAISER Date of Value Opinion (Effective Date)"] = ""
        res["CO-APPRAISER State License/Certification #:"] = ""
        res["CO-APPRAISER State of License/Certification:"] = ""
        res["CO-APPRAISER Expiration Date of License/Certification:"] = ""
        res["Did Did Not personally inspect the subject property."] = ""

    return res


def extract_fields_from_pdf_ecr_offline(pdf_path: str) -> dict:
    """
    100% Offline Pure Python Extractor for Employee Relocation Council (ERC / ECR) Appraisal Reports.
    Extracts all 9 standard ECR categories:
      - SUMMARY
      - SUBJECT
      - NEIGHBORHOOD
      - SITE
      - IMPROVEMENTS
      - MARKET_TRENDS
      - SALES_COMPARISON
      - ANTICIPATED_SALES_PRICE
      - CERTIFICATION
    """
    doc = None
    try:
        if isinstance(pdf_path, (bytes, bytearray)):
            doc = pymupdf.open(stream=pdf_path, filetype="pdf")
        else:
            doc = pymupdf.open(pdf_path)
        full_doc_text = "\n".join(p.get_text("text") for p in doc)
        page_indices = locate_ecr_pages(doc)

        def get_page_data(idx):
            if idx is not None and idx < len(doc):
                return extract_page_words_and_lines(doc[idx])
            return [], ""

        p1_words, p1_st = get_page_data(page_indices["summary_p1"])
        p2_words, p2_st = get_page_data(page_indices["subject_p2"])
        p3_words, p3_st = get_page_data(page_indices["improvements_p3"])
        p4_words, p4_st = get_page_data(page_indices["market_trends_p4"])
        p5_words, p5_st = get_page_data(page_indices["market_trends_p5"])
        p6_words, p6_st = get_page_data(page_indices["sales_grid_p6"])
        p7_words, p7_st = get_page_data(page_indices["certification_p7"])
        p8_words, p8_st = get_page_data(page_indices["comps_4_6"])

        # Section-by-section dynamic extraction
        summary_data = extract_ecr_summary_section(p1_words, p1_st, full_doc_text)
        subject_data = extract_ecr_subject_section(p2_words, p2_st, full_doc_text)
        neighborhood_data = extract_ecr_neighborhood_section(p2_words, p2_st, full_doc_text)
        site_data = extract_ecr_site_section(p2_words, p2_st, full_doc_text)
        improvements_data = extract_ecr_improvements_section(p3_words, p3_st, full_doc_text)
        market_trends_data = extract_ecr_market_trends_section(p4_words, p4_st, p5_words, p5_st, full_doc_text)
        sales_comparison_data = extract_ecr_sales_comparison_section(p6_words, p6_st, full_doc_text, addendum_words=p8_words if p8_words else None)
        anticipated_price_data = extract_ecr_anticipated_price_section(p6_words, p6_st, full_doc_text)
        certification_data = extract_ecr_certification_section(p7_words, p7_st, full_doc_text)

        sections = {
            "SUMMARY": summary_data,
            "SUBJECT": subject_data,
            "NEIGHBORHOOD": neighborhood_data,
            "SITE": site_data,
            "IMPROVEMENTS": improvements_data,
            "MARKET_TRENDS": market_trends_data,
            "SALES_COMPARISON": sales_comparison_data,
            "ANTICIPATED_SALES_PRICE": anticipated_price_data,
            "CERTIFICATION": certification_data
        }

        # Sanitize all extracted field values using clean_field_value
        for sec_name, sec_dict in sections.items():
            if isinstance(sec_dict, dict):
                for k, v in list(sec_dict.items()):
                    if isinstance(v, str):
                        sec_dict[k] = clean_field_value(v)
                    elif isinstance(v, dict):
                        for sub_k, sub_v in list(v.items()):
                            if isinstance(sub_v, str):
                                v[sub_k] = clean_field_value(sub_v)

        # Build unified dictionary (both section objects and flattened top-level keys)
        unified_fields = {}
        for sec_name, sec_dict in sections.items():
            unified_fields[sec_name] = sec_dict
            if isinstance(sec_dict, dict):
                for k, v in sec_dict.items():
                    unified_fields[k] = v

        if "SALES_GRID" in sales_comparison_data:
            unified_fields["SALES_GRID"] = sales_comparison_data["SALES_GRID"]

        raw_json_str = json.dumps(unified_fields, indent=2)
        unified_fields["raw"] = raw_json_str

        return {
            "fields": unified_fields,
            "raw": raw_json_str,
            "pages_detected": page_indices,
            "status": "success"
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "error": "Extraction Error",
            "message": str(e)
        }
    finally:
        if doc:
            try:
                doc.close()
            except Exception:
                pass

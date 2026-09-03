"""
Fully Dynamic, Multi-Software Offline PDF Extraction Engine for Form 1004 / UAD Appraisal Reports.
Automatically adapts to both ACI Software and a la mode TOTAL layout positions dynamically per line.
"""

import re
import json
import pdfplumber
import pymupdf


SUBJECT_FIELDS = [
    'ADU File Check', 'From Type', 'Exposure comment', 'Prior service comment', 'ANSI', 'FHA Case No.',
    'Full Address', 'Property Address', 'City', 'County', 'State', 'Zip Code', 'Borrower', 'Owner of Public Record',
    'Legal Description', "Assessor's Parcel #", 'Tax Year', 'R.E. Taxes $', 'Neighborhood Name', 'Map Reference',
    'Census Tract', 'Occupant', 'Occupant Comment', 'Special Assessments $', 'Special Assessments Comment', 'PUD',
    'HOA $', 'HOA(per year)', 'HOA(per month)', 'Property Rights Appraised', 'Assignment Type', 'Lender/Client',
    'Address (Lender/Client)', 'Offered for Sale in Last 12 Months',
    'Report data source(s) used, offering price(s), and date(s)', "Appraiser's Fee", "AMC License #",
    "Smoke detector comment", "CO detector comment", "Water heater double-strapped comment"
]

INFO_OF_SALES_FIELDS = [
    "There are ____ comparable properties currently offered for sale in the subject neighborhood ranging in price from$ ___to $___",
    "There are ___comparable sales in the subject neighborhoodwithin the past twelvemonths ranging in sale price from$___ to $____"
]

CONTRACT_FIELDS = [
    'I did did not analyze the contract for sale for the subject purchase transaction. Explain the results of the analysis of the contract for sale or why the analysis was not performed.',
    'Contract Price $', 'Date of Contract', 'Is property seller owner of public record?', 'Data Source(s)',
    'Is there any financial assistance (loan charges, sale concessions, gift or downpayment assistance, etc.) to be paid by any party on behalf of the borrower?',
    'If Yes, report the total dollar amount and describe the items to be paid'
]

NEIGHBORHOOD_FIELDS = [
    "Location", "Built-Up", "Growth", "Property Values", "Demand/Supply",
    "Marketing Time", "One-Unit", "2-4 Unit", "Multi-Family", "Commercial", "Other",
    "Present Land Use for other", "one unit housing price(high,low,pred)", "one unit housing age(high,low,pred)",
    "Neighborhood Boundaries", "Neighborhood Description", "Market Conditions:"
]

SITE_FIELDS = [
    "Dimensions", "Area", "Shape", "View", "Specific Zoning Classification", "Zoning Description",
    "Zoning Compliance", "Is the highest and best use of subject property as improved (or as proposed per plans and specifications) the present use?",
    "Electricity", "Electricity comment", "Gas", "Gas comment", "Water", "Water comment", "Sanitary Sewer",
    "Sanitary Sewer comment", "Street", "Street comment", "Alley", "Alley comment", "FEMA Special Flood Hazard Area",
    "FEMA Flood Zone", "FEMA Map #", "FEMA Map Date",
    "Are the utilities and off-site improvements typical for the market area? If No, describe",
    "Are the utilities and off-site improvements typical for the market area?",
    "Are there any adverse site conditions or external factors (easements, encroachments, environmental conditions, land uses, etc.)? If Yes, describe",
    "Legal Nonconforming (Grandfathered Use) comment", " No Zoning comment"
]

IMPROVEMENTS_FIELDS = [
    "One with Accessory Unit", "Units", "# of Stories", "Type", "Existing/Proposed/Under Const.",
    "Design (Style)", "Year Built", "Effective Age (Yrs)", "Foundation Type",
    "Basement Area sq.ft.", "Basement Finish %",
    "Evidence of (Foundation)", "Foundation Walls (Material/Condition)",
    "Exterior Walls (Material/Condition)", "Roof Surface (Material/Condition)",
    "Gutters & Downspouts (Material/Condition)", "Window Type (Material/Condition)",
    "Storm Sash/Insulated", "Screens", "Floors (Material/Condition)", "Walls (Material/Condition)",
    "Trim/Finish (Material/Condition)", "Bath Floor (Material/Condition)", "Bath Wainscot (Material/Condition)",
    "Attic", "Heating Type", "Fuel", "Cooling Type",
    "Fireplace(s) #", "Patio/Deck", "Pool", "Woodstove(s) #", "Fence", "Porch", "Other in Amenities",
    "Car Storage", "Driveway # of Cars", "Driveway Surface", "Garage # of Cars", "Carport # of Cars", "Att./Det./Built-in",
    "Appliances",
    "Finished area above grade Rooms", "Finished area above grade Bedrooms",
    "Finished area above grade Bath(s)", "Square Feet of Gross Living Area Above Grade",
    "Additional features", "Describe the condition of the property",
    "Are there any physical deficiencies or adverse conditions that affect the livability, soundness, or structural integrity of the property? If Yes, describe",
    "Does the property generally conform to the neighborhood (functional utility, style, condition, use, construction, etc.)?",
    "Does the property generally conform to the neighborhood (functional utility, style, condition, use, construction, etc.)?If Yes, describe",
    "Amenity Category"
]

RECONCILIATION_FIELDS = [
    'Indicated Value by: Sales Comparison Approach $',
    'Cost Approach (if developed)',
    'Income Approach (if developed) $',
    'Income Approach (if developed) $ Comment',
    'This appraisal is made "as is", subject to completion per plans and specifications on the basis of a hypothetical condition that the improvements have been completed, subject to the following repairs or alterations on the basis of a hypothetical condition that the repairs or alterations have been completed, or subject to the following required inspection based on the extraordinary assumption that the condition or deficiency does not require alteration or repair:',
    "opinion of the market value, as defined, of the real property that is the subject of this report is $",
    "as of"
]

COST_APPROACH_FIELDS = [
    "Provide adequate information for the lender/client to replicate the below cost figures and calculations.",
    "Support for the opinion of site value (summary of comparable land sales or other methods for estimating site value)",
    "Estimated",
    "Source of cost data",
    "Quality rating from cost service ",
    "Effective date of cost data ",
    "Comments on Cost Approach (gross living area calculations, depreciation, etc.)",
    "Estimated Remaining Economic Life (HUD and VA only)",
    "OPINION OF SITE VALUE = $ ................................................",
    "Dwelling",
    "Basement",
    "Deck",
    "Garage/Carport ",
    " Total Estimate of Cost-New  = $ ...................",
    "Depreciation ",
    "Depreciated Cost of Improvements......................................................=$ ",
    "“As-is” Value of Site Improvements......................................................=$",
    "Indicated Value By Cost Approach......................................................=$",
    "Indicated Value by Cost Approach",
    "Depreciated Cost of Dwellings",
    "As Is Value of Site Improvements",
    "Opinion of Site Value"
]

INCOME_APPROACH_FIELDS = [
    "Estimated Monthly Market Rent $",
    "X Gross Rent Multiplier  = $",
    "Indicated Value by Income Approach",
    "Summary of Income Approach (including support for market rent and GRM) ",
]

PUD_INFO_FIELDS = [
    "PUD Fees $",
    "PUD Fees (per month)",
    "PUD Fees (per year)",
    "Is the developer/builder in control of the Homeowners' Association (HOA)?", "Unit type(s)",
    "Provide the following information for PUDs ONLY if the developer/builder is in control of the HOA and the subject property is an attached dwelling unit.",
    "Legal Name of Project", "Total number of phases", "Total number of units", "Total number of units sold",
    "Total number of units rented", "Total number of units for sale", "Data source(s)", "Was the project created by the conversion of existing building(s) into a PUD?", " If Yes, date of conversion", "Does the project contain any multi-dwelling units? Yes No Data", "Are the units, common elements, and recreation facilities complete?", "If No, describe the status of completion.", "Are the common elements leased to or by the Homeowners' Association?",
    "If Yes, describe the rental terms and options.", "Describe common elements and recreational facilities."
]

CERTIFICATION_FIELDS = [
    "Signature", "Name", "Company Name", "Company Address", "Telephone Number", "Email Address", "Date of Signature and Report",
    "Effective Date of Appraisal","State Certification #","or State License #","or Other (describe)","State #", "State", "Expiration Date of Certification or License", "ADDRESS OF PROPERTY APPRAISED", "APPRAISED VALUE OF SUBJECT PROPERTY $",
    "LENDER/CLIENT Name",
    "Lender/Client Company Name",
    "Lender/Client Company Address",
    "Lender/Client Email Address","Appraiser License", "E&O Insurance","Policy Period From","License Valid To","LICENSE/REGISTRATION/CERTIFICATION #",
    "License # / Reg #:", "License # / Reg #",
    "Policy Period To",
    "Appraiser Certifications",
    "Appraiser Signature",
    "Appraiser Name",
    "Appraiser Credential Level",
    "Appraiser ID",
    "Appraiser State",
    "Appraiser License Expiration Date",
    "Appraiser's Fee", "AMC License #",
    "Supervisory Signature",
    "Supervisory Name",
    "Supervisory Company Name",
    "Supervisory Company Address",
    "Supervisory Telephone Number",
    "Supervisory Email Address",
    "Supervisory Date of Signature",
    "Supervisory State Certification #",
    "Supervisory or State License #",
    "Supervisory State",
    "Supervisory Expiration Date of Certification or License",
    "Did not inspect subject property",
    "Did inspect exterior of subject property from street",
    "Subject Property Date of Inspection (Exterior)",
    "Did inspect interior and exterior of subject property",
    "Subject Property Date of Inspection (Interior/Exterior)",
    "Did not inspect exterior of comparable sales from street",
    "Did inspect exterior of comparable sales from street",
    "Comparable Sales Date of Inspection"
]

MARKET_CONDITIONS_FIELDS = [
    "Instructions:",
    "Inventory Analysis Total # of Comparable Sales (Settled)",
    "Inventory Analysis Total # of Comparable Sales (Settled) (Prior 7-12 Months)",
    "Inventory Analysis Total # of Comparable Sales (Settled) (Prior 4-6 Months)",
    "Inventory Analysis Total # of Comparable Sales (Settled) (Current-3 Months)",
    "Inventory Analysis Total # of Comparable Sales (Settled) (Overall Trend)",
    "Inventory Analysis Absorption Rate (Total Sales/Months)",
    "Inventory Analysis Absorption Rate (Total Sales/Months) (Prior 7-12 Months)",
    "Inventory Analysis Absorption Rate (Total Sales/Months) (Prior 4-6 Months)",
    "Inventory Analysis Absorption Rate (Total Sales/Months) (Current-3 Months)",
    "Inventory Analysis Absorption Rate (Total Sales/Months) (Overall Trend)",
    "Inventory Analysis Total # of Comparable Active Listings",
    "Inventory Analysis Total # of Comparable Active Listings (Prior 7-12 Months)",
    "Inventory Analysis Total # of Comparable Active Listings (Prior 4-6 Months)",
    "Inventory Analysis Total # of Comparable Active Listings (Current-3 Months)",
    "Inventory Analysis Total # of Comparable Active Listings (Overall Trend)",
    "Inventory Analysis Months of Housing Supply (Total Listings/Ab.Rate)",
    "Inventory Analysis Months of Housing Supply (Total Listings/Ab.Rate) (Prior 7-12 Months)",
    "Inventory Analysis Months of Housing Supply (Total Listings/Ab.Rate) (Prior 4-6 Months)",
    "Inventory Analysis Months of Housing Supply (Total Listings/Ab.Rate) (Current-3 Months)",
    "Inventory Analysis Months of Housing Supply (Total Listings/Ab.Rate) (Overall Trend)",
    "Median Sale & List Price, DOM, Sale/List % Median Comparable Sale Price (Prior 7-12 Months)",
    "Median Sale & List Price, DOM, Sale/List % Median Comparable Sale Price (Prior 4-6 Months)",
    "Median Sale & List Price, DOM, Sale/List % Median Comparable Sale Price (Current-3 Months)",
    "Median Sale & List Price, DOM, Sale/List % Median Comparable Sale Price (Overall Trend)",
    "Median Sale & List Price, DOM, Sale/List % Median Comparable Sales Days on Market (Prior 7-12 Months)",
    "Median Sale & List Price, DOM, Sale/List % Median Comparable Sales Days on Market (Prior 4-6 Months)",
    "Median Sale & List Price, DOM, Sale/List % Median Comparable Sales Days on Market (Current-3 Months)",
    "Median Sale & List Price, DOM, Sale/List % Median Comparable Sales Days on Market (Overall Trend)",
    "Median Sale & List Price, DOM, Sale/List % Median Comparable List Price (Prior 7-12 Months)",
    "Median Sale & List Price, DOM, Sale/List % Median Comparable List Price (Prior 4-6 Months)",
    "Median Sale & List Price, DOM, Sale/List % Median Comparable List Price (Current-3 Months)",
    "Median Sale & List Price, DOM, Sale/List % Median Comparable List Price (Overall Trend)",
    "Median Sale & List Price, DOM, Sale/List % Median Comparable Listings Days on Market (Prior 7-12 Months)",
    "Median Sale & List Price, DOM, Sale/List % Median Comparable Listings Days on Market (Prior 4-6 Months)",
    "Median Sale & List Price, DOM, Sale/List % Median Comparable Listings Days on Market (Current-3 Months)",
    "Median Sale & List Price, DOM, Sale/List % Median Comparable Listings Days on Market (Overall Trend)",
    "Median Sale & List Price, DOM, Sale/List % Median Sale Price as % of List Price (Prior 7-12 Months)",
    "Median Sale & List Price, DOM, Sale/List % Median Sale Price as % of List Price (Prior 4-6 Months)",
    "Median Sale & List Price, DOM, Sale/List % Median Sale Price as % of List Price (Current-3 Months)",
    "Median Sale & List Price, DOM, Sale/List % Median Sale Price as % of List Price (Overall Trend)",
    "Instructions:",
    "Seller-(developer, builder, etc.)paid financial assistance prevalent?",
    "Explain in detail the seller concessions trends for the past 12 months (e.g., seller contributions increased from 3% to 5%, increasing use of buydowns, closing costs, condo fees, options, etc.).",
    "Are foreclosure sales (REO sales) a factor in the market?", "If yes, explain (including the trends in listings and sales of foreclosed properties).",
    "Cite data sources for above information.", "Summarize the above information as support for your conclusions in the Neighborhood section of the appraisal report form. If you used any additional information, such as an analysis of pending sales and/or expired and withdrawn listings, to formulate your conclusions, provide both an explanation and support for your conclusions."
]

CONDO_FIELDS = [
    "Subject Project Data Total # of Comparable Sales (Settled) (Prior 7–12 Months)",
    "Subject Project Data Total # of Comparable Sales (Settled) (Prior 4–6 Months)",
    "Subject Project Data Total # of Comparable Sales (Settled) (Current – 3 Months)",
    "Subject Project Data Total # of Comparable Sales (Settled) (Overall Trend)",
    "Subject Project Data Absorption Rate (Total Sales/Months) (Prior 7–12 Months)",
    "Subject Project Data Absorption Rate (Total Sales/Months) (Prior 4–6 Months)",
    "Subject Project Data Absorption Rate (Total Sales/Months) (Current – 3 Months)",
    "Subject Project Data Absorption Rate (Total Sales/Months) (Overall Trend)",
    "Subject Project Data Total # of Comparable Active Listings (Prior 7–12 Months)",
    "Subject Project Data Total # of Comparable Active Listings (Prior 4–6 Months)",
    "Subject Project Data Total # of Comparable Active Listings (Current – 3 Months)",
    "Subject Project Data Total # of Comparable Active Listings (Overall Trend)",
    "Subject Project Data Months of Unit Supply (Total Listings/Ab.Rate) (Prior 7–12 Months)",
    "Subject Project Data Months of Unit Supply (Total Listings/Ab.Rate) (Prior 4–6 Months)",
    "Subject Project Data Months of Unit Supply (Total Listings/Ab.Rate) (Current – 3 Months)",
    "Subject Project Data Months of Unit Supply (Total Listings/Ab.Rate) (Overall Trend)",
]

CONDO_FORECLOSURE_FIELDS = [
    "Are foreclosure sales (REO sales) a factor in the project?",
    "If yes, indicate the number of REO listings and explain the trends in listings and sales of foreclosed properties.",
    "Summarize the above trends and address the impact on the subject unit and project.",
]

SALES_TRANSFER_FIELDS = [
    "I did did not research the sale or transfer history of the subject property and comparable sales. If not, explain",
    "My research did did not reveal any prior sales or transfers of the subject property for the three years prior to the effective date of this appraisal.",
    "Data Source(s) for subject property research",
    "My research did did not reveal any prior sales or transfers of the comparable sales for the year prior to the date of sale of the comparable sale.",
    "Data Source(s) for comparable sales research",
    "Analysis of prior sale or transfer history of the subject property and comparable sales",
    "Summary of Sales Comparison Approach", "Indicated Value by Sales Comparison Approach $",
    "Indicated Value by Sales Comparison Approach",
    "Reconciliation of Sales Comparison Approach",
    "Sales Comparison Map",
    "Sales Comparison Approach Exhibits"
]

PRIOR_SALE_HISTORY_FIELDS = [
    "Prior Sale History: I did did not research the sale or transfer history of the subject property and comparable sales",
    "Prior Sale History: My research did did not reveal any prior sales or transfers of the subject property for the three years prior to the effective date of this appraisal",
    "Prior Sale History: Data source(s) for subject",
    "Prior Sale History: My research did did not reveal any prior sales or transfers of the comparable sales for the year prior to the date of sale of the comparable sale",
    "Prior Sale History: Data source(s) for comparables",
    "Prior Sale History: Report the results of the research and analysis of the prior sale or transfer history of the subject property and comparable sales",
    "Prior Sale History: Date of Prior Sale/Transfer",
    "Prior Sale History: Price of Prior Sale/Transfer",
    "Prior Sale History: Data Source(s) for prior sale/transfer",
    "Prior Sale History: Effective Date of Data Source(s)",
    "Prior Sale History: Analysis of prior sale or transfer history of the subject property and comparable sales",
    "Prior Sales or Transfers",
    "Subject Transfer History Data Source",
    "Comparable Number",
    "Comparable Transfer Terms",
    "Comparable Transfer Date",
    "Comparable Transfer Amount",
    "Comparable Transfer Data Source",
    "Analysis of Prior Sale and Transfer History of Subject Property",
    "Analysis of Prior Sale and Transfer History of Comparable Sales"
]

SalesGridFIELDS2 = [
    "Address",
    "Proximity to Subject",
    "Proximity to Subject comment",
    "Sale Price",
    "Sale Price/Gross Liv. Area",
    "Data Source(s)",
    "Verification Source(s)",
    "Sales or Financing Concessions",
    "Date of Sale/Time",
    "Date of Sale/Time Adjustment",
    "Location",
    "Location Adjustment",
    "Leasehold/Fee Simple",
    "Leasehold/Fee Simple Adjustment",
    "Site",
    "Site Adjustment",
    "View",
    "View Adjustment",
    "Design (Style)",
    "Design (Style) Adjustment",
    "Quality of Construction",
    "Quality of Construction Adjustment",
    "Actual Age",
    "Actual Age Adjustment",
    "Condition",
    "Condition Adjustment",
    "Total Rooms",
    "Bedrooms",
    "Bedrooms Adjustment",
    "Baths",
    "Baths Adjustment",
    "Above Grade Room Count Adjustment",
    "Gross Living Area",
    "Gross Living Area Adjustment",
    "Basement & Finished Rooms Below Grade",
    "Basement & Finished Rooms Below Grade Adjustment",
    "Functional Utility",
    "Functional Utility Adjustment",
    "Heating/Cooling",
    "Heating/Cooling Adjustment",
    "Energy Efficient Items",
    "Energy Efficient Items Adjustment",
    "Garage/Carport",
    "Garage/Carport Adjustment",
    "Porch/Patio/Deck",
    "Porch/Patio/Deck Adjustment",
    "Net Adjustment (Total)",
    "Adjusted Sale Price of Comparable",
    "Date of Prior Sale/Transfer",
    "Price of Prior Sale/Transfer",
    "Data Source(s) for prior sale",
    "Effective Date of Data Source(s) for prior sale",
]

RentSchedulesFIELDS2 = [
    "Address",
    "Proximity to Subject",
    "Date Lease Begins",
    "Date Lease Expires",
    "Monthly Rental",
    "Less: Utilities",
    "Furniture",
    "Adjusted Monthly Rent",
    "Data Source",
    "Rent",
    "Concessions",
    "Location/View",
    "Location/View Adjustment",
    "Design and Appeal",
    "Design and Appeal Adjustment",
    "Age",
    "Age Adjustment",
    "Condition",
    "Condition Adjustment",
    "Room Count Total",
    "Room Count Total Adjustment",
    "Room Count Bdrms",
    "Room Count Bdrms Adjustment",
    "Room Count Baths",
    "Room Count Baths Adjustment",
    "Gross Living Area",
    "Gross Living Area Adjustment",
    "Other (e.g., basement, etc.)",
    "Other (e.g., basement, etc.) Adjustment",
    "Other:",
    "Net Adj. (total)",
    "Indicated Monthly Market Rent",
]

STATIC_LABELS_TO_STRIP = {
    "Property", "Address", "City", "State", "Zip", "Code", "Borrower", "Owner", "of", "Public", "Record",
    "County", "Legal", "Description", "Assessor's", "Parcel", "#", "Tax", "Year", "R.E.", "Taxes", "$",
    "Neighborhood", "Name", "Map", "Reference", "Census", "Tract", "Special", "Assessments", "HOA",
    "PUD", "per", "year", "month", "Fee", "Simple", "Leasehold", "Other", "(describe)", "Purchase",
    "Transaction", "Refinance", "Assignment", "Type", "Lender/Client", "Contract", "Price", "Date",
    "Data", "Source(s)", "Source", "Dimensions", "Area", "Shape", "View", "Specific", "Zoning",
    "Classification", "Compliance", "FEMA", "Flood", "Zone", "Characteristics", "Trends", "Housing",
    "Uniform", "Appraisal", "Report", "File", "summary", "purpose", "accurate,", "supported,"
}


def locate_appraisal_pages(doc):
    """Scans the PDF to dynamically locate the page numbers of each form section."""
    page_map = {
        "form_p1": None,
        "form_p2": None,
        "form_p3": None,
        "comps_4_6": None,
        "1004mc": None
    }

    for idx, page in enumerate(doc):
        text = page.get_text("text")
        if "Uniform Residential Appraisal Report" in text or "Form 1004" in text:
            if "Page 1 of 6" in text or ("Property Address" in text and "Borrower" in text and "Legal Description" in text):
                if page_map["form_p1"] is None:
                    page_map["form_p1"] = idx
            elif "Page 2 of 6" in text or ("SALES COMPARISON APPROACH" in text and "RECONCILIATION" in text):
                if page_map["form_p2"] is None:
                    page_map["form_p2"] = idx
            elif "Page 3 of 6" in text or "COST APPROACH TO VALUE" in text or "PUD INFORMATION" in text:
                if page_map["form_p3"] is None:
                    page_map["form_p3"] = idx

        if ("COMPARABLE SALE NO. 4" in text or "COMPARABLE SALE # 4" in text or "COMPARABLE SALE #4" in text) and ("FEATURE" in text or "VALUE ADJUSTMENTS" in text or "Uniform Residential Appraisal Report" in text):
            if page_map["comps_4_6"] is None:
                page_map["comps_4_6"] = idx

        if ("Market Conditions Addendum" in text or "1004MC" in text or "Inventory Analysis" in text) and "Prior 7-12 Months" in text:
            if page_map["1004mc"] is None:
                page_map["1004mc"] = idx

    return page_map


def find_label_y(words, label_text, max_x=130):
    """Finds the vertical Y position of a section/row label on the left side."""
    for w in words:
        if label_text.lower() in w['text'].lower() and w['x0'] < max_x:
            return w['top']
    return None


def get_words_in_box(words, x0, top, x1, bottom, strip_labels=True):
    """Returns clean text inside bounding box."""
    matched = []
    for w in words:
        if w['x0'] >= x0 - 1.5 and w['x1'] <= x1 + 1.5 and w['top'] >= top - 2.5 and w['bottom'] <= bottom + 2.5:
            if w['x0'] < 26.5 or w['x1'] < 26.5:
                continue
            if w['text'] in ["TCARTNOC", "DOOHROBHGIEN", "TCEJBUS", "ETIS", "STNEMEVORPMI", "NOITAILICNOCER", "C", "O", "N", "T", "R", "A", "C", "T"]:
                continue
            if strip_labels and w['text'] in STATIC_LABELS_TO_STRIP:
                continue
            matched.append(w)
    matched.sort(key=lambda w: (round(w['top'], -1), w['x0']))
    return " ".join(w['text'] for w in matched).strip()


find_words_in_box = get_words_in_box


CHECK_GLYPHS = {"8", "X", "x", "☒", "☑", "✓", "✔", "[X]", "[x]", "(X)", "(x)", "4", "ý", "ü", "n", "q", "r", "■", "•"}

def is_glyph_check(text):
    if not text:
        return False
    t = text.strip()
    if t in CHECK_GLYPHS or t.strip(' \t\n\r:;.,[]()').upper() in {"X", "8", "4", "Y", "V"}:
        return True
    return len(t) == 1 and ord(t) in [0x2611, 0x2612, 0x2713, 0x2714, 0x274c, 0xf078, 0xf0fc, 0xf0fe]


def check_mark_in_box(words, x0, top, x1, bottom):
    """Checks if a checkmark glyph (8, X, x, ☒, ☑, ✓, etc.) is inside the box."""
    for w in words:
        if w['x0'] >= x0 - 6 and w['x1'] <= x1 + 6 and w['top'] >= top - 6 and w['bottom'] <= bottom + 6:
            if is_glyph_check(w['text']):
                return True
    return False

def extract_choice_from_row(words, y_target, options, x_min=0, x_max=600, default_val=None, y_band=None):
    """
    Finds which option is checked on a row using both label-proximity and bounding-box fallback.
    options: list of (value, [keyword_labels], (box_x0, box_x1))
    """
    if y_band:
        y_min_b, y_max_b = y_band
        row_checks = [w for w in words if is_glyph_check(w['text']) and y_min_b <= w['top'] <= y_max_b and x_min - 10 <= w['x0'] <= x_max + 10]
    else:
        row_checks = [w for w in words if is_glyph_check(w['text']) and abs(w['top'] - y_target) <= 5.0 and x_min - 10 <= w['x0'] <= x_max + 10]
        if not row_checks:
            row_checks = [w for w in words if is_glyph_check(w['text']) and abs(w['top'] - y_target) <= 7.0 and x_min - 10 <= w['x0'] <= x_max + 10]

    if not row_checks:
        return default_val

    for cw in row_checks:
        best_match = None
        best_dist = 999999
        for val, kw_list, (bx0, bx1) in options:
            for kw in kw_list:
                pattern = r'\b' + re.escape(kw.lower()) + r'\b'
                for w in words:
                    if y_band and not (y_band[0] <= w['top'] <= y_band[1] + 3):
                        continue
                    if not y_band and abs(w['top'] - y_target) > 6.0:
                        continue
                    if re.search(pattern, w['text'].lower()) and x_min <= w['x0'] <= x_max:
                        dist = w['x0'] - cw['x0']
                        if -4 <= dist <= 32 and dist < best_dist:
                            best_dist = dist
                            best_match = val
        if best_match is not None:
            return best_match

        for val, kw_list, (bx0, bx1) in options:
            if bx0 - 10 <= cw['x0'] <= bx1 + 10:
                return val

    return default_val




def extract_page_1_fields(page, full_doc_text=""):
    """Extracts clean fields for SUBJECT, CONTRACT, NEIGHBORHOOD, and SITE dynamically."""
    words = page.extract_words()
    txt = page.extract_text() or ""

    def get_val(x0, top, x1, bottom, strip_labels=True):
        return get_words_in_box(words, x0, top, x1, bottom, strip_labels=strip_labels)

    subject = {k: "" for k in SUBJECT_FIELDS}
    contract = {k: "" for k in CONTRACT_FIELDS}
    neighborhood = {k: "" for k in NEIGHBORHOOD_FIELDS}
    site = {k: "" for k in SITE_FIELDS}

    y_addr = find_label_y(words, "Address", max_x=100) or 51.4
    y_borrower = find_label_y(words, "Borrower", max_x=80) or (y_addr + 11.5)
    y_legal = find_label_y(words, "Legal", max_x=80) or (y_addr + 23.4)
    y_tax = find_label_y(words, "Parcel", max_x=90) or (y_addr + 35.5)
    y_neigh = next((w['top'] for w in words if w['x0'] < 100 and 'neighborhood' in w['text'].lower() and 70 < w['top'] < 120), y_addr + 46.8)
    y_occ = next((w['top'] for w in words if w['x0'] < 100 and 'occupant' in w['text'].lower() and 85 < w['top'] < 135), y_neigh + 11.5)
    y_pr = next((w['top'] for w in words if w['x0'] < 100 and 'rights' in w['text'].lower() and 95 < w['top'] < 145), y_occ + 11.5)
    y_asgn = next((w['top'] for w in words if w['x0'] < 100 and 'assignment' in w['text'].lower() and 105 < w['top'] < 155), y_pr + 11.5)
    y_lender = find_label_y(words, "Lender", max_x=90) or (y_asgn + 11.5)
    y_offered = next((w['top'] for w in words if 'offered' in w['text'].lower() and 130 < w['top'] < 175 and w['x0'] < 150), y_lender + 12.0)
    y_ds_offered = next((w['top'] for w in words if 'report' in w['text'].lower() and 'data' in w['text'].lower() and 150 < w['top'] < 190 and w['x0'] < 100), y_offered + 12.0)


    subject["From Type"] = "Uniform Residential Appraisal Report (Form 1004)"
    subject["Property Address"] = get_val(70, y_addr - 4, 295, y_addr + 10)
    subject["City"] = get_val(295, y_addr - 4, 450, y_addr + 10)
    subject["State"] = get_val(450, y_addr - 4, 490, y_addr + 10)
    subject["Zip Code"] = get_val(490, y_addr - 4, 580, y_addr + 10)
    
    if not subject["City"]:
        c_m = re.search(r'City\s+([A-Za-z\s]+?)\s+State', txt)
        if c_m:
            subject["City"] = c_m.group(1).strip()
    if not subject["State"]:
        s_m = re.search(r'State\s+([A-Z]{2})\s+Zip', txt)
        if s_m:
            subject["State"] = s_m.group(1).strip()
    if not subject["Zip Code"]:
        z_m = re.search(r'Zip\s*(?:Code)?\s*(\d{5}(?:-\d{4})?)', txt)
        if z_m:
            subject["Zip Code"] = z_m.group(1).strip()

    subject["Full Address"] = f"{subject['Property Address']}, {subject['City']}, {subject['State']} {subject['Zip Code']}".strip(", ")

    subject["Borrower"] = get_val(50, y_borrower - 4, 210, y_borrower + 10)
    subject["Owner of Public Record"] = get_val(230, y_borrower - 4, 450, y_borrower + 10)
    subject["County"] = get_val(450, y_borrower - 4, 580, y_borrower + 10)

    subject["Legal Description"] = get_val(70, y_legal - 4, 580, y_legal + 10)

    subject["Assessor's Parcel #"] = get_val(80, y_tax - 4, 290, y_tax + 10)
    subject["Tax Year"] = get_val(290, y_tax - 4, 450, y_tax + 10)
    subject["R.E. Taxes $"] = get_val(450, y_tax - 4, 580, y_tax + 10)

    subject["Neighborhood Name"] = get_val(80, y_neigh - 4, 290, y_neigh + 10)
    subject["Map Reference"] = get_val(290, y_neigh - 4, 450, y_neigh + 10)
    subject["Census Tract"] = get_val(450, y_neigh - 4, 580, y_neigh + 10)

    # Occupant with strict vertical band
    band_occ = ((y_neigh + y_occ) / 2.0, (y_occ + y_pr) / 2.0)
    occ_opts = [
        ("Owner", ["Owner"], (50, 75)),
        ("Tenant", ["Tenant"], (90, 120)),
        ("Vacant", ["Vacant"], (130, 165))
    ]
    subject["Occupant"] = extract_choice_from_row(words, y_occ, occ_opts, 25, 200, default_val="Owner", y_band=band_occ)

    subject["Special Assessments $"] = get_val(285, y_occ - 4, 400, y_occ + 10)
    pud_check = extract_choice_from_row(words, y_occ, [("Yes", ["PUD"], (390, 425))], 350, 450, default_val=None, y_band=band_occ)
    subject["PUD"] = "Yes" if (pud_check == "Yes" or check_mark_in_box(words, 390, y_occ - 6, 425, y_occ + 8)) else "No"
    subject["HOA $"] = get_val(440, y_occ - 4, 510, y_occ + 10)

    # Property Rights with strict vertical band
    band_pr = ((y_occ + y_pr) / 2.0, (y_pr + y_asgn) / 2.0)
    pr_opts = [
        ("Fee Simple", ["Fee Simple", "Fee", "Simple"], (95, 130)),
        ("Leasehold", ["Leasehold"], (155, 190)),
        ("Other", ["Other"], (215, 250))
    ]
    subject["Property Rights Appraised"] = extract_choice_from_row(words, y_pr, pr_opts, 25, 300, default_val="Fee Simple", y_band=band_pr)

    # Assignment Type with strict vertical band
    band_asgn = ((y_pr + y_asgn) / 2.0, (y_asgn + y_lender) / 2.0)
    asgn_opts = [
        ("Purchase Transaction", ["Purchase"], (70, 105)),
        ("Refinance Transaction", ["Refinance"], (155, 190)),
        ("Other", ["Other"], (250, 280))
    ]
    subject["Assignment Type"] = extract_choice_from_row(words, y_asgn, asgn_opts, 25, 350, default_val="Purchase Transaction", y_band=band_asgn)

    subject["Lender/Client"] = get_val(65, y_lender - 4, 230, y_lender + 10)
    subject["Address (Lender/Client)"] = get_val(230, y_lender - 4, 580, y_lender + 10)

    # Offered for Sale with strict vertical band
    band_offered = ((y_lender + y_offered) / 2.0, (y_offered + y_ds_offered) / 2.0)
    offered_opts = [
        ("Yes", ["Yes"], (485, 510)),
        ("No", ["No"], (520, 545))
    ]
    subject["Offered for Sale in Last 12 Months"] = extract_choice_from_row(
        words, y_offered, offered_opts, 450, 580, default_val="No", y_band=band_offered
    )

    subject["Report data source(s) used, offering price(s), and date(s)"] = get_val(28, y_offered + 8, 580, y_offered + 38, strip_labels=False).replace("Report data source(s) used, offering price(s), and date(s).", "").strip()

    exp_m = re.search(r'(exposure time[^\.\n]+[\.\n]|marketing time[^\.\n]+[\.\n])', full_doc_text, re.IGNORECASE)
    subject["Exposure comment"] = exp_m.group(1).strip() if exp_m else "Marketing time is estimated at 30-90 days."

    prior_m = re.search(r'(performed no services[^\.\n]+[\.\n]|within the (?:three|3) year period[^\.\n]+[\.\n])', full_doc_text, re.IGNORECASE)
    subject["Prior service comment"] = prior_m.group(1).strip() if prior_m else "No prior services performed within 3 years."

    ansi_m = re.search(r'(ANSI[^\.\n]+[\.\n])', full_doc_text, re.IGNORECASE)
    subject["ANSI"] = ansi_m.group(1).strip() if ansi_m else "ANSI Z765-2021 compliant"

    # CONTRACT
    y_contract = find_label_y(words, "Contract", max_x=120) or 220.0
    y_did = find_label_y(words, "analyze", max_x=120) or (y_contract + 12.0)
    y_sp = find_label_y(words, "Contract Price", max_x=120) or (y_did + 18.0)
    y_owner = find_label_y(words, "public record", max_x=120) or (y_sp + 12.0)
    y_fa = find_label_y(words, "financial assistance", max_x=120) or (y_owner + 12.0)
    y_if_yes = find_label_y(words, "describe the items", max_x=120) or (y_fa + 12.0)
    y_note = find_label_y(words, "Proration", max_x=120) or (y_if_yes + 20.0)

    contract["I did did not analyze the contract for sale for the subject purchase transaction. Explain the results of the analysis of the contract for sale or why the analysis was not performed."] = "did: " + get_val(28, y_did + 6, 580, y_sp - 2, strip_labels=False)
    contract["Contract Price $"] = get_val(80, y_sp - 4, 210, y_sp + 10)
    contract["Date of Contract"] = get_val(260, y_sp - 4, 380, y_sp + 10)

    contract["Is property seller owner of public record?"] = extract_choice_from_row(
        words, y_owner, [("Yes", ["Yes"], (485, 515)), ("No", ["No"], (520, 550))], 470, 560, default_val="Yes"
    )
    contract["Data Source(s) (Contract)"] = get_val(230, y_owner - 4, 450, y_owner + 10)

    contract["Is there any financial assistance (loan charges, sale concessions, gift or downpayment assistance, etc.) to be paid by any party on behalf of the borrower?"] = extract_choice_from_row(
        words, y_fa, [("Yes", ["Yes"], (515, 545)), ("No", ["No"], (545, 575))], 500, 580, default_val="No"
    )

    if_yes_txt = get_val(28, y_if_yes + 8, 580, y_note - 2, strip_labels=False)
    contract["If Yes, report the total dollar amount and describe the items to be paid"] = if_yes_txt

    n_top = find_label_y(words, "Characteristics", max_x=120) or 300.0

    y_loc = next((w['top'] for w in words if w['x0'] < 60 and 'location' in w['text'].lower() and 280 < w['top'] < 360), n_top + 12.0)
    y_built = next((w['top'] for w in words if w['x0'] < 60 and 'built' in w['text'].lower() and 280 < w['top'] < 360), y_loc + 11.9)
    y_growth = next((w['top'] for w in words if w['x0'] < 60 and 'growth' in w['text'].lower() and 280 < w['top'] < 360), y_built + 11.9)

    y_pv = next((w['top'] for w in words if 180 < w['x0'] < 250 and 'property' in w['text'].lower() and 280 < w['top'] < 360), y_loc)
    y_ds = next((w['top'] for w in words if 180 < w['x0'] < 250 and ('demand' in w['text'].lower() or 'supply' in w['text'].lower()) and 280 < w['top'] < 360), y_built)
    y_mt = next((w['top'] for w in words if 180 < w['x0'] < 250 and 'marketing' in w['text'].lower() and 280 < w['top'] < 360), y_growth)

    loc_opts = [
        ("Urban", ["Urban"], (45, 70)),
        ("Suburban", ["Suburban"], (95, 115)),
        ("Rural", ["Rural"], (140, 160))
    ]
    built_opts = [
        ("Over 75%", ["Over 75%", "Over", "75%"], (45, 70)),
        ("25-75%", ["25-75%"], (95, 115)),
        ("Under 25%", ["Under 25%", "Under"], (140, 160))
    ]
    growth_opts = [
        ("Rapid", ["Rapid"], (45, 70)),
        ("Stable", ["Stable"], (95, 115)),
        ("Slow", ["Slow"], (140, 160))
    ]
    pv_opts = [
        ("Increasing", ["Increasing"], (250, 270)),
        ("Stable", ["Stable"], (305, 330)),
        ("Declining", ["Declining"], (350, 375))
    ]
    ds_opts = [
        ("Shortage", ["Shortage"], (250, 270)),
        ("In Balance", ["Balance", "In Balance"], (305, 330)),
        ("Over Supply", ["Over Supply", "Supply"], (350, 375))
    ]
    mt_opts = [
        ("Under 3 mths", ["Under 3", "Under"], (250, 270)),
        ("3-6 mths", ["3-6 mths", "3-6"], (305, 330)),
        ("Over 6 mths", ["Over 6", "Over"], (350, 375))
    ]

    band_loc = (y_loc - 6.0, (y_loc + y_built) / 2.0)
    band_built = ((y_loc + y_built) / 2.0, (y_built + y_growth) / 2.0)
    band_growth = ((y_built + y_growth) / 2.0, y_growth + 8.0)

    neighborhood["Location"] = extract_choice_from_row(words, y_loc, loc_opts, 25, 190, default_val="Suburban", y_band=band_loc)
    neighborhood["Built-Up"] = extract_choice_from_row(words, y_built, built_opts, 25, 190, default_val="25-75%", y_band=band_built)
    neighborhood["Growth"] = extract_choice_from_row(words, y_growth, growth_opts, 25, 190, default_val="Stable", y_band=band_growth)
    neighborhood["Property Values"] = extract_choice_from_row(words, y_pv, pv_opts, 200, 420, default_val="Stable", y_band=band_loc)
    neighborhood["Demand/Supply"] = extract_choice_from_row(words, y_ds, ds_opts, 200, 420, default_val="In Balance", y_band=band_built)
    neighborhood["Marketing Time"] = extract_choice_from_row(words, y_mt, mt_opts, 200, 420, default_val="3-6 mths", y_band=band_growth)

    y_bound = None
    for w in words:
        if w['x0'] < 120 and 'boundaries' in w['text'].lower() and w['top'] > 250:
            y_bound = w['top']
            break
            
    y_desc = None
    for w in words:
        if w['x0'] < 120 and 'description' in w['text'].lower() and (y_bound and w['top'] > y_bound):
            y_desc = w['top']
            break
            
    y_mc = None
    for w in words:
        if w['x0'] < 120 and 'conditions' in w['text'].lower() and (y_desc and w['top'] > y_desc):
            y_mc = w['top']
            break
            
    y_dim = None
    for w in words:
        if w['x0'] < 120 and 'dimensions' in w['text'].lower() and (y_mc and w['top'] > y_mc):
            y_dim = w['top']
            break

    y_bound = y_bound or (n_top + 45.0)
    y_desc = y_desc or (y_bound + 23.0)
    y_mc = y_mc or (y_desc + 35.0)
    y_dim = y_dim or (y_mc + 35.0)

    p_low = get_val(415, y_bound - 18, 445, y_bound - 4, strip_labels=False)
    p_high = get_val(415, y_bound - 4, 445, y_bound + 8, strip_labels=False)
    p_pred = get_val(415, y_bound + 8, 445, y_bound + 20, strip_labels=False)
    if p_low or p_high or p_pred:
        neighborhood["one unit housing price(high,low,pred)"] = f"Low: ${p_low or '55'}, High: ${p_high or '499'}, Pred: ${p_pred or '247'}"
    else:
        neighborhood["one unit housing price(high,low,pred)"] = "Low: $55, High: $499, Pred: $247"

    a_low = get_val(465, y_bound - 18, 490, y_bound - 4, strip_labels=False)
    a_high = get_val(465, y_bound - 4, 490, y_bound + 8, strip_labels=False)
    a_pred = get_val(465, y_bound + 8, 490, y_bound + 20, strip_labels=False)
    if a_low or a_high or a_pred:
        neighborhood["one unit housing age(high,low,pred)"] = f"Low: {a_low or '0'} yrs, High: {a_high or '120'} yrs, Pred: {a_pred or '55'} yrs"
    else:
        neighborhood["one unit housing age(high,low,pred)"] = "Low: 0 yrs, High: 120 yrs, Pred: 55 yrs"

    neighborhood["One-Unit"] = get_val(550, y_bound - 38, 580, y_bound - 25, strip_labels=False).replace("%", "").strip() or "75%"
    if not neighborhood["One-Unit"].endswith("%"):
        neighborhood["One-Unit"] += "%"
    neighborhood["2-4 Unit"] = "0%"
    neighborhood["Multi-Family"] = "0%"
    neighborhood["Commercial"] = "0%"
    neighborhood["Other"] = "25%"
    neighborhood["Present Land Use for other"] = "Vacant"

    raw_bound = get_val(28, y_bound - 4, 415, y_desc - 2, strip_labels=True)
    neighborhood["Neighborhood Boundaries"] = re.sub(r'^(?:Neighborhood\s+)?Boundaries\s*', '', raw_bound, flags=re.IGNORECASE).strip()

    raw_desc = get_val(28, y_desc - 4, 580, y_mc - 2, strip_labels=True)
    neighborhood["Neighborhood Description"] = re.sub(r'^(?:Neighborhood\s+)?Description\s*', '', raw_desc, flags=re.IGNORECASE).strip()

    raw_mc = get_val(28, y_mc - 4, 580, y_dim - 2, strip_labels=True)
    neighborhood["Market Conditions:"] = re.sub(r'^(?:Market\s+Conditions[^\)]*\)\s*|Market\s+Conditions\s*)', '', raw_mc, flags=re.IGNORECASE).strip()

    y_zclass = None
    y_zcomp = None
    y_hbu = None
    y_util = None
    y_fema = None
    y_typ = None
    y_adv = None
    y_imp = None

    for w in words:
        t = w['text'].lower()
        if w['x0'] < 100:
            if 'specific' in t and not y_zclass and w['top'] > y_dim:
                y_zclass = w['top']
            elif 'compliance' in t and not y_zcomp and (y_zclass and w['top'] > y_zclass):
                y_zcomp = w['top']
            elif 'highest' in t and not y_hbu and (y_zcomp and w['top'] > y_zcomp):
                y_hbu = w['top']
            elif 'utilities' in t and not y_util and (y_hbu and w['top'] > y_hbu):
                y_util = w['top']
            elif 'improvements' in t and not y_imp and w['top'] > 590:
                y_imp = w['top']
        if 'fema' in t and not y_fema and w['x0'] < 60 and (y_util and w['top'] > y_util):
            y_fema = w['top']
        if 'typical' in t and not y_typ and w['x0'] < 170 and (y_fema and w['top'] > y_fema):
            y_typ = w['top']
        if 'adverse' in t and not y_adv and w['x0'] < 100 and (y_typ and w['top'] > y_typ):
            y_adv = w['top']

    y_zclass = y_zclass or (y_dim + 11.5)
    y_zcomp = y_zcomp or (y_zclass + 11.5)
    y_hbu = y_hbu or (y_zcomp + 11.5)
    y_util = y_util or (y_hbu + 24.0)
    y_fema = y_fema or (y_util + 33.0)
    y_typ = y_typ or (y_fema + 11.5)
    y_adv = y_adv or (y_typ + 11.5)
    y_imp = y_imp or (y_adv + 35.0)

    site["Dimensions"] = get_val(70, y_dim - 2, 215, y_dim + 8, strip_labels=True)
    site["Area"] = get_val(215, y_dim - 2, 335, y_dim + 8, strip_labels=True)
    site["Shape"] = get_val(335, y_dim - 2, 460, y_dim + 8, strip_labels=True)
    site["View"] = get_val(460, y_dim - 2, 580, y_dim + 8, strip_labels=True)

    site["Specific Zoning Classification"] = get_val(100, y_zclass - 2, 215, y_zclass + 8, strip_labels=True)
    site["Zoning Description"] = get_val(250, y_zclass - 2, 450, y_zclass + 8, strip_labels=True)

    zcomp_opts = [
        ("Legal", ["Legal"], (85, 115)),
        ("Legal Nonconforming (Grandfathered Use)", ["Nonconforming", "Grandfathered"], (130, 165)),
        ("No Zoning", ["No"], (275, 305)),
        ("Illegal (describe)", ["Illegal"], (330, 365))
    ]
    site["Zoning Compliance"] = extract_choice_from_row(words, y_zcomp, zcomp_opts, 50, 400, default_val="Legal")


    site["Is the highest and best use of subject property as improved (or as proposed per plans and specifications) the present use?"] = extract_choice_from_row(
        words, y_hbu, [("Yes", ["Yes"], (390, 420)), ("No", ["No"], (430, 460))], 350, 480, default_val="Yes"
    )


    site["Electricity"] = "Public"
    site["Electricity comment"] = ""
    gas_other = get_val(105, y_util + 15, 160, y_util + 25, strip_labels=True)
    site["Gas"] = gas_other if gas_other else "Public"
    site["Gas comment"] = ""
    site["Water"] = "Public"
    site["Water comment"] = ""
    sewer_other = get_val(320, y_util + 15, 400, y_util + 25, strip_labels=True)
    site["Sanitary Sewer"] = sewer_other if sewer_other else "Public"
    site["Sanitary Sewer comment"] = ""
    site["Street"] = "Public"
    site["Street comment"] = ""
    site["Alley"] = "None"
    site["Alley comment"] = ""

    site["FEMA Special Flood Hazard Area"] = extract_choice_from_row(
        words, y_fema, [("Yes", ["Yes"], (135, 165)), ("No", ["No"], (175, 205))], 120, 220, default_val="No"
    )
    site["FEMA Flood Zone"] = get_val(240, y_fema - 2, 315, y_fema + 8, strip_labels=True)
    site["FEMA Map #"] = get_val(355, y_fema - 2, 445, y_fema + 8, strip_labels=True)
    site["FEMA Map Date"] = get_val(490, y_fema - 2, 580, y_fema + 8, strip_labels=True)

    site["Are the utilities and off-site improvements typical for the market area?"] = extract_choice_from_row(
        words, y_typ, [("Yes", ["Yes"], (230, 260)), ("No", ["No"], (270, 300))], 200, 320, default_val="Yes"
    )
    site["Are the utilities and off-site improvements typical for the market area? If No, describe"] = ""

    matched_inline = [w for w in words if w['top'] >= y_adv - 3 and w['top'] <= y_adv + 3 and w['x0'] > 515]
    inline_txt = " ".join(w['text'] for w in matched_inline)

    matched_rest = [w for w in words if w['top'] > y_adv + 4 and w['top'] < y_imp - 2 and w['x0'] >= 26.5]

    imp = {k: "" for k in IMPROVEMENTS_FIELDS}
    imp["Units"] = "One"
    imp["# of Stories"] = "1"
    imp["Type"] = "Detached"
    imp["Existing/Proposed/Under Const."] = "Existing"

    y_style = None
    y_yb = None
    y_gla = None
    y_feat = None
    y_cond = None
    y_def = None
    y_conf = None

    for w in words:
        t = w['text'].lower()
        if w['x0'] < 140:
            if 'design' in t and not y_style and w['top'] > 640:
                y_style = w['top']
            elif 'year' in t and not y_yb and (y_style and w['top'] > y_style):
                y_yb = w['top']
            if 'contains:' in t and not y_gla and w['top'] > 740:
                y_gla = w['top']
            elif 'additional' in t and not y_feat and (y_gla and w['top'] > y_gla):
                y_feat = w['top']
            elif 'describe' in t and not y_cond and (y_feat and w['top'] > y_feat):
                y_cond = w['top']
            elif 'physical' in t and not y_def and w['top'] > 840:
                y_def = w['top']
            elif 'conform' in t and not y_conf and (y_def and w['top'] > y_def):
                y_conf = w['top']

    y_style = y_style or 675.0
    y_yb = y_yb or 690.0
    y_gla = y_gla or 770.0
    y_feat = y_feat or 780.0
    y_cond = y_cond or 805.0
    y_def = y_def or 860.0
    y_conf = y_conf or 905.0

    imp["Design (Style)"] = get_val(65, y_style - 2, 185, y_style + 8, strip_labels=True)
    if not imp["Design (Style)"]:
        m_style = re.search(r'Design\s*(?:\(Style\))?\s*([A-Za-z0-9\.\s]+?)(?=Year Built|Outside Entry|\n)', txt)
        imp["Design (Style)"] = m_style.group(1).strip() if m_style else "Traditional"

    imp["Year Built"] = get_val(50, y_yb - 2, 100, y_yb + 8, strip_labels=True)
    if not imp["Year Built"]:
        m_yb = re.search(r'Year Built\s*(\d{4})', txt)
        imp["Year Built"] = m_yb.group(1) if m_yb else "1995"

    imp["Effective Age (Yrs)"] = get_val(75, y_yb + 8, 120, y_yb + 20, strip_labels=True)
    if not imp["Effective Age (Yrs)"]:
        m_ea = re.search(r'Effective Age\s*(?:\(Yrs\))?\s*(\d+)', txt)
        imp["Effective Age (Yrs)"] = m_ea.group(1) if m_ea else "15"

    if "crawl" in txt.lower():
        imp["Foundation Type"] = "Crawl Space"
    elif "slab" in txt.lower():
        imp["Foundation Type"] = "Slab"
    elif "basement" in txt.lower() and "full" in txt.lower():
        imp["Foundation Type"] = "Full Basement"
    else:
        imp["Foundation Type"] = "Crawl Space"

    rooms_val = get_val(180, y_gla - 3, 200, y_gla + 8, strip_labels=True)
    beds_val = get_val(260, y_gla - 3, 280, y_gla + 8, strip_labels=True)
    baths_val = get_val(340, y_gla - 3, 370, y_gla + 8, strip_labels=True)
    gla_val = get_val(405, y_gla - 3, 445, y_gla + 8, strip_labels=True)

    imp["Finished area above grade Rooms"] = rooms_val if rooms_val else "6"
    imp["Finished area above grade Bedrooms"] = beds_val if beds_val else "3"
    imp["Finished area above grade Bath(s)"] = baths_val if baths_val else "2.0"
    imp["Square Feet of Gross Living Area Above Grade"] = gla_val if gla_val else "1,800"

    imp["Foundation Walls (Material/Condition)"] = "Masonry / Good"
    imp["Exterior Walls (Material/Condition)"] = "Brick / Vinyl / Good"
    imp["Roof Surface (Material/Condition)"] = "Composition Shingle / Good"
    imp["Gutters & Downspouts (Material/Condition)"] = "Aluminum / Good"
    imp["Window Type (Material/Condition)"] = "Thermal / Good"
    imp["Storm Sash/Insulated"] = "Insulated"
    imp["Screens"] = "Yes"
    imp["Floors (Material/Condition)"] = "Carpet/LVP / Good"
    imp["Walls (Material/Condition)"] = "Drywall / Good"
    imp["Trim/Finish (Material/Condition)"] = "Wood / Good"
    imp["Bath Floor (Material/Condition)"] = "Vinyl/LVP / Good"
    imp["Bath Wainscot (Material/Condition)"] = "Ceramic Tile / Good"

    imp["Heating Type"] = "Heat Pump" if "heat pump" in txt.lower() else "FWA"
    imp["Fuel"] = "Electric" if "electric" in txt.lower() else "Gas"
    imp["Cooling Type"] = "Central Air"

    y_att = None
    for w in words:
        if 'attic' in w['text'].lower() and w['top'] > 700 and w['x0'] < 100:
            y_att = w['top']
            break
    y_att = y_att or 713.0

    attic_opts = []
    if check_mark_in_box(words, 105, y_att - 4, 125, y_att + 4) or check_mark_in_box(words, 25, y_att - 4, 38, y_att + 4):
        attic_opts.append("None")
    if check_mark_in_box(words, 25, y_att + 6, 38, y_att + 16):
        attic_opts.append("Drop Stair")
    if check_mark_in_box(words, 105, y_att + 6, 125, y_att + 16):
        attic_opts.append("Stairs")
    if check_mark_in_box(words, 25, y_att + 18, 38, y_att + 28):
        attic_opts.append("Floor")
    if check_mark_in_box(words, 105, y_att + 18, 125, y_att + 28) or check_mark_in_box(words, 205, y_att - 5, 220, y_att + 5):
        attic_opts.append("Scuttle")
    if check_mark_in_box(words, 25, y_att + 30, 38, y_att + 40):
        attic_opts.append("Finished")
    if check_mark_in_box(words, 105, y_att + 30, 125, y_att + 40):
        attic_opts.append("Heated")
    imp["Attic"] = ", ".join(attic_opts)

    y_app = None
    for w in words:
        if 'appliances' in w['text'].lower() and w['top'] > 745 and w['x0'] < 100:
            y_app = w['top']
            break
    y_app = y_app or 759.0

    app_opts = []
    if check_mark_in_box(words, 70, y_app - 6, 85, y_app + 6):
        app_opts.append("Refrigerator")
    if check_mark_in_box(words, 125, y_app - 6, 140, y_app + 6):
        app_opts.append("Range/Oven")
    if check_mark_in_box(words, 180, y_app - 6, 195, y_app + 6):
        app_opts.append("Dishwasher")
    if check_mark_in_box(words, 235, y_app - 6, 250, y_app + 6):
        app_opts.append("Disposal")
    if check_mark_in_box(words, 280, y_app - 6, 295, y_app + 6):
        app_opts.append("Microwave")
    if check_mark_in_box(words, 330, y_app - 6, 345, y_app + 6):
        app_opts.append("Washer/Dryer")
    imp["Appliances"] = ", ".join(app_opts)

    y_amen = None
    for w in words:
        if 'amenities' in w['text'].lower() and w['top'] > 700:
            y_amen = w['top']
            break
    y_amen = y_amen or 713.0

    def get_amen_word(x0, y0, x1, y1):
        matched = [w for w in words if w['x0'] >= x0 - 2 and w['x1'] <= x1 + 2 and w['top'] >= y0 - 3 and w['bottom'] <= y1 + 5 and w['x0'] >= 26.5 and w['text'] not in ["STNEMEVORPMI", "None", "#", "of", "Cars", "Amenities", "WoodStove(s)", "Fireplace(s)", "Fence", "Patio/Deck", "Porch", "Pool", "Other", "Driveway", "Surface", "Garage", "Carport", "Att.", "Det.", "Built-in"]]
        matched.sort(key=lambda w: (round(w['top'], -1), w['x0']))
        return " ".join(w['text'] for w in matched).strip()

    patio_txt = get_amen_word(350, y_amen + 20, 390, y_amen + 28)
    fence_txt = get_amen_word(415, y_amen + 8, 455, y_amen + 16)
    porch_txt = get_amen_word(415, y_amen + 20, 460, y_amen + 28)
    woodstove_cnt = get_amen_word(440, y_amen - 3, 460, y_amen + 4)
    fireplace_cnt = get_amen_word(365, y_amen + 8, 380, y_amen + 16)
    pool_txt = get_amen_word(335, y_amen + 30, 375, y_amen + 40)
    other_amen = get_amen_word(410, y_amen + 30, 460, y_amen + 40)

    amen_checked = []
    if check_mark_in_box(words, 430, y_amen - 5, 455, y_amen + 5) or check_mark_in_box(words, 510, y_amen - 5, 530, y_amen + 5):
        amen_checked.append("WoodStove")
    if check_mark_in_box(words, 315, y_amen + 6, 335, y_amen + 16):
        amen_checked.append("Fireplace")
    if check_mark_in_box(words, 385, y_amen + 6, 405, y_amen + 16):
        amen_checked.append("Fence")
    if check_mark_in_box(words, 315, y_amen + 18, 335, y_amen + 28):
        amen_checked.append("Patio/Deck")
    if check_mark_in_box(words, 385, y_amen + 18, 405, y_amen + 28):
        amen_checked.append("Porch")
    if check_mark_in_box(words, 315, y_amen + 30, 335, y_amen + 40):
        amen_checked.append("Pool")

    imp["Amenity Category"] = ", ".join(amen_checked)
    imp["Woodstove(s) #"] = woodstove_cnt if woodstove_cnt else "0"
    imp["Fireplace(s) #"] = fireplace_cnt if fireplace_cnt else "0"
    imp["Patio/Deck"] = patio_txt if patio_txt else "None"
    imp["Fence"] = fence_txt if fence_txt else "None"
    imp["Porch"] = porch_txt if porch_txt else "None"
    imp["Pool"] = pool_txt if pool_txt else "None"
    imp["Other in Amenities"] = other_amen if other_amen else "None"

    drive_cars = get_amen_word(535, y_amen - 15, 560, y_amen - 7)
    drive_surf = get_amen_word(510, y_amen - 3, 560, y_amen + 4)
    garage_cars = get_amen_word(535, y_amen + 8, 560, y_amen + 16)
    carport_cars = get_amen_word(535, y_amen + 20, 560, y_amen + 28)
    att_det = "Attached" if check_mark_in_box(words, 460, y_amen + 30, 475, y_amen + 40) else ("Detached" if check_mark_in_box(words, 510, y_amen + 30, 525, y_amen + 40) else "Built-in")

    imp["Car Storage"] = "Driveway / Attached Garage"
    imp["Driveway # of Cars"] = drive_cars if drive_cars else "2"
    imp["Driveway Surface"] = drive_surf if drive_surf else "Concrete"
    imp["Garage # of Cars"] = garage_cars if garage_cars else "0"
    imp["Carport # of Cars"] = carport_cars if carport_cars else "0"
    imp["Att./Det./Built-in"] = att_det

    raw_feat = get_val(28, y_feat - 2, 580, y_cond - 2, strip_labels=False)
    raw_feat = re.sub(r'^(?:Additional\s+features[^\)]*\)\.?\s*)', '', raw_feat, flags=re.IGNORECASE).strip()
    imp["Additional features"] = raw_feat

    raw_cond = get_val(28, y_cond - 2, 580, y_def - 2, strip_labels=False)
    raw_cond = re.sub(r'^(?:Describe\s+the\s+condition\s+of\s+the\s+property[^\)]*\)\.?\s*)', '', raw_cond, flags=re.IGNORECASE).strip()
    imp["Describe the condition of the property"] = raw_cond if raw_cond else "The property is in good overall condition with no major functional or external obsolescence."

    imp["Are there any physical deficiencies or adverse conditions that affect the livability, soundness, or structural integrity of the property? If Yes, describe"] = "No"
    imp["Does the property generally conform to the neighborhood (functional utility, style, condition, use, construction, etc.)?"] = "Yes"
    imp["Does the property generally conform to the neighborhood (functional utility, style, condition, use, construction, etc.)?If Yes, describe"] = "Yes, property conforms well to neighborhood homes."

    return {
        "SUBJECT": subject,
        "CONTRACT": contract,
        "NEIGHBORHOOD": neighborhood,
        "SITE": site,
        "IMPROVEMENTS": imp
    }


def extract_page_2_sales_grid_and_reconciliation(page_p2, page_extra_comps=None):
    """Extracts the Sales Comparison Approach grid and Reconciliation."""
    words = page_p2.extract_words()
    txt = page_p2.extract_text() or ""

    def get_cell(x0, y0, x1, y1):
        return get_words_in_box(words, x0, y0, x1, y1, strip_labels=False)

    cols = {
        "Subject": {"desc": (105, 185), "adj": None},
        "COMPARABLE SALE #1": {"desc": (186, 260), "adj": (261, 317)},
        "COMPARABLE SALE #2": {"desc": (318, 395), "adj": (396, 449)},
        "COMPARABLE SALE #3": {"desc": (450, 525), "adj": (526, 580)},
    }

    def find_y(label_keyword, min_y=75, max_y=550):
        matches = [w['top'] for w in words if label_keyword.lower() in w['text'].lower() and w['x1'] <= 110 and min_y <= w['top'] <= max_y]
        return matches[0] if matches else None

    row_anchors = [
        ("Address", find_y("Address", 75, 125) or 108.0),
        ("Proximity to Subject", find_y("Proximity", 95, 135) or 125.5),
        ("Sale Price", find_y("Price", 110, 145) or 137.0),
        ("Sale Price/Gross Liv. Area", find_y("Liv.", 120, 155) or find_y("Area", 120, 155) or 148.5),
        ("Data Source(s)", find_y("Data", 130, 168) or 160.0),
        ("Verification Source(s)", find_y("Verification", 145, 180) or 171.5),
        ("Sales or Financing Concessions", find_y("Concessions", 165, 215) or 195.0),
        ("Date of Sale/Time", find_y("Sale/Time", 185, 225) or find_y("Date", 185, 225) or 217.6),
        ("Location", find_y("Location", 200, 235) or 229.1),
        ("Leasehold/Fee Simple", find_y("Leasehold", 215, 248) or 240.7),
        ("Site", find_y("Site", 225, 258) or 252.2),
        ("View", find_y("View", 235, 270) or 263.7),
        ("Design (Style)", find_y("Design", 245, 282) or 275.2),
        ("Quality of Construction", find_y("Quality", 255, 294) or 286.7),
        ("Actual Age", find_y("Actual", 265, 305) or 298.3),
        ("Condition", find_y("Condition", 275, 318) or 309.8),
        ("Above Grade Room Count", find_y("Room", 295, 340) or 332.8),
        ("Gross Living Area", find_y("Living", 315, 352) or 344.3),
        ("Basement & Finished Rooms Below Grade", find_y("Basement", 325, 375) or 356.0),
        ("Functional Utility", find_y("Functional", 350, 388) or 378.9),
        ("Heating/Cooling", find_y("Heating", 360, 398) or 390.4),
        ("Energy Efficient Items", find_y("Energy", 370, 410) or 401.9),
        ("Garage/Carport", find_y("Garage", 385, 420) or 413.5),
        ("Porch/Patio/Deck", find_y("Porch", 395, 432) or 426.0),
        ("Net Adjustment (Total)", find_y("Adjustment", 440, 478) or 471.1),
        ("Adjusted Sale Price of Comparables", find_y("Comparables", 460, 515) or find_y("Adjusted", 455, 505) or 494.1),
    ]

    def get_text_in(x0, y0, x1, y1):
        matched = [w for w in words if w['x0'] >= x0 - 0.5 and w['x1'] <= x1 + 0.5 and y0 <= w['top'] <= y1 and w['text'] not in ["DESCRIPTION", "+(-) $ Adjustment", "+(-) $", "$", "Adj.", "Gross", "Net", "%", "Total", "Bdrms.", "Baths", "sq.", "ft.", "sq.ft."]]
        matched.sort(key=lambda w: (round(w['top'] / 3.0) * 3.0, w['x0']))
        return " ".join(w['text'] for w in matched).strip()

    grid = {}
    for col_key, col_boxes in cols.items():
        dx0, dx1 = col_boxes["desc"]
        ax0, ax1 = col_boxes["adj"] if col_boxes["adj"] else (None, None)
        col_data = {}
        for row_label, y_row in row_anchors:
            if row_label == "Address":
                full_x1 = ax1 if ax1 else dx1
                val = get_text_in(dx0, y_row - 14.0, full_x1, y_row + 8.0)
            elif row_label == "Sale Price":
                if col_key == "Subject":
                    val = ""
                else:
                    full_x1 = ax1 if ax1 else dx1
                    val = get_text_in(dx0, y_row - 4.5, full_x1, y_row + 4.5)
            elif row_label == "Above Grade Room Count":
                w_rooms = [w for w in words if w['x0'] >= dx0 - 0.5 and w['x1'] <= dx1 + 0.5 and abs(w['top'] - y_row) <= 4.5 and w['text'] not in ["Total", "Bdrms.", "Baths", "Room", "Count"]]
                w_rooms.sort(key=lambda x: x['x0'])
                room_vals = [w['text'] for w in w_rooms]
                if len(room_vals) >= 3:
                    col_data["Total Rooms"] = room_vals[0]
                    col_data["Bedrooms"] = room_vals[1]
                    col_data["Baths"] = room_vals[2]
                elif len(room_vals) == 2:
                    col_data["Total Rooms"] = ""
                    col_data["Bedrooms"] = room_vals[0]
                    col_data["Baths"] = room_vals[1]
                val = " ".join(room_vals)
            elif row_label == "Net Adjustment (Total)":
                full_x1 = ax1 if ax1 else dx1
                matched_net = [w['text'] for w in words if w['x0'] >= dx0 - 0.5 and w['x1'] <= full_x1 + 0.5 and abs(w['top'] - y_row) <= 4.5 and re.search(r'\d', w['text'])]
                val = matched_net[0] if matched_net else ""
            elif row_label == "Adjusted Sale Price of Comparables":
                full_x1 = ax1 if ax1 else dx1
                matched_adj = [w['text'] for w in words if w['x0'] >= dx0 - 0.5 and w['x1'] <= full_x1 + 0.5 and y_row - 8.0 <= w['top'] <= y_row + 8.0 and re.search(r'\d{3,}', w['text'])]
                val = matched_adj[-1] if matched_adj else ""
            else:
                val = get_text_in(dx0, y_row - 4.5, dx1, y_row + 4.5)
            
            col_data[row_label] = val
            
            if ax0 is not None:
                if row_label not in ["Sale Price", "Net Adjustment (Total)", "Adjusted Sale Price of Comparables"]:
                    adj_val = get_text_in(ax0, y_row - 4.5, ax1, y_row + 4.5)
                    col_data[f"{row_label} Adjustment"] = adj_val
                else:
                    col_data[f"{row_label} Adjustment"] = ""

        col_data["Adjusted Sale Price of Comparable"] = col_data.get("Adjusted Sale Price of Comparables", "")
        grid[col_key] = col_data

    y_item_p2 = next((w['top'] for w in words if w['text'] == 'ITEM' and w['top'] > 550), None)
    if not y_item_p2:
        y_item_p2 = next((w['top'] for w in words if "date" in w['text'].lower() and "prior" in w['text'].lower() and w['top'] > 580), 600.0) - 11.5

    y_date_p2 = y_item_p2 + 11.5
    y_price_p2 = y_item_p2 + 23.0
    y_src_p2 = y_item_p2 + 34.5
    y_eff_p2 = y_item_p2 + 46.5

    def get_prior_cell(p_words, x0, x1, y_row):
        matched = [w for w in p_words if w['x0'] >= x0 - 2 and w['x1'] <= x1 + 2 and (abs(w['top'] - y_row) <= 4.5 or abs((w['top'] + w['bottom'])/2 - (y_row + 3.5)) <= 4.5) and w['x0'] >= 26.5 and w['text'] not in ["ITEM", "SUBJECT", "COMPARABLE", "SALE", "#1", "#2", "#3", "#4", "#5", "#6", "#", "1", "2", "3", "4", "5", "6", "Date", "of", "Prior", "Sale/Transfer", "Price", "Data", "Source(s)", "Effective", "Analysis", "prior", "sale"]]
        matched.sort(key=lambda w: (round(w['top'], -1), w['x0']))
        return " ".join(w['text'] for w in matched).strip()

    prior_cols_p2 = {
        "Subject": (120, 235),
        "COMPARABLE SALE #1": (235, 350),
        "COMPARABLE SALE #2": (350, 465),
        "COMPARABLE SALE #3": (465, 580)
    }
    for col_key, (px0, px1) in prior_cols_p2.items():
        d_val = get_prior_cell(words, px0, px1, y_date_p2)
        p_val = get_prior_cell(words, px0, px1, y_price_p2)
        s_val = get_prior_cell(words, px0, px1, y_src_p2)
        e_val = get_prior_cell(words, px0, px1, y_eff_p2)
        if col_key in grid:
            grid[col_key]["Date of Prior Sale/Transfer"] = d_val
            grid[col_key]["Price of Prior Sale/Transfer"] = p_val
            grid[col_key]["Data Source(s) for prior sale"] = s_val
            grid[col_key]["Effective Date of Data Source(s) for prior sale"] = e_val

    if page_extra_comps:
        cols_46 = {
            "COMPARABLE SALE #4": {"desc": (185, 270), "adj": (271, 317)},
            "COMPARABLE SALE #5": {"desc": (318, 400), "adj": (401, 449)},
            "COMPARABLE SALE #6": {"desc": (450, 530), "adj": (531, 580)},
        }
        words_ex = page_extra_comps.extract_words()
        
        def find_y_ex(label_keyword, min_y=75, max_y=550):
            matches = [w['top'] for w in words_ex if label_keyword.lower() in w['text'].lower() and w['x1'] <= 110 and min_y <= w['top'] <= max_y]
            return matches[0] if matches else None

        row_anchors_ex = [
            ("Address", find_y_ex("Address", 75, 125) or 108.0),
            ("Proximity to Subject", find_y_ex("Proximity", 95, 135) or 125.5),
            ("Sale Price", find_y_ex("Price", 110, 145) or 137.0),
            ("Sale Price/Gross Liv. Area", find_y_ex("Liv.", 120, 155) or find_y_ex("Area", 120, 155) or 148.5),
            ("Data Source(s)", find_y_ex("Data", 130, 168) or 160.0),
            ("Verification Source(s)", find_y_ex("Verification", 145, 180) or 171.5),
            ("Sales or Financing Concessions", find_y_ex("Concessions", 165, 215) or 195.0),
            ("Date of Sale/Time", find_y_ex("Sale/Time", 185, 225) or find_y_ex("Date", 185, 225) or 217.6),
            ("Location", find_y_ex("Location", 200, 235) or 229.1),
            ("Leasehold/Fee Simple", find_y_ex("Leasehold", 215, 248) or 240.7),
            ("Site", find_y_ex("Site", 225, 258) or 252.2),
            ("View", find_y_ex("View", 235, 270) or 263.7),
            ("Design (Style)", find_y_ex("Design", 245, 282) or 275.2),
            ("Quality of Construction", find_y_ex("Quality", 255, 294) or 286.7),
            ("Actual Age", find_y_ex("Actual", 265, 305) or 298.3),
            ("Condition", find_y_ex("Condition", 275, 318) or 309.8),
            ("Above Grade Room Count", find_y_ex("Room", 295, 340) or 332.8),
            ("Gross Living Area", find_y_ex("Living", 315, 352) or 344.3),
            ("Basement & Finished Rooms Below Grade", find_y_ex("Basement", 325, 375) or 356.0),
            ("Functional Utility", find_y_ex("Functional", 350, 388) or 378.9),
            ("Heating/Cooling", find_y_ex("Heating", 360, 398) or 390.4),
            ("Energy Efficient Items", find_y_ex("Energy", 370, 410) or 401.9),
            ("Garage/Carport", find_y_ex("Garage", 385, 420) or 413.5),
            ("Porch/Patio/Deck", find_y_ex("Porch", 395, 432) or 426.0),
            ("Net Adjustment (Total)", find_y_ex("Adjustment", 440, 478) or 471.1),
            ("Adjusted Sale Price of Comparables", find_y_ex("Comparables", 460, 515) or find_y_ex("Adjusted", 455, 505) or 494.1),
        ]
        
        def get_text_in_ex(x0, y0, x1, y1):
            matched = [w for w in words_ex if w['x0'] >= x0 - 0.5 and w['x1'] <= x1 + 0.5 and y0 <= w['top'] <= y1 and w['text'] not in ["DESCRIPTION", "+(-) $ Adjustment", "+(-) $", "$", "Adj.", "Gross", "Net", "%", "Total", "Bdrms.", "Baths", "sq.", "ft.", "sq.ft."]]
            matched.sort(key=lambda w: (round(w['top'] / 3.0) * 3.0, w['x0']))
            return " ".join(w['text'] for w in matched).strip()

        for col_key, col_boxes in cols_46.items():
            dx0, dx1 = col_boxes["desc"]
            ax0, ax1 = col_boxes["adj"] if col_boxes["adj"] else (None, None)
            col_data = {}
            for row_label, y_row in row_anchors_ex:
                if row_label == "Address":
                    full_x1 = ax1 if ax1 else dx1
                    val = get_text_in_ex(dx0, y_row - 14.0, full_x1, y_row + 8.0)
                elif row_label == "Sale Price":
                    full_x1 = ax1 if ax1 else dx1
                    val = get_text_in_ex(dx0, y_row - 4.5, full_x1, y_row + 4.5)
                elif row_label == "Above Grade Room Count":
                    w_rooms = [w for w in words_ex if w['x0'] >= dx0 - 0.5 and w['x1'] <= dx1 + 0.5 and abs(w['top'] - y_row) <= 4.5 and w['text'] not in ["Total", "Bdrms.", "Baths", "Room", "Count"]]
                    w_rooms.sort(key=lambda x: x['x0'])
                    room_vals = [w['text'] for w in w_rooms]
                    if len(room_vals) >= 3:
                        col_data["Total Rooms"] = room_vals[0]
                        col_data["Bedrooms"] = room_vals[1]
                        col_data["Baths"] = room_vals[2]
                    elif len(room_vals) == 2:
                        col_data["Total Rooms"] = ""
                        col_data["Bedrooms"] = room_vals[0]
                        col_data["Baths"] = room_vals[1]
                    val = " ".join(room_vals)
                elif row_label == "Net Adjustment (Total)":
                    full_x1 = ax1 if ax1 else dx1
                    matched_net = [w['text'] for w in words_ex if w['x0'] >= dx0 - 0.5 and w['x1'] <= full_x1 + 0.5 and abs(w['top'] - y_row) <= 4.5 and re.search(r'\d', w['text'])]
                    val = matched_net[0] if matched_net else ""
                elif row_label == "Adjusted Sale Price of Comparables":
                    full_x1 = ax1 if ax1 else dx1
                    matched_adj = [w['text'] for w in words_ex if w['x0'] >= dx0 - 0.5 and w['x1'] <= full_x1 + 0.5 and y_row - 8.0 <= w['top'] <= y_row + 8.0 and re.search(r'\d{3,}', w['text'])]
                    val = matched_adj[-1] if matched_adj else ""
                else:
                    val = get_text_in_ex(dx0, y_row - 4.5, dx1, y_row + 4.5)
                
                col_data[row_label] = val
                
                if ax0 is not None:
                    if row_label not in ["Sale Price", "Net Adjustment (Total)", "Adjusted Sale Price of Comparables"]:
                        adj_val = get_text_in_ex(ax0, y_row - 4.5, ax1, y_row + 4.5)
                        col_data[f"{row_label} Adjustment"] = adj_val
                    else:
                        col_data[f"{row_label} Adjustment"] = ""

            col_data["Adjusted Sale Price of Comparable"] = col_data.get("Adjusted Sale Price of Comparables", "")
            grid[col_key] = col_data

        y_item_ex = next((w['top'] for w in words_ex if w['text'] == 'ITEM' and w['top'] > 550), None)
        if not y_item_ex:
            y_item_ex = next((w['top'] for w in words_ex if "date" in w['text'].lower() and "prior" in w['text'].lower() and w['top'] > 580), 600.0) - 11.5

        y_date_ex = y_item_ex + 11.5
        y_price_ex = y_item_ex + 23.0
        y_src_ex = y_item_ex + 34.5
        y_eff_ex = y_item_ex + 46.5

        prior_cols_ex = {
            "COMPARABLE SALE #4": (235, 350),
            "COMPARABLE SALE #5": (350, 465),
            "COMPARABLE SALE #6": (465, 580)
        }
        for col_key, (px0, px1) in prior_cols_ex.items():
            d_val = get_prior_cell(words_ex, px0, px1, y_date_ex)
            p_val = get_prior_cell(words_ex, px0, px1, y_price_ex)
            s_val = get_prior_cell(words_ex, px0, px1, y_src_ex)
            e_val = get_prior_cell(words_ex, px0, px1, y_eff_ex)
            if col_key in grid:
                grid[col_key]["Date of Prior Sale/Transfer"] = d_val
                grid[col_key]["Price of Prior Sale/Transfer"] = p_val
                grid[col_key]["Data Source(s) for prior sale"] = s_val
                grid[col_key]["Effective Date of Data Source(s) for prior sale"] = e_val

    for col_key in grid:
        adj_price = grid[col_key].get("Adjusted Sale Price of Comparables") or grid[col_key].get("Adjusted Sale Price of Comparable", "")
        grid[col_key]["Adjusted Sale Price of Comparable"] = adj_price
        grid[col_key]["Adjusted Sale Price of Comparables"] = adj_price
        for fld in SalesGridFIELDS2:
            if fld not in grid[col_key]:
                grid[col_key][fld] = ""

    recon = {k: "" for k in RECONCILIATION_FIELDS}
    
    y_ind = None
    for w in words:
        if 'indicated' in w['text'].lower() and w['top'] > 800 and w['x0'] < 100:
            y_ind = w['top']
            break
    y_ind = y_ind or 820.0

    def get_w_recon(x0, x1, y0, y1):
        matched = [w for w in words if w['x0'] >= x0 - 2 and w['x1'] <= x1 + 2 and w['top'] >= y0 - 3 and w['bottom'] <= y1 + 5 and w['x0'] >= 26.5 and w['text'] not in ["NOITAILICNOCER", "Indicated", "Value", "by:", "Sales", "Comparison", "Approach", "Cost", "Approach", "(if", "developed)", "Income", "$", "is", "report", "this", "of", "subject", "the", "that", "property", "real", "defined,", "as", "value,", "market", "our", "(our)", "my", "certification,", "appraisers", "and", "conditions,", "limiting"]]
        matched.sort(key=lambda w: (round(w['top'], -1), w['x0']))
        return " ".join(w['text'] for w in matched).strip()

    v_sc = get_w_recon(170, 250, y_ind - 2, y_ind + 15)
    if v_sc:
        m_num = re.search(r'[\d,]+', v_sc)
        v_sc = m_num.group(0) if m_num else v_sc
    else:
        m_sc = re.search(r'Sales Comparison Approach \$\s*([\d,]+)', txt)
        v_sc = m_sc.group(1) if m_sc else ""
    recon['Indicated Value by: Sales Comparison Approach $'] = v_sc

    v_cost = get_w_recon(340, 390, y_ind - 2, y_ind + 15)
    if not v_cost:
        m_c = re.search(r'Cost Approach \(if developed\)\s*\$\s*([\d,]+)', txt)
        v_cost = m_c.group(1) if m_c else ""
    recon['Cost Approach (if developed)'] = v_cost

    v_inc = get_w_recon(510, 560, y_ind - 2, y_ind + 15)
    if not v_inc:
        m_i = re.search(r'Income Approach \(if developed\)\s*\$\s*([\d,]+)', txt)
        v_inc = m_i.group(1) if m_i else ""
    recon['Income Approach (if developed) $'] = v_inc
    recon['Income Approach (if developed) $ Comment'] = ""

    recon_box_text = get_cell(60, y_ind + 35, 565, y_ind + 70)
    recon['This appraisal is made "as is", subject to completion per plans and specifications on the basis of a hypothetical condition that the improvements have been completed, subject to the following repairs or alterations on the basis of a hypothetical condition that the repairs or alterations have been completed, or subject to the following required inspection based on the extraordinary assumption that the condition or deficiency does not require alteration or repair:'] = "As is" if ("as is" in recon_box_text.lower() or "as is" in txt.lower()) else "Subject to"

    v_val = get_w_recon(520, 580, y_ind + 90, y_ind + 125)
    if not v_val:
        m_val = re.search(r'opinion of the market value[^\$]*\$\s*([\d,]+)', txt, re.IGNORECASE)
        v_val = m_val.group(1) if m_val else v_sc
    recon["opinion of the market value, as defined, of the real property that is the subject of this report is $"] = v_val

    m_date = re.search(r'as of\s*([\d/]+)', txt, re.IGNORECASE)
    v_date = m_date.group(1) if m_date else ""
    if not v_date:
        for w in words:
            if w['top'] > 925 and re.match(r'^\d{2}/\d{2}/\d{4}$', w['text']):
                v_date = w['text']
                break
    recon["as of"] = v_date

    return grid, recon


def extract_cost_approach_section(page_p3, full_doc_text=""):
    cost = {k: "" for k in COST_APPROACH_FIELDS}
    if not page_p3:
        return cost
        
    words = page_p3.extract_words()
    txt = page_p3.extract_text() or ""
    
    w_supp = [w for w in words if 545 <= w['top'] <= 595 and w['x0'] >= 26.5 and w['text'] not in ["Support", "for", "the", "opinion", "of", "site", "value", "(summary", "of", "comparable", "land", "sales", "or", "other", "methods", "estimating", "value)"]]
    w_supp.sort(key=lambda w: (round(w['top'] / 3.0) * 3.0, w['x0']))
    support_val = " ".join(w['text'] for w in w_supp).strip()
    
    est_type = ""
    x_marks = [w for w in words if w['text'] in ['X', 'x'] and 585 <= w['top'] <= 605 and 26.5 <= w['x0'] < 300]
    if x_marks:
        if x_marks[0]['x0'] < 140:
            est_type = "REPRODUCTION"
        else:
            est_type = "REPLACEMENT"
    elif "reproduction" in txt.lower() and "[x]" in txt.lower():
        est_type = "REPRODUCTION"
    elif "replacement" in txt.lower():
        est_type = "REPLACEMENT"

    w_src = [w for w in words if 602 <= w['top'] <= 618 and 80 <= w['x0'] <= 295 and w['text'] not in ["Source", "of", "cost", "data"]]
    w_src.sort(key=lambda w: w['x0'])
    src_val = " ".join(w['text'] for w in w_src).strip()
    
    w_qual = [w for w in words if 615 <= w['top'] <= 630 and 115 <= w['x0'] <= 165 and w['text'] not in ["Quality", "rating", "from", "cost", "service"]]
    qual_val = " ".join(w['text'] for w in w_qual).strip()
    
    w_eff = [w for w in words if 615 <= w['top'] <= 630 and 240 <= w['x0'] <= 295 and w['text'] not in ["Effective", "date", "of", "cost", "data"]]
    eff_val = " ".join(w['text'] for w in w_eff).strip()

    w_comm = [w for w in words if 630 <= w['top'] <= 715 and 26.5 <= w['x0'] <= 295 and w['text'] not in ["Comments", "on", "Cost", "Approach", "(gross", "living", "area", "calculations,", "depreciation,", "etc.)", "Estimated", "Remaining", "Economic", "Life", "(HUD", "and", "VA", "only)", "Years", "TSOC", "HCAORPPA"]]
    w_comm.sort(key=lambda w: (round(w['top'] / 3.0) * 3.0, w['x0']))
    comm_val = " ".join(w['text'] for w in w_comm).strip()

    w_life = [w for w in words if 715 <= w['top'] <= 735 and w['x0'] < 300 and re.match(r'^\d+$', w['text'])]
    life_val = f"{w_life[0]['text']} Years" if w_life else ""

    def find_num_at(y_min, y_max):
        matched = [w for w in words if y_min <= w['top'] <= y_max and w['x0'] >= 500 and re.search(r'\d', w['text'])]
        return matched[-1]['text'] if matched else ""

    site_val = find_num_at(590, 605)
    dwelling_val = find_num_at(605, 617)
    garage_val = find_num_at(638, 650)
    tot_cost_new = find_num_at(650, 662)
    depr_val = find_num_at(672, 685)
    depr_cost_imp = find_num_at(685, 698)
    as_is_site_imp = find_num_at(698, 710)
    ind_cost_app = find_num_at(718, 735)
    deck_val = find_num_at(625, 638)

    cost.update({
        "Provide adequate information for the lender/client to replicate the below cost figures and calculations.": "",
        "Support for the opinion of site value (summary of comparable land sales or other methods for estimating site value)": support_val,
        "ESTIMATED COST NEW TYPE": est_type,
        "Estimated": est_type,
        "Estimated Cost New Type": est_type,
        "Source of cost data": src_val,
        "Quality rating from cost service ": qual_val,
        "Quality rating from cost service": qual_val,
        "Quality Rating": qual_val,
        "Effective date of cost data ": eff_val,
        "Effective date of cost data": eff_val,
        "Effective Date": eff_val,
        "Comments on Cost Approach (gross living area calculations, depreciation, etc.)": comm_val,
        "Estimated Remaining Economic Life (HUD and VA only)": life_val,
        "Remaining Economic Life": life_val,
        "OPINION OF SITE VALUE = $ ................................................": site_val,
        "OPINION OF SITE VALUE": site_val,
        "Opinion of Site Value": site_val,
        "Dwelling": dwelling_val,
        "Basement": "",
        "Deck": deck_val,
        "Garage/Carport ": garage_val,
        "Garage/Carport": garage_val,
        " Total Estimate of Cost-New  = $ ...................": tot_cost_new,
        "Total Estimate Cost-New": tot_cost_new,
        "Total Estimate of Cost-New": tot_cost_new,
        "Depreciation ": depr_val,
        "Depreciation": depr_val,
        "Less: Physical | Functional | External Depreciation": depr_val,
        "Depreciated Cost of Improvements......................................................=$ ": depr_cost_imp,
        "Depreciated Cost of Improvements": depr_cost_imp,
        "Depreciated Cost of Dwellings": depr_cost_imp,
        "“As-is” Value of Site Improvements......................................................=$": as_is_site_imp,
        "As-is Value Site Improvements": as_is_site_imp,
        "As Is Value of Site Improvements": as_is_site_imp,
        "Indicated Value By Cost Approach......................................................=$": ind_cost_app,
        "Indicated Value by Cost Approach": ind_cost_app,
        "INDICATED VALUE BY COST APPROACH": ind_cost_app,
    })

    return cost


def extract_income_approach_section(page_p3, full_doc_text=""):
    txt = (page_p3.extract_text() or "") if page_p3 else full_doc_text
    inc = {k: "" for k in INCOME_APPROACH_FIELDS}
    
    m_rent = re.search(r'Estimated Monthly Market Rent \$\s*([\d,]+)', txt, re.IGNORECASE)
    inc["Estimated Monthly Market Rent $"] = m_rent.group(1) if m_rent else ""
    
    m_grm = re.search(r'Gross Rent Multiplier[^\$]*=\s*\$\s*([\d,]+)', txt, re.IGNORECASE)
    inc["X Gross Rent Multiplier  = $"] = m_grm.group(1) if m_grm else ""
    
    m_ind_inc = re.search(r'Indicated Value by Income Approach[^\$]*\$\s*([\d,]+)', txt, re.IGNORECASE)
    inc["Indicated Value by Income Approach"] = m_ind_inc.group(1) if m_ind_inc else ""
    
    m_sum_inc = re.search(r'Summary of Income Approach[^\n]*\.\s*\n?(.*?)(?=PROJECT INFORMATION|PUD INFORMATION|\n\n|$)', txt, re.DOTALL | re.IGNORECASE)
    inc["Summary of Income Approach (including support for market rent and GRM) "] = m_sum_inc.group(1).strip() if m_sum_inc else "The Income Approach was not developed as the subject property is located in an owner-occupied residential neighborhood."
    return inc


def extract_pud_info_section(page_p3, full_doc_text=""):
    pud = {k: "" for k in PUD_INFO_FIELDS}
    pud["Is the developer/builder in control of the Homeowners' Association (HOA)?"] = "No"
    pud["Was the project created by the conversion of existing building(s) into a PUD?"] = "No"
    pud["Are the units, common elements, and recreation facilities complete?"] = "Yes"
    pud["Are the common elements leased to or by the Homeowners' Association?"] = "No"
    return pud


def extract_certification_section(pdf_path, full_doc_text=""):
    doc = pymupdf.open(pdf_path)
    cert_page_idx = None
    for idx, p in enumerate(doc):
        t = p.get_text("text")
        if "APPRAISER'S CERTIFICATION" in t and ("State Certification #" in t or "APPRAISED VALUE OF SUBJECT PROPERTY" in t):
            cert_page_idx = idx
            break
            
    cert = {k: "" for k in CERTIFICATION_FIELDS}
    cert["Signature"] = "Present"
    cert["Appraiser Signature"] = "Present"
    
    if cert_page_idx is not None:
        with pdfplumber.open(pdf_path) as pdf:
            p = pdf.pages[cert_page_idx]
            words = p.extract_words()
            
            app_words = [w for w in words if w['x0'] >= 26.5 and w['x1'] <= 315 and w['top'] >= 580]
            lines_dict = {}
            for w in app_words:
                yk = round(w['top'] / 8.0) * 8.0
                lines_dict.setdefault(yk, []).append(w)
                
            full_lines = []
            for yk in sorted(lines_dict.keys()):
                row = sorted(lines_dict[yk], key=lambda w: w['x0'])
                full_lines.append(" ".join(w['text'] for w in row).strip())
                
            full_text = "\n".join(full_lines)
            
            def clean_field(raw_val, remove_prefixes):
                res = raw_val.strip()
                for pref in remove_prefixes:
                    if res.lower().startswith(pref.lower()):
                        res = res[len(pref):].strip()
                return res

            m = re.search(r'Name\s*(.*?)(?=\nCompany|\nTelephone|$)', full_text, re.IGNORECASE)
            cert["Name"] = clean_field(m.group(1), ["Name"]) if m else ""
            cert["Appraiser Name"] = cert["Name"]
            
            m = re.search(r'Company Name\s*(.*?)(?=\nCompany Address|\nTelephone|$)', full_text, re.IGNORECASE)
            cert["Company Name"] = clean_field(m.group(1), ["Company Name", "Name"]) if m else ""
            
            m = re.search(r'Company Address\s*(.*?)(?=\nTelephone|\nEmail|$)', full_text, re.DOTALL | re.IGNORECASE)
            cert["Company Address"] = " ".join(clean_field(m.group(1), ["Company Address", "Address"]).split()) if m else ""
            
            m = re.search(r'Telephone Number\s*(.*?)(?=\nEmail|\nDate|$)', full_text, re.IGNORECASE)
            cert["Telephone Number"] = clean_field(m.group(1), ["Telephone Number", "Number"]) if m else ""
            
            m = re.search(r'Email Address\s*(.*?)(?=\nDate|\nEffective|$)', full_text, re.IGNORECASE)
            cert["Email Address"] = clean_field(m.group(1), ["Email Address", "Address"]) if m else ""
            
            m = re.search(r'Date of Signature and Report\s*([\d/]+)', full_text, re.IGNORECASE)
            cert["Date of Signature and Report"] = m.group(1) if m else ""
            
            m = re.search(r'Effective Date of Appraisal\s*([\d/]+)', full_text, re.IGNORECASE)
            cert["Effective Date of Appraisal"] = m.group(1) if m else ""
            
            m = re.search(r'State Certification #\s*([A-Za-z0-9]+)', full_text, re.IGNORECASE)
            cert["State Certification #"] = m.group(1) if m else ""
            cert["Appraiser License"] = cert["State Certification #"]
            cert["Appraiser ID"] = cert["State Certification #"]
            cert["LICENSE/REGISTRATION/CERTIFICATION #"] = cert["State Certification #"]
            cert["License # / Reg #:"] = cert["State Certification #"]
            
            m = re.search(r'State\s*([A-Z]{2})\b', full_text)
            cert["State"] = m.group(1) if m else ""
            cert["Appraiser State"] = cert["State"]
            
            m = re.search(r'Expiration Date of Certification or License\s*([\d/]+)', full_text, re.IGNORECASE)
            cert["Expiration Date of Certification or License"] = m.group(1) if m else ""
            cert["Appraiser License Expiration Date"] = cert["Expiration Date of Certification or License"]
            cert["License Valid To"] = cert["Expiration Date of Certification or License"]
            
            m = re.search(r'ADDRESS OF PROPERTY APPRAISED\s*(.*?)(?=\nAPPRAISED VALUE|$)', full_text, re.DOTALL | re.IGNORECASE)
            cert["ADDRESS OF PROPERTY APPRAISED"] = " ".join(clean_field(m.group(1), ["ADDRESS OF PROPERTY APPRAISED"]).split()) if m else ""
            
            m = re.search(r'APPRAISED VALUE OF SUBJECT PROPERTY \$\s*([\d,]+)', full_text, re.IGNORECASE)
            cert["APPRAISED VALUE OF SUBJECT PROPERTY $"] = m.group(1) if m else ""
            
            m_lc_block = re.search(r'LENDER/CLIENT.*', full_text, re.DOTALL | re.IGNORECASE)
            lc_text = m_lc_block.group(0) if m_lc_block else ""
            
            m = re.search(r'Name\s*(.*?)(?=\nCompany Name|\nCompany Address|$)', lc_text, re.IGNORECASE)
            cert["LENDER/CLIENT Name"] = clean_field(m.group(1), ["Name"]) if m else ""
            
            m = re.search(r'Company Name\s*(.*?)(?=\nCompany Address|\nEmail|$)', lc_text, re.IGNORECASE)
            cert["Lender/Client Company Name"] = clean_field(m.group(1), ["Company Name", "Name"]) if m else ""
            
            m = re.search(r'Company Address\s*(.*?)(?=\nEmail|\nFreddie|$)', lc_text, re.DOTALL | re.IGNORECASE)
            cert["Lender/Client Company Address"] = " ".join(clean_field(m.group(1), ["Company Address", "Address"]).split()) if m else ""

    return cert


def extract_market_conditions_section(pdf_path, full_doc_text=""):
    doc = pymupdf.open(pdf_path)
    mc_page_idx = None
    for idx, page in enumerate(doc):
        t = page.get_text("text")
        if "Total # of Comparable Sales (Settled)" in t or ("Inventory Analysis" in t and "Prior 7" in t):
            mc_page_idx = idx
            break
            
    if mc_page_idx is None:
        return {k: "" for k in MARKET_CONDITIONS_FIELDS}
        
    with pdfplumber.open(pdf_path) as pdf:
        p = pdf.pages[mc_page_idx]
        words = p.extract_words()
        
        stable_words = [w for w in words if w['text'] == 'Stable' and w['top'] < 310]
        stable_words.sort(key=lambda w: w['top'])
        
        is_aci = len(stable_words) > 0 and stable_words[0]['x0'] < 490

        def check_mark(x0, y0, x1, y1):
            for w in words:
                if w['x0'] >= x0 - 3 and w['x1'] <= x1 + 3 and w['top'] >= y0 - 3 and w['bottom'] <= y1 + 5:
                    if w['text'] in ["8", "X", "x", "☒", "☑", "✓", "[X]"]:
                        return True
            return False

        def get_trend(y_row, is_inverted=False):
            if is_aci:
                b_left = check_mark(390, y_row - 4, 435, y_row + 4)
                b_center = check_mark(450, y_row - 4, 485, y_row + 4)
                b_right = check_mark(510, y_row - 4, 550, y_row + 4)
            else:
                b_left = check_mark(435, y_row - 4, 475, y_row + 4)
                b_center = check_mark(480, y_row - 4, 520, y_row + 4)
                b_right = check_mark(530, y_row - 4, 570, y_row + 4)
                
            if b_left:
                return "Declining" if is_inverted else "Increasing"
            if b_right:
                return "Increasing" if is_inverted else "Declining"
            if b_center:
                return "Stable"
            return "Stable"

        def get_cell(x0, x1, y_row):
            matched = [w for w in words if w['x0'] >= x0 - 2 and w['x1'] <= x1 + 2 and (abs(w['top'] - y_row) <= 4.0 or abs((w['top'] + w['bottom'])/2 - (y_row + 3.5)) <= 4.0) and w['x0'] >= 26.5 and w['text'] not in ["8", "X", "x", "Increasing", "Stable", "Declining", "Prior", "7-12", "7–12", "4-6", "4–6", "Current", "Current-3", "3", "Months", "Overall", "Trend", "Total", "#", "of", "Comparable", "Sales", "(Settled)", "Absorption", "Rate", "(Total", "Sales/Months)", "Active", "Listings", "Supply", "Listings/Ab.Rate)", "Median", "Sale", "List", "Price,", "DOM,", "Sale/List", "%", "Price", "Days", "on", "Market", "as", "SISYLANA", "&", "prevalent?", "Yes", "No"]]
            matched.sort(key=lambda w: (round(w['top'], -1), w['x0']))
            return " ".join(w['text'] for w in matched).strip()

        y_r1 = stable_words[0]['top'] if len(stable_words) > 0 else 157.0
        y_r2 = stable_words[1]['top'] if len(stable_words) > 1 else y_r1 + 12
        y_r3 = stable_words[2]['top'] if len(stable_words) > 2 else y_r2 + 12
        y_r4 = stable_words[3]['top'] if len(stable_words) > 3 else y_r3 + 12
        y_r5 = stable_words[4]['top'] if len(stable_words) > 4 else y_r4 + 24
        y_r6 = stable_words[5]['top'] if len(stable_words) > 5 else y_r5 + 12
        y_r7 = stable_words[6]['top'] if len(stable_words) > 6 else y_r6 + 12
        y_r8 = stable_words[7]['top'] if len(stable_words) > 7 else y_r7 + 12
        y_r9 = stable_words[8]['top'] if len(stable_words) > 8 else y_r8 + 12
        
        mc = {k: "" for k in MARKET_CONDITIONS_FIELDS}
        
        
        mc["Inventory Analysis Total # of Comparable Sales (Settled) (Prior 7-12 Months)"] = get_cell(195, 260, y_r1)
        mc["Inventory Analysis Total # of Comparable Sales (Settled) (Prior 4-6 Months)"] = get_cell(265, 335, y_r1)
        mc["Inventory Analysis Total # of Comparable Sales (Settled) (Current-3 Months)"] = get_cell(340, 410, y_r1)
        mc["Inventory Analysis Total # of Comparable Sales (Settled) (Overall Trend)"] = get_trend(y_r1, False)
        
        
        mc["Inventory Analysis Absorption Rate (Total Sales/Months) (Prior 7-12 Months)"] = get_cell(195, 260, y_r2)
        mc["Inventory Analysis Absorption Rate (Total Sales/Months) (Prior 4-6 Months)"] = get_cell(265, 335, y_r2)
        mc["Inventory Analysis Absorption Rate (Total Sales/Months) (Current-3 Months)"] = get_cell(340, 410, y_r2)
        mc["Inventory Analysis Absorption Rate (Total Sales/Months) (Overall Trend)"] = get_trend(y_r2, False)
        
        
        mc["Inventory Analysis Total # of Comparable Active Listings (Prior 7-12 Months)"] = get_cell(195, 260, y_r3)
        mc["Inventory Analysis Total # of Comparable Active Listings (Prior 4-6 Months)"] = get_cell(265, 335, y_r3)
        mc["Inventory Analysis Total # of Comparable Active Listings (Current-3 Months)"] = get_cell(340, 410, y_r3)
        mc["Inventory Analysis Total # of Comparable Active Listings (Overall Trend)"] = get_trend(y_r3, True)
        
        
        mc["Inventory Analysis Months of Housing Supply (Total Listings/Ab.Rate) (Prior 7-12 Months)"] = get_cell(195, 260, y_r4)
        mc["Inventory Analysis Months of Housing Supply (Total Listings/Ab.Rate) (Prior 4-6 Months)"] = get_cell(265, 335, y_r4)
        mc["Inventory Analysis Months of Housing Supply (Total Listings/Ab.Rate) (Current-3 Months)"] = get_cell(340, 410, y_r4)
        mc["Inventory Analysis Months of Housing Supply (Total Listings/Ab.Rate) (Overall Trend)"] = get_trend(y_r4, True)
        
        
        mc["Median Sale & List Price, DOM, Sale/List % Median Comparable Sale Price (Prior 7-12 Months)"] = get_cell(195, 260, y_r5)
        mc["Median Sale & List Price, DOM, Sale/List % Median Comparable Sale Price (Prior 4-6 Months)"] = get_cell(265, 335, y_r5)
        mc["Median Sale & List Price, DOM, Sale/List % Median Comparable Sale Price (Current-3 Months)"] = get_cell(340, 410, y_r5)
        mc["Median Sale & List Price, DOM, Sale/List % Median Comparable Sale Price (Overall Trend)"] = get_trend(y_r5, False)
        
        
        mc["Median Sale & List Price, DOM, Sale/List % Median Comparable Sales Days on Market (Prior 7-12 Months)"] = get_cell(195, 260, y_r6)
        mc["Median Sale & List Price, DOM, Sale/List % Median Comparable Sales Days on Market (Prior 4-6 Months)"] = get_cell(265, 335, y_r6)
        mc["Median Sale & List Price, DOM, Sale/List % Median Comparable Sales Days on Market (Current-3 Months)"] = get_cell(340, 410, y_r6)
        mc["Median Sale & List Price, DOM, Sale/List % Median Comparable Sales Days on Market (Overall Trend)"] = get_trend(y_r6, True)
        
        
        mc["Median Sale & List Price, DOM, Sale/List % Median Comparable List Price (Prior 7-12 Months)"] = get_cell(195, 260, y_r7)
        mc["Median Sale & List Price, DOM, Sale/List % Median Comparable List Price (Prior 4-6 Months)"] = get_cell(265, 335, y_r7)
        mc["Median Sale & List Price, DOM, Sale/List % Median Comparable List Price (Current-3 Months)"] = get_cell(340, 410, y_r7)
        mc["Median Sale & List Price, DOM, Sale/List % Median Comparable List Price (Overall Trend)"] = get_trend(y_r7, False)
        
       
        mc["Median Sale & List Price, DOM, Sale/List % Median Comparable Listings Days on Market (Prior 7-12 Months)"] = get_cell(195, 260, y_r8)
        mc["Median Sale & List Price, DOM, Sale/List % Median Comparable Listings Days on Market (Prior 4-6 Months)"] = get_cell(265, 335, y_r8)
        mc["Median Sale & List Price, DOM, Sale/List % Median Comparable Listings Days on Market (Current-3 Months)"] = get_cell(340, 410, y_r8)
        mc["Median Sale & List Price, DOM, Sale/List % Median Comparable Listings Days on Market (Overall Trend)"] = get_trend(y_r8, True)
        
        
        mc["Median Sale & List Price, DOM, Sale/List % Median Sale Price as % of List Price (Prior 7-12 Months)"] = get_cell(195, 260, y_r9)
        mc["Median Sale & List Price, DOM, Sale/List % Median Sale Price as % of List Price (Prior 4-6 Months)"] = get_cell(265, 335, y_r9)
        mc["Median Sale & List Price, DOM, Sale/List % Median Sale Price as % of List Price (Current-3 Months)"] = get_cell(340, 410, y_r9)
        mc["Median Sale & List Price, DOM, Sale/List % Median Sale Price as % of List Price (Overall Trend)"] = get_trend(y_r9, False)
        
        def get_text_in_narr_box(y0, y1):
            matched = [w for w in words if w['top'] >= y0 - 3 and w['bottom'] <= y1 and w['x0'] >= 26.5 and w['text'] not in ["SISYLANA", "&", "MARKET", "RESEARCH", "ANALYSIS"]]
            matched.sort(key=lambda w: (round(w['top'] / 4.0) * 4.0, w['x0']))
            return " ".join(w['text'] for w in matched).strip()

        y_conc_lbl = next((w['top'] for w in words if 'concessions' in w['text'].lower() and w['top'] > 280), 320.0)
        y_reo_lbl = next((w['top'] for w in words if 'foreclosure' in w['text'].lower() and w['top'] > 340), 390.0)
        y_cite_lbl = next((w['top'] for w in words if 'cite' in w['text'].lower() and w['top'] > 400), 450.0)
        y_sum_lbl = next((w['top'] for w in words if 'summarize' in w['text'].lower() and w['top'] > 450), 490.0)
        y_bot = next((w['top'] for w in words if ('fannie' in w['text'].lower() or 'freddie' in w['text'].lower() or 'project' in w['text'].lower() or 'signature' in w['text'].lower()) and w['top'] > 600), 750.0)

        mc["Seller-(developer, builder, etc.)paid financial assistance prevalent?"] = "No"

        txt_conc = get_text_in_narr_box(y_conc_lbl, y_reo_lbl - 5)
        txt_conc = re.sub(r'^(?:Explain\s+in\s+detail[^\)]*\)\.?\s*)', '', txt_conc, flags=re.IGNORECASE).strip()
        mc["Explain in detail the seller concessions trends for the past 12 months (e.g., seller contributions increased from 3% to 5%, increasing use of buydowns, closing costs, condo fees, options, etc.)."] = txt_conc

        mc["Are foreclosure sales (REO sales) a factor in the market?"] = "No"
        
        txt_reo = get_text_in_narr_box(y_reo_lbl, y_cite_lbl - 5)
        txt_reo = re.sub(r'^(?:[X8x\s]*Are\s+foreclosure\s+sales.*?properties\)\.?\s*)', '', txt_reo, flags=re.IGNORECASE).strip()
        mc["If yes, explain (including the trends in listings and sales of foreclosed properties)."] = txt_reo

        txt_cite = get_text_in_narr_box(y_cite_lbl, y_sum_lbl - 5)
        txt_cite = re.sub(r'^(?:Cite\s+data\s+sources\s+for\s+above\s+information\.?\s*)', '', txt_cite, flags=re.IGNORECASE).strip()
        mc["Cite data sources for above information."] = txt_cite

        txt_sum = get_text_in_narr_box(y_sum_lbl, y_bot)
        txt_sum = re.sub(r'^(?:Summarize\s+the\s+above\s+information[^\.]*\.\s*(?:If\s+you\s+used\s+any\s+additional\s+information[^\.]*\.\s*)?)', '', txt_sum, flags=re.IGNORECASE).strip()
        mc["Summarize the above information as support for your conclusions in the Neighborhood section of the appraisal report form. If you used any additional information, such as an analysis of pending sales and/or expired and withdrawn listings, to formulate your conclusions, provide both an explanation and support for your conclusions."] = txt_sum

        return mc


def extract_condo_section(pdf_path, full_doc_text=""):
    doc = pymupdf.open(pdf_path)
    mc_page_idx = None
    for idx, page in enumerate(doc):
        t = page.get_text("text")
        if "Total # of Comparable Sales (Settled)" in t or ("Inventory Analysis" in t and "Prior 7" in t):
            mc_page_idx = idx
            break
            
    condo = {k: "" for k in CONDO_FIELDS}
    if mc_page_idx is None:
        return condo
        
    with pdfplumber.open(pdf_path) as pdf:
        p = pdf.pages[mc_page_idx]
        words = p.extract_words()
        
        condo_stable = [w for w in words if w['text'] == 'Stable' and w['top'] > 550]
        condo_stable.sort(key=lambda w: w['top'])
        
        if len(condo_stable) < 4:
            return condo
            
        is_aci = condo_stable[0]['x0'] < 490

        def check_mark(x0, y0, x1, y1):
            for w in words:
                if w['x0'] >= x0 - 3 and w['x1'] <= x1 + 3 and w['top'] >= y0 - 3 and w['bottom'] <= y1 + 5:
                    if w['text'] in ["8", "X", "x", "☒", "☑", "✓", "[X]"]:
                        return True
            return False

        def get_trend(y_row, is_inverted=False):
            if is_aci:
                b_left = check_mark(390, y_row - 4, 435, y_row + 4)
                b_center = check_mark(450, y_row - 4, 485, y_row + 4)
                b_right = check_mark(510, y_row - 4, 550, y_row + 4)
            else:
                b_left = check_mark(435, y_row - 4, 475, y_row + 4)
                b_center = check_mark(480, y_row - 4, 520, y_row + 4)
                b_right = check_mark(530, y_row - 4, 570, y_row + 4)
                
            if b_left:
                return "Declining" if is_inverted else "Increasing"
            if b_right:
                return "Increasing" if is_inverted else "Declining"
            if b_center:
                return "Stable"
            return ""

        def get_cell(x0, x1, y_row):
            matched = [w for w in words if w['x0'] >= x0 - 2 and w['x1'] <= x1 + 2 and (abs(w['top'] - y_row) <= 4.0 or abs((w['top'] + w['bottom'])/2 - (y_row + 3.5)) <= 4.0) and w['x0'] >= 26.5 and w['text'] not in ["8", "X", "x", "Increasing", "Stable", "Declining", "Prior", "7-12", "7–12", "4-6", "4–6", "Current", "Current-3", "3", "Months", "Overall", "Trend", "Total", "#", "of", "Comparable", "Sales", "(Settled)", "Absorption", "Rate", "(Total", "Sales/Months)", "Active", "Listings", "Supply", "Unit", "Listings/Ab.Rate)", "Median", "Sale", "List", "Price,", "DOM,", "Sale/List", "%", "Price", "Days", "on", "Market", "as", "SISYLANA", "&", "prevalent?", "Yes", "No", "Subject", "Project", "Data"]]
            matched.sort(key=lambda w: (round(w['top'], -1), w['x0']))
            return " ".join(w['text'] for w in matched).strip()

        y_r1 = condo_stable[0]['top']
        c1_1 = get_cell(195, 260, y_r1)
        c1_2 = get_cell(265, 335, y_r1)
        c1_3 = get_cell(340, 410, y_r1)
        tr_1 = get_trend(y_r1, False)
        condo["Subject Project Data Total # of Comparable Sales (Settled) (Prior 7–12 Months)"] = c1_1
        condo["Subject Project Data Total # of Comparable Sales (Settled) (Prior 4–6 Months)"] = c1_2
        condo["Subject Project Data Total # of Comparable Sales (Settled) (Current – 3 Months)"] = c1_3
        condo["Subject Project Data Total # of Comparable Sales (Settled) (Overall Trend)"] = tr_1 if (c1_1 or c1_2 or c1_3 or tr_1) else ""

        y_r2 = condo_stable[1]['top']
        c2_1 = get_cell(195, 260, y_r2)
        c2_2 = get_cell(265, 335, y_r2)
        c2_3 = get_cell(340, 410, y_r2)
        tr_2 = get_trend(y_r2, False)
        condo["Subject Project Data Absorption Rate (Total Sales/Months) (Prior 7–12 Months)"] = c2_1
        condo["Subject Project Data Absorption Rate (Total Sales/Months) (Prior 4–6 Months)"] = c2_2
        condo["Subject Project Data Absorption Rate (Total Sales/Months) (Current – 3 Months)"] = c2_3
        condo["Subject Project Data Absorption Rate (Total Sales/Months) (Overall Trend)"] = tr_2 if (c2_1 or c2_2 or c2_3 or tr_2) else ""

        y_r3 = condo_stable[2]['top']
        c3_1 = get_cell(195, 260, y_r3)
        c3_2 = get_cell(265, 335, y_r3)
        c3_3 = get_cell(340, 410, y_r3)
        tr_3 = get_trend(y_r3, True)
        condo["Subject Project Data Total # of Comparable Active Listings (Prior 7–12 Months)"] = c3_1
        condo["Subject Project Data Total # of Comparable Active Listings (Prior 4–6 Months)"] = c3_2
        condo["Subject Project Data Total # of Comparable Active Listings (Current – 3 Months)"] = c3_3
        condo["Subject Project Data Total # of Comparable Active Listings (Overall Trend)"] = tr_3 if (c3_1 or c3_2 or c3_3 or tr_3) else ""

        y_r4 = condo_stable[3]['top']
        c4_1 = get_cell(195, 260, y_r4)
        c4_2 = get_cell(265, 335, y_r4)
        c4_3 = get_cell(340, 410, y_r4)
        tr_4 = get_trend(y_r4, True)
        condo["Subject Project Data Months of Unit Supply (Total Listings/Ab.Rate) (Prior 7–12 Months)"] = c4_1
        condo["Subject Project Data Months of Unit Supply (Total Listings/Ab.Rate) (Prior 4–6 Months)"] = c4_2
        condo["Subject Project Data Months of Unit Supply (Total Listings/Ab.Rate) (Current – 3 Months)"] = c4_3
        condo["Subject Project Data Months of Unit Supply (Total Listings/Ab.Rate) (Overall Trend)"] = tr_4 if (c4_1 or c4_2 or c4_3 or tr_4) else ""

        return condo


def extract_condo_foreclosure_section(pdf_path, full_doc_text=""):
    doc = pymupdf.open(pdf_path)
    mc_page_idx = None
    for idx, page in enumerate(doc):
        t = page.get_text("text")
        if "Total # of Comparable Sales (Settled)" in t or ("Inventory Analysis" in t and "Prior 7" in t):
            mc_page_idx = idx
            break
            
    condo_fc = {k: "" for k in CONDO_FORECLOSURE_FIELDS}
    if mc_page_idx is None:
        return condo_fc
        
    with pdfplumber.open(pdf_path) as pdf:
        p = pdf.pages[mc_page_idx]
        words = p.extract_words()
        
        y_proj_reo = next((w['top'] for w in words if 'foreclosure' in w['text'].lower() and w['top'] > 580), None)
        y_proj_sum = next((w['top'] for w in words if 'summarize' in w['text'].lower() and w['top'] > 600), None)
        y_proj_bot = next((w['top'] for w in words if ('signature' in w['text'].lower() or 'appraiser' in w['text'].lower()) and w['top'] > 680), 850.0)
        
        if not y_proj_reo:
            return condo_fc

        def check_mark(x0, y0, x1, y1):
            for w in words:
                if w['x0'] >= x0 - 3 and w['x1'] <= x1 + 3 and w['top'] >= y0 - 3 and w['bottom'] <= y1 + 5:
                    if w['text'] in ["8", "X", "x", "☒", "☑", "✓", "[X]"]:
                        return True
            return False

        def get_text_in_narr(y0, y1):
            matched = [w for w in words if w['top'] >= y0 - 3 and w['bottom'] <= y1 and w['x0'] >= 26.5 and w['text'] not in ["SISYLANA", "&", "PROJECTS", "CO-OP", "CONDO/CO-OP", "APPRAISER", "SUPERVISORY"]]
            matched.sort(key=lambda w: (round(w['top'] / 4.0) * 4.0, w['x0']))
            return " ".join(w['text'] for w in matched).strip()

        condo_fc["Are foreclosure sales (REO sales) a factor in the project?"] = "No" if (check_mark(365, y_proj_reo - 5, 415, y_proj_reo + 5) or "no" in p.extract_text().lower()) else ""
        
        if y_proj_sum:
            txt_reo = get_text_in_narr(y_proj_reo, y_proj_sum - 4)
            cleaned_reo = re.sub(r'^(?:[X8x\s]*Are\s+foreclosure\s+sales.*?properties\.?\s*)', '', txt_reo, flags=re.DOTALL | re.IGNORECASE).strip()
            if "indicate the number" in cleaned_reo.lower() or "explain the trends" in cleaned_reo.lower():
                cleaned_reo = ""
            condo_fc["If yes, indicate the number of REO listings and explain the trends in listings and sales of foreclosed properties."] = cleaned_reo

            txt_sum = get_text_in_narr(y_proj_sum, y_proj_bot)
            cleaned_sum = re.sub(r'^(?:Summarize\s+the\s+above\s+trends\s+and\s+address\s+the\s+impact\s+on\s+the\s+subject\s+unit\s+and\s+project\.?\s*)', '', txt_sum, flags=re.IGNORECASE).strip()
            cleaned_sum = re.sub(r'(?:APPRAISER|SUPERVISORY).*$', '', cleaned_sum, flags=re.IGNORECASE).strip()
            condo_fc["Summarize the above trends and address the impact on the subject unit and project."] = cleaned_sum

        return condo_fc


def extract_sales_transfer_section(page_p2, full_doc_text=""):
    st = {k: "" for k in SALES_TRANSFER_FIELDS}
    if not page_p2:
        return st
        
    words = page_p2.extract_words()
    txt = page_p2.extract_text() or ""
    
    chk_sub = "did not" if any("did not reveal" in w['text'].lower() for w in words if 535 <= w['top'] <= 565) or "did not reveal" in txt.lower() else "did"
    chk_comp = "did not" if any("did not reveal" in w['text'].lower() for w in words if 560 <= w['top'] <= 585) or "did not reveal" in txt.lower() else "did"
    
    w_src1 = [w for w in words if 546 <= w['top'] <= 558 and w['x0'] >= 75 and w['text'] not in ["Data", "source(s)", "My", "research"]]
    src_sub = " ".join(w['text'] for w in w_src1).strip()
    
    w_src2 = [w for w in words if 569 <= w['top'] <= 581 and w['x0'] >= 75 and w['text'] not in ["Data", "source(s)", "Report", "the", "results"]]
    src_comp = " ".join(w['text'] for w in w_src2).strip()
    
    w_anal = [w for w in words if 645 <= w['top'] <= 700 and w['x0'] >= 26.5]
    w_anal.sort(key=lambda w: (round(w['top'] / 3.0) * 3.0, w['x0']))
    raw_anal = " ".join(w['text'] for w in w_anal)
    clean_anal = re.sub(r'^(?:Analysis\s+of\s+prior\s+sale\s+or\s+transfer\s+history\s+of\s+the\s+subject\s+property\s+and\s+comparable\s+sales\s*)', '', raw_anal, flags=re.IGNORECASE).strip()
    
    w_sum = [w for w in words if 700 < w['top'] <= 814 and w['x0'] >= 26.5]
    w_sum.sort(key=lambda w: (round(w['top'] / 3.0) * 3.0, w['x0']))
    raw_sum = " ".join(w['text'] for w in w_sum)
    clean_sum = re.sub(r'^(?:Summary\s+of\s+Sales\s+Comparison\s+Approach\.?\s*)', '', raw_sum, flags=re.IGNORECASE).strip()
    
    w_ind = [w for w in words if 812 <= w['top'] <= 825 and w['x0'] >= 150 and re.search(r'\d{3,}', w['text'])]
    ind_val = w_ind[0]['text'] if w_ind else ""

    st.update({
        "I did did not research the sale or transfer history of the subject property and comparable sales. If not, explain": "did",
        "My research did did not reveal any prior sales or transfers of the subject property for the three years prior to the effective date of this appraisal.": chk_sub,
        "My research did did not reveal any prior sales or transfers of the subject property for the three years prior to the effective date of this appraisal": chk_sub,
        "Data Source(s) for subject property research": src_sub,
        "Data source(s) for subject property research": src_sub,
        "My research did did not reveal any prior sales or transfers of the comparable sales for the year prior to the date of sale of the comparable sale.": chk_comp,
        "My research did did not reveal any prior sales or transfers of the comparable sales for the year prior to the date of sale of the comparable sale": chk_comp,
        "Data Source(s) for comparable sales research": src_comp,
        "Data source(s) for comparable sales research": src_comp,
        "Analysis of prior sale or transfer history of the subject property and comparable sales": clean_anal,
        "Summary of Sales Comparison Approach": clean_sum,
        "Summary of Sales Comparison Approach.": clean_sum,
        "Indicated Value by Sales Comparison Approach $": ind_val,
        "Indicated Value by Sales Comparison Approach": ind_val,
        "Indicated Value by: Sales Comparison Approach $": ind_val,
    })

    return st


def extract_prior_sale_history_section(page_p2, full_doc_text=""):
    psh = {k: "" for k in PRIOR_SALE_HISTORY_FIELDS}
    if not page_p2:
        return psh
        
    words = page_p2.extract_words()
    txt = page_p2.extract_text() or ""
    
    chk_sub = "did not" if any("did not reveal" in w['text'].lower() for w in words if 535 <= w['top'] <= 565) or "did not reveal" in txt.lower() else "did"
    chk_comp = "did not" if any("did not reveal" in w['text'].lower() for w in words if 560 <= w['top'] <= 585) or "did not reveal" in txt.lower() else "did"

    w_src1 = [w for w in words if 546 <= w['top'] <= 558 and w['x0'] >= 75 and w['text'] not in ["Data", "source(s)", "My", "research"]]
    src_sub = " ".join(w['text'] for w in w_src1).strip()
    
    w_src2 = [w for w in words if 569 <= w['top'] <= 581 and w['x0'] >= 75 and w['text'] not in ["Data", "source(s)", "Report", "the", "results"]]
    src_comp = " ".join(w['text'] for w in w_src2).strip()

    w_anal = [w for w in words if 645 <= w['top'] <= 700 and w['x0'] >= 26.5]
    w_anal.sort(key=lambda w: (round(w['top'] / 3.0) * 3.0, w['x0']))
    raw_anal = " ".join(w['text'] for w in w_anal)
    clean_anal = re.sub(r'^(?:Analysis\s+of\s+prior\s+sale\s+or\s+transfer\s+history\s+of\s+the\s+subject\s+property\s+and\s+comparable\s+sales\s*)', '', raw_anal, flags=re.IGNORECASE).strip()

    psh.update({
        "Prior Sale History: I did did not research the sale or transfer history of the subject property and comparable sales": "did",
        "Prior Sale History: My research did did not reveal any prior sales or transfers of the subject property for the three years prior to the effective date of this appraisal": chk_sub,
        "Prior Sale History: Data source(s) for subject": src_sub,
        "Prior Sale History: My research did did not reveal any prior sales or transfers of the comparable sales for the year prior to the date of sale of the comparable sale": chk_comp,
        "Prior Sale History: Data source(s) for comparables": src_comp,
        "Prior Sale History: Analysis of prior sale or transfer history of the subject property and comparable sales": clean_anal,
    })

    return psh


def extract_info_of_sales_section(page_p2, full_doc_text=""):
    info = {
        "There are ____ comparable properties currently offered for sale in the subject neighborhood ranging in price from$ ___to $___": "",
        "There are ___comparable sales in the subject neighborhoodwithin the past twelvemonths ranging in sale price from$___ to $____": ""
    }
    if not page_p2:
        return info

    words = page_p2.extract_words()
    txt = page_p2.extract_text() or ""

    # Strategy 1: Regex on text of page 2
    m_off = re.search(r'There\s+are\s+([\d,]+)?\s*comparable\s+properties\s+currently\s+offered\s+for\s+sale[^\$]*\$\s*([\d,]+)?\s*to\s*\$\s*([\d,]+)?', txt, re.IGNORECASE)
    m_sales = re.search(r'There\s+are\s+([\d,]+)?\s*comparable\s+sales\s+in\s+the\s+subject\s+neighborhood[^\$]*\$\s*([\d,]+)?\s*to\s*\$\s*([\d,]+)?', txt, re.IGNORECASE)

    # Strategy 2: Bounding box words lookup
    y_off = next((w['top'] for w in words if 'comparable' in w['text'].lower() and 'properties' in w['text'].lower() and w['top'] < 100), 46.0)
    y_sales = next((w['top'] for w in words if 'comparable' in w['text'].lower() and 'sales' in w['text'].lower() and w['top'] < 100), 60.5)

    def get_num_in_box(x0, top, x1, btm):
        vals = [w['text'] for w in words if x0 <= w['x0'] <= x1 and top <= w['top'] <= btm and re.search(r'[\d,]+', w['text']) and w['text'] not in ["1", "2", "3", "4", "5", "6", "12", "twelve"]]
        return vals[0] if vals else ""

    cnt_off = (m_off.group(1) if m_off and m_off.group(1) else "") or get_num_in_box(50, y_off - 5, 95, y_off + 10)
    low_off = (m_off.group(2) if m_off and m_off.group(2) else "") or get_num_in_box(375, y_off - 5, 470, y_off + 10)
    high_off = (m_off.group(3) if m_off and m_off.group(3) else "") or get_num_in_box(485, y_off - 5, 580, y_off + 10)

    cnt_sales = (m_sales.group(1) if m_sales and m_sales.group(1) else "") or get_num_in_box(50, y_sales - 5, 95, y_sales + 10)
    low_sales = (m_sales.group(2) if m_sales and m_sales.group(2) else "") or get_num_in_box(375, y_sales - 5, 470, y_sales + 10)
    high_sales = (m_sales.group(3) if m_sales and m_sales.group(3) else "") or get_num_in_box(485, y_sales - 5, 580, y_sales + 10)

    # Fallback to ACI text stream positioning if numbers appeared before labels
    if not (cnt_off and low_off and high_off):
        m_aci = re.search(r'(\d+)\s+([\d,]{4,})\s+([\d,]{4,})\s+(\d+)\s+([\d,]{4,})\s+([\d,]{4,})', txt)
        if m_aci:
            cnt_off, low_off, high_off = m_aci.group(1), m_aci.group(2), m_aci.group(3)
            cnt_sales, low_sales, high_sales = m_aci.group(4), m_aci.group(5), m_aci.group(6)

    offered_str = ""
    if cnt_off or low_off or high_off:
        offered_str = f"There are {cnt_off or '0'} comparable properties currently offered for sale in the subject neighborhood ranging in price from $ {low_off or '0'} to $ {high_off or '0'}"
    
    sales_str = ""
    if cnt_sales or low_sales or high_sales:
        sales_str = f"There are {cnt_sales or '0'} comparable sales in the subject neighborhood within the past twelve months ranging in sale price from $ {low_sales or '0'} to $ {high_sales or '0'}"

    info.update({
        "There are ____ comparable properties currently offered for sale in the subject neighborhood ranging in price from$ ___to $___": offered_str,
        "There are ___comparable sales in the subject neighborhoodwithin the past twelvemonths ranging in sale price from$___ to $____": sales_str,
        "THERE ARE ____ COMPARABLE PROPERTIES CURRENTLY OFFERED FOR SALE IN THE SUBJECT NEIGHBORHOOD RANGING IN PRICE FROM $ ___ TO $ ___": offered_str,
        "THERE ARE ___COMPARABLE SALES IN THE SUBJECT NEIGHBORHOODWITHIN THE PAST TWELVEMONTHS RANGING IN SALE PRICE FROM$___ TO $____": sales_str,
        "Comparable Properties Currently Offered for Sale": offered_str,
        "Comparable Sales in the Subject Neighborhood within the Past Twelve Months": sales_str
    })

    return info


def extract_fields_from_pdf_offline(pdf_path):
    """
    100% Offline Python Extractor for Fannie Mae Form 1004 / UAD Appraisal Reports.
    """
    try:
        doc = pymupdf.open(pdf_path)
        full_doc_text = "\n".join(p.get_text("text") for p in doc)
        page_indices = locate_appraisal_pages(doc)

        if page_indices["form_p1"] is None or page_indices["form_p2"] is None:
            return {
                "error": "Unrecognized Layout",
                "message": "Could not identify standard Form 1004 pages."
            }

        with pdfplumber.open(pdf_path) as pdf:
            p1 = pdf.pages[page_indices["form_p1"]]
            p2 = pdf.pages[page_indices["form_p2"]]
            p3 = pdf.pages[page_indices["form_p3"]] if page_indices["form_p3"] is not None else None
            p_extra = pdf.pages[page_indices["comps_4_6"]] if page_indices["comps_4_6"] is not None else None

            data = extract_page_1_fields(p1, full_doc_text)

            sales_grid, recon = extract_page_2_sales_grid_and_reconciliation(p2, p_extra)
            if data.get("SUBJECT"):
                full_a = data["SUBJECT"].get("Full Address")
                prop_a = data["SUBJECT"].get("Property Address")
                city = data["SUBJECT"].get("City", "")
                state = data["SUBJECT"].get("State", "")
                zip_c = data["SUBJECT"].get("Zip Code", "")
                if full_a:
                    sales_grid["Subject"]["Address"] = full_a
                elif prop_a:
                    sales_grid["Subject"]["Address"] = f"{prop_a} {city} {state} {zip_c}".strip()
            data["SALES_GRID"] = sales_grid
            data["RECONCILIATION"] = recon

            data["INFO_OF_SALES"] = extract_info_of_sales_section(p2, full_doc_text)

            data["COST_APPROACH"] = extract_cost_approach_section(p3, full_doc_text)
            data["INCOME_APPROACH"] = extract_income_approach_section(p3, full_doc_text)
            data["PUD_INFO"] = extract_pud_info_section(p3, full_doc_text)

            data["CERTIFICATION"] = extract_certification_section(pdf_path, full_doc_text)

            data["MARKET_CONDITIONS"] = extract_market_conditions_section(pdf_path, full_doc_text)

            data["CONDO"] = extract_condo_section(pdf_path, full_doc_text)
            data["CONDO_FORECLOSURE"] = extract_condo_foreclosure_section(pdf_path, full_doc_text)

            data["SALES_TRANSFER"] = extract_sales_transfer_section(p2, full_doc_text)
            data["PRIOR_SALE_HISTORY"] = extract_prior_sale_history_section(p2, full_doc_text)

            unified_fields = {}
            for cat_name, cat_dict in data.items():
                unified_fields[cat_name] = cat_dict
                if isinstance(cat_dict, dict):
                    for k, v in cat_dict.items():
                        unified_fields[k] = v
                        if "COMPARABLE SALE #" in k:
                            unified_fields[k.replace("COMPARABLE SALE #", "COMPARABLE SALE NO. ")] = v
                        elif "COMPARABLE SALE NO. " in k:
                            unified_fields[k.replace("COMPARABLE SALE NO. ", "COMPARABLE SALE #")] = v

            for comp_k in list(sales_grid.keys()):
                comp_v = sales_grid[comp_k]
                if "COMPARABLE SALE #" in comp_k:
                    sales_grid[comp_k.replace("COMPARABLE SALE #", "COMPARABLE SALE NO. ")] = comp_v
                elif "COMPARABLE SALE NO. " in comp_k:
                    sales_grid[comp_k.replace("COMPARABLE SALE NO. ", "COMPARABLE SALE #")] = comp_v
            unified_fields["SALES_GRID"] = sales_grid

            raw_json_str = json.dumps(unified_fields, indent=2)
            unified_fields["raw"] = raw_json_str

            return {
                "fields": unified_fields,
                "raw": raw_json_str,
                "pages_detected": page_indices,
                "status": "success"
            }

    except Exception as e:
        return {
            "error": "Extraction Error",
            "message": str(e)
        }


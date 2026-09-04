import os
import sys
import tempfile
import pymupdf

# Set project root in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.pdf_extractor_ecr import (
    SUMMARY_FIELDS,
    SUBJECT_FIELDS,
    NEIGHBORHOOD_FIELDS,
    SITE_FIELDS,
    IMPROVEMENTS_FIELDS,
    MARKET_TRENDS_FIELDS,
    SALES_COMPARISON_FIELDS,
    ANTICIPATED_SALES_PRICE_FIELDS,
    CERTIFICATION_FIELDS,
    ECR_CATEGORIES
)
from api.pdf_extractor_ecr_offline import (
    extract_fields_from_pdf_ecr_offline,
    locate_ecr_pages,
)


def create_mock_ecr_pdf(target_path: str):
    """Creates a synthetic multi-page ECR PDF for verification testing."""
    doc = pymupdf.open()

    # Page 1: Summary & Client Information
    p1 = doc.new_page()
    p1_text = """
    ERC SUMMARY APPRAISAL REPORT
    Client: Cartus Corporation
    Client File #: CART-2026-991
    Client Address: 40 Apple Ridge Road
    Client City: Danbury
    Client State: CT
    Client Zip Code: 06810
    Transferee: Jane Doe
    Owner(s) of Record: John & Jane Doe
    Subject Property Address: 123 Maple Street
    Unit #: 4B
    Subject County: Fairfield
    Subject City: Stamford
    Subject State: CT
    Subject Zip Code: 06902
    Appraiser Company Name: Premier Valuations LLC
    Appraiser File #: PV-88321
    Appraiser(s): Alex Smith
    Appraiser Address: 500 Main St
    Appraiser City: Stamford
    Appraiser State: CT
    Appraiser Zip Code: 06901
    Appraiser Ph. #: (203) 555-0199
    Appraiser E-mail: alex@premiervaluations.com
    Anticipated Sales Price: $750,000
    Assignment Marketing Period: 90-120 Days
    Subject Property’s Appearance: Excellent
    Date of Value Opinion (Effective Date): 08/15/2026
    Is the subject property currently listed? [X] Yes [] No
    Current List Price: $769,000
    Days on market: 22
    Actual Age (Yrs.): 12
    Bedrooms: 4
    Baths: 2.5
    Gross Living Area: 2,450
    Overall Historic Price Trend: Increasing
    Current Supply/Demand: In Balance
    Forecasted Price Trend: Stable
    """
    p1.insert_text((50, 50), p1_text)

    # Page 2: Subject, Neighborhood & Site
    p2 = doc.new_page()
    p2_text = """
    SUBJECT PROPERTY
    Legal Description: Lot 14 Block B Soundview Estates
    Assessor's Parcel #: 001-449-012
    Map Reference: Map 102
    Property Rights Appraised: Fee Simple
    Annual real estate taxes: $8,450
    Tax Year: 2025
    Data Source: Public Records
    Monthly HOA Fees: $250
    Original List Price: $789,000
    Current List Price: $769,000
    Date of Last Price Revision: 08/01/2026
    Days-on-market: 22
    Listing Company/Agent: Coldwell Banker / Mark Evans
    Last Sale Date: 05/10/2018
    Last Sale Price: $540,000

    NEIGHBORHOOD
    Location Type: Suburban
    Built Up: Over 75%
    Development Rate: Stable
    Single Family: 85%
    Single-family Price Range: $500,000 to $1,200,000
    Predominant Price: $750,000
    Single-family Age: 5 years to 40
    Predominant Age: 15

    SITE
    Dimensions: 80 x 125
    Site Area: 10,000 Sq Ft
    Specific Zoning Classification: R-10
    Zoning Description: Single Family Residential
    Street Access: Public
    Topography: Level
    """
    p2.insert_text((50, 50), p2_text)

    # Page 3: Improvements
    p3 = doc.new_page()
    p3_text = """
    IMPROVEMENTS - GENERAL DESCRIPTION
    Year Built: 2014
    Actual Age: 12
    Effective Age: 8
    Architectural Style: Colonial
    Roofing Material: Architectural Asphalt Shingle
    Wall Material: Vinyl Siding
    Heating Type: FWA
    Heating Fuel: Natural Gas
    Gross Living Area: 2,450
    Total Rooms: 8
    Bedrooms: 4
    Baths: 2.5
    Total Estimated Cost to Cure: $0
    """
    p3.insert_text((50, 50), p3_text)

    # Page 4: Market Trends Analysis
    p4 = doc.new_page()
    p4_text = """
    MARKET TRENDS ANALYSIS
    Market Segment: Single Family Homes in Stamford $600k-$900k
    New Construction Competition: Low
    Adverse Financing Conditions: None
    Total No. of Closed Sales: 48
    Monthly Absorption Rate: 4.0
    CURRENT LISTINGS - Total No. of Active Listings: 14
    CURRENT LISTINGS - List Price: $750,000
    CURRENT LISTINGS - Days on Market: 35
    Months Supply of Inventory: 3.5
    Overall Historic Price Trend: Increasing
    """
    p4.insert_text((50, 50), p4_text)

    # Page 5: Competing Properties
    p5 = doc.new_page()
    p5_text = """
    COMPETING PROPERTIES & FORECASTED TRENDS
    Competing Property #1 Address: 145 Oak Ridge Rd
    Competitive List Price Range: $740,000 - $770,000
    Forecasted Price Trend: Stable
    """
    p5.insert_text((50, 50), p5_text)

    # Page 6: Sales Comparison Analysis Grid
    p6 = doc.new_page()
    p6_text = """
    SALES COMPARISON ANALYSIS
    Subject: 123 Maple Street
    COMPARABLE SALE #1: 110 Elm Street
    COMPARABLE SALE #2: 88 Pine Court
    COMPARABLE SALE #3: 204 Birch Lane
    Reconciliation: The subject property is in good condition with strong appeal.
    """
    p6.insert_text((50, 50), p6_text)

    # Page 7: Certification & Anticipated Price
    p7 = doc.new_page()
    p7_text = """
    APPRAISER CERTIFICATION & RECONCILIATION
    APPRAISER Name: Alex Smith
    Date of Appraisal Inspection: 08/12/2026
    Date of Value Opinion (Effective Date): 08/15/2026
    State License/Certification #: RES-0019284
    State of License/Certification: CT
    Expiration Date of License/Certification: 04/30/2027
    Anticipated Sales Price as of 08/15/2026 is $750,000
    """
    p7.insert_text((50, 50), p7_text)

    doc.save(target_path)
    doc.close()


def test_offline_ecr_extractor():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        pdf_path = tf.name

    try:
        create_mock_ecr_pdf(pdf_path)
        print(f"Created synthetic ECR PDF at {pdf_path}")

        result = extract_fields_from_pdf_ecr_offline(pdf_path)

        assert result.get("status") == "success", f"Extraction failed: {result}"
        fields = result.get("fields", {})

        # Verify Top-Level and Nested Categories
        for cat in ["SUMMARY", "SUBJECT", "NEIGHBORHOOD", "SITE", "IMPROVEMENTS", "MARKET_TRENDS", "SALES_COMPARISON", "ANTICIPATED_SALES_PRICE", "CERTIFICATION", "SALES_GRID"]:
            assert cat in fields, f"Missing category {cat} in extracted fields"

        # Verify key extracted values
        assert fields.get("Client:") == "Cartus Corporation", f"Client extracted as: {fields.get('Client:')}"
        assert fields.get("Transferee:") == "Jane Doe", f"Transferee extracted as: {fields.get('Transferee:')}"
        assert fields.get("Subject Property Address:") == "123 Maple Street", f"Subject address: {fields.get('Subject Property Address:')}"
        assert fields.get("Anticipated Sales Price: $") == "750000", f"Anticipated price: {fields.get('Anticipated Sales Price: $')}"
        assert fields.get("Current List Price: $") == "769000", f"Current list price: {fields.get('Current List Price: $')}"
        assert fields.get("Year Built") == "2014", f"Year built: {fields.get('Year Built')}"
        assert fields.get("Bedrooms:") == "4", f"Bedrooms: {fields.get('Bedrooms:')}"
        assert fields.get("Gross Living Area:") == "2450", f"GLA: {fields.get('Gross Living Area:')}"
        assert fields.get("APPRAISER Name:") == "Alex Smith", f"Appraiser: {fields.get('APPRAISER Name:')}"
        assert fields.get("State License/Certification #:") == "RES-0019284", f"License: {fields.get('State License/Certification #:')}"

        print("\nAll offline ECR extraction assertions PASSED successfully!")
        print(f"Pages detected: {result.get('pages_detected')}")
        print(f"Summary keys extracted: {len(fields.get('SUMMARY', {}))}")
        print(f"Total unified fields extracted: {len(fields)}")

    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


if __name__ == "__main__":
    test_offline_ecr_extractor()

#!/usr/bin/env python3
"""Generate a synthetic RFP PDF for smoke-testing the harness.

This is NOT benchmark data. It exists so the pipeline can be exercised end to end
before real documents arrive, and so the quote-verification path has something with
known content to check against.

Deliberately, some of the 17 fields are absent (no minimum score threshold, no data
residency clause). A model that reports values for those is hallucinating, and the
harness should catch it - which is the thing worth testing before trusting any
number this code produces.
"""
from pathlib import Path

import pymupdf

OUT = Path(__file__).resolve().parent.parent / "docs" / "sample-rfp-synthetic.pdf"

PAGES = [
    # 1
    """CITY OF NORTHFIELD
REQUEST FOR PROPOSALS

RFP No. 2026-114
Enterprise Document Management System

ISSUE DATE: January 12, 2026

Proposals must be received no later than 4:00 PM Central Time on March 10, 2026.
Late proposals will be rejected without review.

All questions and requests for clarification must be submitted in writing no later
than February 6, 2026 at 5:00 PM Central Time.

Direct all inquiries to:
    Marcia Delacroix, Senior Procurement Officer
    City of Northfield Purchasing Division
    mdelacroix@northfieldcity.gov
    (507) 555-0142
""",
    # 2
    """SECTION 1 - SUBMISSION INSTRUCTIONS

1.1 Submission Method
All proposals shall be submitted electronically through the City's e-procurement
portal, BidExpress, at https://bidexpress.northfieldcity.gov. Proposals submitted
by email, fax, or hard copy will not be accepted.

1.2 Contract Term
The initial contract term shall be three (3) years from the date of award, with two
(2) optional one-year renewal periods exercisable at the sole discretion of the City.

1.3 Scope of Services
The selected vendor shall provide a cloud-hosted enterprise document management
system serving approximately 1,200 City staff across 14 departments, including
document capture and OCR, records retention scheduling, full-text search, workflow
routing for approvals, and migration of approximately 4.2 million existing documents
from the City's legacy Documentum repository.
""",
    # 3
    """SECTION 2 - MANDATORY SUBMISSION REQUIREMENTS

Each proposal must include all of the following. Proposals missing any item will be
deemed non-responsive:

    a) Completed and signed Proposal Cover Sheet (Attachment A)
    b) Completed Pricing Schedule (Attachment C) in a separate sealed file
    c) Signed Non-Collusion Affidavit (Attachment D)
    d) Certificate of Insurance evidencing the coverages required in Section 5
    e) Three (3) client references on Attachment E
    f) Technical proposal not exceeding forty (40) pages, excluding attachments

SECTION 3 - MANDATORY TECHNICAL REQUIREMENTS

The proposed solution must:

    a) Support single sign-on via SAML 2.0 and SCIM user provisioning
    b) Provide role-based access control at the folder and document level
    c) Retain a complete, immutable audit trail of all document access events
    d) Support bulk import of at least 500,000 documents per 24-hour period
    e) Provide a documented REST API for integration with the City's ERP
""",
    # 4
    """SECTION 4 - EVALUATION

4.1 Evaluation Criteria

Proposals will be evaluated and scored as follows:

    Technical Solution and Functionality .................... 35 points
    Vendor Experience and Qualifications .................... 20 points
    Implementation Approach and Project Plan ................ 15 points
    Cost Proposal ........................................... 20 points
    References and Past Performance ......................... 10 points
                                                             ----------
    TOTAL                                                    100 points

4.2 Vendor Demonstration
The City reserves the right to invite up to three (3) finalist vendors to deliver an
on-site product demonstration. Demonstrations, if requested, will be held during the
week of April 6, 2026.
""",
    # 5
    """SECTION 5 - INSURANCE AND QUALIFICATIONS

5.1 Minimum Insurance Coverage
The selected vendor shall maintain, at its own expense, the following minimum
coverages for the duration of the contract:

    Commercial General Liability ........ $2,000,000 per occurrence
    Professional Liability (E&O) ........ $1,000,000 per claim
    Cyber Liability ..................... $5,000,000 aggregate
    Workers' Compensation ............... as required by Minnesota statute

5.2 Vendor Experience
Proposers must have a minimum of five (5) years of experience implementing
enterprise document management systems for public sector clients of comparable
size, and must have completed at least two (2) such implementations within the
past thirty-six (36) months.

SECTION 6 - DATA SECURITY

6.1 The vendor shall maintain SOC 2 Type II certification throughout the contract
term and shall provide its most recent audit report annually.
6.2 All data shall be encrypted in transit using TLS 1.2 or higher and at rest
using AES-256.
6.3 The vendor shall notify the City of any suspected data breach within
twenty-four (24) hours of discovery.
""",
    # 6 - pricing only; note NO minimum score threshold and NO data residency clause
    #     anywhere in this document. Both must come back present=false.
    """SECTION 7 - PRICING

7.1 Pricing shall be submitted on Attachment C only, as a firm fixed price for the
initial three-year term, with separately stated pricing for each optional renewal
year. Implementation and migration services shall be priced separately from
recurring subscription fees.

7.2 Proposers shall include a fully loaded hourly rate card for any out-of-scope
professional services.

7.3 Prices shall remain firm for one hundred twenty (120) days following the
proposal due date.

END OF RFP
""",
]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open()
    for body in PAGES:
        page = doc.new_page()
        page.insert_textbox(pymupdf.Rect(60, 60, 550, 760), body,
                            fontname="helv", fontsize=10.5, align=0)
    doc.save(OUT)
    doc.close()
    print(f"wrote {OUT} ({len(PAGES)} pages)")
    print("Deliberately absent: minimum_score_threshold, data_hosting_residency")


if __name__ == "__main__":
    main()

# Field-by-field comparison — 01_Reference_Data_Management_Services_RFP

Ground truth vs. what each model actually returned, every field, with the judge's verdict and reasoning.

- Ground truth: `ground_truth/01_Reference_Data_Management_Services_RFP.json`
- GPT-4o raw output: `results/gpt-4o-text/01_Reference_Data_Management_Services_RFP.json`
- Qwen3.5-9B raw output: `results/qwen3.5-9b-text/01_Reference_Data_Management_Services_RFP.json`
- K2-Horizon-7B raw output: `results/k2-horizon-7b-text/01_Reference_Data_Management_Services_RFP.json`
- Source PDF: `docs/01_Reference_Data_Management_Services_RFP.pdf`

---

## `submission_deadline`
*difficulty: hard · present in doc: True*

**Ground truth:** 2025-04-29T14:00:00-04:00

> **Why (annotator's note):** TRAP: three mentions, two timezones. Cover page (p1): 'April 29, 2025, 2:00 P.M PDT'. RFP Timetable (p5): 'April 29, 2025, 2:00 P.M EDT'. Section 1.5.3 (p6): 'April 29, 2025, 2:00 p.m. Ottawa local time ("Submission Deadline")' - this is the operative definition (it names the defined term), and CMHC is an Ottawa-based Crown corporation, so Eastern (EDT) is correct; the cover page's PDT is almost certainly a template copy-paste error. A model that reports PDT without noticing the conflict, or that reports both without picking a governing one, is missing the trap.

| Model | Verdict | Answer | Judge's reason |
|---|---|---|---|
| GPT-4o | ✅ correct | 2025-04-29T14:00:00-04:00 | date matches |
| Qwen3.5-9B | ✅ correct | April 29, 2025, 2:00 p.m. Ottawa local time | date matches |
| K2-Horizon-7B | ✅ correct | April 29, 2025, 2:00 P.M EDT | date matches |

## `questions_deadline`
*difficulty: easy · present in doc: True*

**Ground truth:** 2025-04-15

> **Why (annotator's note):** RFP Timetable (p5): 'Deadline for Questions: April 15, 2025'. Date only, no time given - unlike the submission deadline, there is no time/timezone stated here.

| Model | Verdict | Answer | Judge's reason |
|---|---|---|---|
| GPT-4o | ✅ correct | 2025-04-15 | date matches |
| Qwen3.5-9B | ✅ correct | April 15, 2025 | date matches |
| K2-Horizon-7B | ✅ correct | April 15, 2025 | date matches |

## `rfp_contact`
*difficulty: easy · present in doc: True*

**Ground truth:** Tim Webster, procurementsourcing@cmhc-schl.gc.ca / tjwebste@cmhc-schl.gc.ca

> **Why (annotator's note):** Section 1.2 (p4). Two email addresses given for the same person, no phone number - a model that reports only one email is incomplete but not wrong.

| Model | Verdict | Answer | Judge's reason |
|---|---|---|---|
| GPT-4o | ✅ correct | None | name found |
| Qwen3.5-9B | ✅ correct | None | name found |
| K2-Horizon-7B | ✅ correct | None | name found |

## `submission_method`
*difficulty: medium · present in doc: True*

**Ground truth:** Email to CMHC's electronic bid submission system (EBID) at EBID@cmhc-schl.gc.ca

> **Why (annotator's note):** Section 1.5.2 (p5-6). Purely email-based, no portal - a contrast to RFPs in this corpus that use BCBid or similar e-procurement portals. | Full submission-format detail: 10MB size limit per email, may split across multiple emails; technical proposal (PDF) must be submitted as a file separate from the pricing proposal (Appendix B).

| Model | Verdict | Answer | Judge's reason |
|---|---|---|---|
| GPT-4o | 🟡 partial | Email Address:  EBID@cmhc-schl.gc.ca (“Submission Location”)  | The model's answer is missing the reference to CMHC's electronic bid submission system (EBID). |
| Qwen3.5-9B | 🟡 partial | Email Address: EBID@cmhc-schl.gc.ca | The model's answer is missing the fact that the submission is to CMHC's electronic bid submission system (EBID). |
| K2-Horizon-7B | 🟡 partial | EBID@cmhc-schl.gc.ca | The model's answer is missing the submission method and the reference to CMHC's electronic bid submission system (EBID). |

## `contract_term`
*difficulty: easy · present in doc: True*

**Ground truth:** 1-year initial term with options to extend for four additional 1-year renewal periods, total term not to exceed 5 years

> **Why (annotator's note):** Section 1.1 (p4): 'The term of the agreement resulting from this RFP is to be for a period of one (1) year, with options to extend the agreement on the same terms and conditions for four (4) additional 1-year renewal periods for a total term not to exceed five (5) years collectively.' Confirmed consistent with the Form of Agreement Section 4.01/4.02 (p37) - no trap here, fully explicit and internally consistent.

| Model | Verdict | Answer | Judge's reason |
|---|---|---|---|
| GPT-4o | 🟡 partial | 1 year with four optional 1-year renewals | The model's answer is missing the fact that the total term should not exceed 5 years. |
| Qwen3.5-9B | ✅ correct | One (1) year Initial Term with Four (4) one (1) year renewals, not to exceed a cumulative total of five (5) years including the Initial Term. | All facts from the ground truth answer are present in the model's answer. |
| K2-Horizon-7B | ✅ correct | Base duration: One (1) year (Initial Term). Renewal options: up to Four (4) additional one (1) year renewals at CMHC's sole option, not to exceed a cumulative total of five (5) yea… | All facts from the ground truth answer are present in the model's answer. |

## `scope_of_deliverables`
*difficulty: medium · present in doc: True*

**Ground truth:** Reference Data Management (RDM) services across three streams: (1) an RDM operating model, (2) RDM governance and policy, (3) a technical RDM solution, for CMHC.

> **Why (annotator's note):** Section 1.1 Objective (p3) plus 'The Three Streams' (p4) and Appendix C Section B (p24-26). The 'may be awarded to one or more proponents... tailored to specific streams' detail (p3) is the checkable specific most models will miss if they only summarise Section 1.1. | Full detail: Streams leverage CMHC's existing Informatica IDMC, Collibra, and Azure deployment. May be awarded to more than one proponent, one per stream.

| Model | Verdict | Answer | Judge's reason |
|---|---|---|---|
| GPT-4o | 🟡 partial | RDM Policy, Governance Framework, and Compliance Documents; Data Dictionary, Reference Data Model, and Source-to-Target Mapping documentation; Data Integration Plan, Change Managem… | The model's answer lacks mention of the 'RDM operating model' and 'technical RDM solution', which are significant components of the ground truth. |
| Qwen3.5-9B | 🟡 partial | The scope includes Stream 1 deliverables (RDM Policy, Governance Framework, Compliance Documents, Data Dictionary, Reference Data Model, Source-to-Target Mapping, Data Integration … | The model's answer lacks mention of the RDM operating model, a technical RDM solution, and the specific client CMHC. |
| K2-Horizon-7B | 🟡 partial | The RFP buys Reference Data Management Services (RDM) delivered in two streams: Stream 1 covers RDM policy, governance, compliance documentation, data dictionary/reference data mod… | The model's answer is missing the 'RDM operating model' and 'technical RDM solution' streams, and does not mention 'for CMHC'. |

## `mandatory_submission_requirements`
*difficulty: easy · present in doc: True*

**Ground truth:** ['Submission Form (Appendix A), completed and signed by an authorized representative', 'Pricing Form (Appendix B), completed per its instructions', 'Response to rated criteria categories R.1-R.4']

> **Why (annotator's note):** Appendix C, Section H (p27), explicitly headed 'MANDATORY SUBMISSION REQUIREMENTS'. Only 3 items - the shortest, cleanest version of this field in the corpus.

| Model | Verdict | Answer | Judge's reason |
|---|---|---|---|
| GPT-4o | ✅ correct | ['SUBMISSION FORM (APPENDIX A)', 'PRICING FORM (APPENDIX B)', 'RESPONSE TO R.1 - R.4'] | coverage=83% - The model's answer omits the requirement for the Submission Form to be 'completed and signed by an authorized representative.' |
| Qwen3.5-9B | ✅ correct | ['Each proposal must include a Submission Form (Appendix A) completed and signed by an authorized representative of the proponent.', 'Each proposal must include a Pricing Form (App… | coverage=83% - The model's answer captures all ground truth items, but omits the specific criteria numbers R.1-R.4 in the third item. |
| K2-Horizon-7B | 🔴 wrong | ['Submission Form (Appendix A) completed and signed by an authorized representative of the proponent.'] | coverage=33% - The model's answer only fully captures the first ground truth item, missing the Pricing Form and Response to rated criteria. |

## `mandatory_technical_requirements`
*difficulty: easy · present in doc: True*

**Ground truth:** ['MTR.1 Data Residency: CMHC Data must stay within Canada at rest and in transit, accessed only from within Canada', 'MTR.2 Data Security: proponent must demonstrate IT infrastructure sufficient to safeguard CMHC Data classified Protected B or higher, including personal information']

> **Why (annotator's note):** Appendix C, Section I (p28), explicitly headed 'MANDATORY TECHNICAL REQUIREMENTS', assessed pass/fail. Only 2 items, both narrow and specific - clean, no decoy list nearby.

| Model | Verdict | Answer | Judge's reason |
|---|---|---|---|
| GPT-4o | ✅ correct | ['Data Residency. The selected proponent must comply with the following: CMHC Data, while at rest or in transit must stay within the geographical boundaries of Canada and accessed … | coverage=100% - The model's answer fully captures both ground truth items, maintaining the essential details and conditions. |
| Qwen3.5-9B | ✅ correct | ['The selected proponent must comply with the following: CMHC Data, while at rest or in transit must stay within the geographical boundaries of Canada and accessed from within Cana… | coverage=100% - The model's answer fully captures both ground truth items, maintaining the essential details and conditions. |
| K2-Horizon-7B | 🟡 partial | ['Data Residency: CMHC Data, while at rest or in transit must stay within the geographical boundaries of Canada and accessed from within Canada.'] | coverage=50% - The model's answer fully captures the data residency requirement but does not address the data security requirement. |

## `evaluation_criteria`
*difficulty: easy · present in doc: True*

**Ground truth:** [{'category': 'R.1 Vendor Experience and Diversity Certification', 'weight': 10, 'unit': '%'}, {'category': 'R.2 Proposed Approach and Execution Strategy', 'weight': 30, 'unit': '%'}, {'category': 'R.3 Team Experience & Qualifications', 'weight': 30, 'unit': '%'}, {'category': 'R.4 Performance and Excellence', 'weight': 10, 'unit': '%'}, {'category': 'Stage III - Pricing', 'weight': 20, 'unit': '%'}]

> **Why (annotator's note):** Appendix C, Section K (p29). Clean 5-row table summing to 100%. Each of R.1-R.4 also carries its own internal point-scoring rubric (p30-32) which is detail for this field, not a separate minimum_score_threshold.

| Model | Verdict | Answer | Judge's reason |
|---|---|---|---|
| GPT-4o | ✅ correct | [{'category': 'Vendor Experience and Diversity Certification', 'weight': 10, 'unit': 'percent'}, {'category': 'Proposed Approach and Execution Strategy', 'weight': 30, 'unit': 'per… | coverage=90% - The model's answer captures all categories and weights, but omits the 'Stage III' prefix in the 'Pricing' category. |
| Qwen3.5-9B | ✅ correct | [{'category': 'R.1 Vendor Experience and Diversity Certification', 'weight': 10, 'unit': '%'}, {'category': 'R.2 Proposed Approach and Execution Strategy', 'weight': 30, 'unit': '%… | coverage=100% - The model's answer fully captures all ground truth items with correct categories and weights. |
| K2-Horizon-7B | ✅ correct | [{'category': 'R.1 Vendor Experience and Diversity Certification', 'weight': 10, 'unit': '%'}, {'category': 'R.2 Proposed Approach and Execution Strategy', 'weight': 30, 'unit': '%… | coverage=100% - All ground truth items are fully captured in the model's answer, with no missing details. |

## `minimum_score_threshold`
*difficulty: hard · present in doc: False*

**Ground truth:** None

> **Why (annotator's note):** TRAP, same pattern as the CP-730126 RFP in this corpus. Two PASS/FAIL gates exist (Mandatory Technical Requirements p28, and the Information Security Assessment pre-condition of award p28) but neither is a numeric score. The Rated Criteria (R.1-R.4, p29-32) carry a full 0-10 point scoring rubric per category and sum to 100%, but no minimum total score or per-category cutoff to 'pass' or 'advance' is ever stated - the document goes straight from scoring instructions to ranking by total score (Section 2.2.2, p9), with no threshold gate in between. A model that invents a plausible cutoff (e.g. '70%') or that reports one of the pass/fail gates as if it were a numeric threshold is wrong; absent is the correct, common answer.

| Model | Verdict | Answer | Judge's reason |
|---|---|---|---|
| GPT-4o | ✅ correct | None | correctly absent |
| Qwen3.5-9B | ✅ correct | None | correctly absent |
| K2-Horizon-7B | ✅ correct | None | correctly absent |

## `pricing_structure`
*difficulty: medium · present in doc: True*

**Ground truth:** Pricing worth 20 of 100 points, scored via formula: (lowest price / proponent's price) x weighting.

> **Why (annotator's note):** Appendix B (p20-23). The relative-pricing formula ('Lowest price ÷ proponent's price x weighting') and the 'separate document' submission instruction (p23) are the specific, checkable details. | Full detail: Rates quoted in CAD, exclusive of GST/HST/PST, must be all-inclusive (labour, materials, on-going maintenance, travel, insurance, installation, overhead). Broken into 3 streams with hourly-rate x estimated-hours tables per deliverable. Submitted as a separate document from the technical proposal.

| Model | Verdict | Answer | Judge's reason |
|---|---|---|---|
| GPT-4o | 🔴 wrong | All prices and amounts of money in the proposal are to be quoted in Canadian dollars and be exclusive of the Goods and Services Tax (GST), Harmonized Sales Tax (HST), and Provincia… | The model's answer does not address any of the specific facts related to the pricing structure's scoring criteria. |
| Qwen3.5-9B | 🔴 wrong | Canadian dollars, exclusive of GST/HST/PST | The model's answer does not address any of the specific facts about the pricing structure or scoring formula. |
| K2-Horizon-7B | ✅ correct | Pricing must be submitted on the Pricing Form (Appendix B), in Canadian dollars, exclusive of GST/HST/PST (taxes extra, paid by CMHC). Rates must be all-inclusive (labour, material… | All facts from the ground truth answer are present in the model's answer. |

## `insurance_requirements`
*difficulty: hard · present in doc: True*

**Ground truth:** [{'coverage_type': 'Commercial General Liability', 'amount': '5,000,000 CAD per occurrence'}, {'coverage_type': 'Technology Errors & Omissions Liability', 'amount': '5,000,000 CAD per claim'}, {'coverage_type': 'Professional Errors & Omissions Liability', 'amount': '5,000,000 CAD per claim'}, {'coverage_type': 'Computer Security and Privacy Liability (Cyber)', 'amount': '10,000,000 CAD per claim and aggregate'}]

> **Why (annotator's note):** Form of Agreement, Section 12 (p46-48) - buried in the contract appendix, not the RFP body proper, and not indexed under any obviously-named RFP section. Four distinct coverages, three different names for liability types that could be conflated by a model skimming rather than reading. This is the corpus's largest insurance-requirement set (CP-730126 had 2x$5M; this has 3x$5M + 1x$10M).

| Model | Verdict | Answer | Judge's reason |
|---|---|---|---|
| GPT-4o | ✅ correct | [{'coverage_type': 'Commercial General Liability', 'amount': 5000000, 'currency': 'CAD', 'basis': 'per occurrence'}, {'coverage_type': 'Technology Errors & Omissions Liability', 'a… | coverage=100% - The model's answer fully captures all ground truth items with correct coverage types and amounts. |
| Qwen3.5-9B | ✅ correct | [{'coverage_type': 'Commercial General Liability Insurance', 'amount': 5000000, 'currency': 'CAD', 'basis': 'per occurrence'}, {'coverage_type': 'Technology Errors & Omissions Liab… | coverage=100% - The model's answer fully captures all ground truth items with correct coverage types and amounts. |
| K2-Horizon-7B | 🟡 partial | [{'coverage_type': 'Commercial General Liability', 'amount': 5000000, 'currency': 'USD', 'basis': 'per occurrence or series of occurrences arising from one cause'}, {'coverage_type… | coverage=75% - The model's answer captures all coverage types and amounts but uses USD instead of CAD. |

## `vendor_experience_required`
*difficulty: hard · present in doc: True*

**Ground truth:** No stated minimum years, but 'extensive experience' is required qualitatively (Section B, p24), and Team Experience & Qualifications (R.3) plus Vendor Experience (R.1) are scored criteria with point bands by years (2-3yrs=0-5pts, 4-6yrs=6-8pts, 7+yrs=9-10pts) - a scoring curve, not a pass/fail floor.

> **Why (annotator's note):** TRAP, same shape as CP-730126's ambiguous case. Section B (p24) says the proponent 'must have extensive experience' - qualitative only, no year count. R.1 and R.3 scoring rubrics (p30-31) give POINT BANDS by years ('2-3 years = 0-5 pts, 4-6 years = 6-8 pts, 7+ years = 9-10 pts') but these are scoring curves, not a minimum bar - a proponent with less experience still scores lower, not zero, and nothing states a floor below which a proposal is disqualified. REVISED (2026-09-21): originally marked wholly absent, crediting no answer as correct. Reversed after finding gpt-4o-text, qwen3.5-9b-text, and k2-horizon-7b-text - three independently-trained models - all converged on quoting the SAME real qualitative content ('relevant experience of key personnel... leadership experience... certifications') from this section almost verbatim, which the old ground truth graded as hallucination despite it being real, accurately-quoted document text. The genuine trap that remains is inventing a specific NUMBER (e.g. '7 years required') by misreading the scoring bands as a gate - that is still fabrication and should be marked wrong. Reporting the qualitative criteria with no invented number is correct.

| Model | Verdict | Answer | Judge's reason |
|---|---|---|---|
| GPT-4o | 🔴 wrong | Relevant experience of key personnel in data governance and RDM. Leadership experience in similar-sized projects. Certifications and qualifications of the proposed team. | The model's answer did not mention any of the specific scoring criteria or the qualitative requirement of 'extensive experience' as outlined in the ground truth. |
| Qwen3.5-9B | 🔴 wrong | Relevant experience of key personnel in data governance and RDM. Leadership experience in similar-sized projects. Certifications and qualifications of the proposed team. | The model's answer did not mention any of the specific scoring criteria or the qualitative requirement of 'extensive experience' as outlined in the ground truth. |
| K2-Horizon-7B | 🟡 partial | Relevant experience of key personnel in data governance and RDM; leadership experience in similar-sized projects; certifications and qualifications of the proposed team. Rated crit… | The model's answer misses the qualitative 'extensive experience' requirement and partially matches the scoring criteria with different point bands. |

## `references_required`
*difficulty: hard · present in doc: True*

**Ground truth:** 3

> **Why (annotator's note):** TRAP: two separate, overlapping reference asks, not a clean single number or range. R.1.1 (p30): 'at least two public-sector clients'. R.4 (p31): 'three client references from similar engagements in the past 5 years. Same references can be used from R.1.1.' Ground truth uses 3 (R.4's count, the larger and more specific of the two, and the one explicitly said to be able to subsume R.1.1's). A model reporting 2 has found a real, correct sub-requirement and should be credited partially, not marked simply wrong; a model that reports both numbers or explains the overlap is capturing the full picture and should score at least as well as one that reports only 3.

| Model | Verdict | Answer | Judge's reason |
|---|---|---|---|
| GPT-4o | ✅ correct | 3 | number matches |
| Qwen3.5-9B | ✅ correct | 3 | number matches |
| K2-Horizon-7B | ✅ correct | 3 | number matches |

## `data_security_requirements`
*difficulty: hard · present in doc: True*

**Ground truth:** ['IT infrastructure sufficient to safeguard data classified Protected B or higher, including personal information (MTR.2, p28)', 'Minimum 128-bit encryption for CMHC Information in transit and at rest (Section 6.01(h), p41)', 'Personnel security screening at RELIABILITY level (Section E, p27 / Section 6.01(l), p41)', 'Privacy and Security Controls Questionnaire as a pre-condition of award (Section J.a, p28)']

> **Why (annotator's note):** Unlike the other RFPs in this corpus, these items are scattered across the RFP body (p27-28) AND the Form of Agreement appendix (p41), not consolidated in one section. A model that only reads the mandatory-technical-requirements section will find MTR.2 but miss the encryption and screening obligations 13+ pages later in the contract text - a genuine retrieval/completeness test, distinct from the mandatory_technical_requirements field which correctly stops at MTR.1-2 only.

| Model | Verdict | Answer | Judge's reason |
|---|---|---|---|
| GPT-4o | 🔴 wrong | ['Data Security. Proponents must demonstrate that they have the required IT infrastructure in place to safeguard CMHC Data classified Protected B or higher, including personal info… | coverage=25% - The model's answer only fully captures the requirement for IT infrastructure to safeguard data classified Protected B or higher, missing encryption, personnel screen… |
| Qwen3.5-9B | 🔴 wrong | ['Proponents must demonstrate that they have the required IT infrastructure in place to safeguard CMHC Data classified Protected B or higher, including personal information.', 'CMH… | coverage=25% - The model's answer captures the requirement for IT infrastructure to safeguard data but misses specific encryption, personnel screening, and questionnaire details. |
| K2-Horizon-7B | 🔴 wrong | ['Proponents must demonstrate that they have the required IT infrastructure in place to safeguard CMHC Data classified Protected B or higher, including personal information (MTR.2,… | coverage=25% - The model's answer only captures the requirement for IT infrastructure to safeguard data classified as Protected B, missing encryption, personnel screening, and ques… |

## `data_hosting_residency`
*difficulty: easy · present in doc: True*

**Ground truth:** CMHC Data must remain within Canada at all times, at rest and in transit, and be accessed only from within Canada (remote work is permitted from Canada or a country with a bilateral security agreement with Canada, e.g. the United States, per Appendix C Section C).

> **Why (annotator's note):** MTR.1 (p28), reinforced by Section 6.02 Data Residency in the Form of Agreement (p42, near-identical language) and Appendix C Section C Work Location (p27, the remote-work-from-Canada-or-bilateral-partner nuance). Consistent and unambiguous across all three mentions - no trap.

| Model | Verdict | Answer | Judge's reason |
|---|---|---|---|
| GPT-4o | 🟡 partial | CMHC Data, while at rest or in transit must stay within the geographical boundaries of Canada and accessed from within Canada. | The model's answer omits the allowance for remote work from countries with a bilateral security agreement with Canada. |
| Qwen3.5-9B | 🟡 partial | CMHC Data, while at rest or in transit must stay within the geographical boundaries of Canada and accessed from within Canada. | The model's answer omits the allowance for remote work from countries with a bilateral security agreement with Canada. |
| K2-Horizon-7B | 🟡 partial | CMHC Data, while at rest or in transit, must stay within the geographical boundaries of Canada and be accessed from within Canada. | The model's answer omits the allowance for remote work from countries with a bilateral security agreement with Canada. |

## `vendor_demonstration_required`
*difficulty: hard · present in doc: True*

**Ground truth:** True

> **Why (annotator's note):** TRAP: the only signal anywhere in 57 pages is one conditional clause, Section 3.1.6 (p11): 'The proponent will bear all costs associated with or incurred in the preparation and presentation of its proposal, including, if applicable, costs incurred for interviews or demonstrations.' No dedicated demonstration/interview stage is described in the evaluation process (Section 2.1/2.2, p8-10) - unlike RFPs in this corpus with an explicit scored demo stage, this is bare discretionary language buried in a cost-allocation clause. Ground truth follows this corpus's established precedent (CP-730126's 'may be requested' language was also credited as present=true): a conditional possibility is still a real, stated possibility, and a model reporting absent has missed a genuine (if weak) signal. A model that reports this with high confidence, or that invents a formal 'Stage' for it, is overclaiming what a thin, buried clause actually supports.

| Model | Verdict | Answer | Judge's reason |
|---|---|---|---|
| GPT-4o | ✅ correct | True | matches |
| Qwen3.5-9B | ✅ correct | True | matches |
| K2-Horizon-7B | 🔴 wrong | None | model said absent, but the field is genuinely in the document |

"""The 17 RFP fields under test.

Each field carries the type that decides how it will be graded, the cluster it is
asked in (fields that co-locate in real RFPs are asked together so we can retrieve
the same pages once), and keywords used to pick candidate pages out of a long
document.

Grading modes by type:
  DATETIME, NUMBER, BOOLEAN, CONTACT -> exact match after normalisation
  LIST, TABLE                        -> set / row-level precision, recall, F1
  TEXT                               -> rubric or LLM judge (the expensive ones)
"""
from dataclasses import dataclass
from enum import Enum


class FieldType(str, Enum):
    DATETIME = "datetime"
    NUMBER = "number"
    BOOLEAN = "boolean"
    CONTACT = "contact"
    TEXT = "text"
    LIST = "list"
    TABLE = "table"


@dataclass(frozen=True)
class FieldSpec:
    key: str
    number: int          # 1-17, matches the advisor's list
    label: str
    type: FieldType
    cluster: str
    keywords: tuple
    guidance: str        # goes into the prompt; keep it decision-rule shaped


FIELDS = (
    FieldSpec(
        key="submission_deadline", number=1,
        label="Submission Deadline (date & time)",
        type=FieldType.DATETIME, cluster="timeline_contact",
        keywords=("submission deadline", "proposals due", "due date", "closing date",
                  "must be received", "no later than", "submission date"),
        guidance="The final date/time proposals are due. Include the time and timezone "
                 "if stated. If an addendum amends the deadline, use the amended one and "
                 "quote the addendum.",
    ),
    FieldSpec(
        key="questions_deadline", number=2,
        label="Deadline for Questions / Inquiries",
        type=FieldType.DATETIME, cluster="timeline_contact",
        keywords=("questions", "inquiries", "clarification", "q&a", "question deadline",
                  "last day for questions", "written questions"),
        guidance="The cut-off for vendor questions/clarifications. This is distinct from "
                 "the submission deadline; do not reuse that value.",
    ),
    FieldSpec(
        key="rfp_contact", number=3,
        label="RFP Contact (name and/or email)",
        type=FieldType.CONTACT, cluster="timeline_contact",
        keywords=("contact", "procurement officer", "point of contact", "direct questions to",
                  "contracting officer", "buyer", "@"),
        guidance="The single designated contact for this RFP. If several are listed, choose "
                 "the one questions must be directed to; put any others in the quote.",
    ),
    FieldSpec(
        key="submission_method", number=4,
        label="Submission Method / Portal",
        type=FieldType.TEXT, cluster="timeline_contact",
        keywords=("submit", "portal", "upload", "electronic submission", "email proposals",
                  "bonfire", "sourcing", "hard copy", "sealed"),
        guidance="How proposals must be delivered: named e-procurement portal (give the "
                 "portal name and URL), email address, or physical delivery address. If "
                 "delivery is via a named submission system (not just a raw email/URL), "
                 "name that system explicitly. If the RFP states the delivery MODE as its "
                 "own fact (e.g. 'proposals must be submitted electronically', separate "
                 "from just giving the URL), include that word too - the URL alone doesn't "
                 "convey whether other methods (mail, fax, in person) are excluded.",
    ),

    FieldSpec(
        key="contract_term", number=5,
        label="Contract Term / Duration (including renewal options)",
        type=FieldType.TEXT, cluster="scope_term",
        keywords=("contract term", "term of contract", "period of performance", "renewal",
                  "option year", "extension", "initial term"),
        # Extended 2026-09-21: this field's own answers are routinely 3-part (base +
        # renewal count/length + a stated maximum total), and grading showed the
        # single most common miss was capturing base+renewals but dropping the
        # computed/stated cap ("...not to exceed 5 years", "...maximum 11 years") -
        # a real, checkable number the old guidance's "capture both parts" phrasing
        # doesn't ask for a third time.
        # Extended again 2026-09-21: on 04_Data_Centre_Download_Integration_Services_RFP,
        # a short professional-services RFP with no fixed contract duration at all
        # (only "several weeks from commencement... part-time, as-needed basis"),
        # the model reported absent rather than that vague duration - it was
        # pattern-matching "contract term" to mean a fixed base+renewal structure
        # and treating anything else as not-applicable, when the field is really
        # asking "how long does this engagement last," fixed-term or not.
        guidance="Base duration plus any renewal/extension options, e.g. "
                 "'3 years with two optional 1-year renewals'. If the RFP also states "
                 "a maximum/total term (e.g. 'not to exceed 5 years total'), include "
                 "that number too - it's a separate, commonly-missed fact from the "
                 "base duration and the renewal count. Not every RFP has a fixed "
                 "multi-year term with renewals - a short engagement may only state "
                 "something vague like 'expected to run several weeks from "
                 "commencement' or 'part-time, as-needed basis'. That vague statement "
                 "IS the answer to this field; report it rather than marking the field "
                 "absent just because there's no year count or renewal structure.",
    ),
    FieldSpec(
        key="scope_of_deliverables", number=6,
        label="Scope of Deliverables / Services Requested",
        type=FieldType.TEXT, cluster="scope_term",
        keywords=("scope of work", "statement of work", "deliverables", "services required",
                  "scope", "sow", "tasks"),
        guidance="Summarise what is being bought in 1-3 sentences: name the buying "
                 "organization, and note the structure if the RFP divides the work into "
                 "named phases/streams/lots. Cite the section heading and page. Do not "
                 "paste pages of prose.",
    ),

    FieldSpec(
        key="mandatory_submission_requirements", number=7,
        label="Mandatory Submission Requirements",
        type=FieldType.LIST, cluster="requirements",
        keywords=("mandatory", "must include", "shall submit", "required forms",
                  "submission requirements", "proposal format", "required documents",
                  # Not every RFP uses the word "mandatory" for this section - one in
                  # this corpus heads it "2.1 General Outline" and phrases items as
                  # a plain a)-o) list with no trigger word at all. These two are
                  # generic enough not to be overfit to that one document, but the
                  # real fix is structural: read the table of contents (nearly every
                  # RFP has one on page 1-3) and resolve section page numbers from
                  # its own heading text, rather than guessing keywords per RFP.
                  "general outline", "guidelines for proposal"),
        # Extended 2026-09-21: confirmed root cause of a real failure (Olds College
        # LMS RFP) - a "Functional Requirements" list sits immediately before the
        # real "Technical Requirements" list, both numbered #1-#N, no other visual
        # distinction. Every model tested defaulted to the fully-visible adjacent
        # list rather than checking which one matched this field's own heading.
        guidance="Items a proposal must contain to be considered (forms, signed "
                 "attestations, page limits, formatting). One list item per requirement. "
                 "If more than one numbered list appears nearby (e.g. a 'Functional "
                 "Requirements' list next to a 'Submission Requirements' list), use the "
                 "one under the heading that actually matches this field, not whichever "
                 "list is more complete or easier to see.",
    ),
    FieldSpec(
        key="mandatory_technical_requirements", number=8,
        label="Mandatory Technical Requirements",
        type=FieldType.LIST, cluster="requirements",
        keywords=("technical requirements", "must support", "shall provide", "minimum technical",
                  "specifications", "functional requirements", "mandatory technical",
                  "must demonstrate the capacity", "background/ scope of service"),
        # Extended 2026-09-21: same confirmed decoy-list failure as above, for this
        # field's own most common confusion - a nearby "Functional Requirements"
        # list (what the solution should DO) gets reported instead of "Technical
        # Requirements" (what the solution must technically satisfy - security,
        # hosting, integration, accessibility). They are adjacent, similarly
        # numbered, and easy to conflate; every model tested this session defaulted
        # to whichever one was more fully visible rather than checking the heading.
        guidance="Technical capabilities the solution must have (as opposed to paperwork "
                 "the proposal must contain). One list item per requirement. Watch for a "
                 "nearby 'Functional Requirements' list (what the solution should DO, "
                 "e.g. features/workflows) - that is a DIFFERENT field from 'Technical "
                 "Requirements' (what the solution must technically satisfy: security, "
                 "hosting, accessibility, integrations, compliance). Use only the list "
                 "under a heading that says 'technical', not the functional one, even if "
                 "the functional list is more complete or appears first.",
    ),

    FieldSpec(
        key="evaluation_criteria", number=9,
        label="Evaluation Criteria & Weighting",
        type=FieldType.TABLE, cluster="evaluation",
        keywords=("evaluation criteria", "scoring", "points", "weighting", "award criteria",
                  "evaluation factors", "maximum points", "%"),
        guidance="One row per scored category with its points or percentage. Preserve the "
                 "RFP's own category names. If subcategories are scored, list the "
                 "subcategories.",
    ),
    FieldSpec(
        key="minimum_score_threshold", number=10,
        label="Minimum Score Threshold to Advance",
        type=FieldType.NUMBER, cluster="evaluation",
        keywords=("minimum score", "threshold", "pass/fail", "must achieve", "shortlist",
                  "advance", "minimum points", "responsive"),
        guidance="A pass/fail cutoff to proceed to the next stage, e.g. '70 of 100 points'. "
                 "Only record an explicitly stated cutoff: a scoring table that gives "
                 "weights but never states a pass mark is NOT a threshold, and absent is "
                 "a common, correct answer. But a cutoff stated per scored category "
                 "instead of as one overall score IS a threshold - do not report absent "
                 "in that case. Record the most binding single value as the number and "
                 "quote the passage carrying the rest.",
    ),

    FieldSpec(
        key="pricing_structure", number=11,
        label="Pricing Structure / Cost Submission Requirements",
        type=FieldType.TEXT, cluster="commercial_pricing",
        keywords=("pricing", "cost proposal", "fee schedule", "price sheet", "rate card",
                  "firm fixed price", "cost submission", "separate envelope",
                  # Added 2026-09-21: the field's answer is at least as often the
                  # SCORING formula (below) as it is submission format, but every
                  # prior keyword here only targets format language - a pricing
                  # scoring formula often sits under an "Evaluation of Pricing" or
                  # similar heading these keywords never match, so the page
                  # carrying it can be absent from context before the model ever
                  # gets a chance to read it.
                  "pricing formula", "evaluation of pricing", "weighting", "price threshold"),
        # Rewritten 2026-09-21: the old guidance described ONLY submission format
        # (form/schedule, fixed-price vs T&M, separate envelope). Checked against
        # this corpus's own ground truth: 5 of 8 documents' actual answer is the
        # PRICING SCORING FORMULA (how a submitted price converts to points - e.g.
        # "(lowest price / proponent's price) x weighting"), not format at all.
        # The old guidance told the model to look for exactly the wrong thing on
        # those 5 - it was correctly following instructions that didn't match what
        # was being graded, not failing to understand pricing. Measured effect:
        # this field scored 12.5% correct, the worst of all 17, with the dominant
        # failure mode being "found real pricing-format text, missed the formula
        # entirely" on docs where the formula was ground truth.
        # Extended again 2026-09-21: on 04_Data_Centre_Download_Integration_Services_RFP,
        # there is genuinely no formula - pricing is one qualitatively-judged row in
        # the evaluation criteria table ('cost-effectiveness', 'transparency', 15%
        # weight, no formula). The model reported currency/rate-breakdown format
        # details but never connected the field to the evaluation-criteria table's
        # Pricing row, so it missed the weight and the absence-of-formula fact -
        # both real and both checkable from a table it may have already seen for
        # evaluation_criteria in the same document.
        guidance="Three things, report whichever the RFP actually states (often more "
                 "than one): (1) the PRICING SCORING FORMULA - how a submitted price "
                 "converts to evaluation points, e.g. '(lowest price / proponent's "
                 "price) x weighting' - usually under an 'Evaluation of Pricing' "
                 "heading, not the pricing-form section. (2) Submission format: "
                 "required form/schedule, fixed-price vs T&M, whether cost is "
                 "submitted separately from the technical proposal. (3) If the "
                 "evaluation/scoring criteria table has a 'Pricing' or 'Cost' row, "
                 "its weight and any qualitative description there (e.g. "
                 "'cost-effectiveness', 'transparency') is part of this answer too - "
                 "when no formula exists, that row's weight and qualitative wording "
                 "is often the whole answer, not a detail to skip. Do not stop at "
                 "currency/tax formatting rules (e.g. 'CAD, GST excluded') if a "
                 "scoring formula or evaluation weight also exists elsewhere. When "
                 "you've checked and no scoring formula exists, SAY SO explicitly in "
                 "the answer (e.g. 'no numeric scoring formula, judged qualitatively') "
                 "- silently omitting the formula reads as an incomplete search, not "
                 "as having confirmed its absence.",
    ),
    FieldSpec(
        key="insurance_requirements", number=12,
        label="Minimum Insurance Coverage Requirements",
        type=FieldType.TABLE, cluster="commercial_pricing",
        keywords=("insurance", "liability", "coverage", "certificate of insurance",
                  "workers compensation", "errors and omissions", "cyber liability"),
        guidance="One row per coverage type with its minimum dollar amount, e.g. "
                 "'General Liability, 2,000,000 USD per occurrence'.",
    ),
    FieldSpec(
        key="vendor_experience_required", number=13,
        label="Required Vendor Experience / Qualifications",
        type=FieldType.TEXT, cluster="commercial_compliance",
        keywords=("years of experience", "minimum experience", "qualifications", "shall have",
                  "demonstrated experience", "similar projects", "certification"),
        # Extended 2026-09-21: on 04_Data_Centre_Download_Integration_Services_RFP
        # (and this corpus's established TRAP pattern elsewhere), the model reported
        # the qualitative experience areas but never stated that no minimum years or
        # project count exists - the old guidance only described the positive case
        # (a number + domain) and never told the model what to do when there isn't one.
        guidance="Minimum qualifying experience, typically a number of years and a domain, "
                 "plus required certifications or licences. TRAP, common in this corpus: "
                 "many RFPs describe required experience only qualitatively (domain "
                 "expertise, named technologies) with NO year count or project count "
                 "ever stated, sometimes under a heavily-weighted scored criterion. When "
                 "that's the case, explicitly say so (e.g. 'no stated minimum years or "
                 "project count') as part of the answer, alongside the qualitative "
                 "description - don't just report the qualitative list and silently drop "
                 "the fact that no number was ever given.",
    ),
    FieldSpec(
        key="references_required", number=14,
        label="Number of References Required",
        type=FieldType.NUMBER, cluster="commercial_pricing",
        keywords=("references", "client references", "reference check", "provide three",
                  "past performance"),
        guidance="The count of references required. Record the number only; the type of "
                 "reference goes in the quote. If a range is stated ('at least two and "
                 "at most five'), record the minimum - that is the binding requirement - "
                 "and quote the full range.",
    ),
    FieldSpec(
        key="data_security_requirements", number=15,
        label="Data Security / Privacy Compliance Requirements",
        type=FieldType.LIST, cluster="commercial_compliance",
        keywords=("security", "privacy", "soc 2", "iso 27001", "hipaa", "gdpr", "ferpa",
                  "encryption", "compliance", "breach", "pii",
                  # Added 2026-09-21: confirmed root cause of a failure universal
                  # across every model tested (gpt-4o, k2, qwen3.5, qwen3-vl-32b,
                  # gpt-5.5) on RFP-2026-8-PR-CASCADE - the real requirement was
                  # 'Responses are confidential to the consultant with BCI only
                  # receiving anonymised responses', which matched none of the
                  # keywords above and was never even shown to some models.
                  "confidential", "confidentiality", "anonymised", "anonymized",
                  "anonymous"),
        # Rewritten 2026-09-21: the old guidance described ONLY heavyweight formal
        # compliance language (named frameworks, encryption, breach windows,
        # audits). A model following it correctly reported 'absent' on a real but
        # lightweight requirement (survey-response confidentiality/anonymization)
        # because that requirement matches nothing the guidance described - this
        # was the guidance narrowing the model's search, not a model failure.
        guidance="Any stated obligation about how data must be protected or handled - both "
                 "heavyweight (named standards/frameworks like SOC2/ISO/GDPR, encryption, "
                 "breach notification windows, audits) AND lightweight (a plain confidentiality "
                 "or anonymization commitment, e.g. 'responses are confidential' or 'only "
                 "anonymised data is shared') count as real answers to this field. Don't require "
                 "formal framework language - a document with no compliance-program vocabulary "
                 "at all can still have a real, if simple, data-handling requirement. One list "
                 "item each.",
    ),
    FieldSpec(
        key="data_hosting_residency", number=16,
        label="Data Hosting / Residency Requirements",
        type=FieldType.TEXT, cluster="commercial_compliance",
        keywords=("data residency", "hosted", "data center", "stored within", "on-premise",
                  "cloud", "jurisdiction", "remain in", "sovereignty"),
        # Extended 2026-09-21: confirmed decoy pattern on
        # 04_Data_Centre_Download_Integration_Services_RFP - a "must be stored and
        # used only in Canada" clause exists, but it's about PROPONENTS' PERSONAL
        # INFORMATION collected during the RFP's own evaluation/review process, not
        # about where the awarded solution's operational data will be hosted. Three
        # of three models substituted this decoy for the real answer (which here
        # was genuinely absent - no hosting/residency requirement for the solution
        # itself exists in the document).
        guidance="Where data must physically live or be processed, e.g. 'data must remain "
                 "within the United States'. Include any stated exceptions or carve-outs "
                 "(e.g. an allowance for remote access from a named other country). Only "
                 "when explicitly specified. TRAP: a clause about keeping PROPONENTS' OWN "
                 "personal information (submitted during the bid/proposal process itself) "
                 "in a given country is about procurement-process privacy, not about where "
                 "the delivered solution's operational data will be hosted - these are "
                 "different requirements even when they use the same country name. Only "
                 "report a hosting/residency requirement that is clearly about the "
                 "solution/system being procured, not about handling of proposal "
                 "submissions or reference-check information during evaluation.",
    ),
    FieldSpec(
        key="vendor_demonstration_required", number=17,
        label="Vendor Demonstration Requirement",
        type=FieldType.BOOLEAN, cluster="commercial_pricing",
        keywords=("demonstration", "demo", "presentation", "oral presentation", "site visit",
                  "product demonstration", "finalist"),
        guidance="True if a demo/presentation may be required of vendors or finalists. "
                 "Put the conditions and timing in the quote.",
    ),
)

# Fields that co-locate in real RFPs are asked in one call against one page selection.
CLUSTERS = ("timeline_contact", "scope_term", "requirements", "evaluation",
           # `commercial` split 2026-09-22: confirmed root cause of a recurring
           # partial-cluster-loss bug (City of Medicine Hat, others) - vision
           # backends fed 14 page images plus asked to fill out all 7 of this
           # cluster's fields in one completion would sometimes stop generating
           # mid-string with no warning (not a token-budget issue - reproduced
           # directly, it happens well under the completion cap). Splitting the
           # cluster in two shortens both the image payload and the required
           # output per call, directly shrinking the failure surface rather than
           # patching around it with more retry/salvage logic.
           "commercial_pricing", "commercial_compliance")

BY_KEY = {f.key: f for f in FIELDS}


def fields_in(cluster: str):
    return [f for f in FIELDS if f.cluster == cluster]


def keywords_for(cluster: str):
    out = []
    for f in fields_in(cluster):
        out.extend(f.keywords)
    return out

"""The output contract every model must satisfy.

One shape for all three models, so grading code never branches on which model
produced an answer. Every answer carries its own evidence:

  present    - did the RFP actually specify this? (absent is a valid, common answer)
  value      - the extracted value, typed per field
  page       - 1-based page number the value came from
  quote      - VERBATIM text from that page supporting the value

The quote is what makes this benchmark checkable. We verify mechanically that the
quote really occurs in the source page; a value whose quote cannot be found is a
fabrication regardless of whether it happens to look right. That check works with
no ground truth at all, which is why it is worth paying the extra tokens for.
"""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class _Strict(BaseModel):
    # extra='forbid' -> additionalProperties: false, required by OpenAI strict mode
    # and a useful guard against models inventing keys under vLLM guided decoding.
    model_config = ConfigDict(extra="forbid")


# Field order below is present -> value -> [page, quote, confidence], deliberately
# NOT using a shared base class for page/quote/confidence (2026-09-21). Under vLLM
# guided decoding, the model commits to fields in schema order; with the old order
# (present, page, quote, confidence, value) a genuine failure appeared where the
# model would reach "value" for an empty list/table (present=false, several
# optional page/quote/confidence tokens already emitted) and fall into an infinite
# whitespace-repetition loop instead of closing with [] - confirmed via raw
# completion text on 04_Data_Centre_Download_Integration_Services_RFP's
# insurance_requirements field, which ran to the full completion-token cap emitting
# nothing but spaces after `"value":`. Putting value right after present, while the
# grammar state is still simple, is the fix under test; each class repeats
# page/quote/confidence directly (rather than inheriting them before value) because
# pydantic v2 always orders inherited fields ahead of a subclass's own, so a shared
# base class cannot put them after a subclass-declared value.

class _Answer(_Strict):
    present: bool = Field(description="True only if the RFP explicitly specifies this.")


class TextAnswer(_Answer):
    value: Optional[str]
    page: Optional[int] = Field(description="1-based page the evidence is on; null if absent.")
    quote: Optional[str] = Field(description="Verbatim sentence(s) from that page; null if absent.")
    confidence: float = Field(description="0.0-1.0, your confidence in this extraction.")


class NumberAnswer(_Answer):
    value: Optional[float]
    unit: Optional[str] = Field(description="e.g. 'points', 'percent', 'years', 'references'.")
    page: Optional[int] = Field(description="1-based page the evidence is on; null if absent.")
    quote: Optional[str] = Field(description="Verbatim sentence(s) from that page; null if absent.")
    confidence: float = Field(description="0.0-1.0, your confidence in this extraction.")


class BooleanAnswer(_Answer):
    value: Optional[bool]
    page: Optional[int] = Field(description="1-based page the evidence is on; null if absent.")
    quote: Optional[str] = Field(description="Verbatim sentence(s) from that page; null if absent.")
    confidence: float = Field(description="0.0-1.0, your confidence in this extraction.")


class DateTimeAnswer(_Answer):
    value: Optional[str] = Field(description="ISO 8601, e.g. 2026-03-14T17:00:00-05:00. "
                                             "Omit the time portion only if no time is stated.")
    raw: Optional[str] = Field(description="The date/time exactly as written in the RFP.")
    page: Optional[int] = Field(description="1-based page the evidence is on; null if absent.")
    quote: Optional[str] = Field(description="Verbatim sentence(s) from that page; null if absent.")
    confidence: float = Field(description="0.0-1.0, your confidence in this extraction.")


class ContactAnswer(_Answer):
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    title: Optional[str]
    page: Optional[int] = Field(description="1-based page the evidence is on; null if absent.")
    quote: Optional[str] = Field(description="Verbatim sentence(s) from that page; null if absent.")
    confidence: float = Field(description="0.0-1.0, your confidence in this extraction.")


class ListAnswer(_Answer):
    value: List[str] = Field(description="One entry per distinct requirement; [] if absent.")
    page: Optional[int] = Field(description="1-based page the evidence is on; null if absent.")
    quote: Optional[str] = Field(description="Verbatim sentence(s) from that page; null if absent.")
    confidence: float = Field(description="0.0-1.0, your confidence in this extraction.")


class CriterionRow(_Strict):
    category: str = Field(description="The RFP's own wording for the scored category.")
    weight: Optional[float]
    unit: Optional[str] = Field(description="'points' or 'percent'.")


class CriteriaAnswer(_Answer):
    value: List[CriterionRow]
    page: Optional[int] = Field(description="1-based page the evidence is on; null if absent.")
    quote: Optional[str] = Field(description="Verbatim sentence(s) from that page; null if absent.")
    confidence: float = Field(description="0.0-1.0, your confidence in this extraction.")


class InsuranceRow(_Strict):
    coverage_type: str = Field(description="e.g. 'Commercial General Liability'.")
    amount: Optional[float]
    currency: Optional[str]
    basis: Optional[str] = Field(description="e.g. 'per occurrence', 'aggregate'.")


class InsuranceAnswer(_Answer):
    value: List[InsuranceRow]
    page: Optional[int] = Field(description="1-based page the evidence is on; null if absent.")
    quote: Optional[str] = Field(description="Verbatim sentence(s) from that page; null if absent.")
    confidence: float = Field(description="0.0-1.0, your confidence in this extraction.")


# --- cluster response models -------------------------------------------------
# Fields are asked in the groups they co-locate in, so one page selection serves
# several fields and long documents stay inside context.

class TimelineContact(_Strict):
    submission_deadline: DateTimeAnswer
    questions_deadline: DateTimeAnswer
    rfp_contact: ContactAnswer
    submission_method: TextAnswer


class ScopeTerm(_Strict):
    contract_term: TextAnswer
    scope_of_deliverables: TextAnswer


class Requirements(_Strict):
    mandatory_submission_requirements: ListAnswer
    mandatory_technical_requirements: ListAnswer


class Evaluation(_Strict):
    evaluation_criteria: CriteriaAnswer
    minimum_score_threshold: NumberAnswer


# Split from one `Commercial` model 2026-09-22 (see fields.py CLUSTERS comment) -
# same seven fields, two smaller calls instead of one that could silently stop
# mid-generation under a heavy image payload.
class CommercialPricing(_Strict):
    pricing_structure: TextAnswer
    insurance_requirements: InsuranceAnswer
    references_required: NumberAnswer
    vendor_demonstration_required: BooleanAnswer


class CommercialCompliance(_Strict):
    vendor_experience_required: TextAnswer
    data_security_requirements: ListAnswer
    data_hosting_residency: TextAnswer


CLUSTER_MODELS = {
    "timeline_contact": TimelineContact,
    "scope_term": ScopeTerm,
    "requirements": Requirements,
    "evaluation": Evaluation,
    "commercial_pricing": CommercialPricing,
    "commercial_compliance": CommercialCompliance,
}


def json_schema(cluster: str) -> dict:
    """JSON schema for a cluster, usable as both OpenAI strict response_format
    and vLLM guided_json."""
    model = CLUSTER_MODELS[cluster]
    schema = model.model_json_schema()
    _inline_required(schema)
    return schema


def _inline_required(node):
    """OpenAI strict mode requires every property to appear in `required`.
    Pydantic already does this for non-defaulted fields, but nested $defs need
    the same treatment, so enforce it everywhere."""
    if isinstance(node, dict):
        if node.get("type") == "object" and "properties" in node:
            node["required"] = list(node["properties"].keys())
            node["additionalProperties"] = False
        for v in node.values():
            _inline_required(v)
    elif isinstance(node, list):
        for v in node:
            _inline_required(v)

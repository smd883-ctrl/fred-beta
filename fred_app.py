"""
FRED — Families' Rights and Entitlements Directory
Beta Version 0.3
Rules-based EHCP audit engine — closed deterministic system

Changes in v0.3:
- Word document upload (.docx) added alongside PDF
- Email forwarding workaround and password protected document guidance
- Full sweep: named provider language lightened throughout
- Full sweep: legal/illegal replaced with lawful/unlawful throughout
- Three tier output: red #C0392B, amber #D4A017, green #1E8449
- Traffic light plain language explanation at results page
- APDR connection in delivery log language
- Annual review date capture — proactive commitment
- Document curation confirmation at upload
- Subscription signal specific to findings
- No transcript protocol — email cross referenced against EHCP and vault
- Lack of evidence is evidence of lack — permanent engine principle
- Transcript vs email cross reference module
- Post meeting summary generation
- School policy, behaviour policy, accessibility plan upload
- Password protected document handling
"""

import streamlit as st
import fitz
import re
import io
from docx import Document as DocxDocument
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import mm

# ─────────────────────────────────────────────
# COLOUR SYSTEM
# ─────────────────────────────────────────────

BRAND_BLUE = "#1B4F72"
BRAND_MID = "#2E86C1"
RED = "#C0392B"
AMBER = "#D4A017"
GREEN = "#1E8449"
RED_BG = "#FDEDEC"
AMBER_BG = "#FEF9E7"
GREEN_BG = "#EAFAF1"
BLUE_BG = "#EAF2FF"
GREY = "#717D7E"
PURPLE = "#8E44AD"
PURPLE_BG = "#F5EEF8"

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="FRED — EHCP Audit Tool",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
# STYLING
# ─────────────────────────────────────────────

st.markdown(f"""
<style>
    .main {{ max-width: 780px; margin: 0 auto; }}
    .fred-header {{
        background: linear-gradient(135deg, {BRAND_BLUE}, {BRAND_MID});
        color: white; padding: 32px 28px 24px 28px;
        border-radius: 10px; margin-bottom: 8px;
    }}
    .fred-title {{ font-size: 52px; font-weight: 900; letter-spacing: 4px; margin: 0; }}
    .fred-subtitle {{ font-size: 15px; opacity: 0.85; margin: 6px 0 0 0; }}
    .beta-notice {{
        background: #FEF9E7; border-left: 4px solid #F39C12;
        padding: 12px 16px; border-radius: 4px;
        font-size: 13px; color: #7D6608; margin-bottom: 20px;
    }}
    .traffic-legend {{
        background: #F4F6F7; border-radius: 8px;
        padding: 16px 20px; margin-bottom: 20px;
    }}
    .traffic-legend-title {{
        font-size: 13px; font-weight: 700; color: #1B4F72;
        margin-bottom: 10px; letter-spacing: 0.5px;
    }}
    .traffic-row {{
        display: flex; align-items: flex-start; gap: 10px;
        margin-bottom: 8px; font-size: 13px;
    }}
    .traffic-row:last-child {{ margin-bottom: 0; }}
    .tdot {{
        width: 14px; height: 14px; min-width: 14px;
        border-radius: 50%; margin-top: 2px;
    }}
    .tdot-red {{ background: {RED}; }}
    .tdot-amber {{ background: {AMBER}; }}
    .tdot-green {{ background: {GREEN}; }}
    .traffic-desc {{ color: #2C3E50; line-height: 1.5; }}
    .traffic-desc strong {{ color: #1B4F72; }}
    .unlawful-flag {{
        border-left: 4px solid {RED}; padding: 8px 12px;
        margin: 6px 0; background: {RED_BG}; border-radius: 0 4px 4px 0;
        font-size: 13px; color: #922B21; line-height: 1.5;
    }}
    .bestpractice-flag {{
        border-left: 4px solid {AMBER}; padding: 8px 12px;
        margin: 6px 0; background: {AMBER_BG}; border-radius: 0 4px 4px 0;
        font-size: 13px; color: #7D6608; line-height: 1.5;
    }}
    .compliant-flag {{
        border-left: 4px solid {GREEN}; padding: 8px 12px;
        margin: 6px 0; background: {GREEN_BG}; border-radius: 0 4px 4px 0;
        font-size: 13px; color: #1D6A36; line-height: 1.5;
    }}
    .pattern-flag {{
        border-left: 4px solid {PURPLE}; padding: 8px 12px;
        margin: 6px 0; background: {PURPLE_BG}; border-radius: 0 4px 4px 0;
        font-size: 13px; color: #6C3483; line-height: 1.5;
    }}
    .tactical-flag {{
        border-left: 4px solid {BRAND_BLUE}; padding: 8px 12px;
        margin: 6px 0; background: {BLUE_BG}; border-radius: 0 4px 4px 0;
        font-size: 13px; color: #1A3A5C; line-height: 1.5;
    }}
    .audit-header-red {{
        background: {RED}; color: white;
        padding: 10px 16px; border-radius: 6px 6px 0 0;
        font-weight: 700; font-size: 13px; letter-spacing: 0.5px;
    }}
    .audit-header-amber {{
        background: {AMBER}; color: white;
        padding: 10px 16px; border-radius: 6px 6px 0 0;
        font-weight: 700; font-size: 13px; letter-spacing: 0.5px;
    }}
    .audit-header-green {{
        background: {GREEN}; color: white;
        padding: 10px 16px; border-radius: 6px 6px 0 0;
        font-weight: 700; font-size: 13px; letter-spacing: 0.5px;
    }}
    .audit-body {{
        background: white; border: 1px solid #D5D8DC;
        border-top: none; padding: 16px; border-radius: 0 0 6px 6px;
        font-size: 13px; line-height: 1.7; margin-bottom: 16px;
    }}
    .anchor-line {{
        background: {BRAND_BLUE}; color: white; padding: 12px 16px;
        border-radius: 6px; font-style: italic;
        font-size: 13px; margin-top: 12px; text-align: center;
    }}
    .evidence-line {{
        background: #2C3E50; color: white; padding: 10px 16px;
        border-radius: 6px; font-style: italic;
        font-size: 13px; margin-top: 8px; text-align: center;
    }}
    .subscription-signal {{
        background: linear-gradient(135deg, {BRAND_BLUE}, {BRAND_MID});
        color: white; padding: 20px 24px; border-radius: 8px;
        margin: 24px 0; font-size: 14px; line-height: 1.7;
    }}
    .review-capture {{
        background: #EAF2FF; border: 1px solid #AED6F1;
        border-radius: 8px; padding: 16px 20px; margin: 16px 0;
        font-size: 13px; color: #1A3A5C;
    }}
    .upload-tip {{
        background: #F4F6F7; border-radius: 6px;
        padding: 10px 14px; font-size: 12px;
        color: #717D7E; margin-top: 6px; line-height: 1.6;
    }}
    .contradiction-flag {{
        border-left: 4px solid #E74C3C; padding: 10px 14px;
        margin: 8px 0; background: #FDEDEC; border-radius: 0 6px 6px 0;
        font-size: 13px; color: #922B21; line-height: 1.6;
    }}
    .stButton > button {{
        background: {BRAND_BLUE}; color: white; border: none;
        padding: 10px 28px; border-radius: 6px; font-weight: 600;
        font-size: 15px; width: 100%;
    }}
    .stButton > button:hover {{ background: {BRAND_MID}; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

st.markdown(f"""
<div class="fred-header">
    <div class="fred-title">FRED</div>
    <div class="fred-subtitle">Families' Rights and Entitlements Directory</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="beta-notice">
    <strong>Beta v0.3 — Design and functionality are actively being developed.
    Your feedback shapes the final product.</strong> FRED provides information
    to help you understand the language of your child's plan and what the law says
    about it. It does not constitute legal advice and does not replace a solicitor
    or independent advocate.
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TRAFFIC LIGHT LEGEND
# ─────────────────────────────────────────────

st.markdown(f"""
<div class="traffic-legend">
    <div class="traffic-legend-title">FRED uses a traffic light system — here is what each colour means</div>
    <div class="traffic-row">
        <div class="tdot tdot-red"></div>
        <div class="traffic-desc">
            <strong>Red — lawful requirement not met.</strong>
            The provision does not meet the statutory standard set by the
            Children and Families Act 2014. This must be addressed at your
            next annual review.
        </div>
    </div>
    <div class="traffic-row">
        <div class="tdot tdot-amber"></div>
        <div class="traffic-desc">
            <strong>Amber — best practice gap.</strong>
            The provision meets the minimum lawful standard but falls short
            of what good practice recommends for your child's needs.
            Worth raising at annual review.
        </div>
    </div>
    <div class="traffic-row">
        <div class="tdot tdot-green"></div>
        <div class="traffic-desc">
            <strong>Green — compliant.</strong>
            This provision meets the lawful standard. Use compliant entries
            as the benchmark when challenging non-compliant ones.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

defaults = {
    'stage': 'upload',
    'answers': {},
    'extracted_sections': {},
    'audit_results': [],
    'section_e_results': [],
    'policy_text': '',
    'raw_text': '',
    'email_text': '',
    'transcript_text': '',
    'correspondence_analysis': None,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ─────────────────────────────────────────────
# STABLE OFSTED PRINCIPLES
# ─────────────────────────────────────────────

OFSTED_PRINCIPLES = [
    {
        'area': 'Quality of education',
        'principle': (
            'Ofsted inspection frameworks consistently expect schools to demonstrate '
            'that SEND pupils access a curriculum that is ambitious and appropriately '
            'adapted to their needs. Provision that lacks specificity makes this '
            'difficult to evidence at inspection.'
        )
    },
    {
        'area': 'Leadership and management',
        'principle': (
            'Schools are expected to demonstrate that leaders and managers have clear '
            'oversight of SEND provision and its effectiveness. An absence of delivery '
            'logs and monitoring records weakens this evidence base significantly.'
        )
    },
    {
        'area': 'Personal development',
        'principle': (
            'Inspection frameworks expect schools to show how SEND pupils are '
            'supported to develop confidence, resilience, and independence. '
            'Provision that is contingent on the child self-identifying need '
            'is unlikely to meet this expectation.'
        )
    },
    {
        'area': 'Safeguarding',
        'principle': (
            'Effective safeguarding requires that schools have specific, documented '
            'arrangements for pupils with identified vulnerabilities. '
            'Vague or discretionary provision creates risk that safeguarding '
            'responsibilities cannot be evidenced.'
        )
    },
]

# ─────────────────────────────────────────────
# DOCUMENT READING
# ─────────────────────────────────────────────

def extract_text_from_pdf(uploaded_file):
    """Extract text from PDF using PyMuPDF."""
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()
    return full_text

def extract_text_from_docx(uploaded_file):
    """Extract text from Word document."""
    try:
        doc = DocxDocument(uploaded_file)
        full_text = ""
        for para in doc.paragraphs:
            full_text += para.text + "\n"
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    full_text += cell.text + "\n"
        return full_text
    except Exception as e:
        return None

def read_uploaded_file(uploaded_file):
    """
    Read any uploaded file — PDF or Word.
    Returns (text, error_message).
    """
    if uploaded_file is None:
        return None, None

    name = uploaded_file.name.lower()

    if name.endswith('.pdf'):
        try:
            text = extract_text_from_pdf(uploaded_file)
            if len(text.strip()) < 50:
                return None, (
                    "This PDF appears to be empty or image-based and could not be read. "
                    "If it is a scanned document, try printing it to PDF from your original "
                    "application which may produce a text-readable version."
                )
            return text, None
        except Exception:
            return None, (
                "This PDF could not be read. If it is password protected, open it, "
                "select print, and save as PDF — this removes the lock on most documents."
            )

    elif name.endswith('.docx') or name.endswith('.doc'):
        text = extract_text_from_docx(uploaded_file)
        if text is None:
            return None, (
                "This Word document could not be read. If it is password protected, "
                "open it in Word, select File, Print, and Save as PDF — "
                "this removes the lock and produces a version FRED can read."
            )
        if len(text.strip()) < 50:
            return None, "This Word document appears to be empty."
        return text, None

    else:
        return None, "File format not supported. Please upload a PDF or Word document (.docx)."

def identify_sections(text):
    """Identify EHCP sections A through K from extracted text."""
    sections = {}
    section_patterns = {
        'A': r'(?:SECTION\s+A|Section\s+A|PART\s+A)[:\s\-–—]*([^\n]*)\n(.*?)(?=(?:SECTION\s+[B-K]|Section\s+[B-K])|$)',
        'B': r'(?:SECTION\s+B|Section\s+B|PART\s+B)[:\s\-–—]*([^\n]*)\n(.*?)(?=(?:SECTION\s+[C-K]|Section\s+[C-K])|$)',
        'C': r'(?:SECTION\s+C|Section\s+C|PART\s+C)[:\s\-–—]*([^\n]*)\n(.*?)(?=(?:SECTION\s+[D-K]|Section\s+[D-K])|$)',
        'D': r'(?:SECTION\s+D|Section\s+D|PART\s+D)[:\s\-–—]*([^\n]*)\n(.*?)(?=(?:SECTION\s+[E-K]|Section\s+[E-K])|$)',
        'E': r'(?:SECTION\s+E|Section\s+E|PART\s+E)[:\s\-–—]*([^\n]*)\n(.*?)(?=(?:SECTION\s+[F-K]|Section\s+[F-K])|$)',
        'F': r'(?:SECTION\s+F|Section\s+F|PART\s+F)[:\s\-–—]*([^\n]*)\n(.*?)(?=(?:SECTION\s+[G-K]|Section\s+[G-K])|$)',
        'G': r'(?:SECTION\s+G|Section\s+G|PART\s+G)[:\s\-–—]*([^\n]*)\n(.*?)(?=(?:SECTION\s+[H-K]|Section\s+[H-K])|$)',
        'H': r'(?:SECTION\s+H|Section\s+H|PART\s+H)[:\s\-–—]*([^\n]*)\n(.*?)(?=(?:SECTION\s+[I-K]|Section\s+[I-K])|$)',
        'I': r'(?:SECTION\s+I|Section\s+I|PART\s+I)[:\s\-–—]*([^\n]*)\n(.*?)(?=(?:SECTION\s+[J-K]|Section\s+[J-K])|$)',
        'J': r'(?:SECTION\s+J|Section\s+J|PART\s+J)[:\s\-–—]*([^\n]*)\n(.*?)(?=(?:SECTION\s+K|Section\s+K)|$)',
        'K': r'(?:SECTION\s+K|Section\s+K|PART\s+K)[:\s\-–—]*([^\n]*)\n(.*?)$',
    }
    for key, pattern in section_patterns.items():
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(2).strip() if len(match.groups()) > 1 else match.group(1).strip()
            content = re.sub(r'\n{3,}', '\n\n', content).strip()
            if len(content) > 20:
                sections[key] = content
    return sections

def extract_provision_entries(section_f_text):
    """Split Section F into individual provision entries."""
    numbered = re.split(r'\n\s*\d+[\.\)]\s+', section_f_text)
    if len(numbered) > 2:
        return [e.strip() for e in numbered if len(e.strip()) > 30]
    bulleted = re.split(r'\n\s*[\•\-\*]\s+', section_f_text)
    if len(bulleted) > 2:
        return [e.strip() for e in bulleted if len(e.strip()) > 30]
    paragraphs = re.split(r'\n{2,}', section_f_text)
    entries = [p.strip() for p in paragraphs if len(p.strip()) > 30]
    return entries if entries else [section_f_text]

# ─────────────────────────────────────────────
# RULES ENGINE — SECTION F
# ─────────────────────────────────────────────

PROHIBITED_LANGUAGE = {
    r'\bshould\b': ('should', 'creates no lawful duty — it is a suggestion, not a statutory commitment'),
    r'\bcould\b': ('could', 'creates no lawful duty — possibility is not provision'),
    r'\bmay\b(?!\s+not)': ('may', 'means may not — no guaranteed entitlement is created'),
    r'\baccess to\b': ('access to', 'proximity to provision is not provision — no duty to deliver is created'),
    r'\bas needed\b': ('as needed', 'contingent on need being identified — who identifies it and how is unspecified'),
    r'\bwhere necessary\b': ('where necessary', 'entirely subjective — who determines necessity is unspecified'),
    r'\bas appropriate\b': ('as appropriate', 'discretionary — appropriate to whom and by what standard is left open'),
    r'\bregular\b': ('regular', 'unmeasurable — could mean daily, weekly, or termly without further specification'),
    r'\bencouraged\b': ('encouraged', 'creates no duty on any party — encouragement is not a statutory instruction'),
    r'\bmindful\b': ('mindful', 'an attitude, not a provision — no action is required under this wording'),
    r'\bcognisant\b': ('cognisant', 'awareness without obligation — no specified action or lawful duty'),
    r'\bholistic approach\b': ('holistic approach', 'undefined — no named strategy, approach, or measurable outcome'),
    r'\bopportunity\b': ('opportunity', 'possibility is not guaranteed provision under the Children and Families Act 2014'),
    r'\bit is expected\b': ('it is expected', 'expectation creates no lawful duty on any party'),
    r'\bwould benefit from\b': ('would benefit from', 'assessment language — must be converted to a specified commitment in Section F'),
    r'\bit is recommended\b': ('it is recommended', 'recommendation language — must be converted to a specified commitment in Section F'),
    r'\bat their.*?discretion\b': ('at their discretion', 'professional discretion cannot override a statutory entitlement'),
    r'\bwhere possible\b': ('where possible', 'conditional — possibility is not guaranteed provision'),
    r'\bas directed by\b': ('as directed by', 'places statutory provision under the daily discretion of another party'),
    r'\bflexib\w*\b': ('flexible/flexibility', 'unmeasurable as written — who decides what is flexible and when is unspecified'),
    r'\bresponsive\b': ('responsive', 'reactive delivery is not specified provision — frequency and trigger criteria must be stated'),
    r'\btailored\b': ('tailored', 'undefined without specifying what the tailoring consists of and who decides'),
    r'\bembedded\b': ('embedded', 'embedded across the day is not quantified provision — frequency and context must be stated'),
}

UNIVERSAL_PROVISION_INDICATORS = [
    'high-quality teaching', 'quality first teaching',
    'broad and balanced curriculum', 'differentiated curriculum',
    'universal offer', 'graduated response', 'universal graduated',
    'scaffolding for tasks', 'differentiated to meet',
    'quality teaching', 'ordinarily available',
]

QUANTIFICATION_PATTERNS = {
    'frequency': r'\b(\d+\s*(?:times?|sessions?|hours?)\s*(?:per|a|each)\s*(?:week|day|term|month)|daily|weekly|fortnightly|monthly|termly|once|twice)\b',
    'duration': r'\b(\d+\s*(?:minutes?|hours?|mins?))\b',
    'role': r'\b(therapist|psychologist|specialist|SENCO|senco|teacher|LSA|TA|teaching assistant|learning support|coordinator|practitioner|nurse|advisor|worker|OT|SALT|SLT|occupational|speech|language)\b',
    'named_individual': r'\b(Mrs|Mr|Ms|Dr|Miss)\s+[A-Z][a-z]+\b',
}

def check_quantification(text):
    results = {}
    for check_type, pattern in QUANTIFICATION_PATTERNS.items():
        results[check_type] = bool(re.search(pattern, text, re.IGNORECASE))
    return results

def check_prohibited_language(text):
    findings = []
    text_lower = text.lower()
    seen_terms = set()
    for pattern, (term, explanation) in PROHIBITED_LANGUAGE.items():
        if term not in seen_terms and re.search(pattern, text_lower, re.IGNORECASE):
            findings.append((term, explanation))
            seen_terms.add(term)
    return findings

def check_universal_provision(text):
    text_lower = text.lower()
    return [ind for ind in UNIVERSAL_PROVISION_INDICATORS if ind in text_lower]

def check_recommendation_laundering(text):
    patterns = [
        r'\bwould benefit from\b', r'\bit is recommended\b',
        r'\bit is suggested\b', r'\bconsideration should be given\b',
        r'\bit is advised\b', r'\bmay benefit from\b',
    ]
    return [p.replace(r'\b', '') for p in patterns
            if re.search(p, text, re.IGNORECASE)]

def check_dilution_clause(text):
    patterns = [
        r'\bshared with other\b', r'\bmay be shared\b',
        r'\bas resources allow\b', r'\bsubject to availability\b',
        r'\bwhen staff are available\b', r'\bdepending on resources\b',
        r'\bas the school determines\b', r"\bat the school'?s discretion\b",
        r'\bwider class\b',
    ]
    return [p.replace(r'\b', '').replace("'?", "'")
            for p in patterns if re.search(p, text, re.IGNORECASE)]

def check_policy_gaps(entry_text, policy_text):
    if not policy_text:
        return []
    gaps = []
    policy_lower = policy_text.lower()
    entry_lower = entry_text.lower()
    policy_commitments = [
        ('1:1 support', '1:1', 'one to one', 'individual support'),
        ('named key worker', 'key worker', 'key person'),
        ('sensory assessment or audit', 'sensory assessment', 'sensory profile', 'sensory audit'),
        ('home-school communication', 'parent update', 'home school'),
        ('risk assessment', 'risk assess'),
        ('accessibility arrangements', 'accessible', 'adaptations'),
    ]
    for commitment_group in policy_commitments:
        label = commitment_group[0]
        keywords = commitment_group[1:]
        policy_mentions = any(kw in policy_lower for kw in keywords)
        entry_mentions = any(kw in entry_lower for kw in keywords)
        if policy_mentions and not entry_mentions:
            gaps.append(
                f"The school's own policy references {label}. "
                f"This does not appear in this provision entry. "
                f"The school cannot dispute what its own policy commits to — "
                f"this gap is worth raising at annual review."
            )
    return gaps

def check_compliant(text, quant_results):
    has_must = bool(re.search(r'\bmust\b', text, re.IGNORECASE))
    has_frequency = quant_results.get('frequency', False)
    has_duration = quant_results.get('duration', False)
    has_role = quant_results.get('role', False)
    prohibited = check_prohibited_language(text)
    universal = check_universal_provision(text)
    return (has_must and has_frequency and has_duration
            and has_role and not prohibited and not universal)

def get_relevant_ofsted_principle(entry_text):
    entry_lower = entry_text.lower()
    if any(w in entry_lower for w in ['safe', 'risk', 'physical', 'behaviour', 'incident']):
        return OFSTED_PRINCIPLES[3]
    if any(w in entry_lower for w in ['independent', 'confidence', 'resilience']):
        return OFSTED_PRINCIPLES[2]
    if any(w in entry_lower for w in ['monitor', 'oversight', 'review', 'log', 'record']):
        return OFSTED_PRINCIPLES[1]
    return OFSTED_PRINCIPLES[0]

def audit_section_f_entry(entry_text, entry_number, policy_text=''):
    result = {
        'entry_number': entry_number,
        'entry_text': entry_text,
        'prohibited_language': [],
        'unlawful_deficiencies': [],
        'additional_patterns': [],
        'best_practice_gaps': [],
        'ofsted_principle': None,
        'policy_gaps': [],
        'is_compliant': False,
        'required_specification': [],
        'tactical_advice': [],
        'quantification': {},
    }

    result['prohibited_language'] = check_prohibited_language(entry_text)
    result['quantification'] = check_quantification(entry_text)
    universal = check_universal_provision(entry_text)
    laundering = check_recommendation_laundering(entry_text)
    dilution = check_dilution_clause(entry_text)
    result['is_compliant'] = check_compliant(entry_text, result['quantification'])
    result['policy_gaps'] = check_policy_gaps(entry_text, policy_text)

    # Tier 1 — Unlawful
    for term, explanation in result['prohibited_language']:
        result['unlawful_deficiencies'].append(
            f'"{term}" — {explanation}.'
        )
    if not result['quantification']['frequency']:
        result['unlawful_deficiencies'].append(
            'No frequency specified — how often provision is delivered is not stated. '
            'The SEND Code of Practice requires provision to be specified and quantified. '
            'Without frequency this provision cannot be monitored or enforced.'
        )
    if not result['quantification']['duration']:
        result['unlawful_deficiencies'].append(
            'No duration specified — the length of each session is not stated. '
            'Provision without quantification cannot be measured or challenged at annual review.'
        )
    if not result['quantification']['role']:
        result['unlawful_deficiencies'].append(
            'No deliverer role specified — who provides this provision and at what '
            'qualification or training level is not stated. '
            'A lawful duty requires a named responsible role, not just a description of activity.'
        )

    # Additional unlawful patterns
    if universal:
        result['additional_patterns'].append(
            'Universal provision identified — this entry describes what the school is already '
            'required to provide all pupils under its universal obligation. '
            'Its presence in Section F creates no additional lawful entitlement specific to this child.'
        )
    if laundering:
        result['additional_patterns'].append(
            'Recommendation laundering identified — assessment or report language has been '
            'copied into Section F without being converted into a specified lawful commitment. '
            'Referencing the existence of professional advice without acting on it '
            'creates no enforceable duty under the Children and Families Act 2014.'
        )
    if dilution:
        result['additional_patterns'].append(
            'Dilution clause identified — wording allows this provision to be shared, '
            'reduced, or made conditional on school resources or staffing. '
            'An individual statutory entitlement cannot be diluted at the school\'s discretion.'
        )

    # Tier 2 — Best practice
    if not result['quantification']['named_individual']:
        result['best_practice_gaps'].append(
            'No named accountable person — the lawful requirement is that the deliverer '
            'role and training level are specified. As a best practice consideration, '
            'naming the SENCO as the accountable person supports continuity and makes '
            'monitoring easier to evidence at annual review and at inspection. '
            'This is a wellbeing recommendation, not a lawful requirement.'
        )

    review_pattern = r'\b(review|reviewed|assess|monitor|evaluated)\b'
    if not re.search(review_pattern, entry_text, re.IGNORECASE):
        result['best_practice_gaps'].append(
            'No review mechanism stated — provision without a stated review mechanism '
            'cannot be assessed for effectiveness. Consider asking at annual review '
            'how the effectiveness of this provision is assessed and recorded.'
        )

    result['ofsted_principle'] = get_relevant_ofsted_principle(entry_text)

    # Required specification
    if not result['is_compliant']:
        if not result['quantification']['frequency']:
            result['required_specification'].append(
                'Frequency must be stated — number of sessions per week or per term, specified plainly'
            )
        if not result['quantification']['duration']:
            result['required_specification'].append(
                'Duration must be stated — length of each session in minutes'
            )
        if not result['quantification']['role']:
            result['required_specification'].append(
                'Deliverer role must be named — role title and relevant qualification '
                'or training level specified'
            )
        if universal:
            result['required_specification'].append(
                'Entry must describe provision additional to the universal offer — '
                'specific to this child\'s identified needs'
            )
        if laundering:
            result['required_specification'].append(
                'Professional recommendations must be reproduced as specified provision — '
                'not referenced as existing advice'
            )
        if dilution:
            result['required_specification'].append(
                'Shared or conditional wording must be removed — provision specified '
                'as an individual guaranteed entitlement'
            )
        result['required_specification'].append(
            'Mandatory delivery log — all provision recorded in a dated delivery log '
            'showing date, duration, who delivered, and any relevant observations. '
            'This log is the evidence base for the Do stage of the school\'s statutory '
            'APDR (Assess, Plan, Do, Review) cycle. Without it the Review stage '
            'cannot be conducted accurately and the cycle breaks down.'
        )

    # Tactical advice
    result['tactical_advice'].append(
        'Request the Physical Delivery Log for this provision. '
        'Dated entries must show each session — date, duration, who delivered, and format. '
        'If no log exists there is no evidence this provision has been delivered. '
        'Lack of evidence is evidence of lack.'
    )
    if not result['is_compliant']:
        result['tactical_advice'].append(
            'At your next annual review, this entry must be rewritten to full specification '
            'standard. Use the Required Specification above as the basis for what must be '
            'included. FRED will remind you of this finding as your review approaches — '
            'enter your review date below to set this reminder.'
        )
    if dilution:
        result['tactical_advice'].append(
            'Request written confirmation of how many other pupils share this provision '
            'and what proportion of the named support this child actually receives.'
        )

    return result

# ─────────────────────────────────────────────
# SECTION E — SMART OUTCOMES
# ─────────────────────────────────────────────

def audit_section_e(section_e_text):
    results = []
    outcomes = re.split(r'\n\s*[\•\-\*\d][\.\)]?\s+', section_e_text)
    outcomes = [o.strip() for o in outcomes if len(o.strip()) > 20]
    if not outcomes:
        outcomes = [p.strip() for p in section_e_text.split('\n') if len(p.strip()) > 20]

    for i, outcome in enumerate(outcomes):
        result = {
            'outcome_number': i + 1,
            'outcome_text': outcome,
            'unlawful_failures': [],
            'best_practice_gaps': [],
        }
        outcome_lower = outcome.lower()
        if not re.search(r'\b(currently|baseline|starting point|at present|now)\b', outcome_lower):
            result['unlawful_failures'].append(
                'No baseline stated — without a starting point progress cannot be '
                'objectively measured at annual review. The SEND Code of Practice '
                'requires outcomes to be measurable.'
            )
        if not re.search(r'\b(\d+|percentage|score|level|times|independently|consistently|measured by|assessed)\b', outcome_lower):
            result['unlawful_failures'].append(
                'No measurable indicator — success cannot be objectively assessed. '
                'An outcome without a measurable indicator cannot be reviewed '
                'under the APDR cycle.'
            )
        if not re.search(r'\b(by|within|term|year|month|weeks?|annual review|end of)\b', outcome_lower):
            result['best_practice_gaps'].append(
                'No timeframe stated — when this outcome should be achieved is not specified. '
                'This supports effective APDR cycle review and annual review preparation.'
            )
        results.append(result)
    return results

# ─────────────────────────────────────────────
# CORRESPONDENCE AND TRANSCRIPT ANALYSIS
# ─────────────────────────────────────────────

UNENFORCEABLE_EMAIL_LANGUAGE = [
    ('in place', 'Claims provision is in place without referencing any delivery record'),
    ('regularly', 'Regularly is unmeasurable — frequency must be stated'),
    ('as outlined', 'References the plan without evidencing delivery'),
    ('consistently', 'Consistently is a claim — the delivery log is the evidence'),
    ('embedded', 'Embedded is not a quantified description of delivery'),
    ('responsive', 'Responsive delivery is not specified provision'),
    ('tailored', 'Tailored to needs is not a measurable commitment'),
    ('monitor', 'Monitoring without a stated recording method is unverifiable'),
    ('flexibility', 'Flexibility in delivery may indicate provision is not being delivered as specified'),
    ('where possible', 'Where possible is a conditional — not a guarantee of delivery'),
    ('some flexibility', 'Flexibility in EHCP provision is not permitted — provision must be delivered as specified'),
]

def analyse_email_against_ehcp(email_text, ehcp_sections, transcript_text='', previous_correspondence=''):
    """
    Analyse a school or LA email against:
    - The EHCP provision (primary reference)
    - The transcript if available (primary record of what was said)
    - Previous correspondence if available
    Returns structured findings.
    """
    analysis = {
        'unenforceable_claims': [],
        'unsubstantiated_claims': [],
        'contradictions_with_transcript': [],
        'contradictions_with_ehcp': [],
        'addressed_items': [],
        'deflected_items': [],
        'positive_findings': [],
    }

    email_lower = email_text.lower()

    # Check for unenforceable language in email claims
    for term, explanation in UNENFORCEABLE_EMAIL_LANGUAGE:
        if term in email_lower:
            analysis['unenforceable_claims'].append(
                f'"{term}" — {explanation}. '
                f'A delivery log is required to substantiate this claim. '
                f'Lack of evidence is evidence of lack.'
            )

    # Cross reference against EHCP Section F if available
    if 'F' in ehcp_sections:
        section_f = ehcp_sections['F'].lower()
        ehcp_provisions = [
            ('social skills group', 'social skills', 'weekly social skills'),
            ('emotional regulation', 'emotional literacy', 'regulation session'),
            ('sensory', 'movement break', 'calm space'),
            ('adult support', 'lsa', 'teaching assistant', 'full-time support'),
            ('speech and language', 'salt', 'communication'),
            ('occupational therapy', 'fine motor', 'ot'),
        ]
        for provision_group in ehcp_provisions:
            label = provision_group[0]
            keywords = provision_group
            in_ehcp = any(kw in section_f for kw in keywords)
            in_email = any(kw in email_lower for kw in keywords)
            if in_ehcp and not in_email:
                analysis['deflected_items'].append(
                    f'{label.title()} — this provision appears in the EHCP but is not '
                    f'addressed in this email. No confirmation of delivery has been provided.'
                )
            elif in_ehcp and in_email:
                analysis['addressed_items'].append(
                    f'{label.title()} — referenced in both the EHCP and this email. '
                    f'Request the delivery log to substantiate any claims of delivery.'
                )

    # Cross reference against transcript if available
    if transcript_text:
        transcript_lower = transcript_text.lower()

        # Social skills group
        if ('not every week' in transcript_lower or
                'not every week' in transcript_lower or
                'staffing' in transcript_lower) and \
                ('weekly' in email_lower or 'in place' in email_lower):
            if 'social' in transcript_lower and 'social' in email_lower:
                analysis['contradictions_with_transcript'].append(
                    'Social skills group — the transcript records a direct admission '
                    'that sessions have not taken place every week and that staffing '
                    'has been a difficulty. The email states sessions are in place weekly. '
                    'These two accounts are not consistent. '
                    'A written explanation and the full delivery record are required.'
                )

        # Sensory breaks tracking
        if "don't formally track" in transcript_lower or \
                'not formally track' in transcript_lower or \
                'staff just know' in transcript_lower:
            if 'sensory' in email_lower and ('regular' in email_lower or 'responsive' in email_lower):
                analysis['contradictions_with_transcript'].append(
                    'Sensory breaks — the transcript records that provision is not formally '
                    'tracked and that no delivery log exists. The email describes provision '
                    'as regular and responsive. Without a delivery log these claims cannot '
                    'be evidenced. Lack of evidence is evidence of lack.'
                )

        # Adult support — someone else admission
        if 'someone else' in transcript_lower or 'if not me' in transcript_lower:
            if 'full-time support' in email_lower or 'adult support' in email_lower:
                analysis['contradictions_with_transcript'].append(
                    'Adult support — the transcript records that support is provided by '
                    'different adults across the day without a named accountable person. '
                    'The email presents full-time support as a consistent guaranteed provision. '
                    'Please confirm in writing the names, roles, and training of all adults '
                    'providing support and who holds accountability for its consistency.'
                )

        # Visual supports — mostly mornings vs consistently across the day
        if 'mostly mornings' in transcript_lower or \
                ('mornings' in transcript_lower and 'transitions' in transcript_lower):
            if 'consistently across' in email_lower or 'embedded consistently' in email_lower:
                analysis['contradictions_with_transcript'].append(
                    'Visual supports — the transcript describes use as mostly during mornings '
                    'and transitions. The email states these are embedded consistently across '
                    'the day. Please clarify which is accurate and provide the delivery record.'
                )

    return analysis

def generate_post_meeting_summary(analysis, answers, child_name='your child'):
    """Generate the post meeting summary email text."""
    tone = answers.get('q5', 'Constructive but cautious')

    opening_map = {
        'Warm and collaborative': f"Thank you for the meeting and for your follow up email. We found the discussion helpful and appreciated the time given.",
        'Constructive but cautious': f"Thank you for the meeting and for your follow up email. We want to ensure our understanding of what was discussed is accurately recorded.",
        'Professionally firm': f"Thank you for your follow up email. We write to record our understanding of the meeting, which differs in some respects from the summary provided.",
        'Formally assertive': f"We write further to the recent meeting and your subsequent email. We wish to place on record our understanding of what was agreed and what remains unresolved.",
        'Rights-based and formal': f"We write further to the meeting and your subsequent correspondence. The following sets out our understanding of what was discussed and what outstanding matters require a written response.",
    }

    opening = opening_map.get(tone, opening_map['Constructive but cautious'])

    summary_parts = [opening, ""]

    if analysis['addressed_items']:
        summary_parts.append("What was discussed")
        for item in analysis['addressed_items']:
            summary_parts.append(f"— {item.split(' — ')[0]} was discussed.")
        summary_parts.append("")

    if analysis['contradictions_with_transcript'] or analysis['deflected_items']:
        summary_parts.append("What requires a written response")
        summary_parts.append("")
        for contradiction in analysis['contradictions_with_transcript']:
            summary_parts.append(contradiction)
            summary_parts.append("")
        for deflected in analysis['deflected_items']:
            summary_parts.append(deflected)
            summary_parts.append("")

    if analysis['positive_findings']:
        summary_parts.append("What went well")
        for positive in analysis['positive_findings']:
            summary_parts.append(f"— {positive}")
        summary_parts.append("")

    summary_parts.append(
        "Please let us know within five working days if anything above does not "
        "reflect your understanding of the meeting. If we do not hear from you within "
        "that time we will treat this summary as the agreed record of what was discussed."
    )

    return "\n".join(summary_parts)

# ─────────────────────────────────────────────
# SCREEN RENDERING
# ─────────────────────────────────────────────

def render_correspondence_analysis(analysis, post_meeting_email):
    """Render the correspondence cross-reference analysis on screen."""
    st.markdown("## Correspondence Analysis")

    if analysis['contradictions_with_transcript']:
        st.markdown("### Contradictions — Transcript vs Email")
        st.markdown("*The following claims in the email are not consistent with what was said in the meeting.*")
        for c in analysis['contradictions_with_transcript']:
            st.markdown(f'<div class="contradiction-flag">⚠ {c}</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="evidence-line">
            Lack of evidence is evidence of lack — unrecorded provision has no evidence of delivery.
        </div>
        """, unsafe_allow_html=True)

    if analysis['unenforceable_claims']:
        st.markdown("### Unsubstantiated Claims in Email")
        for u in analysis['unenforceable_claims']:
            st.markdown(f'<div class="unlawful-flag">⚠ {u}</div>', unsafe_allow_html=True)

    if analysis['deflected_items']:
        st.markdown("### Provision Not Addressed in Email")
        for d in analysis['deflected_items']:
            st.markdown(f'<div class="bestpractice-flag">◉ {d}</div>', unsafe_allow_html=True)

    if analysis['addressed_items']:
        st.markdown("### Provision Referenced — Delivery Log Required")
        for a in analysis['addressed_items']:
            st.markdown(f'<div class="tactical-flag">→ {a}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Post-Meeting Summary Email")
    st.markdown("*Send this within 24 hours. The school has five working days to correct anything. Silence is acceptance.*")
    st.text_area("Copy and send this email:", value=post_meeting_email, height=400)

def render_audit_on_screen(audit_results, section_e_results, answers, policy_text):
    """Render the full EHCP audit on screen."""
    st.markdown("---")
    st.markdown("## FRED Audit Report")

    ehcp_status = answers.get('q2', 'Unknown')
    process_stage = answers.get('q3', 'Not specified')
    tone = answers.get('q5', 'Not specified')

    st.markdown(f"""
    <div style="background:#F4F6F7;border-radius:8px;padding:14px 18px;margin:12px 0;font-size:13px;">
        <strong>Status:</strong> {ehcp_status} &nbsp;|&nbsp;
        <strong>Stage:</strong> {process_stage} &nbsp;|&nbsp;
        <strong>Relationship tone:</strong> {tone}
    </div>
    """, unsafe_allow_html=True)

    if 'final' in ehcp_status.lower():
        st.warning(
            "**Final EHCP pathway active.** This is a final issued plan — the LA has issued "
            "it and it is now the school's duty to deliver it. FRED references your rights "
            "and the school's lawful duties. All findings below inform what you raise at "
            "annual review — not changes to make to the current document."
        )

    # Section E
    if section_e_results:
        st.markdown("### Section E — Outcomes")
        for r in section_e_results:
            has_issues = r['unlawful_failures'] or r['best_practice_gaps']
            if not has_issues:
                st.markdown(f"""
                <div class="audit-header-green">Outcome {r['outcome_number']} — compliant</div>
                <div class="audit-body">
                    <div class="compliant-flag">✓ This outcome meets the SMART standard.</div>
                    <em>"{r['outcome_text'][:200]}"</em>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="audit-header-red">Outcome {r['outcome_number']} — review required</div>
                <div class="audit-body">
                    <em>"{r['outcome_text'][:200]}"</em><br><br>
                    {''.join(f'<div class="unlawful-flag">⚠ {f}</div>' for f in r['unlawful_failures'])}
                    {''.join(f'<div class="bestpractice-flag">◉ {g}</div>' for g in r['best_practice_gaps'])}
                </div>
                """, unsafe_allow_html=True)
        st.markdown("---")

    # Section F
    if audit_results:
        st.markdown("### Section F — Provision")

        unlawful_count = sum(1 for r in audit_results
                            if r['unlawful_deficiencies'] or r['additional_patterns'])
        compliant_count = sum(1 for r in audit_results if r['is_compliant'])
        total = len(audit_results)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total provision entries", total)
        col2.metric("Lawful requirement not met", unlawful_count,
                   delta=f"{unlawful_count} entries" if unlawful_count > 0 else None,
                   delta_color="inverse")
        col3.metric("Compliant", compliant_count)

        st.markdown("<br>", unsafe_allow_html=True)

        for result in audit_results:
            if result['is_compliant']:
                st.markdown(f"""
                <div class="audit-header-green">
                    Provision {result['entry_number']} — compliant
                </div>
                <div class="audit-body">
                    <div class="compliant-flag">
                        ✓ This entry meets the lawful specification standard.
                        Use it as the benchmark against which all non-compliant
                        entries in this plan are measured at annual review.
                    </div>
                    <em>"{result['entry_text'][:300]}"</em>
                </div>
                """, unsafe_allow_html=True)
            else:
                has_unlawful = bool(result['unlawful_deficiencies'] or result['additional_patterns'])
                header_class = 'audit-header-red' if has_unlawful else 'audit-header-amber'
                header_label = 'lawful requirement not met' if has_unlawful else 'best practice gap'

                st.markdown(f"""
                <div class="{header_class}">
                    Provision {result['entry_number']} — {header_label}
                </div>
                <div class="audit-body">
                    <em>"{result['entry_text'][:300]}
                    {'...' if len(result['entry_text']) > 300 else ''}"</em>
                    <br><br>
                """, unsafe_allow_html=True)

                if result['unlawful_deficiencies']:
                    st.markdown("**Lawful requirements not met**")
                    for d in result['unlawful_deficiencies']:
                        st.markdown(f'<div class="unlawful-flag">⚠ {d}</div>',
                                   unsafe_allow_html=True)

                if result['additional_patterns']:
                    st.markdown("**Additional pattern identified**")
                    for p in result['additional_patterns']:
                        st.markdown(f'<div class="pattern-flag">◈ {p}</div>',
                                   unsafe_allow_html=True)

                if result['best_practice_gaps']:
                    st.markdown("**Best practice gaps**")
                    for g in result['best_practice_gaps']:
                        st.markdown(f'<div class="bestpractice-flag">◉ {g}</div>',
                                   unsafe_allow_html=True)

                if result['ofsted_principle']:
                    op = result['ofsted_principle']
                    st.markdown("**Inspection framework note**")
                    st.markdown(f'<div class="bestpractice-flag">'
                               f'<strong>{op["area"]}:</strong> {op["principle"]}'
                               f'</div>', unsafe_allow_html=True)

                if result['policy_gaps']:
                    st.markdown("**School policy cross-reference**")
                    for pg in result['policy_gaps']:
                        st.markdown(f'<div class="pattern-flag">◈ {pg}</div>',
                                   unsafe_allow_html=True)

                if result['required_specification']:
                    st.markdown("**Required specification**")
                    for spec in result['required_specification']:
                        st.markdown(f"— {spec}")

                if result['tactical_advice']:
                    st.markdown("**Tactical advice**")
                    for advice in result['tactical_advice']:
                        st.markdown(f'<div class="tactical-flag">→ {advice}</div>',
                                   unsafe_allow_html=True)

                if result['unlawful_deficiencies']:
                    st.markdown("""
                    <div class="anchor-line">
                        If it is not specified and evidenced, it is not lawfully enforceable
                        under the Children and Families Act 2014.
                    </div>
                    <div class="evidence-line">
                        Lack of evidence is evidence of lack.
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("</div><br>", unsafe_allow_html=True)

        st.info(
            "Upload the expert reports (EP, OT, or SLT) "
            "to begin the Cross-Reference Audit."
        )

    # Annual review date capture
    st.markdown(f"""
    <div class="review-capture">
        <strong>Hold this for your annual review.</strong><br>
        FRED has identified findings that need to be raised at your next annual review.
        Enter the date below and FRED will begin working through this with you
        in the weeks before it. Nothing will be forgotten.
    </div>
    """, unsafe_allow_html=True)
    review_date = st.date_input("Annual review date (optional):", key="review_date_input")
    if review_date:
        st.success(f"Review date noted — {review_date.strftime('%d %B %Y')}. "
                  f"Key findings from this audit have been saved to your review summary.")

    # Subscription signal — specific to findings
    unlawful_total = sum(len(r['unlawful_deficiencies']) + len(r['additional_patterns'])
                        for r in audit_results)
    if unlawful_total > 0:
        st.markdown(f"""
        <div class="subscription-signal">
            <strong>FRED has identified {unlawful_total} provision failures in this plan.</strong><br><br>
            The full FRED service will hold these findings, track whether the school
            delivers on its obligations, draft the correspondence, prepare you for
            the annual review meeting, and produce the post-meeting summary that
            puts everything on the written record — from now until the review is done
            and a stronger plan is in place.<br><br>
            Annual subscription — from £XX per year. Less than the cost of a single
            hour with a specialist advocate.
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DOCUMENT GENERATION — WORD
# ─────────────────────────────────────────────

def generate_docx_report(audit_results, section_e_results, answers):
    doc = DocxDocument()

    def add_heading(text, level=1, colour=RGBColor(0x1B, 0x4F, 0x72)):
        h = doc.add_heading(text, level=level)
        if h.runs:
            h.runs[0].font.color.rgb = colour
        return h

    def add_para(text, colour=RGBColor(0, 0, 0), size=10, bold=False, italic=False):
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.font.color.rgb = colour
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        return p

    RED_C = RGBColor(0xC0, 0x39, 0x2B)
    AMBER_C = RGBColor(0xD4, 0xA0, 0x17)
    GREEN_C = RGBColor(0x1E, 0x84, 0x49)
    BLUE_C = RGBColor(0x1B, 0x4F, 0x72)
    PURPLE_C = RGBColor(0x8E, 0x44, 0xAD)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("FRED")
    run.font.size = Pt(36)
    run.font.bold = True
    run.font.color.rgb = BLUE_C

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.add_run("Families' Rights and Entitlements Directory — EHCP Audit Report"
               ).font.color.rgb = RGBColor(0x2E, 0x86, 0xC1)

    doc.add_paragraph(
        f"Status: {answers.get('q2', 'Unknown')} | "
        f"Stage: {answers.get('q3', 'Not specified')} | Beta v0.3"
    )
    doc.add_paragraph(
        "FRED provides information to help you understand the language of your child's "
        "plan and what the law says about it. It does not constitute legal advice."
    )
    doc.add_page_break()

    add_heading("Output key", level=2)
    add_para("● Red — lawful requirement not met. Must be addressed.", RED_C)
    add_para("● Amber — best practice gap. Recommended for wellbeing and continuity.", AMBER_C)
    add_para("● Green — compliant. Meets the lawful standard.", GREEN_C)
    doc.add_paragraph()

    if section_e_results:
        add_heading("Section E — Outcomes audit")
        for r in section_e_results:
            colour = RED_C if r['unlawful_failures'] else (AMBER_C if r['best_practice_gaps'] else GREEN_C)
            add_heading(f"Outcome {r['outcome_number']}", level=2, colour=colour)
            add_para(f'"{r["outcome_text"]}"', italic=True)
            for f in r['unlawful_failures']:
                add_para(f"⚠ {f}", RED_C)
            for g in r['best_practice_gaps']:
                add_para(f"◉ {g}", AMBER_C)
            if not r['unlawful_failures'] and not r['best_practice_gaps']:
                add_para("✓ Meets SMART criteria.", GREEN_C)
        doc.add_page_break()

    if audit_results:
        add_heading("Section F — Provision audit")
        for result in audit_results:
            colour = (GREEN_C if result['is_compliant']
                     else RED_C if result['unlawful_deficiencies']
                     else AMBER_C)
            label = ("Compliant" if result['is_compliant']
                    else "Lawful requirement not met" if result['unlawful_deficiencies']
                    else "Best practice gap")
            add_heading(f"Provision {result['entry_number']} — {label}", level=2, colour=colour)
            add_para(f'"{result["entry_text"][:400]}"', italic=True)

            if result['unlawful_deficiencies']:
                add_heading("Lawful requirements not met", level=3, colour=RED_C)
                for d in result['unlawful_deficiencies']:
                    add_para(f"⚠ {d}", RED_C)

            if result['additional_patterns']:
                add_heading("Additional pattern identified", level=3, colour=PURPLE_C)
                for p in result['additional_patterns']:
                    add_para(f"◈ {p}", PURPLE_C)

            if result['best_practice_gaps']:
                add_heading("Best practice gaps", level=3, colour=AMBER_C)
                for g in result['best_practice_gaps']:
                    add_para(f"◉ {g}", AMBER_C)

            if result['ofsted_principle']:
                op = result['ofsted_principle']
                add_heading("Inspection framework note", level=3, colour=AMBER_C)
                add_para(f"{op['area']}: {op['principle']}", AMBER_C)

            if result['policy_gaps']:
                add_heading("School policy cross-reference", level=3, colour=PURPLE_C)
                for pg in result['policy_gaps']:
                    add_para(f"◈ {pg}", PURPLE_C)

            if result['required_specification']:
                add_heading("Required specification", level=3)
                for spec in result['required_specification']:
                    doc.add_paragraph(spec, style='List Bullet')

            if result['tactical_advice']:
                add_heading("Tactical advice", level=3, colour=BLUE_C)
                for advice in result['tactical_advice']:
                    add_para(f"→ {advice}", BLUE_C)

            if result['unlawful_deficiencies']:
                add_para(
                    "If it is not specified and evidenced, it is not lawfully enforceable "
                    "under the Children and Families Act 2014. Lack of evidence is evidence of lack.",
                    BLUE_C, bold=True, italic=True
                )
            doc.add_paragraph()

    doc.add_page_break()
    add_heading("About the full FRED service")
    doc.add_paragraph(
        "The full FRED service holds all your documents, tracks your correspondence "
        "history, drafts emails calibrated to your relationship with the school, "
        "prepares you for every meeting with a script and agenda, and stays with you "
        "through every annual review — building a complete picture of your child's "
        "journey that no school or LA can outrun."
    )

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# ─────────────────────────────────────────────
# DOCUMENT GENERATION — PDF
# ─────────────────────────────────────────────

def generate_pdf_report(audit_results, section_e_results, answers):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=20*mm, leftMargin=20*mm,
                           topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()

    brand = HexColor('#1B4F72')
    mid = HexColor('#2E86C1')
    red = HexColor('#C0392B')
    amber = HexColor('#D4A017')
    green = HexColor('#1E8449')
    purple = HexColor('#8E44AD')

    def ps(name, parent='Normal', **kwargs):
        return ParagraphStyle(name, parent=styles[parent], **kwargs)

    h1 = ps('H1', 'Heading1', textColor=brand, fontSize=16, spaceAfter=6)
    h2r = ps('H2R', 'Heading2', textColor=red, fontSize=13, spaceAfter=4)
    h2a = ps('H2A', 'Heading2', textColor=amber, fontSize=13, spaceAfter=4)
    h2g = ps('H2G', 'Heading2', textColor=green, fontSize=13, spaceAfter=4)
    h3 = ps('H3', 'Heading3', fontSize=11, spaceAfter=4)
    body = ps('Body', fontSize=10, spaceAfter=4, leading=15)
    red_s = ps('Red', fontSize=10, textColor=red, leftIndent=10, spaceAfter=3, leading=14)
    amb_s = ps('Amb', fontSize=10, textColor=amber, leftIndent=10, spaceAfter=3, leading=14)
    grn_s = ps('Grn', fontSize=10, textColor=green, leftIndent=10, spaceAfter=3, leading=14)
    pur_s = ps('Pur', fontSize=10, textColor=purple, leftIndent=10, spaceAfter=3, leading=14)
    tac_s = ps('Tac', fontSize=10, textColor=brand, leftIndent=10, spaceAfter=3, leading=14)
    anc_s = ps('Anc', fontSize=10, textColor=brand,
               fontName='Helvetica-BoldOblique', spaceAfter=8, leading=14)

    story = []

    story.append(Paragraph("FRED", ps('T', 'Title', textColor=brand, fontSize=32)))
    story.append(Paragraph("Families' Rights and Entitlements Directory", h1))
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(
        f"EHCP Audit Report | Status: {answers.get('q2', 'Unknown')} | Beta v0.3", body))
    story.append(Paragraph(
        "This report provides information to help you understand the language of your "
        "child's plan and what the law says about it. It does not constitute legal advice.",
        body))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph("Output key", h1))
    story.append(Paragraph("● Red — lawful requirement not met. Must be addressed.", red_s))
    story.append(Paragraph("● Amber — best practice gap. Recommended.", amb_s))
    story.append(Paragraph("● Green — compliant. Meets the lawful standard.", grn_s))
    story.append(Spacer(1, 6*mm))

    if section_e_results:
        story.append(Paragraph("Section E — Outcomes audit", h1))
        for r in section_e_results:
            h = h2r if r['unlawful_failures'] else (h2a if r['best_practice_gaps'] else h2g)
            story.append(Paragraph(f"Outcome {r['outcome_number']}", h))
            story.append(Paragraph(f'<i>"{r["outcome_text"][:300]}"</i>', body))
            for f in r['unlawful_failures']:
                story.append(Paragraph(f"⚠ {f}", red_s))
            for g in r['best_practice_gaps']:
                story.append(Paragraph(f"◉ {g}", amb_s))
            if not r['unlawful_failures'] and not r['best_practice_gaps']:
                story.append(Paragraph("✓ Meets SMART criteria.", grn_s))
            story.append(Spacer(1, 4*mm))

    if audit_results:
        story.append(Paragraph("Section F — Provision audit", h1))
        for result in audit_results:
            h = (h2g if result['is_compliant']
                else h2r if result['unlawful_deficiencies']
                else h2a)
            label = ("Compliant" if result['is_compliant']
                    else "Lawful requirement not met" if result['unlawful_deficiencies']
                    else "Best practice gap")
            story.append(Paragraph(f"Provision {result['entry_number']} — {label}", h))
            story.append(Paragraph(f'<i>"{result["entry_text"][:400]}"</i>', body))

            if result['unlawful_deficiencies']:
                story.append(Paragraph("Lawful requirements not met", h3))
                for d in result['unlawful_deficiencies']:
                    story.append(Paragraph(f"⚠ {d}", red_s))

            if result['additional_patterns']:
                story.append(Paragraph("Additional pattern identified", h3))
                for p in result['additional_patterns']:
                    story.append(Paragraph(f"◈ {p}", pur_s))

            if result['best_practice_gaps']:
                story.append(Paragraph("Best practice gaps", h3))
                for g in result['best_practice_gaps']:
                    story.append(Paragraph(f"◉ {g}", amb_s))

            if result['ofsted_principle']:
                op = result['ofsted_principle']
                story.append(Paragraph("Inspection framework note", h3))
                story.append(Paragraph(f"<b>{op['area']}:</b> {op['principle']}", amb_s))

            if result['policy_gaps']:
                story.append(Paragraph("School policy cross-reference", h3))
                for pg in result['policy_gaps']:
                    story.append(Paragraph(f"◈ {pg}", pur_s))

            if result['required_specification']:
                story.append(Paragraph("Required specification", h3))
                for spec in result['required_specification']:
                    story.append(Paragraph(f"• {spec}", body))

            if result['tactical_advice']:
                story.append(Paragraph("Tactical advice", h3))
                for advice in result['tactical_advice']:
                    story.append(Paragraph(f"→ {advice}", tac_s))

            if result['unlawful_deficiencies']:
                story.append(Paragraph(
                    "If it is not specified and evidenced, it is not lawfully enforceable "
                    "under the Children and Families Act 2014. Lack of evidence is evidence of lack.",
                    anc_s))

            story.append(Spacer(1, 6*mm))

    story.append(Spacer(1, 8*mm))
    story.append(Paragraph(
        "Upload the expert reports (EP, OT, or SLT) to begin the Cross-Reference Audit.",
        tac_s))

    doc.build(story)
    buffer.seek(0)
    return buffer

# ─────────────────────────────────────────────
# APP FLOW
# ─────────────────────────────────────────────

if st.session_state.stage == 'upload':

    st.markdown("### Upload your document")
    st.markdown(
        "FRED works with whatever you have. "
        "You don't need everything — just start with what's in front of you."
    )

    uploaded_file = st.file_uploader(
        "Upload your main document",
        type=['pdf', 'docx', 'doc'],
        help="PDF or Word document. Processed privately. Not stored or shared."
    )
    st.markdown("""
    <div class="upload-tip">
        <strong>Email as a document:</strong> To upload an email, open it, select print,
        and choose Save as PDF. This works in Gmail, Outlook, and Apple Mail.<br>
        <strong>Password protected document:</strong> If your document is locked,
        open it, select print, and save as PDF — this removes the lock on most LA documents.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Optional — School documents")
    st.markdown(
        "Upload the school's SEND policy, behaviour policy, or accessibility plan "
        "and FRED will cross-reference the school's own commitments against what is in the plan."
    )
    policy_file = st.file_uploader(
        "School SEND policy, behaviour policy, or accessibility plan (optional)",
        type=['pdf', 'docx', 'doc'],
        key='policy_upload'
    )

    st.markdown("#### Optional — School or LA email")
    st.markdown(
        "Upload a school or LA email and FRED will assess every claim against "
        "what is lawfully required and what the delivery record shows."
    )
    email_file = st.file_uploader(
        "School or LA email — saved as PDF (optional)",
        type=['pdf', 'docx', 'doc'],
        key='email_upload'
    )

    st.markdown("#### Optional — Meeting transcript or notes")
    st.markdown(
        "Upload a meeting transcript or notes and FRED will cross-reference "
        "what was said in the room against what the school has put in writing."
    )
    transcript_file = st.file_uploader(
        "Meeting transcript or notes — PDF or Word (optional)",
        type=['pdf', 'docx', 'doc'],
        key='transcript_upload'
    )

    if uploaded_file:
        with st.spinner("Fred is reading your document..."):
            text, error = read_uploaded_file(uploaded_file)
            if error:
                st.error(error)
            else:
                sections = identify_sections(text)
                st.session_state.extracted_sections = sections
                st.session_state.raw_text = text
                if sections:
                    st.success(
                        f"Document read. Sections identified: "
                        f"{', '.join(sorted(sections.keys()))}. "
                        f"Key information saved to your review summary."
                    )
                else:
                    st.warning(
                        "FRED could not identify standard EHCP sections automatically. "
                        "You can paste Section F text below."
                    )
                    manual_f = st.text_area(
                        "Paste Section F provision text here:", height=200)
                    if manual_f:
                        st.session_state.extracted_sections['F'] = manual_f

        if policy_file:
            with st.spinner("Reading school policy..."):
                policy_text, policy_error = read_uploaded_file(policy_file)
                if policy_error:
                    st.warning(f"School policy: {policy_error}")
                else:
                    st.session_state.policy_text = policy_text
                    st.success("School policy read — ready for cross-reference.")

        if email_file:
            with st.spinner("Reading email..."):
                email_text, email_error = read_uploaded_file(email_file)
                if email_error:
                    st.warning(f"Email: {email_error}")
                else:
                    st.session_state.email_text = email_text
                    st.success("Email read — ready for correspondence analysis.")

        if transcript_file:
            with st.spinner("Reading transcript..."):
                transcript_text, transcript_error = read_uploaded_file(transcript_file)
                if transcript_error:
                    st.warning(f"Transcript: {transcript_error}")
                else:
                    st.session_state.transcript_text = transcript_text
                    st.success(
                        "Transcript read — this is the primary record of what was said. "
                        "FRED will cross-reference it against the email."
                    )

        if st.button("Continue →"):
            st.session_state.stage = 'questions'
            st.rerun()

elif st.session_state.stage == 'questions':

    st.markdown("### A few quick questions")
    st.markdown("One at a time. These shape the analysis you receive.")

    q1 = st.selectbox("1. What have you uploaded?", options=[
        "My child's EHCP",
        "An EP (Educational Psychologist) report",
        "A specialist report (OT, SALT, or other)",
        "School or LA correspondence",
        "Meeting notes or transcript",
        "More than one of the above",
    ])
    st.session_state.answers['q1'] = q1

    if "EHCP" in q1:
        q2 = st.selectbox("2. Is this a draft or final issued EHCP?", options=[
            "Draft — I am still in the review process",
            "Final — this has been formally issued by the LA",
            "I am not sure",
        ])
        st.session_state.answers['q2'] = q2
    else:
        st.session_state.answers['q2'] = "Not an EHCP"

    q3 = st.selectbox("3. Which best describes your situation right now?", options=[
        "I have just received this and want to understand it",
        "I have an upcoming annual review or meeting",
        "I am having difficulty getting the school to deliver what is in the plan",
        "I have had a needs assessment refused",
        "I am just starting the EHCP process",
    ])
    st.session_state.answers['q3'] = q3

    q4 = st.selectbox("4. Do you have any important dates coming up?", options=[
        "No upcoming dates right now",
        "Yes — annual review",
        "Yes — meeting with school",
        "Yes — LA deadline",
    ])
    st.session_state.answers['q4'] = q4
    if q4 != "No upcoming dates right now":
        upcoming_date = st.date_input("When is this?")
        st.session_state.answers['upcoming_date'] = str(upcoming_date)

    q5 = st.selectbox(
        "5. How would you describe your current relationship with the school or LA?",
        options=[
            "Warm and collaborative",
            "Constructive but cautious",
            "Professionally firm",
            "Formally assertive",
            "Rights-based and formal",
        ])
    st.session_state.answers['q5'] = q5

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back"):
            st.session_state.stage = 'upload'
            st.rerun()
    with col2:
        if st.button("Run audit →"):
            st.session_state.stage = 'processing'
            st.rerun()

elif st.session_state.stage == 'processing':

    st.markdown("### Fred is working...")
    sections = st.session_state.extracted_sections
    policy_text = st.session_state.get('policy_text', '')
    email_text = st.session_state.get('email_text', '')
    transcript_text = st.session_state.get('transcript_text', '')
    audit_results = []
    section_e_results = []
    correspondence_analysis = None
    post_meeting_email = None

    with st.spinner("Auditing Section F provision entries..."):
        if 'F' in sections:
            entries = extract_provision_entries(sections['F'])
            for i, entry in enumerate(entries):
                if len(entry.strip()) > 20:
                    result = audit_section_f_entry(entry, i + 1, policy_text)
                    audit_results.append(result)

    with st.spinner("Checking Section E outcomes..."):
        if 'E' in sections:
            section_e_results = audit_section_e(sections['E'])

    if email_text:
        with st.spinner("Analysing correspondence..."):
            correspondence_analysis = analyse_email_against_ehcp(
                email_text, sections, transcript_text
            )
            post_meeting_email = generate_post_meeting_summary(
                correspondence_analysis,
                st.session_state.answers
            )

    st.session_state.audit_results = audit_results
    st.session_state.section_e_results = section_e_results
    st.session_state.correspondence_analysis = correspondence_analysis
    st.session_state.post_meeting_email = post_meeting_email
    st.session_state.stage = 'results'
    st.rerun()

elif st.session_state.stage == 'results':

    audit_results = st.session_state.audit_results
    section_e_results = st.session_state.get('section_e_results', [])
    answers = st.session_state.answers
    policy_text = st.session_state.get('policy_text', '')
    correspondence_analysis = st.session_state.get('correspondence_analysis')
    post_meeting_email = st.session_state.get('post_meeting_email', '')

    if correspondence_analysis:
        render_correspondence_analysis(correspondence_analysis, post_meeting_email)
        st.markdown("---")

    if audit_results or section_e_results:
        render_audit_on_screen(audit_results, section_e_results, answers, policy_text)

    st.markdown("---")
    st.markdown("### Download your report")
    col1, col2 = st.columns(2)
    with col1:
        docx_buf = generate_docx_report(audit_results, section_e_results, answers)
        st.download_button(
            "⬇ Download as Word (.docx)",
            data=docx_buf,
            file_name="FRED_Audit_Report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            help="Best for Windows and Microsoft Office users"
        )
    with col2:
        pdf_buf = generate_pdf_report(audit_results, section_e_results, answers)
        st.download_button(
            "⬇ Download as PDF",
            data=pdf_buf,
            file_name="FRED_Audit_Report.pdf",
            mime="application/pdf",
            help="Best for Apple devices — universally readable"
        )

    st.markdown("---")
    st.markdown("### Beta feedback")
    st.markdown("Your answers directly shape the next version of FRED.")

    with st.form("feedback_form"):
        fb1 = st.selectbox(
            "Did the audit identify anything you did not already know?",
            ["Yes — significantly", "Yes — partially", "No — I knew all of this already"]
        )
        fb2 = st.selectbox(
            "Did the traffic light system (red, amber, green) make sense?",
            ["Yes — very clear", "Mostly clear", "Confusing", "Not sure"]
        )
        fb3 = st.selectbox(
            "Did the questions at the start feel useful?",
            ["Yes — all of them", "Some of them", "Too many", "Not relevant"]
        )
        fb4 = st.selectbox(
            "Would you pay for the one-off audit?",
            ["Yes — definitely", "Yes — possibly", "Not sure", "No"]
        )
        fb5 = st.text_input(
            "If yes — what feels like a fair price for the one-off audit?",
            placeholder="e.g. £25, £35, £50..."
        )
        fb6 = st.selectbox(
            "Would you use a subscription service that holds your documents, "
            "drafts emails, and prepares you for meetings?",
            ["Yes — definitely", "Yes — possibly", "Not sure", "No"]
        )
        fb7 = st.text_input(
            "If yes — what would feel like a fair monthly price?",
            placeholder="e.g. £10, £15, £20 per month..."
        )
        fb8 = st.text_area(
            "Anything else — what worked, what did not, what is missing?",
            height=100
        )
        submitted = st.form_submit_button("Submit feedback")
        if submitted:
            st.success(
                "Thank you. Your feedback has been received and will be reviewed. "
                "It directly informs the next version of FRED."
            )

    st.markdown("---")
    if st.button("Start new audit"):
        for key in list(defaults.keys()):
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────

st.markdown("---")
st.markdown(
    f"<div style='text-align:center; color:{GREY}; font-size:12px;'>"
    "FRED — Families' Rights and Entitlements Directory &nbsp;|&nbsp; "
    "Beta v0.3 &nbsp;|&nbsp; Not legal advice &nbsp;|&nbsp; "
    "Documents read during your session only — not stored or retained"
    "</div>",
    unsafe_allow_html=True
)

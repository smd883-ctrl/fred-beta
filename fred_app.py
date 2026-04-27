"""
FRED — Families' Rights and Entitlements Directory
Beta Version 0.1
Rules-based EHCP audit engine — closed deterministic system
"""

import streamlit as st
import fitz  # PyMuPDF
import re
import io
from docx import Document as DocxDocument
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import mm

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

st.markdown("""
<style>
    .main { max-width: 780px; margin: 0 auto; }
    .fred-header { 
        background: linear-gradient(135deg, #1B4F72, #2E86C1);
        color: white; padding: 32px 28px 24px 28px;
        border-radius: 10px; margin-bottom: 8px;
    }
    .fred-title { font-size: 52px; font-weight: 900; letter-spacing: 4px; margin: 0; }
    .fred-subtitle { font-size: 15px; opacity: 0.85; margin: 6px 0 0 0; }
    .beta-notice {
        background: #FEF9E7; border-left: 4px solid #F39C12;
        padding: 12px 16px; border-radius: 4px;
        font-size: 13px; color: #7D6608; margin-bottom: 20px;
    }
    .section-box {
        background: #F4F6F7; border-radius: 8px;
        padding: 20px 24px; margin: 16px 0;
    }
    .audit-header {
        background: #1B4F72; color: white;
        padding: 10px 16px; border-radius: 6px 6px 0 0;
        font-weight: 700; font-size: 14px; letter-spacing: 1px;
    }
    .audit-body {
        background: white; border: 1px solid #D5D8DC;
        border-top: none; padding: 16px; border-radius: 0 0 6px 6px;
        font-size: 14px; line-height: 1.7;
    }
    .flag-item {
        border-left: 3px solid #C0392B; padding: 8px 12px;
        margin: 8px 0; background: #FDEDEC; border-radius: 0 4px 4px 0;
        font-size: 13px;
    }
    .compliant-item {
        border-left: 3px solid #1E8449; padding: 8px 12px;
        margin: 8px 0; background: #EAFAF1; border-radius: 0 4px 4px 0;
        font-size: 13px;
    }
    .pattern-item {
        border-left: 3px solid #D35400; padding: 8px 12px;
        margin: 8px 0; background: #FEF5E7; border-radius: 0 4px 4px 0;
        font-size: 13px;
    }
    .tactical-item {
        border-left: 3px solid #1B4F72; padding: 8px 12px;
        margin: 8px 0; background: #EAF2FF; border-radius: 0 4px 4px 0;
        font-size: 13px;
    }
    .anchor-line {
        background: #1B4F72; color: white; padding: 12px 16px;
        border-radius: 6px; font-style: italic;
        font-size: 13px; margin-top: 16px; text-align: center;
    }
    .question-card {
        background: white; border: 1px solid #D5D8DC;
        border-radius: 8px; padding: 20px 24px; margin: 12px 0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .stButton > button {
        background: #1B4F72; color: white; border: none;
        padding: 10px 28px; border-radius: 6px; font-weight: 600;
        font-size: 15px; width: 100%;
    }
    .stButton > button:hover { background: #2E86C1; }
    hr { border: none; border-top: 1px solid #D5D8DC; margin: 20px 0; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

st.markdown("""
<div class="fred-header">
    <div class="fred-title">FRED</div>
    <div class="fred-subtitle">Families' Rights and Entitlements Directory</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="beta-notice">
    <strong>Beta Notice:</strong> FRED is currently in beta. Design and functionality are actively 
    being developed. Your feedback shapes the final product. This tool provides information to 
    help you understand your rights — it does not constitute legal advice.
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

if 'stage' not in st.session_state:
    st.session_state.stage = 'upload'
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'extracted_sections' not in st.session_state:
    st.session_state.extracted_sections = {}
if 'audit_results' not in st.session_state:
    st.session_state.audit_results = []

# ─────────────────────────────────────────────
# PDF EXTRACTION ENGINE
# ─────────────────────────────────────────────

def extract_text_from_pdf(uploaded_file):
    """Extract full text from uploaded PDF."""
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()
    return full_text

def identify_sections(text):
    """
    Identify EHCP sections from extracted text.
    Returns dict of section_label -> section_content.
    Handles varied formatting across different LA documents.
    """
    sections = {}

    # Section patterns — handles SECTION A, Section A, A:, A., PART A etc
    section_patterns = {
        'A': r'(?:SECTION\s+A|Section\s+A|PART\s+A)[:\s\-–—]*([^\n]*)\n(.*?)(?=(?:SECTION\s+[B-K]|Section\s+[B-K]|PART\s+[B-K])|$)',
        'B': r'(?:SECTION\s+B|Section\s+B|PART\s+B)[:\s\-–—]*([^\n]*)\n(.*?)(?=(?:SECTION\s+[C-K]|Section\s+[C-K]|PART\s+[C-K])|$)',
        'C': r'(?:SECTION\s+C|Section\s+C|PART\s+C)[:\s\-–—]*([^\n]*)\n(.*?)(?=(?:SECTION\s+[D-K]|Section\s+[D-K]|PART\s+[D-K])|$)',
        'D': r'(?:SECTION\s+D|Section\s+D|PART\s+D)[:\s\-–—]*([^\n]*)\n(.*?)(?=(?:SECTION\s+[E-K]|Section\s+[E-K]|PART\s+[E-K])|$)',
        'E': r'(?:SECTION\s+E|Section\s+E|PART\s+E)[:\s\-–—]*([^\n]*)\n(.*?)(?=(?:SECTION\s+[F-K]|Section\s+[F-K]|PART\s+[F-K])|$)',
        'F': r'(?:SECTION\s+F|Section\s+F|PART\s+F)[:\s\-–—]*([^\n]*)\n(.*?)(?=(?:SECTION\s+[G-K]|Section\s+[G-K]|PART\s+[G-K])|$)',
        'G': r'(?:SECTION\s+G|Section\s+G|PART\s+G)[:\s\-–—]*([^\n]*)\n(.*?)(?=(?:SECTION\s+[H-K]|Section\s+[H-K]|PART\s+[H-K])|$)',
        'H': r'(?:SECTION\s+H|Section\s+H|PART\s+H)[:\s\-–—]*([^\n]*)\n(.*?)(?=(?:SECTION\s+[I-K]|Section\s+[I-K]|PART\s+[I-K])|$)',
        'I': r'(?:SECTION\s+I|Section\s+I|PART\s+I)[:\s\-–—]*([^\n]*)\n(.*?)(?=(?:SECTION\s+[J-K]|Section\s+[J-K]|PART\s+[J-K])|$)',
        'J': r'(?:SECTION\s+J|Section\s+J|PART\s+J)[:\s\-–—]*([^\n]*)\n(.*?)(?=(?:SECTION\s+K|Section\s+K|PART\s+K)|$)',
        'K': r'(?:SECTION\s+K|Section\s+K|PART\s+K)[:\s\-–—]*([^\n]*)\n(.*?)$',
    }

    for section_key, pattern in section_patterns.items():
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(2).strip() if len(match.groups()) > 1 else match.group(1).strip()
            # Remove excessive whitespace and blank lines
            content = re.sub(r'\n{3,}', '\n\n', content)
            content = content.strip()
            if len(content) > 20:  # Filter out empty or near-empty sections
                sections[section_key] = content

    return sections

def extract_provision_entries(section_f_text):
    """
    Split Section F into individual provision entries for separate audit.
    Handles bullet points, numbered lists, and paragraph breaks.
    """
    entries = []

    # Try numbered list first (1. 2. 3.)
    numbered = re.split(r'\n\s*\d+[\.\)]\s+', section_f_text)
    if len(numbered) > 2:
        entries = [e.strip() for e in numbered if len(e.strip()) > 30]
        return entries

    # Try bullet points
    bulleted = re.split(r'\n\s*[\•\-\*]\s+', section_f_text)
    if len(bulleted) > 2:
        entries = [e.strip() for e in bulleted if len(e.strip()) > 30]
        return entries

    # Fall back to paragraph breaks
    paragraphs = re.split(r'\n{2,}', section_f_text)
    entries = [p.strip() for p in paragraphs if len(p.strip()) > 30]

    return entries if entries else [section_f_text]

# ─────────────────────────────────────────────
# RULES ENGINE — SECTION F AUDIT
# ─────────────────────────────────────────────

# Prohibited language patterns and their descriptions
PROHIBITED_LANGUAGE = {
    r'\bshould\b': ('should', 'creates no legal duty — it is a suggestion, not a commitment'),
    r'\bcould\b': ('could', 'creates no legal duty — possibility is not provision'),
    r'\bmay\b': ('may', 'means may not — no guaranteed entitlement is created'),
    r'\baccess to\b': ('access to', 'proximity to provision is not provision — no duty to deliver is created'),
    r'\bas needed\b': ('as needed', 'contingent on need being identified — who identifies it and how is unspecified'),
    r'\bwhere necessary\b': ('where necessary', 'entirely subjective — who determines necessity is unspecified'),
    r'\bas appropriate\b': ('as appropriate', 'discretionary — appropriate to whom and by what standard is unspecified'),
    r'\bregular\b': ('regular', 'unmeasurable — could mean daily, weekly, or termly without further specification'),
    r'\bencouraged\b': ('encouraged', 'creates no duty on any party — encouragement is not instruction'),
    r'\bmindful\b': ('mindful', 'an attitude, not a provision — no action is required under this wording'),
    r'\bcognisant\b': ('cognisant', 'awareness without obligation — no specified action or duty'),
    r'\bholistic\b': ('holistic', 'undefined — no named strategy, approach, or measurable outcome'),
    r'\bflexib': ('flexible/flexibility', 'unmeasurable — who decides what is flexible and when is unspecified'),
    r'\bopportunity\b': ('opportunity', 'possibility is not guaranteed provision'),
    r'\bit is expected\b': ('it is expected', 'expectation creates no legal duty on any party'),
    r'\bwould benefit\b': ('would benefit from', 'assessment language — must be converted to specified commitment in Section F'),
    r'\bit is recommended\b': ('it is recommended', 'recommendation language — must be converted to specified commitment in Section F'),
    r'\bat their.*discretion\b': ('at their discretion', 'professional discretion cannot override statutory entitlement'),
    r'\bwhere possible\b': ('where possible', 'conditional — possibility is not guaranteed provision'),
    r'\bas directed by\b': ('as directed by', 'places statutory provision under daily discretion of another party'),
}

# Universal provision indicators
UNIVERSAL_PROVISION_INDICATORS = [
    'high-quality teaching',
    'quality first teaching',
    'broad and balanced curriculum',
    'differentiated curriculum',
    'universal offer',
    'graduated response',
    'universal graduated',
    'scaffolding for tasks',
    'differentiated to meet',
    'quality teaching',
    'ordinarily available',
]

# Quantification checks
QUANTIFICATION_PATTERNS = {
    'frequency': r'\b(\d+\s*(?:times?|sessions?|hours?)\s*(?:per|a|each)\s*(?:week|day|term|month)|daily|weekly|fortnightly|monthly|termly|once|twice)\b',
    'duration': r'\b(\d+\s*(?:minutes?|hours?|mins?))\b',
    'deliverer': r'\b(therapist|psychologist|specialist|SENCO|teacher|LSA|TA|assistant|coordinator|practitioner|nurse|advisor|worker|OT|SALT|SLT)\b',
}

def check_quantification(text):
    """Check whether provision entry is quantified."""
    results = {}
    text_lower = text.lower()
    for check_type, pattern in QUANTIFICATION_PATTERNS.items():
        match = re.search(pattern, text_lower, re.IGNORECASE)
        results[check_type] = bool(match)
    return results

def check_prohibited_language(text):
    """Identify prohibited language patterns in text."""
    findings = []
    text_lower = text.lower()
    for pattern, (term, explanation) in PROHIBITED_LANGUAGE.items():
        if re.search(pattern, text_lower, re.IGNORECASE):
            findings.append((term, explanation))
    return findings

def check_universal_provision(text):
    """Check whether entry describes universal classroom practice."""
    text_lower = text.lower()
    found = []
    for indicator in UNIVERSAL_PROVISION_INDICATORS:
        if indicator in text_lower:
            found.append(indicator)
    return found

def check_recommendation_laundering(text):
    """Check for assessment language copied without conversion."""
    patterns = [
        r'\bwould benefit from\b',
        r'\bit is recommended\b',
        r'\bit is suggested\b',
        r'\bconsideration should be given\b',
        r'\bit is advised\b',
        r'\bmay benefit from\b',
    ]
    text_lower = text.lower()
    found = []
    for pattern in patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            match = re.search(pattern, text_lower, re.IGNORECASE)
            found.append(text_lower[max(0, match.start()-20):match.end()+40].strip())
    return found

def check_dilution_clause(text):
    """Check for shared/diluted provision wording."""
    patterns = [
        r'\bshared with other\b',
        r'\bmay be shared\b',
        r'\bas resources allow\b',
        r'\bsubject to availability\b',
        r'\bwhen staff are available\b',
        r'\bdepending on resources\b',
        r'\bas the school determines\b',
        r'\bat the school\'?s discretion\b',
    ]
    text_lower = text.lower()
    found = []
    for pattern in patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            found.append(pattern.replace(r'\b', '').replace('?', ''))
    return found

def check_compliant(text, quant_results):
    """
    Check whether a provision entry meets the full specification standard.
    Must have: must language, frequency, duration, named deliverer.
    """
    has_must = bool(re.search(r'\bmust\b', text, re.IGNORECASE))
    has_frequency = quant_results.get('frequency', False)
    has_duration = quant_results.get('duration', False)
    has_deliverer = quant_results.get('deliverer', False)
    prohibited = check_prohibited_language(text)

    return (has_must and has_frequency and has_duration
            and has_deliverer and len(prohibited) == 0)

def audit_section_f_entry(entry_text, entry_number):
    """
    Run full rules engine audit on a single Section F provision entry.
    Returns structured audit result dict.
    """
    result = {
        'entry_number': entry_number,
        'entry_text': entry_text,
        'prohibited_language': [],
        'quantification': {},
        'universal_provision': [],
        'recommendation_laundering': [],
        'dilution_clause': [],
        'is_compliant': False,
        'legal_deficiencies': [],
        'additional_patterns': [],
        'required_specification': [],
        'tactical_advice': [],
    }

    # Run all checks
    result['prohibited_language'] = check_prohibited_language(entry_text)
    result['quantification'] = check_quantification(entry_text)
    result['universal_provision'] = check_universal_provision(entry_text)
    result['recommendation_laundering'] = check_recommendation_laundering(entry_text)
    result['dilution_clause'] = check_dilution_clause(entry_text)
    result['is_compliant'] = check_compliant(entry_text, result['quantification'])

    # Build legal deficiencies
    for term, explanation in result['prohibited_language']:
        result['legal_deficiencies'].append(
            f'"{term}" — {explanation}. Unlawful/unenforceable.'
        )

    if not result['quantification']['frequency']:
        result['legal_deficiencies'].append(
            'No frequency specified — how often provision is delivered is not stated. '
            'Provision without frequency cannot be monitored or enforced.'
        )
    if not result['quantification']['duration']:
        result['legal_deficiencies'].append(
            'No duration specified — the length of each session or period of support is not stated. '
            'Without quantification this provision cannot be measured or challenged.'
        )
    if not result['quantification']['deliverer']:
        result['legal_deficiencies'].append(
            'No named deliverer — who provides this provision, at what qualification or training level, '
            'is not specified. A duty without a named responsible party is unenforceable.'
        )

    # Additional patterns
    if result['universal_provision']:
        result['additional_patterns'].append(
            'Universal provision identified — this entry describes provision the school is already '
            'required to offer all pupils under its universal obligation. Its presence in Section F '
            'gives the appearance of specialist provision without creating any additional legal entitlement.'
        )

    if result['recommendation_laundering']:
        result['additional_patterns'].append(
            'Recommendation laundering identified — assessment or report language has been copied '
            'into Section F without being converted into a specified legal commitment. '
            'Referencing the existence of advice without acting on it creates no enforceable duty.'
        )

    if result['dilution_clause']:
        result['additional_patterns'].append(
            'Dilution clause identified — wording allows this provision to be shared, reduced, '
            'or made conditional on school resources or availability. '
            'An individual statutory entitlement cannot be diluted at the school\'s discretion.'
        )

    # Required specification
    if not result['is_compliant']:
        if not result['quantification']['frequency']:
            result['required_specification'].append(
                'Frequency must be stated — number of sessions per week or per term, specified plainly'
            )
        if not result['quantification']['duration']:
            result['required_specification'].append(
                'Duration must be stated — length of each session in minutes or hours'
            )
        if not result['quantification']['deliverer']:
            result['required_specification'].append(
                'Deliverer must be named — role, qualification level, and relevant training specified'
            )
        if result['universal_provision']:
            result['required_specification'].append(
                'Entry must describe provision additional to the school\'s universal offer — '
                'what does this child receive that is not available to every other pupil'
            )
        if result['recommendation_laundering']:
            result['required_specification'].append(
                'Professional recommendations must be reproduced in full as specified provision — '
                'not referenced as existing advice'
            )
        if result['dilution_clause']:
            result['required_specification'].append(
                'Shared or conditional wording must be removed — provision must be specified '
                'as an individual guaranteed entitlement with named hours and named deliverer'
            )
        result['required_specification'].append(
            'Mandatory logging — all provision must be recorded in a dated delivery log '
            'showing date, duration, who delivered, and any relevant observations'
        )

    # Tactical advice — always generated
    result['tactical_advice'].append(
        'Request the Physical Delivery Log for this provision. Dated entries must show '
        'each session — date, duration, who delivered, and format. '
        'If no log exists there is no evidence this provision has been delivered.'
    )

    if not result['is_compliant']:
        result['tactical_advice'].append(
            'At the next annual review, this entry must be rewritten to full specification standard. '
            'Use the Required Specification above as the basis for what must be included.'
        )

    if result['dilution_clause']:
        result['tactical_advice'].append(
            'Request written confirmation of how many other pupils share this provision and '
            'what proportion of the named support this child actually receives.'
        )

    return result

# ─────────────────────────────────────────────
# SECTION E AUDIT — SMART OUTCOMES CHECK
# ─────────────────────────────────────────────

def audit_section_e(section_e_text):
    """Check Section E outcomes against SMART criteria."""
    results = []

    # Split into individual outcomes
    outcomes = re.split(r'\n\s*[\•\-\*\d][\.\)]?\s+', section_e_text)
    outcomes = [o.strip() for o in outcomes if len(o.strip()) > 20]

    if not outcomes:
        outcomes = [p.strip() for p in section_e_text.split('\n') if len(p.strip()) > 20]

    for i, outcome in enumerate(outcomes):
        outcome_result = {
            'outcome_number': i + 1,
            'outcome_text': outcome,
            'smart_failures': [],
        }

        outcome_lower = outcome.lower()

        # Check for baseline
        if not re.search(r'\b(currently|baseline|starting point|at present|now|from a starting point)\b',
                         outcome_lower):
            outcome_result['smart_failures'].append(
                'No baseline stated — without a starting point progress cannot be measured'
            )

        # Check for measurable indicator
        if not re.search(r'\b(\d+|percentage|score|level|times|sessions|independently|consistently|'
                         r'measured by|assessed by|recorded)\b', outcome_lower):
            outcome_result['smart_failures'].append(
                'No measurable indicator — success cannot be objectively assessed at review'
            )

        # Check for timeframe
        if not re.search(r'\b(by|within|term|year|month|weeks?|annual review|end of)\b',
                         outcome_lower):
            outcome_result['smart_failures'].append(
                'No timeframe — when this outcome should be achieved is not stated'
            )

        # Check for vague language
        vague_terms = ['improve', 'develop', 'increase', 'better', 'support', 'help']
        for term in vague_terms:
            if term in outcome_lower and len(outcome_result['smart_failures']) > 0:
                outcome_result['smart_failures'].append(
                    f'Vague language — "{term}" is not measurable without a specified baseline and target'
                )
                break

        results.append(outcome_result)

    return results

# ─────────────────────────────────────────────
# OUTPUT RENDERING
# ─────────────────────────────────────────────

def render_audit_on_screen(audit_results, section_e_results, answers):
    """Render full audit output on screen."""

    st.markdown("---")
    st.markdown("## FRED Audit Report")

    # Document context
    doc_type = answers.get('q1', 'EHCP')
    ehcp_status = answers.get('q2', 'Unknown')
    process_stage = answers.get('q3', 'Not specified')

    st.markdown(f"""
    <div class="section-box">
        <strong>Document:</strong> {doc_type} &nbsp;|&nbsp;
        <strong>Status:</strong> {ehcp_status} &nbsp;|&nbsp;
        <strong>Stage:</strong> {process_stage}
    </div>
    """, unsafe_allow_html=True)

    # Important pathway notice for final EHCPs
    if 'final' in ehcp_status.lower():
        st.warning(
            "**Final EHCP pathway active.** This is a final issued plan. "
            "FRED does not advise changes to a final EHCP. "
            "All guidance below references your rights and the school's duties. "
            "Use this audit to prepare for your annual review."
        )

    # ── SECTION E RESULTS ──
    if section_e_results:
        st.markdown("### SECTION E — OUTCOMES AUDIT")
        st.markdown("*Outcomes are assessed against SMART criteria: Specific, Measurable, Achievable, Relevant, Time-bound.*")

        all_e_compliant = all(len(r['smart_failures']) == 0 for r in section_e_results)

        if all_e_compliant:
            st.success("All outcomes meet SMART criteria.")
        else:
            for r in section_e_results:
                if r['smart_failures']:
                    st.markdown(f"""
                    <div class="audit-header">OUTCOME {r['outcome_number']}</div>
                    <div class="audit-body">
                        <em>"{r['outcome_text'][:200]}..."</em><br><br>
                        {''.join(f'<div class="flag-item">⚠ {f}</div>' for f in r['smart_failures'])}
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")

    # ── SECTION F RESULTS ──
    if audit_results:
        st.markdown("### SECTION F — PROVISION AUDIT")

        compliant_count = sum(1 for r in audit_results if r['is_compliant'])
        total_count = len(audit_results)

        if compliant_count == total_count:
            st.success(f"All {total_count} provision entries meet the specification standard.")
        else:
            st.error(
                f"{total_count - compliant_count} of {total_count} provision "
                f"entries contain legal deficiencies."
            )

        for result in audit_results:
            if result['is_compliant']:
                st.markdown(f"""
                <div class="audit-header">PROVISION {result['entry_number']} — COMPLIANT</div>
                <div class="audit-body">
                    <div class="compliant-item">
                        ✓ This entry meets the specification standard. 
                        It may be used as the benchmark against which all non-compliant 
                        entries in this plan are measured at annual review.
                    </div>
                    <em>"{result['entry_text'][:300]}"</em>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="audit-header">
                    AUDIT SUMMARY: PROVISION ENTRY {result['entry_number']}
                </div>
                <div class="audit-body">
                    <em>"{result['entry_text'][:300]}{'...' if len(result['entry_text']) > 300 else ''}"</em>
                    <br><br>
                """, unsafe_allow_html=True)

                if result['legal_deficiencies']:
                    st.markdown("**LEGAL DEFICIENCIES**")
                    for deficiency in result['legal_deficiencies']:
                        st.markdown(f"""
                        <div class="flag-item">⚠ {deficiency}</div>
                        """, unsafe_allow_html=True)

                if result['additional_patterns']:
                    st.markdown("**ADDITIONAL PATTERN IDENTIFIED**")
                    for pattern in result['additional_patterns']:
                        st.markdown(f"""
                        <div class="pattern-item">◈ {pattern}</div>
                        """, unsafe_allow_html=True)

                if result['required_specification']:
                    st.markdown("**REQUIRED SPECIFICATION**")
                    for spec in result['required_specification']:
                        st.markdown(f"- {spec}")

                if result['tactical_advice']:
                    st.markdown("**TACTICAL ADVICE**")
                    for advice in result['tactical_advice']:
                        st.markdown(f"""
                        <div class="tactical-item">→ {advice}</div>
                        """, unsafe_allow_html=True)

                st.markdown("""
                <div class="anchor-line">
                    If it is not specified and evidenced, it is not enforceable 
                    under the Children and Families Act 2014.
                </div>
                """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

        # Cross reference prompt
        st.info(
            "**Next Step:** Upload the expert reports (EP, OT, or SLT) "
            "to begin the Cross-Reference Audit."
        )

def generate_docx_report(audit_results, section_e_results, answers):
    """Generate downloadable Word document report."""
    doc = DocxDocument()

    # Styles
    def add_heading(text, level=1):
        h = doc.add_heading(text, level=level)
        h.runs[0].font.color.rgb = RGBColor(0x1B, 0x4F, 0x72)
        return h

    def add_body(text):
        p = doc.add_paragraph(text)
        p.runs[0].font.size = Pt(11) if p.runs else None
        return p

    def add_flag(text, flag_type='deficiency'):
        p = doc.add_paragraph()
        colours = {
            'deficiency': RGBColor(0xC0, 0x39, 0x2B),
            'pattern': RGBColor(0xD3, 0x54, 0x00),
            'tactical': RGBColor(0x1B, 0x4F, 0x72),
            'compliant': RGBColor(0x1E, 0x84, 0x49),
        }
        run = p.add_run(f"{'⚠' if flag_type == 'deficiency' else '→'} {text}")
        run.font.color.rgb = colours.get(flag_type, RGBColor(0, 0, 0))
        run.font.size = Pt(10)
        return p

    # Cover
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("FRED")
    run.font.size = Pt(36)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x1B, 0x4F, 0x72)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run2 = subtitle.add_run("Families' Rights and Entitlements Directory")
    run2.font.size = Pt(14)
    run2.font.color.rgb = RGBColor(0x2E, 0x86, 0xC1)

    doc.add_paragraph()
    doc.add_paragraph(
        "EHCP AUDIT REPORT\n"
        f"Document: {answers.get('q1', 'EHCP')} | "
        f"Status: {answers.get('q2', 'Unknown')} | "
        f"Stage: {answers.get('q3', 'Not specified')}"
    )

    doc.add_paragraph(
        "Beta Notice: FRED is currently in beta. This report provides information "
        "to help you understand your rights. It does not constitute legal advice."
    )

    doc.add_page_break()

    # Section E
    if section_e_results:
        add_heading("SECTION E — OUTCOMES AUDIT")
        doc.add_paragraph(
            "Outcomes are assessed against SMART criteria: "
            "Specific, Measurable, Achievable, Relevant, Time-bound."
        )

        for r in section_e_results:
            add_heading(f"Outcome {r['outcome_number']}", level=2)
            doc.add_paragraph(f'"{r["outcome_text"]}"').italic = True

            if not r['smart_failures']:
                add_flag("This outcome meets SMART criteria.", 'compliant')
            else:
                for failure in r['smart_failures']:
                    add_flag(failure, 'deficiency')

        doc.add_page_break()

    # Section F
    if audit_results:
        add_heading("SECTION F — PROVISION AUDIT")

        for result in audit_results:
            if result['is_compliant']:
                add_heading(
                    f"Provision {result['entry_number']} — COMPLIANT", level=2
                )
                add_flag(
                    "This entry meets the specification standard and may be used "
                    "as the benchmark against which all non-compliant entries are measured.",
                    'compliant'
                )
                doc.add_paragraph(f'"{result["entry_text"]}"').italic = True
            else:
                add_heading(
                    f"AUDIT SUMMARY: PROVISION ENTRY {result['entry_number']}", level=2
                )
                p = doc.add_paragraph(f'"{result["entry_text"][:400]}"')
                p.italic = True

                if result['legal_deficiencies']:
                    add_heading("LEGAL DEFICIENCIES", level=3)
                    for d in result['legal_deficiencies']:
                        add_flag(d, 'deficiency')

                if result['additional_patterns']:
                    add_heading("ADDITIONAL PATTERN IDENTIFIED", level=3)
                    for pattern in result['additional_patterns']:
                        add_flag(pattern, 'pattern')

                if result['required_specification']:
                    add_heading("REQUIRED SPECIFICATION", level=3)
                    for spec in result['required_specification']:
                        doc.add_paragraph(spec, style='List Bullet')

                if result['tactical_advice']:
                    add_heading("TACTICAL ADVICE", level=3)
                    for advice in result['tactical_advice']:
                        add_flag(advice, 'tactical')

                doc.add_paragraph(
                    "If it is not specified and evidenced, it is not enforceable "
                    "under the Children and Families Act 2014."
                ).bold = True

            doc.add_paragraph()

    # Save to bytes
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def generate_pdf_report(audit_results, section_e_results, answers):
    """Generate downloadable PDF report — Apple compatible."""
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm
    )

    styles = getSampleStyleSheet()
    brand_blue = HexColor('#1B4F72')
    brand_mid = HexColor('#2E86C1')
    red = HexColor('#C0392B')
    orange = HexColor('#D35400')
    green = HexColor('#1E8449')

    title_style = ParagraphStyle('Title', parent=styles['Title'],
                                  textColor=brand_blue, fontSize=32, spaceAfter=8)
    h1_style = ParagraphStyle('H1', parent=styles['Heading1'],
                               textColor=brand_blue, fontSize=16, spaceAfter=6)
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'],
                               textColor=brand_mid, fontSize=13, spaceAfter=4)
    h3_style = ParagraphStyle('H3', parent=styles['Heading3'],
                               fontSize=11, spaceAfter=4)
    body_style = ParagraphStyle('Body', parent=styles['Normal'],
                                 fontSize=10, spaceAfter=4, leading=15)
    flag_style = ParagraphStyle('Flag', parent=styles['Normal'],
                                 fontSize=10, textColor=red,
                                 leftIndent=12, spaceAfter=4, leading=14)
    pattern_style = ParagraphStyle('Pattern', parent=styles['Normal'],
                                    fontSize=10, textColor=orange,
                                    leftIndent=12, spaceAfter=4, leading=14)
    tactical_style = ParagraphStyle('Tactical', parent=styles['Normal'],
                                     fontSize=10, textColor=brand_blue,
                                     leftIndent=12, spaceAfter=4, leading=14)
    compliant_style = ParagraphStyle('Compliant', parent=styles['Normal'],
                                      fontSize=10, textColor=green,
                                      leftIndent=12, spaceAfter=4, leading=14)
    anchor_style = ParagraphStyle('Anchor', parent=styles['Normal'],
                                   fontSize=10, textColor=brand_blue,
                                   fontName='Helvetica-BoldOblique',
                                   spaceAfter=8, leading=14)

    story = []

    # Cover
    story.append(Paragraph("FRED", title_style))
    story.append(Paragraph("Families' Rights and Entitlements Directory", h2_style))
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph(
        f"EHCP Audit Report &nbsp;|&nbsp; "
        f"Document: {answers.get('q1', 'EHCP')} &nbsp;|&nbsp; "
        f"Status: {answers.get('q2', 'Unknown')}",
        body_style
    ))
    story.append(Paragraph(
        "Beta Notice: FRED is currently in beta. This report provides information "
        "to help you understand your rights. It does not constitute legal advice.",
        body_style
    ))
    story.append(Spacer(1, 10*mm))

    # Section E
    if section_e_results:
        story.append(Paragraph("SECTION E — OUTCOMES AUDIT", h1_style))
        story.append(Paragraph(
            "Outcomes assessed against SMART criteria.", body_style
        ))
        story.append(Spacer(1, 4*mm))

        for r in section_e_results:
            story.append(Paragraph(f"Outcome {r['outcome_number']}", h2_style))
            story.append(Paragraph(f'<i>"{r["outcome_text"][:300]}"</i>', body_style))
            if not r['smart_failures']:
                story.append(Paragraph("✓ Meets SMART criteria.", compliant_style))
            else:
                for failure in r['smart_failures']:
                    story.append(Paragraph(f"⚠ {failure}", flag_style))
            story.append(Spacer(1, 4*mm))

    # Section F
    if audit_results:
        story.append(Paragraph("SECTION F — PROVISION AUDIT", h1_style))
        story.append(Spacer(1, 4*mm))

        for result in audit_results:
            if result['is_compliant']:
                story.append(Paragraph(
                    f"Provision {result['entry_number']} — COMPLIANT", h2_style
                ))
                story.append(Paragraph(
                    "✓ This entry meets the specification standard.", compliant_style
                ))
            else:
                story.append(Paragraph(
                    f"AUDIT SUMMARY: PROVISION ENTRY {result['entry_number']}", h2_style
                ))
                story.append(Paragraph(
                    f'<i>"{result["entry_text"][:400]}"</i>', body_style
                ))
                story.append(Spacer(1, 3*mm))

                if result['legal_deficiencies']:
                    story.append(Paragraph("LEGAL DEFICIENCIES", h3_style))
                    for d in result['legal_deficiencies']:
                        story.append(Paragraph(f"⚠ {d}", flag_style))

                if result['additional_patterns']:
                    story.append(Paragraph("ADDITIONAL PATTERN IDENTIFIED", h3_style))
                    for p in result['additional_patterns']:
                        story.append(Paragraph(f"◈ {p}", pattern_style))

                if result['required_specification']:
                    story.append(Paragraph("REQUIRED SPECIFICATION", h3_style))
                    for spec in result['required_specification']:
                        story.append(Paragraph(f"• {spec}", body_style))

                if result['tactical_advice']:
                    story.append(Paragraph("TACTICAL ADVICE", h3_style))
                    for advice in result['tactical_advice']:
                        story.append(Paragraph(f"→ {advice}", tactical_style))

                story.append(Paragraph(
                    "If it is not specified and evidenced, it is not enforceable "
                    "under the Children and Families Act 2014.",
                    anchor_style
                ))

            story.append(Spacer(1, 6*mm))

    story.append(Spacer(1, 8*mm))
    story.append(Paragraph(
        "Upload the expert reports (EP, OT, or SLT) to begin the Cross-Reference Audit.",
        tactical_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer

# ─────────────────────────────────────────────
# MAIN APP FLOW
# ─────────────────────────────────────────────

# ── STAGE: UPLOAD ──
if st.session_state.stage == 'upload':

    st.markdown("### Upload Your Document")
    st.markdown(
        "Upload your EHCP, EP report, specialist report, or correspondence. "
        "FRED works with whatever you have — you do not need everything."
    )

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Your document is processed privately and not stored or shared."
    )

    if uploaded_file:
        with st.spinner("Fred is reading your document..."):
            raw_text = extract_text_from_pdf(uploaded_file)
            sections = identify_sections(raw_text)
            st.session_state.extracted_sections = sections
            st.session_state.raw_text = raw_text

        if sections:
            st.success(
                f"Document read successfully. "
                f"Sections identified: {', '.join(sorted(sections.keys()))}"
            )
        else:
            st.warning(
                "FRED could not identify standard EHCP sections in this document. "
                "It may be formatted differently. "
                "You can still proceed — paste your Section F text below."
            )
            manual_f = st.text_area(
                "Paste Section F provision text here:",
                height=200
            )
            if manual_f:
                st.session_state.extracted_sections['F'] = manual_f

        if st.button("Continue →"):
            st.session_state.stage = 'questions'
            st.rerun()

# ── STAGE: QUESTIONS ──
elif st.session_state.stage == 'questions':

    st.markdown("### A Few Quick Questions")
    st.markdown("These help FRED give you the right analysis for your situation.")

    with st.container():
        st.markdown('<div class="question-card">', unsafe_allow_html=True)

        # Q1 — Document type
        q1 = st.selectbox(
            "1. What have you uploaded?",
            options=[
                "My child's EHCP",
                "An EP (Educational Psychologist) report",
                "A specialist report (OT, SALT, or other)",
                "School or LA correspondence",
                "Meeting notes or transcript",
                "More than one of the above",
            ]
        )
        st.session_state.answers['q1'] = q1

        # Q2 — EHCP status (shown only if EHCP uploaded)
        if "EHCP" in q1:
            q2 = st.selectbox(
                "2. Is this a draft or final issued EHCP?",
                options=[
                    "Draft — I am still in the review process",
                    "Final — this has been formally issued",
                    "I am not sure",
                ]
            )
            st.session_state.answers['q2'] = q2
        else:
            st.session_state.answers['q2'] = "Not an EHCP"

        # Q3 — Process stage
        q3 = st.selectbox(
            "3. Which best describes your situation right now?",
            options=[
                "I have just received this and want to understand it",
                "I have an upcoming annual review or meeting",
                "I am having difficulty getting the school to deliver what is in the plan",
                "I have had a needs assessment refused",
                "I am just starting the EHCP process",
            ]
        )
        st.session_state.answers['q3'] = q3

        # Q4 — Upcoming dates
        q4 = st.selectbox(
            "4. Do you have any important dates coming up?",
            options=[
                "No upcoming dates right now",
                "Yes — annual review",
                "Yes — meeting with school",
                "Yes — LA deadline",
            ]
        )
        st.session_state.answers['q4'] = q4

        if q4 != "No upcoming dates right now":
            upcoming_date = st.date_input("When is this?")
            st.session_state.answers['upcoming_date'] = str(upcoming_date)

        # Q5 — Relationship tone
        q5 = st.selectbox(
            "5. How would you describe your current relationship with the school or LA?",
            options=[
                "Warm and collaborative",
                "Constructive but cautious",
                "Professionally firm",
                "Formally assertive",
                "Rights-based and formal",
            ]
        )
        st.session_state.answers['q5'] = q5

        st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back"):
            st.session_state.stage = 'upload'
            st.rerun()
    with col2:
        if st.button("Run Audit →"):
            st.session_state.stage = 'processing'
            st.rerun()

# ── STAGE: PROCESSING ──
elif st.session_state.stage == 'processing':

    st.markdown("### Fred is working...")

    audit_results = []
    section_e_results = []

    sections = st.session_state.extracted_sections

    with st.spinner("Auditing Section F provision entries..."):
        if 'F' in sections:
            entries = extract_provision_entries(sections['F'])
            for i, entry in enumerate(entries):
                if len(entry.strip()) > 20:
                    result = audit_section_f_entry(entry, i + 1)
                    audit_results.append(result)

    with st.spinner("Checking Section E outcomes against SMART criteria..."):
        if 'E' in sections:
            section_e_results = audit_section_e(sections['E'])

    st.session_state.audit_results = audit_results
    st.session_state.section_e_results = section_e_results
    st.session_state.stage = 'results'
    st.rerun()

# ── STAGE: RESULTS ──
elif st.session_state.stage == 'results':

    audit_results = st.session_state.audit_results
    section_e_results = st.session_state.get('section_e_results', [])
    answers = st.session_state.answers

    # Render on screen
    render_audit_on_screen(audit_results, section_e_results, answers)

    # Download options
    st.markdown("---")
    st.markdown("### Download Your Report")

    col1, col2 = st.columns(2)

    with col1:
        docx_buffer = generate_docx_report(audit_results, section_e_results, answers)
        st.download_button(
            label="⬇ Download as Word (.docx)",
            data=docx_buffer,
            file_name="FRED_Audit_Report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            help="Best for Windows and Microsoft Office users"
        )

    with col2:
        pdf_buffer = generate_pdf_report(audit_results, section_e_results, answers)
        st.download_button(
            label="⬇ Download as PDF",
            data=pdf_buffer,
            file_name="FRED_Audit_Report.pdf",
            mime="application/pdf",
            help="Best for Apple devices and universal reading"
        )

    # Feedback section
    st.markdown("---")
    st.markdown("### Beta Feedback")
    st.markdown(
        "Your feedback directly shapes FRED. "
        "Please take two minutes to answer these questions."
    )

    with st.form("feedback_form"):
        fb1 = st.selectbox(
            "Did the audit identify anything you did not already know?",
            ["Yes — significantly", "Yes — partially", "No — I knew all of this already"]
        )
        fb2 = st.selectbox(
            "Did the questions at the start feel useful?",
            ["Yes — all of them", "Some of them", "No — too many", "No — not relevant"]
        )
        fb3 = st.selectbox(
            "Would you pay for this service?",
            ["Yes — definitely", "Yes — possibly", "Not sure", "No"]
        )
        fb4 = st.text_input(
            "If you would pay — what feels like a fair price for the one-off audit?",
            placeholder="e.g. £25, £35, £50..."
        )
        fb5 = st.text_area(
            "Anything else — what worked, what didn't, what's missing?",
            height=100
        )
        submitted = st.form_submit_button("Submit Feedback")

        if submitted:
            st.success(
                "Thank you. Your feedback has been received and will be reviewed. "
                "It directly informs the next version of FRED."
            )

    # Restart
    st.markdown("---")
    if st.button("Start New Audit"):
        for key in ['stage', 'answers', 'extracted_sections',
                    'audit_results', 'section_e_results', 'raw_text']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────

st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#717D7E; font-size:12px;'>"
    "FRED — Families' Rights and Entitlements Directory &nbsp;|&nbsp; Beta v0.1 &nbsp;|&nbsp; "
    "Not legal advice &nbsp;|&nbsp; All documents processed privately"
    "</div>",
    unsafe_allow_html=True
)

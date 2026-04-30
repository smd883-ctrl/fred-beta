"""
FRED — Families' Rights and Entitlements Directory
Beta Version 0.6

New in v0.6:
- Handshake model: one-off report is clean, subscription adds correspondence intelligence
- Correspondence upload: last two emails active, history as background context
- Three finding briefing format
- Intent detection: case building vs collaborative vs mixed
- Vacuum detection: statements implying undocumented history
- Hold option alongside draft and brief me
- APDR continuous description flagged specifically
- Professional dignity flag at escalation points
- Email output options: Word, bullets, or as drafted
- What-if scenario library: first set from real thread analysis
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
# CONSTANTS
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
TEAL = "#148F77"
TEAL_BG = "#E8F8F5"

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="FRED — Families' Rights and Entitlements Directory",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────

st.markdown(f"""
<style>
*{{box-sizing:border-box;}}
.main{{max-width:780px;margin:0 auto;}}
.fred-nav{{display:flex;justify-content:space-between;align-items:center;
    padding:14px 0;border-bottom:0.5px solid #D5D8DC;}}
.fred-nav-logo{{font-size:15px;font-weight:500;letter-spacing:1px;color:{GREY};}}
.fred-nav-link{{font-size:13px;color:{GREY};cursor:pointer;}}
.fred-nav-links{{display:flex;gap:24px;}}
.fred-beta{{background:#FEF9E7;border-top:0.5px solid #F9CA24;
    border-bottom:0.5px solid #F9CA24;padding:9px 0;text-align:center;
    font-size:12px;color:#7D6608;}}
.fred-hero{{padding:52px 0 44px;text-align:center;}}
.fred-big{{font-size:80px;font-weight:500;letter-spacing:8px;
    color:{BRAND_BLUE};line-height:1;margin-bottom:6px;}}
.fred-full{{font-size:12px;letter-spacing:1.5px;color:{GREY};
    margin-bottom:24px;text-transform:uppercase;}}
.fred-hero-title{{font-size:26px;font-weight:500;color:#1A252F;
    line-height:1.25;margin-bottom:12px;}}
.fred-hero-title span{{color:{BRAND_BLUE};}}
.fred-hero-origin{{font-size:13px;color:{GREY};font-style:italic;margin-bottom:16px;}}
.fred-hero-sub{{font-size:14px;color:#2C3E50;line-height:1.75;
    max-width:500px;margin:0 auto 12px;}}
.fred-hero-flex{{font-size:14px;color:#2C3E50;line-height:1.6;
    max-width:460px;margin:0 auto 28px;}}
.fred-hero-flex span{{color:{BRAND_BLUE};font-weight:500;}}
.fred-hero-cta{{display:flex;flex-direction:column;align-items:center;gap:5px;}}
.fred-btn-reassure{{font-size:13px;color:{GREY};font-style:italic;margin:3px 0 6px;}}
.fred-btn-pricing{{font-size:13px;color:{GREY};}}
.fred-btn-pricing span{{color:{BRAND_BLUE};text-decoration:underline;cursor:pointer;}}
.fred-divider{{border:none;border-top:0.5px solid #D5D8DC;margin:0;}}
.fred-section{{padding:44px 0;}}
.fred-sec-label{{font-size:11px;letter-spacing:2px;text-transform:uppercase;
    color:{GREY};margin-bottom:8px;text-align:center;}}
.fred-sec-title{{font-size:20px;font-weight:500;color:#1A252F;
    margin-bottom:16px;text-align:center;}}
.fred-sec-sub{{font-size:14px;color:#2C3E50;line-height:1.7;
    margin-bottom:20px;text-align:center;max-width:480px;
    margin-left:auto;margin-right:auto;}}
.fred-bullets{{list-style:none;display:flex;flex-direction:column;
    align-items:center;gap:10px;margin-bottom:24px;padding:0;}}
.fred-bullets li{{font-size:14px;color:#2C3E50;line-height:1.65;
    display:flex;align-items:flex-start;gap:9px;max-width:460px;}}
.fred-bdot{{width:6px;height:6px;min-width:6px;border-radius:50%;
    background:{BRAND_BLUE};margin-top:7px;}}
.fred-sub-bullet{{color:{BRAND_BLUE};font-weight:500;}}
.fred-upload-wrap{{display:flex;flex-direction:column;align-items:center;gap:8px;}}
.fred-upload-note{{font-size:11px;color:{GREY};font-style:italic;}}
.fred-traffic-legend{{background:#F4F6F7;border-radius:10px;
    padding:18px 20px;margin-bottom:16px;}}
.fred-traffic-title{{font-size:13px;font-weight:500;color:#1A252F;margin-bottom:12px;}}
.fred-trow{{display:flex;gap:11px;align-items:flex-start;margin-bottom:10px;}}
.fred-trow:last-child{{margin-bottom:0;}}
.fred-tdot{{width:13px;height:13px;min-width:13px;border-radius:50%;margin-top:3px;}}
.tdot-red{{background:{RED};}}
.tdot-amber{{background:{AMBER};}}
.tdot-green{{background:{GREEN};}}
.fred-ttext{{font-size:13px;color:#2C3E50;line-height:1.55;}}
.fred-ttext strong{{color:#1A252F;font-weight:500;}}
.fred-pricing-grid{{display:grid;
    grid-template-columns:repeat(auto-fit,minmax(190px,1fr));
    gap:14px;margin-top:4px;}}
.fred-price-card{{background:white;border:0.5px solid #D5D8DC;
    border-radius:12px;padding:20px;display:flex;flex-direction:column;}}
.fred-price-card.featured{{border:2px solid {BRAND_BLUE};}}
.fred-price-badge{{font-size:11px;font-weight:500;background:{BLUE_BG};
    color:#0C447C;padding:3px 10px;border-radius:6px;
    display:inline-block;margin-bottom:12px;}}
.fred-price-name{{font-size:14px;font-weight:500;color:#1A252F;margin-bottom:3px;}}
.fred-price-amount{{font-size:28px;font-weight:500;color:{BRAND_BLUE};margin-bottom:2px;}}
.fred-price-period{{font-size:11px;color:{GREY};margin-bottom:6px;line-height:1.5;}}
.fred-price-first{{font-size:11px;color:#2C3E50;background:#F4F6F7;
    border-radius:6px;padding:6px 10px;margin-bottom:12px;line-height:1.5;}}
.fred-price-features{{list-style:none;padding:0;display:flex;flex-direction:column;
    gap:7px;margin-bottom:18px;flex:1;}}
.fred-price-features li{{font-size:12px;color:#2C3E50;display:flex;gap:7px;
    align-items:flex-start;line-height:1.4;}}
.fred-price-features li::before{{content:"";width:5px;height:5px;min-width:5px;
    border-radius:50%;background:{BRAND_BLUE};margin-top:4px;}}
.fred-quote-box{{background:#F4F6F7;border-radius:12px;padding:28px 24px;}}
.fred-quote{{font-size:16px;color:#1A252F;line-height:1.75;
    font-style:italic;margin-bottom:14px;}}
.fred-quote-attr{{font-size:13px;color:{GREY};}}
.fred-faq-item{{padding:14px 0;border-bottom:0.5px solid #D5D8DC;}}
.fred-faq-item:last-child{{border-bottom:none;}}
.fred-faq-q{{font-size:14px;font-weight:500;color:#1A252F;margin-bottom:5px;}}
.fred-faq-a{{font-size:13px;color:#2C3E50;line-height:1.65;}}
.fred-footer{{padding:28px 0;border-top:0.5px solid #D5D8DC;text-align:center;}}
.fred-footer-logo{{font-size:16px;font-weight:500;color:{BRAND_BLUE};
    letter-spacing:3px;margin-bottom:8px;}}
.fred-footer-text{{font-size:11px;color:{GREY};line-height:1.8;}}
.fred-header-bar{{background:linear-gradient(135deg,{BRAND_BLUE},{BRAND_MID});
    color:white;padding:24px;border-radius:10px;margin-bottom:12px;}}
.fred-header-title{{font-size:40px;font-weight:500;letter-spacing:4px;margin:0;}}
.fred-header-sub{{font-size:13px;opacity:0.85;margin:4px 0 0 0;}}
.fred-beta-notice{{background:#FEF9E7;border-left:4px solid #F39C12;
    padding:12px 16px;border-radius:4px;font-size:13px;
    color:#7D6608;margin-bottom:20px;}}
.fred-sub-badge{{background:{BLUE_BG};border:1px solid {BRAND_BLUE};
    border-radius:6px;padding:8px 14px;font-size:12px;color:{BRAND_BLUE};
    font-weight:500;text-align:center;margin-bottom:16px;}}
.unlawful-flag{{border-left:4px solid {RED};padding:8px 12px;margin:6px 0;
    background:{RED_BG};border-radius:0 4px 4px 0;font-size:13px;
    color:#922B21;line-height:1.5;}}
.bestpractice-flag{{border-left:4px solid {AMBER};padding:8px 12px;margin:6px 0;
    background:{AMBER_BG};border-radius:0 4px 4px 0;font-size:13px;
    color:#7D6608;line-height:1.5;}}
.compliant-flag{{border-left:4px solid {GREEN};padding:8px 12px;margin:6px 0;
    background:{GREEN_BG};border-radius:0 4px 4px 0;font-size:13px;
    color:#1D6A36;line-height:1.5;}}
.pattern-flag{{border-left:4px solid {PURPLE};padding:8px 12px;margin:6px 0;
    background:{PURPLE_BG};border-radius:0 4px 4px 0;font-size:13px;
    color:#6C3483;line-height:1.5;}}
.tactical-flag{{border-left:4px solid {BRAND_BLUE};padding:8px 12px;margin:6px 0;
    background:{BLUE_BG};border-radius:0 4px 4px 0;font-size:13px;
    color:#1A3A5C;line-height:1.5;}}
.intent-flag{{border-left:4px solid {TEAL};padding:8px 12px;margin:6px 0;
    background:{TEAL_BG};border-radius:0 4px 4px 0;font-size:13px;
    color:#0E6655;line-height:1.5;}}
.vacuum-flag{{border-left:4px solid {PURPLE};padding:10px 14px;margin:8px 0;
    background:{PURPLE_BG};border-radius:0 6px 6px 0;font-size:13px;
    color:#6C3483;line-height:1.6;}}
.finding-card{{border:1px solid #D5D8DC;border-radius:10px;
    overflow:hidden;margin-bottom:16px;}}
.finding-header{{background:{BRAND_BLUE};color:white;padding:10px 16px;
    font-size:13px;font-weight:500;}}
.finding-body{{padding:14px 16px;background:white;}}
.finding-extract{{font-size:12px;color:{GREY};font-style:italic;
    background:#F4F6F7;padding:8px 12px;border-radius:6px;
    margin-bottom:10px;line-height:1.5;}}
.finding-comment{{font-size:13px;color:#2C3E50;line-height:1.65;}}
.tone-card{{background:#F4F6F7;border-radius:8px;padding:14px 18px;margin-bottom:12px;}}
.tone-label{{font-size:11px;font-weight:500;letter-spacing:1px;
    text-transform:uppercase;color:{GREY};margin-bottom:6px;}}
.tone-text{{font-size:13px;color:#2C3E50;line-height:1.65;}}
.record-card{{background:white;border:0.5px solid #D5D8DC;
    border-radius:8px;padding:14px 18px;margin-bottom:12px;}}
.record-item{{font-size:13px;color:#2C3E50;padding:4px 0;
    display:flex;gap:8px;align-items:flex-start;}}
.record-dot{{width:5px;height:5px;min-width:5px;border-radius:50%;
    background:{BRAND_BLUE};margin-top:6px;}}
.hold-card{{background:#FEF9E7;border:1px solid #F9CA24;
    border-radius:8px;padding:14px 18px;margin:12px 0;
    font-size:13px;color:#7D6608;line-height:1.6;}}
.dignity-flag{{background:#FEF9E7;border-left:4px solid #F39C12;
    padding:10px 14px;border-radius:0 6px 6px 0;
    font-size:13px;color:#7D6608;line-height:1.6;margin:8px 0;}}
.audit-header-red{{background:{RED};color:white;padding:10px 16px;
    border-radius:6px 6px 0 0;font-weight:500;font-size:13px;}}
.audit-header-amber{{background:{AMBER};color:white;padding:10px 16px;
    border-radius:6px 6px 0 0;font-weight:500;font-size:13px;}}
.audit-header-green{{background:{GREEN};color:white;padding:10px 16px;
    border-radius:6px 6px 0 0;font-weight:500;font-size:13px;}}
.audit-body{{background:white;border:1px solid #D5D8DC;border-top:none;
    padding:16px;border-radius:0 0 6px 6px;font-size:13px;
    line-height:1.7;margin-bottom:16px;}}
.anchor-line{{background:{BRAND_BLUE};color:white;padding:11px 16px;
    border-radius:6px;font-style:italic;font-size:13px;
    margin-top:10px;text-align:center;}}
.evidence-line{{background:#2C3E50;color:white;padding:9px 16px;
    border-radius:6px;font-style:italic;font-size:13px;
    margin-top:6px;text-align:center;}}
.review-capture{{background:{BLUE_BG};border:1px solid #AED6F1;
    border-radius:8px;padding:16px 20px;margin:16px 0;
    font-size:13px;color:#1A3A5C;line-height:1.6;}}
.subscription-signal{{background:linear-gradient(135deg,{BRAND_BLUE},{BRAND_MID});
    color:white;padding:22px 24px;border-radius:8px;
    margin:24px 0;font-size:14px;line-height:1.75;}}
.upload-tip{{background:#F4F6F7;border-radius:6px;padding:10px 14px;
    font-size:12px;color:{GREY};margin-top:6px;line-height:1.6;}}
.stButton>button{{background:{BRAND_BLUE};color:white;border:none;
    padding:10px 28px;border-radius:6px;font-weight:500;
    font-size:15px;width:100%;}}
.stButton>button:hover{{background:{BRAND_MID};}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

defaults = {
    'stage': 'landing',
    'answers': {},
    'extracted_sections': {},
    'report_results': [],
    'section_e_results': [],
    'policy_text': '',
    'raw_text': '',
    'active_emails': [],
    'history_emails': [],
    'transcript_text': '',
    'correspondence_analysis': None,
    'three_findings': None,
    'post_meeting_email': '',
    'sneak_peek_result': None,
    'email_captured': False,
    'is_subscriber': False,
    'correspondence_action': None,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ─────────────────────────────────────────────
# OFSTED PRINCIPLES
# ─────────────────────────────────────────────

OFSTED_PRINCIPLES = [
    {'area': 'Quality of education', 'principle': 'Ofsted inspection frameworks consistently expect schools to demonstrate that SEND pupils access a curriculum that is ambitious and appropriately adapted to their needs. Provision that lacks specificity makes this difficult to evidence at inspection.'},
    {'area': 'Leadership and management', 'principle': 'Schools are expected to demonstrate that leaders and managers have clear oversight of SEND provision and its effectiveness. An absence of delivery logs and monitoring records weakens this evidence base significantly.'},
    {'area': 'Personal development', 'principle': 'Inspection frameworks expect schools to show how SEND pupils are supported to develop confidence, resilience, and independence. Provision contingent on the child self-identifying need is unlikely to meet this expectation.'},
    {'area': 'Safeguarding', 'principle': 'Effective safeguarding requires that schools have specific, documented arrangements for pupils with identified vulnerabilities. Vague or discretionary provision creates risk that safeguarding responsibilities cannot be evidenced.'},
]

# ─────────────────────────────────────────────
# WHAT-IF SCENARIO LIBRARY
# First set drawn from real thread analysis
# ─────────────────────────────────────────────

WHAT_IF_SCENARIOS = [
    {
        'id': 'case_building',
        'label': 'Case building pattern',
        'trigger_words': ['unpredictable', 'other students', 'worrying', 'concerns raised', 'counts as a sanction', 'previous incidents', 'not the first time'],
        'description': (
            'This communication documents multiple incidents in a single message and focuses on '
            'peer perception and disruption. This pattern sometimes precedes a request for managed '
            'removal or a formal behaviour plan. It does not necessarily indicate bad intent — '
            'schools document incidents routinely. However when combined with head of year involvement '
            'it is worth noting what is being put on record and why.'
        ),
        'what_to_watch': 'Watch for follow-up communications that reference this email as establishing a pattern.',
    },
    {
        'id': 'hoy_involvement',
        'label': 'Head of year involvement',
        'trigger_words': ['head of year', 'HOY', 'form tutor', 'cc', 'copied in'],
        'description': (
            'Head of year involvement typically signals the disruption management pathway rather than '
            'the SEND support pathway. This does not mean the communication is adversarial — HOYs '
            'often have genuine care for students. It does mean the frame of reference is behaviour '
            'management rather than needs-led support.'
        ),
        'what_to_watch': 'Check whether SENCO or SEND support staff are involved. If not, consider whether the communication should be redirected.',
    },
    {
        'id': 'reassurance_without_evidence',
        'label': 'Reassurance without evidence',
        'trigger_words': ['reassure you', 'please be assured', 'rest assured', 'want you to know', 'not concerned'],
        'description': (
            'Reassurance language is common in school correspondence and is often genuine. '
            'It becomes significant when it appears in response to specific requests for documentation. '
            'A reassurance is not a record. If you asked for something specific and received '
            'reassurance instead, the specific request remains outstanding.'
        ),
        'what_to_watch': 'Note what was specifically requested and whether the reassurance addresses it or replaces it.',
    },
    {
        'id': 'provision_substitution',
        'label': 'Provision substitution',
        'trigger_words': ['through', 'via', 'as part of', 'during lunch', 'informally', 'gentle', 'we support'],
        'description': (
            'When a school describes provision in response to a question about statutory provision, '
            'check whether what is described matches what the EHCP specifies. Informal or universal '
            'provision described in response to a question about specific statutory provision '
            'does not confirm that statutory provision is being delivered.'
        ),
        'what_to_watch': 'Compare the description against the exact wording in Section F. If they do not match, the question was not answered.',
    },
    {
        'id': 'apdr_continuous',
        'label': 'APDR described as ongoing',
        'trigger_words': ['runs continuously', 'ongoing', 'continuous', 'always running', 'live process', 'live document'],
        'description': (
            'The APDR cycle is Assess, Plan, Do, Review. Review is a defined event — '
            'a documented moment where progress is formally assessed and new targets are set. '
            'It cannot run continuously. Describing APDR as ongoing or continuous '
            'either conflates the stages or avoids confirming when the last formal Review '
            'took place and what it produced.'
        ),
        'what_to_watch': 'Ask for the date of the last formal Review and its documented outcomes.',
    },
    {
        'id': 'recording_admission',
        'label': 'Recording inadequacy admission',
        'trigger_words': ['improve how we record', 'new software', 'looking to improve', 'working on our systems', 'better recording'],
        'description': (
            'Statements about plans to improve recording systems confirm that current recording '
            'is insufficient. This is framed positively but it also means the records you have '
            'requested may not currently exist in an adequate form. '
            'Any records subsequently produced should be assessed against when they were created.'
        ),
        'what_to_watch': 'Note the date of this statement. If records are later produced, compare their content against what was admitted here.',
    },
    {
        'id': 'collaborative_genuine',
        'label': 'Genuine collaborative signal',
        'trigger_words': ['would really value your thoughts', 'keep you updated', 'work together', 'named programme', 'will record', 'structured intervention'],
        'description': (
            'This communication contains specific commitments — named deliverer, named programme, '
            'recording commitment, parental update. These are positive signals that distinguish '
            'genuine collaborative intent from relationship management language. '
            'When a school makes specific commitments they are worth welcoming and noting.'
        ),
        'what_to_watch': 'Record these commitments as on the record. They become the baseline against which future delivery is measured.',
    },
]

# ─────────────────────────────────────────────
# DOCUMENT READING
# ─────────────────────────────────────────────

def read_file(uploaded_file):
    if uploaded_file is None:
        return None, None
    name = uploaded_file.name.lower()
    if name.endswith('.pdf'):
        try:
            pdf_bytes = uploaded_file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = "".join(page.get_text() for page in doc)
            doc.close()
            if len(text.strip()) < 50:
                return None, "This PDF appears to be image-based. Try printing it to PDF from the original application."
            return text, None
        except Exception:
            return None, "This PDF could not be read. If password protected, open it, select print, and save as PDF."
    elif name.endswith('.docx') or name.endswith('.doc'):
        try:
            doc = DocxDocument(uploaded_file)
            text = "\n".join(p.text for p in doc.paragraphs)
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        text += "\n" + cell.text
            if len(text.strip()) < 50:
                return None, "This Word document appears to be empty."
            return text, None
        except Exception:
            return None, "This Word document could not be read. If password protected, open it in Word and save as PDF."
    else:
        return None, "Format not supported. Please upload a PDF or Word document."

def identify_sections(text):
    sections = {}
    patterns = {
        'A': r'(?:SECTION\s+A|Section\s+A)[:\s\-–—]*[^\n]*\n(.*?)(?=(?:SECTION\s+[B-K]|Section\s+[B-K])|$)',
        'B': r'(?:SECTION\s+B|Section\s+B)[:\s\-–—]*[^\n]*\n(.*?)(?=(?:SECTION\s+[C-K]|Section\s+[C-K])|$)',
        'E': r'(?:SECTION\s+E|Section\s+E)[:\s\-–—]*[^\n]*\n(.*?)(?=(?:SECTION\s+[F-K]|Section\s+[F-K])|$)',
        'F': r'(?:SECTION\s+F|Section\s+F)[:\s\-–—]*[^\n]*\n(.*?)(?=(?:SECTION\s+[G-K]|Section\s+[G-K])|$)',
        'I': r'(?:SECTION\s+I|Section\s+I)[:\s\-–—]*[^\n]*\n(.*?)(?=(?:SECTION\s+[J-K]|Section\s+[J-K])|$)',
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            content = re.sub(r'\n{3,}', '\n\n', match.group(1).strip())
            if len(content) > 20:
                sections[key] = content
    return sections

def extract_entries(text):
    numbered = re.split(r'\n\s*\d+[\.\)]\s+', text)
    if len(numbered) > 2:
        return [e.strip() for e in numbered if len(e.strip()) > 30]
    bulleted = re.split(r'\n\s*[\•\-\*]\s+', text)
    if len(bulleted) > 2:
        return [e.strip() for e in bulleted if len(e.strip()) > 30]
    paragraphs = re.split(r'\n{2,}', text)
    entries = [p.strip() for p in paragraphs if len(p.strip()) > 30]
    return entries if entries else [text]

def detect_doc_type(text):
    tl = text.lower()
    if any(kw in tl for kw in ['send policy', 'accessibility plan', 'behaviour policy']):
        return 'policy'
    if any(kw in tl for kw in ['dear', 'kind regards', 'best wishes', 'subject:']):
        return 'email'
    if any(kw in tl for kw in ['speaker 1', 'speaker 2', 'transcript', '[end]']):
        return 'transcript'
    if any(kw in tl for kw in ['section a', 'section b', 'section f', 'education health and care']):
        return 'ehcp'
    return 'other'

# ─────────────────────────────────────────────
# RULES ENGINE — SECTION F
# ─────────────────────────────────────────────

PROHIBITED = {
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
    r'\bflexib\w*\b': ('flexible/flexibility', 'unmeasurable — who decides what is flexible and when is unspecified'),
    r'\bresponsive\b': ('responsive', 'reactive delivery is not specified provision — frequency and trigger criteria must be stated'),
    r'\btailored\b': ('tailored', 'undefined without specifying what the tailoring consists of'),
    r'\bembedded\b': ('embedded', 'not a quantified description of delivery — frequency and context must be stated'),
}

UNIVERSAL = [
    'high-quality teaching', 'quality first teaching', 'broad and balanced curriculum',
    'differentiated curriculum', 'universal offer', 'graduated response',
    'scaffolding for tasks', 'quality teaching', 'ordinarily available',
]

QUANT = {
    'frequency': r'\b(\d+\s*(?:times?|sessions?|hours?)\s*(?:per|a|each)\s*(?:week|day|term|month)|daily|weekly|fortnightly|monthly|termly|once|twice)\b',
    'duration': r'\b(\d+\s*(?:minutes?|hours?|mins?))\b',
    'role': r'\b(therapist|psychologist|specialist|SENCO|senco|teacher|LSA|TA|teaching assistant|learning support|coordinator|practitioner|nurse|OT|SALT|SLT|occupational|speech|language)\b',
    'named_individual': r'\b(Mrs|Mr|Ms|Dr|Miss)\s+[A-Z][a-z]+\b',
}

def chk_quant(text):
    return {k: bool(re.search(p, text, re.IGNORECASE)) for k, p in QUANT.items()}

def chk_prohibited(text):
    findings = []
    seen = set()
    tl = text.lower()
    for pattern, (term, exp) in PROHIBITED.items():
        if term not in seen and re.search(pattern, tl, re.IGNORECASE):
            findings.append((term, exp))
            seen.add(term)
    return findings

def chk_universal(text):
    return [i for i in UNIVERSAL if i in text.lower()]

def chk_laundering(text):
    patterns = [r'\bwould benefit from\b', r'\bit is recommended\b', r'\bmay benefit from\b']
    return [p.replace(r'\b', '') for p in patterns if re.search(p, text, re.IGNORECASE)]

def chk_dilution(text):
    patterns = [r'\bshared with other\b', r'\bmay be shared\b', r'\bas resources allow\b',
                r'\bsubject to availability\b', r'\bwider class\b']
    return [p.replace(r'\b', '') for p in patterns if re.search(p, text, re.IGNORECASE)]

def chk_policy(entry, policy):
    if not policy:
        return []
    gaps = []
    pl = policy.lower()
    el = entry.lower()
    commitments = [
        ('1:1 support', ['1:1', 'one to one', 'individual support']),
        ('named key worker', ['key worker', 'key person']),
        ('sensory assessment', ['sensory assessment', 'sensory profile']),
        ('home-school communication', ['parent update', 'home school']),
        ('risk assessment', ['risk assess']),
        ('accessibility arrangements', ['accessible', 'adaptations']),
    ]
    for label, keywords in commitments:
        if any(kw in pl for kw in keywords) and not any(kw in el for kw in keywords):
            gaps.append(f"The school's own policy references {label}. This does not appear in this provision entry. The school cannot dispute what its own policy commits to.")
    return gaps

def is_compliant(text, quant):
    has_must = bool(re.search(r'\bmust\b', text, re.IGNORECASE))
    return (has_must and quant.get('frequency') and quant.get('duration')
            and quant.get('role') and not chk_prohibited(text) and not chk_universal(text))

def get_ofsted(text):
    tl = text.lower()
    if any(w in tl for w in ['safe', 'risk', 'physical', 'behaviour', 'incident']):
        return OFSTED_PRINCIPLES[3]
    if any(w in tl for w in ['independent', 'confidence', 'resilience']):
        return OFSTED_PRINCIPLES[2]
    if any(w in tl for w in ['monitor', 'oversight', 'review', 'log', 'record']):
        return OFSTED_PRINCIPLES[1]
    return OFSTED_PRINCIPLES[0]

def audit_entry(entry_text, entry_number, policy_text=''):
    quant = chk_quant(entry_text)
    prohibited = chk_prohibited(entry_text)
    universal = chk_universal(entry_text)
    laundering = chk_laundering(entry_text)
    dilution = chk_dilution(entry_text)
    compliant = is_compliant(entry_text, quant)
    policy_gaps = chk_policy(entry_text, policy_text)

    unlawful = []
    for term, exp in prohibited:
        unlawful.append(f'"{term}" — {exp}.')
    if not quant['frequency']:
        unlawful.append('No frequency specified — how often provision is delivered is not stated. The SEND Code of Practice requires provision to be specified and quantified.')
    if not quant['duration']:
        unlawful.append('No duration specified — the length of each session is not stated. Provision without quantification cannot be measured or challenged at annual review.')
    if not quant['role']:
        unlawful.append('No deliverer role specified — who provides this provision and at what qualification or training level is not stated.')

    patterns = []
    if universal:
        patterns.append('Universal provision identified — this entry describes what the school is already required to provide all pupils. Its presence in Section F creates no additional lawful entitlement specific to this child.')
    if laundering:
        patterns.append('Recommendation laundering identified — assessment language has been copied into Section F without being converted into a specified lawful commitment.')
    if dilution:
        patterns.append('Dilution clause identified — wording allows this provision to be shared or made conditional on school resources.')

    best_practice = []
    if not quant['named_individual']:
        best_practice.append('No named accountable person — the lawful requirement is that the deliverer role and training level are specified. As best practice, naming the SENCO as the accountable person supports continuity. This is a wellbeing recommendation, not a lawful requirement.')
    if not re.search(r'\b(review|reviewed|assess|monitor|evaluated)\b', entry_text, re.IGNORECASE):
        best_practice.append('No review mechanism stated — provision without a stated review mechanism cannot be assessed for effectiveness.')

    required = []
    if not compliant:
        if not quant['frequency']:
            required.append('Frequency must be stated — number of sessions per week or per term')
        if not quant['duration']:
            required.append('Duration must be stated — length of each session in minutes')
        if not quant['role']:
            required.append('Deliverer role must be named — role title and relevant qualification or training level')
        if universal:
            required.append('Entry must describe provision additional to the universal offer')
        if laundering:
            required.append('Professional recommendations must be reproduced as specified provision')
        if dilution:
            required.append('Shared or conditional wording must be removed')
        required.append(
            'Mandatory delivery log — all provision recorded in a dated delivery log '
            'showing date, duration, who delivered, and any relevant observations. '
            'This is the evidence base for the Do stage of the school\'s statutory '
            'APDR (Assess, Plan, Do, Review) cycle. Without it the Review stage '
            'cannot be conducted accurately.'
        )

    tactical = [
        'Request the Physical Delivery Log for this provision. '
        'Dated entries must show each session — date, duration, who delivered, and format. '
        'If no log exists there is no evidence this provision has been delivered. '
        'Lack of evidence is evidence of lack.'
    ]
    if not compliant:
        tactical.append('At your next annual review this entry must be rewritten to full specification standard. FRED will remind you of this finding as your review approaches.')
    if dilution:
        tactical.append('Request written confirmation of how many other pupils share this provision and what proportion of the named support this child actually receives.')

    return {
        'entry_number': entry_number,
        'entry_text': entry_text,
        'is_compliant': compliant,
        'unlawful_deficiencies': unlawful,
        'additional_patterns': patterns,
        'best_practice_gaps': best_practice,
        'ofsted_principle': get_ofsted(entry_text),
        'policy_gaps': policy_gaps,
        'required_specification': required,
        'tactical_advice': tactical,
    }

def audit_section_e(text):
    results = []
    outcomes = re.split(r'\n\s*[\•\-\*\d][\.\)]?\s+', text)
    outcomes = [o.strip() for o in outcomes if len(o.strip()) > 20]
    if not outcomes:
        outcomes = [p.strip() for p in text.split('\n') if len(p.strip()) > 20]
    for i, outcome in enumerate(outcomes):
        ol = outcome.lower()
        unlawful = []
        bp = []
        if not re.search(r'\b(currently|baseline|starting point|at present|now)\b', ol):
            unlawful.append('No baseline stated — without a starting point progress cannot be objectively measured at annual review.')
        if not re.search(r'\b(\d+|percentage|score|level|times|independently|consistently|measured by|assessed)\b', ol):
            unlawful.append('No measurable indicator — success cannot be objectively assessed. An outcome without a measurable indicator cannot be reviewed under the APDR cycle.')
        if not re.search(r'\b(by|within|term|year|month|weeks?|annual review|end of)\b', ol):
            bp.append('No timeframe stated — when this outcome should be achieved is not specified.')
        results.append({'outcome_number': i+1, 'outcome_text': outcome, 'unlawful_failures': unlawful, 'best_practice_gaps': bp})
    return results

# ─────────────────────────────────────────────
# CORRESPONDENCE ENGINE v2
# ─────────────────────────────────────────────

VACUUM_PATTERNS = [
    (r'\b(happening a lot recently|not the first time|previous incidents|similar before|we have noticed before|as has been the case|happening more|increasingly)\b',
     'frequency', 'This statement implies a documented history of incidents. Request the records.'),
    (r'\b(tried to address|spoken to.*before|discussed previously|put things in place|tried before|we have spoken)\b',
     'previous_attempt', 'This statement implies previous strategies were deployed. Request documentation of what was tried and what outcomes were recorded.'),
    (r'\b(we have noticed|we have observed|staff have been aware|keeping an eye on|been monitoring|we have seen)\b',
     'observation', 'Observation without a formal record is not evidenced monitoring. Request the observation log.'),
    (r'\b(runs continuously|ongoing process|always running|live process|continuous|live document)\b',
     'apdr_continuous', 'The APDR cycle cannot run continuously. Review is a defined event with documented outcomes. Request the date of the last formal Review and its recorded outcomes.'),
]

INTENT_SIGNALS = {
    'case_building': [
        'unpredictable', 'other students are worried', 'counts as a sanction',
        'previous incidents', 'not the first time', 'coming very close to',
        'aggressive reactions', 'said he wants to kill', 'worrying for others',
    ],
    'hoy_signal': [
        'head of year', 'hoy', 'form tutor raised', 'cc', 'copied in',
    ],
    'collaborative': [
        'would really value your thoughts', 'will record', 'keep you updated',
        'named programme', 'structured intervention', 'working with you',
        'hear both sides', 'took his needs into account',
    ],
    'reassurance_without_evidence': [
        'reassure you', 'please be assured', 'rest assured',
        'want you to know', 'not currently concerned', 'no pattern',
    ],
}

UNENFORCEABLE_EMAIL = [
    ('in place', 'Claims provision is in place without referencing any delivery record'),
    ('regularly', '"Regularly" is unmeasurable — frequency must be stated'),
    ('as outlined', 'References the plan without evidencing delivery'),
    ('consistently', 'A claim — the delivery log is the evidence'),
    ('embedded', 'Not a quantified description of delivery'),
    ('responsive', 'Reactive delivery is not specified provision'),
    ('some flexibility', 'Flexibility in EHCP provision is not permitted'),
    ('monitor', 'Monitoring without a stated recording method is unverifiable'),
    ('runs continuously', 'The APDR cycle cannot run continuously — Review is a defined event not a state'),
]

def detect_intent(email_text):
    tl = email_text.lower()
    case_building_score = sum(1 for signal in INTENT_SIGNALS['case_building'] if signal in tl)
    hoy_score = sum(1 for signal in INTENT_SIGNALS['hoy_signal'] if signal in tl)
    collaborative_score = sum(1 for signal in INTENT_SIGNALS['collaborative'] if signal in tl)
    reassurance_score = sum(1 for signal in INTENT_SIGNALS['reassurance_without_evidence'] if signal in tl)

    if case_building_score >= 2 or hoy_score >= 1:
        if collaborative_score >= 2:
            intent = 'mixed'
        else:
            intent = 'case_building'
    elif collaborative_score >= 2:
        intent = 'collaborative'
    else:
        intent = 'mixed'

    return {
        'intent': intent,
        'case_building_score': case_building_score,
        'hoy_signal': hoy_score > 0,
        'collaborative_score': collaborative_score,
        'reassurance_score': reassurance_score,
    }

def detect_vacuum_statements(email_text):
    findings = []
    for pattern, vacuum_type, explanation in VACUUM_PATTERNS:
        matches = re.findall(pattern, email_text, re.IGNORECASE)
        if matches:
            findings.append({
                'type': vacuum_type,
                'matched': matches[0] if isinstance(matches[0], str) else matches[0][0],
                'explanation': explanation,
            })
    return findings

def match_what_if_scenarios(email_text):
    tl = email_text.lower()
    matched = []
    for scenario in WHAT_IF_SCENARIOS:
        if any(trigger in tl for trigger in scenario['trigger_words']):
            matched.append(scenario)
    return matched

def generate_three_findings(email_text, ehcp_sections, transcript_text='', history_texts=None):
    findings = []
    tl = email_text.lower()

    # Finding 1 — Check for APDR continuous description
    if re.search(r'\b(runs continuously|ongoing|live process|continuous)\b', tl, re.IGNORECASE):
        extract = ''
        for match in re.finditer(r'[^.]*(?:runs continuously|ongoing|live process|continuous)[^.]*\.', email_text, re.IGNORECASE):
            extract = match.group(0).strip()
            break
        if not extract:
            extract = 'APDR described as ongoing or continuous'
        findings.append({
            'label': 'APDR described as continuous',
            'extract': extract,
            'comment': (
                'The APDR cycle is Assess, Plan, Do, Review. Review is a defined event — '
                'a documented moment where progress is formally assessed and new targets set. '
                'It cannot run continuously. This description either conflates the stages '
                'or avoids confirming when the last formal Review took place. '
                'Ask for the date of the last formal Review and its documented outcomes.'
            )
        })

    # Finding 2 — Check for provision substitution
    if 'F' in ehcp_sections:
        fl = ehcp_sections['F'].lower()
        provisions = [
            ('social skills group', ['social skills', 'social group'], ['lunch', 'lunchtime', 'bridge', 'informal', 'gentle']),
            ('emotional regulation sessions', ['emotional regulation', 'emotional literacy'], ['general', 'as needed', 'when needed']),
            ('sensory breaks', ['sensory break', 'movement break'], ['when needed', 'responsive', 'as required']),
        ]
        for label, ehcp_keywords, substitution_keywords in provisions:
            in_ehcp = any(kw in fl for kw in ehcp_keywords)
            in_email = any(kw in tl for kw in ehcp_keywords)
            substituted = any(kw in tl for kw in substitution_keywords)
            if in_ehcp and in_email and substituted:
                extract = ''
                for kw in ehcp_keywords:
                    matches = list(re.finditer(rf'[^.]*{kw}[^.]*\.', email_text, re.IGNORECASE))
                    if matches:
                        extract = matches[0].group(0).strip()
                        break
                findings.append({
                    'label': f'Provision substitution — {label}',
                    'extract': extract or f'Description of {label} in email',
                    'comment': (
                        f'Your EHCP specifies {label} as statutory provision. '
                        f'The email describes a different or informal arrangement in response to this. '
                        f'The question of how the statutory provision is being delivered was not answered — '
                        f'a different provision was described instead. '
                        f'No sessions count was given and no delivery record was referenced.'
                    )
                })
                break

    # Finding 3 — Check for recording inadequacy admission
    if re.search(r'\b(improve how we record|new software|looking to improve|better recording|working on our systems)\b', tl, re.IGNORECASE):
        extract = ''
        for match in re.finditer(r'[^.]*(?:improve how we record|new software|looking to improve|better recording)[^.]*\.', email_text, re.IGNORECASE):
            extract = match.group(0).strip()
            break
        findings.append({
            'label': 'Recording inadequacy admitted',
            'extract': extract or 'Statement about improving recording systems',
            'comment': (
                'This statement confirms that current recording is insufficient. '
                'Framed as a positive investment, it also means the records you have requested '
                'may not currently exist in an adequate form. '
                'Note the date of this statement. If records are subsequently produced, '
                'assess them against what was admitted here.'
            )
        })

    # Finding 4 — Check for vacuum statements (pick most significant)
    vacuum = detect_vacuum_statements(email_text)
    if vacuum and len(findings) < 3:
        v = vacuum[0]
        findings.append({
            'label': f'Implied history — {v["type"].replace("_", " ")}',
            'extract': f'"{v["matched"]}"',
            'comment': v['explanation'],
        })

    # Finding 5 — Unsubstantiated claims
    for term, exp in UNENFORCEABLE_EMAIL:
        if term in tl and len(findings) < 3:
            extract = ''
            for match in re.finditer(rf'[^.]*{re.escape(term)}[^.]*\.', email_text, re.IGNORECASE):
                extract = match.group(0).strip()
                break
            findings.append({
                'label': f'Unsubstantiated claim — "{term}"',
                'extract': extract or f'Use of "{term}" in email',
                'comment': f'{exp}. A delivery log is required to substantiate this claim. Lack of evidence is evidence of lack.',
            })
            break

    return findings[:3]

def generate_on_the_record(email_text):
    records = []
    tl = email_text.lower()

    commitment_patterns = [
        (r'will record', 'Commitment to record sessions made in writing'),
        (r'will keep you updated', 'Commitment to keep parents updated made in writing'),
        (r'will share', 'Commitment to share records made in writing'),
        (r'will speak to', 'Commitment to consult named colleague made in writing'),
        (r'will be in touch', 'Commitment to communicate made in writing'),
        (r'you will.*be kept.*informed', 'Commitment to inform parents made in writing'),
        (r'not currently concerned', 'School has stated no current concern about pattern — dated'),
        (r'oversee this process', 'Named individual has taken responsibility for APDR oversight'),
        (r'recently purchased', 'Admission that new systems are being put in place — implies current systems inadequate'),
    ]
    for pattern, description in commitment_patterns:
        if re.search(pattern, tl, re.IGNORECASE):
            records.append(description)

    return records

def generate_tone_read(intent_result, email_text):
    intent = intent_result['intent']
    hoy = intent_result['hoy_signal']
    reassurance = intent_result['reassurance_score']

    if intent == 'case_building':
        base = (
            'This communication shows features of incident documentation. '
            'Multiple events are recorded in a single message with focus on peer perception '
            'and disruption. '
        )
        if hoy:
            base += 'Head of year involvement suggests the disruption management pathway rather than the SEND support pathway. '
        base += (
            'This does not necessarily indicate adversarial intent — schools document incidents routinely. '
            'What is being put on record and why is worth noting.'
        )
    elif intent == 'collaborative':
        base = (
            'This communication reads as genuinely collaborative. '
            'The focus is on the child\'s experience, named commitments are made, '
            'and the tone is solution-focused rather than incident-focused. '
            'Specific commitments in this email are worth welcoming and noting as on the record.'
        )
    else:
        base = (
            'This communication is mixed. The tone is warm and the care appears genuine. '
            'At the same time, specific requests from previous correspondence have not been fully answered '
            'and reassurance language appears where evidence was requested. '
        )
        if reassurance > 0:
            base += 'Reassurance is not a record. The specific requests remain outstanding.'

    return base

def generate_ehcp_compliance_check(email_text, ehcp_sections, requests_made=None):
    checks = []
    tl = email_text.lower()

    if 'F' in ehcp_sections:
        fl = ehcp_sections['F'].lower()

        if 'social skills' in fl:
            if 'social skills' in tl or 'bridge' in tl or 'lunch' in tl:
                if re.search(r'\b(weekly|sessions|how many|delivered by|recorded)\b', tl):
                    checks.append(('Social skills provision', 'Partially addressed — description provided but sessions count, delivery record, and named deliverer not confirmed.', 'amber'))
                else:
                    checks.append(('Social skills provision', 'Not fully addressed — informal provision described but statutory provision delivery not evidenced.', 'red'))
            else:
                checks.append(('Social skills provision', 'Not addressed in this email.', 'red'))

        if 'emotional regulation' in fl or 'emotional literacy' in fl:
            if 'emotional' in tl or 'volcano' in tl:
                checks.append(('Emotional regulation provision', 'Referenced — Volcano approach mentioned. Delivery record not confirmed.', 'amber'))
            else:
                checks.append(('Emotional regulation provision', 'Not addressed in this email.', 'red'))

    if re.search(r'\b(apdr|assess plan do review|review cycle)\b', tl, re.IGNORECASE):
        if re.search(r'\b(last reviewed|review date|last formal|documented outcomes|new targets set)\b', tl, re.IGNORECASE):
            checks.append(('APDR cycle', 'Partially addressed — responsibility named but last formal review date and documented outcomes not provided.', 'amber'))
        else:
            checks.append(('APDR cycle', 'Not evidenced — described as ongoing but no formal review date or documented outcomes provided. APDR cannot run continuously — Review is a defined event.', 'red'))
    else:
        checks.append(('APDR cycle', 'Not addressed in this email.', 'red'))

    if requests_made:
        for req in requests_made:
            if req.lower() not in tl:
                checks.append((f'Requested: {req}', 'Not addressed in this email — request outstanding.', 'red'))

    return checks

def generate_post_meeting_email(analysis, answers):
    tone = answers.get('q5', 'Constructive but cautious')
    openings = {
        'Warm and collaborative': 'Thank you for the meeting and for your follow up. We want to ensure our understanding of what was discussed is accurately recorded.',
        'Constructive but cautious': 'Thank you for the meeting and for your follow up. We write to ensure our understanding is accurately recorded.',
        'Professionally firm': 'We write to record our understanding of the meeting, which differs in some respects from the summary provided.',
        'Formally assertive': 'We write to place on record our understanding of what was agreed and what remains unresolved.',
        'Rights-based and formal': 'The following sets out our understanding of what was discussed and what outstanding matters require a written response.',
    }
    parts = [openings.get(tone, openings['Constructive but cautious']), '']
    if analysis.get('contradictions'):
        parts.append('What requires a written response\n')
        for c in analysis['contradictions']:
            parts.append(c + '\n')
    if analysis.get('deflected'):
        for d in analysis['deflected']:
            parts.append(d + '\n')
    parts.append('')
    parts.append('Please let us know within five working days if anything above does not reflect your understanding. If we do not hear from you we will treat this as the agreed record.')
    return '\n'.join(parts)

# ─────────────────────────────────────────────
# RENDER — TRAFFIC LEGEND
# ─────────────────────────────────────────────

def render_traffic_legend():
    st.markdown(f"""
    <div class="fred-traffic-legend">
        <div class="fred-traffic-title">Here is how FRED colour codes its findings</div>
        <div class="fred-trow">
            <div class="fred-tdot tdot-red"></div>
            <div class="fred-ttext"><strong>Red — lawful requirement not met.</strong> Must be addressed at annual review.</div>
        </div>
        <div class="fred-trow">
            <div class="fred-tdot tdot-amber"></div>
            <div class="fred-ttext"><strong>Amber — best practice gap.</strong> Meets minimum lawful standard. Worth raising at annual review.</div>
        </div>
        <div class="fred-trow">
            <div class="fred-tdot tdot-green"></div>
            <div class="fred-ttext"><strong>Green — compliant.</strong> Meets the lawful standard.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# RENDER — THREE FINDING BRIEFING
# ─────────────────────────────────────────────

def render_three_findings(findings, tone_read, on_record, compliance_checks, what_if_matches, intent_result):

    st.markdown("## Your correspondence briefing")
    st.markdown("*Three findings. Read in five minutes. You decide what to do with them.*")

    intent = intent_result['intent']
    intent_labels = {
        'case_building': ('⚠ Case building signals detected', RED),
        'collaborative': ('✓ Collaborative signals present', GREEN),
        'mixed': ('◉ Mixed — genuine care and gaps present', AMBER),
    }
    label, colour = intent_labels.get(intent, ('Intent unclear', GREY))
    st.markdown(f"""
    <div style="background:{colour}20;border-left:4px solid {colour};
        padding:10px 14px;border-radius:0 6px 6px 0;font-size:13px;
        font-weight:500;color:{colour};margin-bottom:16px;">
        {label}
        {'&nbsp;&nbsp;|&nbsp;&nbsp;Head of year involvement noted' if intent_result['hoy_signal'] else ''}
    </div>
    """, unsafe_allow_html=True)

    if findings:
        for i, finding in enumerate(findings, 1):
            st.markdown(f"""
            <div class="finding-card">
                <div class="finding-header">Finding {i} — {finding['label']}</div>
                <div class="finding-body">
                    <div class="finding-extract">"{finding['extract']}"</div>
                    <div class="finding-comment">{finding['comment']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="compliant-flag">✓ No significant findings identified in this email.</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"""
    <div class="tone-card">
        <div class="tone-label">Tone read</div>
        <div class="tone-text">{tone_read}</div>
    </div>
    """, unsafe_allow_html=True)

    if on_record:
        st.markdown("**On the record — what the school has confirmed in writing**")
        st.markdown('<div class="record-card">', unsafe_allow_html=True)
        for item in on_record:
            st.markdown(f'<div class="record-item"><span class="record-dot"></span>{item}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if compliance_checks:
        st.markdown("**EHCP compliance check**")
        for label, status, tier in compliance_checks:
            colour_map = {'red': RED, 'amber': AMBER, 'green': GREEN}
            colour = colour_map.get(tier, GREY)
            bg_map = {'red': RED_BG, 'amber': AMBER_BG, 'green': GREEN_BG}
            bg = bg_map.get(tier, '#F4F6F7')
            st.markdown(f"""
            <div style="border-left:3px solid {colour};padding:7px 12px;
                background:{bg};border-radius:0 4px 4px 0;
                font-size:13px;margin:5px 0;line-height:1.5;">
                <strong>{label}</strong> — {status}
            </div>
            """, unsafe_allow_html=True)

    if what_if_matches:
        st.markdown("**Patterns recognised — what-if scenarios**")
        for scenario in what_if_matches[:2]:
            st.markdown(f"""
            <div class="intent-flag">
                <strong>{scenario['label']}</strong><br>
                {scenario['description']}<br>
                <em>Watch for: {scenario['what_to_watch']}</em>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**What do you want to do with this?**")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✍ Draft a response", key="action_draft"):
            st.session_state.correspondence_action = 'draft'
            st.rerun()
    with col2:
        if st.button("📋 Brief me instead", key="action_brief"):
            st.session_state.correspondence_action = 'brief'
            st.rerun()
    with col3:
        if st.button("🗂 Hold in vault", key="action_hold"):
            st.session_state.correspondence_action = 'hold'
            st.rerun()

    if st.session_state.correspondence_action == 'hold':
        st.markdown(f"""
        <div class="hold-card">
            <strong>Held in vault.</strong> These findings are dated and stored.
            FRED will surface them if they become relevant to future correspondence.
            No response will be drafted. You have chosen to observe before acting —
            that is a valid strategic decision.
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.correspondence_action == 'brief':
        st.markdown("**If-this-then-that — your options**")
        options = []
        intent = intent_result['intent']
        if intent == 'case_building':
            options.append(("If you press for records now", "The school will produce them or admit they do not exist. Either is useful. The relationship may become more formal as a result."))
            options.append(("If you acknowledge and hold", "You signal you are across this without confrontation. The records sit on the vault. You act when the moment serves you better."))
        elif intent == 'collaborative':
            options.append(("If you welcome the commitments", "You reinforce collaborative behaviour and create a written record of what has been offered. The commitments become the baseline."))
            options.append(("If you also note the gaps", "You can do both — welcome what is genuine and gently note what remains outstanding. The relationship stays intact and the record is complete."))
        else:
            options.append(("If you respond warmly and specifically", "You maintain the relationship while putting the outstanding requests on the record one more time. Simple. Unanswerable without evidence or admission."))
            options.append(("If you hold and observe", "You have seen what FRED found. The vault holds it. You watch what happens next before deciding whether to press."))
            options.append(("If you request a meeting", "A meeting creates a formal occasion where records will need to exist. The SENCO has to prepare. That preparation often produces the evidence."))

        for condition, consequence in options:
            st.markdown(f"""
            <div style="background:#F4F6F7;border-radius:8px;padding:12px 16px;
                margin-bottom:8px;font-size:13px;line-height:1.6;">
                <strong>{condition}</strong><br>{consequence}
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# RENDER — DRAFT EMAIL WITH OPTIONS
# ─────────────────────────────────────────────

def render_draft_with_options(draft_text, answers):
    st.markdown("### Drafted response")
    st.markdown("*Calibrated to your relationship tone. Edit to your own voice or use as drafted.*")

    tone = answers.get('q5', 'Not specified')
    st.markdown(f"*Tone: {tone}*")

    edited = st.text_area("Your response:", value=draft_text, height=320, key="draft_edit")

    st.markdown("**Download options**")
    c1, c2, c3 = st.columns(3)

    with c1:
        doc = DocxDocument()
        doc.add_paragraph(edited)
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        st.download_button(
            "⬇ Word — edit in your voice",
            data=buf,
            file_name="FRED_Draft_Response.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    with c2:
        lines = [l.strip() for l in edited.split('\n') if l.strip()]
        bullets = '\n'.join(f'• {l}' for l in lines)
        st.download_button(
            "⬇ Bullets — write yourself",
            data=bullets,
            file_name="FRED_Key_Points.txt",
            mime="text/plain"
        )

    with c3:
        st.download_button(
            "⬇ Copy as drafted",
            data=edited,
            file_name="FRED_Response.txt",
            mime="text/plain"
        )

    st.markdown(f"""
    <div class="dignity-flag">
        Before sending — consider whether pressing this point serves your child's
        immediate situation or whether the relationship warrants a different approach.
        FRED holds these findings regardless. You decide when and how to use them.
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# RENDER — FULL EHCP REPORT
# ─────────────────────────────────────────────

def render_full_report(report_results, section_e_results, answers):
    st.markdown("---")
    st.markdown("## Your FRED report")

    ehcp_status = answers.get('q2', 'Unknown')
    process_stage = answers.get('q3', 'Not specified')

    st.markdown(f"""
    <div style="background:#F4F6F7;border-radius:8px;padding:13px 17px;margin:10px 0;font-size:13px;">
        <strong>Status:</strong> {ehcp_status} &nbsp;|&nbsp;
        <strong>Stage:</strong> {process_stage}
    </div>
    """, unsafe_allow_html=True)

    if 'final' in ehcp_status.lower():
        st.warning(
            "**Final EHCP pathway active.** This plan has been formally issued by the LA. "
            "All findings below inform what you raise at annual review — not changes to the current document."
        )

    render_traffic_legend()

    if section_e_results:
        st.markdown("### Section E — Outcomes")
        for r in section_e_results:
            has_issues = r['unlawful_failures'] or r['best_practice_gaps']
            if not has_issues:
                st.markdown(f"""
                <div class="audit-header-green">Outcome {r['outcome_number']} — compliant</div>
                <div class="audit-body">
                    <div class="compliant-flag">✓ Meets the SMART standard.</div>
                    <em>"{r['outcome_text'][:200]}"</em>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="audit-header-red">Outcome {r['outcome_number']} — review required</div>
                <div class="audit-body">
                    <em>"{r['outcome_text'][:200]}"</em><br><br>
                    {''.join(f'<div class="unlawful-flag">⚠ {f}</div>' for f in r['unlawful_failures'])}
                    {''.join(f'<div class="bestpractice-flag">◉ {g}</div>' for g in r['best_practice_gaps'])}
                </div>""", unsafe_allow_html=True)
        st.markdown("---")

    if report_results:
        st.markdown("### Section F — Provision")
        unlawful_count = sum(1 for r in report_results if r['unlawful_deficiencies'] or r['additional_patterns'])
        compliant_count = sum(1 for r in report_results if r['is_compliant'])
        total = len(report_results)

        c1, c2, c3 = st.columns(3)
        c1.metric("Total entries", total)
        c2.metric("Lawful requirement not met", unlawful_count,
                 delta=f"{unlawful_count} entries" if unlawful_count > 0 else None,
                 delta_color="inverse")
        c3.metric("Compliant", compliant_count)
        st.markdown("<br>", unsafe_allow_html=True)

        for result in report_results:
            if result['is_compliant']:
                st.markdown(f"""
                <div class="audit-header-green">Provision {result['entry_number']} — compliant</div>
                <div class="audit-body">
                    <div class="compliant-flag">✓ Meets the lawful specification standard. Use as benchmark at annual review.</div>
                    <em>"{result['entry_text'][:300]}"</em>
                </div>""", unsafe_allow_html=True)
            else:
                has_unlawful = bool(result['unlawful_deficiencies'] or result['additional_patterns'])
                hclass = 'audit-header-red' if has_unlawful else 'audit-header-amber'
                hlabel = 'lawful requirement not met' if has_unlawful else 'best practice gap'
                st.markdown(f"""
                <div class="{hclass}">Provision {result['entry_number']} — {hlabel}</div>
                <div class="audit-body">
                <em>"{result['entry_text'][:300]}{'...' if len(result['entry_text']) > 300 else ''}"</em><br><br>
                """, unsafe_allow_html=True)
                if result['unlawful_deficiencies']:
                    st.markdown("**Lawful requirements not met**")
                    for d in result['unlawful_deficiencies']:
                        st.markdown(f'<div class="unlawful-flag">⚠ {d}</div>', unsafe_allow_html=True)
                if result['additional_patterns']:
                    st.markdown("**Additional pattern identified**")
                    for p in result['additional_patterns']:
                        st.markdown(f'<div class="pattern-flag">◈ {p}</div>', unsafe_allow_html=True)
                if result['best_practice_gaps']:
                    st.markdown("**Best practice gaps**")
                    for g in result['best_practice_gaps']:
                        st.markdown(f'<div class="bestpractice-flag">◉ {g}</div>', unsafe_allow_html=True)
                if result['ofsted_principle']:
                    op = result['ofsted_principle']
                    st.markdown("**Inspection framework note**")
                    st.markdown(f'<div class="bestpractice-flag"><strong>{op["area"]}:</strong> {op["principle"]}</div>', unsafe_allow_html=True)
                if result['policy_gaps']:
                    st.markdown("**School policy cross-reference**")
                    for pg in result['policy_gaps']:
                        st.markdown(f'<div class="pattern-flag">◈ {pg}</div>', unsafe_allow_html=True)
                if result['required_specification']:
                    st.markdown("**Required specification**")
                    for spec in result['required_specification']:
                        st.markdown(f"— {spec}")
                if result['tactical_advice']:
                    st.markdown("**Tactical advice**")
                    for advice in result['tactical_advice']:
                        st.markdown(f'<div class="tactical-flag">→ {advice}</div>', unsafe_allow_html=True)
                if result['unlawful_deficiencies']:
                    st.markdown("""
                    <div class="anchor-line">If it is not specified and evidenced, it is not lawfully enforceable under the Children and Families Act 2014.</div>
                    <div class="evidence-line">Lack of evidence is evidence of lack.</div>
                    """, unsafe_allow_html=True)
                st.markdown("</div><br>", unsafe_allow_html=True)

        st.info("Upload the expert reports (EP, OT, or SLT) to begin the Cross-Reference report.")

    st.markdown(f"""
    <div class="review-capture">
        <strong>Hold this for your annual review.</strong><br>
        Enter your next annual review date and FRED will begin working through
        these findings with you in the weeks before it.
    </div>
    """, unsafe_allow_html=True)
    st.date_input("Annual review date (optional):", key="review_date")

    unlawful_total = sum(len(r['unlawful_deficiencies']) + len(r['additional_patterns']) for r in report_results)
    if unlawful_total > 0:
        st.markdown(f"""
        <div class="subscription-signal">
            <strong>FRED has identified {unlawful_total} provision failures in this plan.</strong><br><br>
            The full FRED service adds correspondence intelligence — intent detection,
            three finding briefings, vacuum detection, and the hold option.
            It also holds your documents, drafts your emails, and prepares you
            for every meeting and annual review.<br><br>
            Annual subscription — from £XX per year.
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DOCUMENT GENERATION
# ─────────────────────────────────────────────

def generate_docx(report_results, section_e_results, answers):
    doc = DocxDocument()
    RED_C = RGBColor(0xC0, 0x39, 0x2B)
    AMBER_C = RGBColor(0xD4, 0xA0, 0x17)
    GREEN_C = RGBColor(0x1E, 0x84, 0x49)
    BLUE_C = RGBColor(0x1B, 0x4F, 0x72)
    PURPLE_C = RGBColor(0x8E, 0x44, 0xAD)

    def h(text, level=1, c=RGBColor(0x1B, 0x4F, 0x72)):
        heading = doc.add_heading(text, level=level)
        if heading.runs:
            heading.runs[0].font.color.rgb = c
        return heading

    def p(text, c=RGBColor(0,0,0), size=10, bold=False, italic=False):
        para = doc.add_paragraph()
        run = para.add_run(text)
        run.font.color.rgb = c
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        return para

    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("FRED")
    r.font.size = Pt(36); r.font.bold = True; r.font.color.rgb = BLUE_C
    s = doc.add_paragraph()
    s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    s.add_run("Families' Rights and Entitlements Directory — EHCP Report").font.color.rgb = RGBColor(0x2E, 0x86, 0xC1)
    doc.add_paragraph(f"Status: {answers.get('q2','Unknown')} | Beta v0.6")
    doc.add_paragraph("FRED provides information to help you understand the language of your child's plan. It does not constitute legal advice.")
    doc.add_page_break()
    h("Output key", level=2)
    p("● Red — lawful requirement not met.", RED_C)
    p("● Amber — best practice gap.", AMBER_C)
    p("● Green — compliant.", GREEN_C)
    doc.add_paragraph()

    if section_e_results:
        h("Section E — Outcomes")
        for r_ in section_e_results:
            c_ = RED_C if r_['unlawful_failures'] else (AMBER_C if r_['best_practice_gaps'] else GREEN_C)
            h(f"Outcome {r_['outcome_number']}", level=2, c=c_)
            p(f'"{r_["outcome_text"]}"', italic=True)
            for f_ in r_['unlawful_failures']:
                p(f"⚠ {f_}", RED_C)
            for g_ in r_['best_practice_gaps']:
                p(f"◉ {g_}", AMBER_C)
            if not r_['unlawful_failures'] and not r_['best_practice_gaps']:
                p("✓ Meets SMART criteria.", GREEN_C)
        doc.add_page_break()

    if report_results:
        h("Section F — Provision")
        for result in report_results:
            c_ = (GREEN_C if result['is_compliant'] else RED_C if result['unlawful_deficiencies'] else AMBER_C)
            label = ("Compliant" if result['is_compliant'] else "Lawful requirement not met" if result['unlawful_deficiencies'] else "Best practice gap")
            h(f"Provision {result['entry_number']} — {label}", level=2, c=c_)
            p(f'"{result["entry_text"][:400]}"', italic=True)
            if result['unlawful_deficiencies']:
                h("Lawful requirements not met", level=3, c=RED_C)
                for d in result['unlawful_deficiencies']:
                    p(f"⚠ {d}", RED_C)
            if result['additional_patterns']:
                h("Additional pattern identified", level=3, c=PURPLE_C)
                for pt in result['additional_patterns']:
                    p(f"◈ {pt}", PURPLE_C)
            if result['best_practice_gaps']:
                h("Best practice gaps", level=3, c=AMBER_C)
                for g in result['best_practice_gaps']:
                    p(f"◉ {g}", AMBER_C)
            if result['required_specification']:
                h("Required specification", level=3)
                for spec in result['required_specification']:
                    doc.add_paragraph(spec, style='List Bullet')
            if result['tactical_advice']:
                h("Tactical advice", level=3, c=BLUE_C)
                for advice in result['tactical_advice']:
                    p(f"→ {advice}", BLUE_C)
            if result['unlawful_deficiencies']:
                p("If it is not specified and evidenced, it is not lawfully enforceable under the Children and Families Act 2014. Lack of evidence is evidence of lack.", BLUE_C, bold=True, italic=True)
            doc.add_paragraph()

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def generate_pdf(report_results, section_e_results, answers):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    brand = HexColor('#1B4F72')
    red = HexColor('#C0392B')
    amber = HexColor('#D4A017')
    green = HexColor('#1E8449')
    purple = HexColor('#8E44AD')

    def ps(name, parent='Normal', **kw):
        return ParagraphStyle(name, parent=styles[parent], **kw)

    h1 = ps('H1', 'Heading1', textColor=brand, fontSize=16, spaceAfter=6)
    h2r = ps('H2R', 'Heading2', textColor=red, fontSize=13, spaceAfter=4)
    h2a = ps('H2A', 'Heading2', textColor=amber, fontSize=13, spaceAfter=4)
    h2g = ps('H2G', 'Heading2', textColor=green, fontSize=13, spaceAfter=4)
    h3 = ps('H3', 'Heading3', fontSize=11, spaceAfter=4)
    body = ps('Body', fontSize=10, spaceAfter=4, leading=15)
    red_s = ps('RS', fontSize=10, textColor=red, leftIndent=10, spaceAfter=3, leading=14)
    amb_s = ps('AS', fontSize=10, textColor=amber, leftIndent=10, spaceAfter=3, leading=14)
    grn_s = ps('GS', fontSize=10, textColor=green, leftIndent=10, spaceAfter=3, leading=14)
    pur_s = ps('PS', fontSize=10, textColor=purple, leftIndent=10, spaceAfter=3, leading=14)
    tac_s = ps('TS', fontSize=10, textColor=brand, leftIndent=10, spaceAfter=3, leading=14)
    anc_s = ps('ANS', fontSize=10, textColor=brand, fontName='Helvetica-BoldOblique', spaceAfter=8, leading=14)

    story = []
    story.append(Paragraph("FRED", ps('TT', 'Title', textColor=brand, fontSize=32)))
    story.append(Paragraph("Families' Rights and Entitlements Directory", h1))
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph(f"EHCP Report | Status: {answers.get('q2','Unknown')} | Beta v0.6", body))
    story.append(Paragraph("Not legal advice.", body))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("● Red — lawful requirement not met.", red_s))
    story.append(Paragraph("● Amber — best practice gap.", amb_s))
    story.append(Paragraph("● Green — compliant.", grn_s))
    story.append(Spacer(1, 5*mm))

    if section_e_results:
        story.append(Paragraph("Section E — Outcomes", h1))
        for r_ in section_e_results:
            h_ = h2r if r_['unlawful_failures'] else (h2a if r_['best_practice_gaps'] else h2g)
            story.append(Paragraph(f"Outcome {r_['outcome_number']}", h_))
            story.append(Paragraph(f'<i>"{r_["outcome_text"][:300]}"</i>', body))
            for f_ in r_['unlawful_failures']:
                story.append(Paragraph(f"⚠ {f_}", red_s))
            for g_ in r_['best_practice_gaps']:
                story.append(Paragraph(f"◉ {g_}", amb_s))
            story.append(Spacer(1, 3*mm))

    if report_results:
        story.append(Paragraph("Section F — Provision", h1))
        for result in report_results:
            h_ = (h2g if result['is_compliant'] else h2r if result['unlawful_deficiencies'] else h2a)
            label = ("Compliant" if result['is_compliant'] else "Lawful requirement not met" if result['unlawful_deficiencies'] else "Best practice gap")
            story.append(Paragraph(f"Provision {result['entry_number']} — {label}", h_))
            story.append(Paragraph(f'<i>"{result["entry_text"][:400]}"</i>', body))
            if result['unlawful_deficiencies']:
                story.append(Paragraph("Lawful requirements not met", h3))
                for d in result['unlawful_deficiencies']:
                    story.append(Paragraph(f"⚠ {d}", red_s))
            if result['additional_patterns']:
                story.append(Paragraph("Additional pattern identified", h3))
                for pt in result['additional_patterns']:
                    story.append(Paragraph(f"◈ {pt}", pur_s))
            if result['best_practice_gaps']:
                story.append(Paragraph("Best practice gaps", h3))
                for g in result['best_practice_gaps']:
                    story.append(Paragraph(f"◉ {g}", amb_s))
            if result['required_specification']:
                story.append(Paragraph("Required specification", h3))
                for spec in result['required_specification']:
                    story.append(Paragraph(f"• {spec}", body))
            if result['tactical_advice']:
                story.append(Paragraph("Tactical advice", h3))
                for advice in result['tactical_advice']:
                    story.append(Paragraph(f"→ {advice}", tac_s))
            if result['unlawful_deficiencies']:
                story.append(Paragraph("If it is not specified and evidenced, it is not lawfully enforceable under the Children and Families Act 2014. Lack of evidence is evidence of lack.", anc_s))
            story.append(Spacer(1, 5*mm))

    doc.build(story)
    buf.seek(0)
    return buf

# ─────────────────────────────────────────────
# SURVEY
# ─────────────────────────────────────────────

def render_survey():
    st.markdown("---")
    st.markdown("### Beta feedback")
    st.markdown(
        "Takes about two minutes. Every answer goes directly to the team building FRED. "
        "Your feedback shapes the final product."
    )
    st.markdown(f"""
    <div style='text-align:center;padding:20px;background:#F4F6F7;
        border-radius:10px;margin:12px 0;'>
        <div style='font-size:15px;font-weight:500;color:#1A252F;margin-bottom:8px;'>
            Open the feedback form
        </div>
        <div style='font-size:13px;color:#717D7E;margin-bottom:16px;line-height:1.6;'>
            Two minutes. Shapes the next version of FRED directly.
        </div>
        <a href='https://tally.so/r/b5NVAE' target='_blank'
            style='background:#1B4F72;color:white;text-decoration:none;
            padding:12px 28px;border-radius:8px;font-size:14px;font-weight:500;'>
            Give feedback →
        </a>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# LANDING PAGE
# ─────────────────────────────────────────────

def render_landing():
    st.markdown(f"""
    <div class="fred-nav">
        <div class="fred-nav-logo">FRED</div>
        <div class="fred-nav-links">
            <span class="fred-nav-link">How it works</span>
            <span class="fred-nav-link">Pricing</span>
            <span class="fred-nav-link">About</span>
        </div>
    </div>
    <div class="fred-beta">Beta — design and functionality are actively being developed. Your feedback shapes the final product.</div>
    <div class="fred-hero">
        <div class="fred-big">FRED</div>
        <div class="fred-full">Families' Rights and Entitlements Directory</div>
        <div class="fred-hero-title">Your child's plan should work for <span>your child.</span></div>
        <div class="fred-hero-origin">Built by a parent who learned the hard way — so you don't have to.</div>
        <div class="fred-hero-sub">FRED reads your child's EHCP, identifies every provision that isn't lawfully enforceable, and tells you exactly what to do about it — in plain language, at any hour.</div>
        <div class="fred-hero-flex">Our service is flexible — either a <span>one-off report on your EHCP and provision</span> or a <span>full subscription</span> that holds your child's complete journey.</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📋  Get my report", key="hero_get_report"):
            st.session_state.stage = 'upload'
            st.rerun()

    st.markdown(f"""
    <div class="fred-hero-cta">
        <div class="fred-btn-reassure">Upload first. Decide after. Your report is ready before you pay.</div>
        <div class="fred-btn-pricing">From £XX for the full report — or <span>see our subscription plans</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="fred-divider">', unsafe_allow_html=True)

    st.markdown("""
    <div class="fred-section">
        <div class="fred-sec-label">How it works</div>
        <div class="fred-sec-title">Everything you need to know.</div>
        <ul class="fred-bullets">
            <li><span class="fred-bdot"></span>Gather your EHCP, EP report, or any school document — PDF or Word is fine</li>
            <li><span class="fred-bdot"></span>Answer five short questions about your situation — draft or final plan, upcoming dates, how things stand with the school</li>
            <li><span class="fred-bdot"></span>Receive a full report — every provision assessed against the Children and Families Act 2014, the SEND Code of Practice 2015, and your school's own policy where provided</li>
            <li><span class="fred-bdot"></span>Download your report as Word or PDF, whichever works for you</li>
            <li><span class="fred-bdot"></span><span>Then with a subscription you can add school emails, meeting transcripts, and specialist reports to <span class="fred-sub-bullet">build the complete picture</span></span></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📋  Get my report", key="how_get_report"):
            st.session_state.stage = 'upload'
            st.rerun()
    st.markdown('<div class="fred-upload-wrap"><span class="fred-upload-note">PDF or Word · processed privately · not stored or shared</span></div>', unsafe_allow_html=True)

    st.markdown('<hr class="fred-divider">', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="fred-section">
        <div class="fred-sec-label" style="text-align:center;">The traffic light system</div>
        <div class="fred-sec-title">You'll always know where you stand.</div>
        <div class="fred-traffic-legend">
            <div class="fred-trow"><div class="fred-tdot tdot-red"></div>
                <div class="fred-ttext"><strong>Red — lawful requirement not met.</strong> Must be addressed at annual review.</div></div>
            <div class="fred-trow"><div class="fred-tdot tdot-amber"></div>
                <div class="fred-ttext"><strong>Amber — best practice gap.</strong> Worth raising at annual review.</div></div>
            <div class="fred-trow"><div class="fred-tdot tdot-green"></div>
                <div class="fred-ttext"><strong>Green — compliant.</strong> Use as benchmark when challenging non-compliant entries.</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="fred-divider">', unsafe_allow_html=True)

    st.markdown("""
    <div class="fred-section">
        <div class="fred-sec-label" style="text-align:center;">Pricing</div>
        <div class="fred-sec-title" style="text-align:center;">Start with what you need.</div>
        <div class="fred-sec-sub">No hidden charges. Your report is ready before you purchase.</div>
        <div class="fred-pricing-grid">
            <div class="fred-price-card">
                <div class="fred-price-name">One-off report</div>
                <div class="fred-price-amount">£XX</div>
                <div class="fred-price-period">single purchase · no commitment</div>
                <ul class="fred-price-features">
                    <li>Full Section F enforceability report</li>
                    <li>Section E SMART outcomes check</li>
                    <li>Traffic light findings — red, amber, green</li>
                    <li>Tactical advice for every finding</li>
                    <li>Downloadable — Word and PDF</li>
                </ul>
            </div>
            <div class="fred-price-card featured">
                <div class="fred-price-badge">Best value</div>
                <div class="fred-price-name">Annual subscription</div>
                <div class="fred-price-amount">£XX</div>
                <div class="fred-price-period">per year · less than £X per week</div>
                <div class="fred-price-first">Includes your report from day one. Year two at a reduced renewal rate.</div>
                <ul class="fred-price-features">
                    <li>Full report included</li>
                    <li>Document vault — all documents held</li>
                    <li>Correspondence briefings — three findings, intent detection</li>
                    <li>Email support — drafted and calibrated</li>
                    <li>Meeting preparation and script</li>
                    <li>Post-meeting summary emails</li>
                    <li>Annual review preparation pack</li>
                </ul>
            </div>
            <div class="fred-price-card">
                <div class="fred-price-name">Monthly</div>
                <div class="fred-price-amount">£XX</div>
                <div class="fred-price-period">per month from month two · cancel anytime</div>
                <div class="fred-price-first">First month £XX — includes your report.</div>
                <ul class="fred-price-features">
                    <li>Report included in first month</li>
                    <li>Everything in the full service</li>
                    <li>No annual commitment</li>
                    <li>Cancel anytime</li>
                </ul>
            </div>
        </div>
        <div style="font-size:11px;color:#717D7E;text-align:center;font-style:italic;margin-top:8px;">Prices shown as placeholders — confirmed at launch.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="fred-divider">', unsafe_allow_html=True)

    st.markdown("""
    <div class="fred-section">
        <div class="fred-sec-label">From a parent</div>
        <div class="fred-sec-title">You already know something isn't right.</div>
        <div class="fred-quote-box">
            <div class="fred-quote">"I spent three years learning what I should have been told on day one. The language in my son's plan looked like provision. It wasn't. FRED would have shown me that in minutes."</div>
            <div class="fred-quote-attr">— Founder, FRED</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="fred-divider">', unsafe_allow_html=True)

    st.markdown("""
    <div class="fred-section">
        <div class="fred-sec-label">Questions</div>
        <div class="fred-sec-title">Straightforward answers.</div>
        <div class="fred-faq-item">
            <div class="fred-faq-q">Is FRED legal advice?</div>
            <div class="fred-faq-a">No. FRED provides information to help you understand the language of your child's plan and what the law says about it. It does not replace a solicitor or independent advocate. All guidance is referenced to the Children and Families Act 2014 and the SEND Code of Practice 2015.</div>
        </div>
        <div class="fred-faq-item">
            <div class="fred-faq-q">When do I pay?</div>
            <div class="fred-faq-a">After FRED has read your plan and you have seen a preview of what it found. You upload first, see a finding, then decide whether to purchase the full report. Nothing is charged until you choose to proceed.</div>
        </div>
        <div class="fred-faq-item">
            <div class="fred-faq-q">Is my data private?</div>
            <div class="fred-faq-a">Yes. For the one-off report your document is read during your session only — not stored or retained. In the full service your documents are held in your own private vault, accessible only to you.</div>
        </div>
        <div class="fred-faq-item">
            <div class="fred-faq-q">What if I don't have an EHCP yet?</div>
            <div class="fred-faq-a">FRED works with EP reports, OT reports, SALT reports, and school correspondence. If you are at the needs assessment stage or have had an assessment refused, FRED can show you what the Children and Families Act 2014 says about your situation and what questions to ask.</div>
        </div>
        <div class="fred-faq-item">
            <div class="fred-faq-q">What documents can I upload?</div>
            <div class="fred-faq-a">Any PDF or Word document — EHCP, EP report, OT report, school emails, meeting transcripts, school SEND policy, behaviour policy, or accessibility plan.</div>
        </div>
        <div class="fred-faq-item">
            <div class="fred-faq-q">Can I cancel my subscription?</div>
            <div class="fred-faq-a">Yes. Monthly subscriptions cancel anytime. Annual subscriptions run twelve months. Year two renewals are at a reduced rate as the report is not repeated.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="fred-divider">', unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;padding:28px 0;background:var(--color-background-secondary);border-radius:10px;margin:16px 0;">
        <div style="font-size:17px;font-weight:500;color:var(--color-text-primary);margin-bottom:6px;">Ready to see what your child's plan actually says?</div>
        <div style="font-size:13px;color:var(--color-text-secondary);margin-bottom:16px;">Upload your document. See a finding. Decide after.</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📋  Get my report", key="bottom_get_report"):
            st.session_state.stage = 'upload'
            st.rerun()

    st.markdown(f"""
    <div class="fred-footer">
        <div class="fred-footer-logo">FRED</div>
        <div class="fred-footer-text">
            Families' Rights and Entitlements Directory<br>
            Not legal advice · All data private and secure · Built for families navigating the EHCP process<br><br>
            Privacy · Terms · Contact
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# APP FLOW
# ─────────────────────────────────────────────

if st.session_state.stage == 'landing':
    render_landing()

elif st.session_state.stage == 'upload':

    st.markdown(f"""
    <div class="fred-header-bar">
        <div class="fred-header-title">FRED</div>
        <div class="fred-header-sub">Families' Rights and Entitlements Directory</div>
    </div>
    <div class="fred-beta-notice">
        <strong>Beta v0.6</strong> — Design and functionality are actively being developed.
        FRED provides information to help you understand the language of your child's plan.
        It does not constitute legal advice.
    </div>
    """, unsafe_allow_html=True)

    render_traffic_legend()

    st.markdown("### Get my report")
    st.markdown("Upload any document — EHCP, EP report, school email, meeting transcript, or school policy. PDF or Word. FRED works out what it is.")

    main_file = st.file_uploader(
        "Upload your main document",
        type=['pdf', 'docx', 'doc'],
        key='main_upload',
        help="Processed privately during this session only. Not stored or shared."
    )

    st.markdown("""
    <div class="upload-tip">
        <strong>Email:</strong> Open it, select print, choose Save as PDF.<br>
        <strong>Password protected document:</strong> Open it, select print, save as PDF — removes the lock on most LA documents.
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Add another document — optional"):
        st.markdown("School policy, specialist report, email, or transcript. FRED cross-references everything.")
        extra_1 = st.file_uploader("Additional document", type=['pdf','docx','doc'], key='extra_1')
        extra_2 = st.file_uploader("Another document", type=['pdf','docx','doc'], key='extra_2')
        extra_3 = st.file_uploader("Another document", type=['pdf','docx','doc'], key='extra_3')

    if st.session_state.is_subscriber or st.session_state.email_captured:
        st.markdown("---")
        st.markdown(f'<div class="fred-sub-badge">✓ Subscription active — correspondence intelligence enabled</div>', unsafe_allow_html=True)
        st.markdown("### Upload correspondence (subscription)")
        st.markdown("Upload the last two emails for active analysis. Older correspondence goes in history.")

        col_a, col_b = st.columns(2)
        with col_a:
            active_1 = st.file_uploader("Most recent email (PDF)", type=['pdf','docx','doc'], key='active_1')
            active_2 = st.file_uploader("Previous email (PDF)", type=['pdf','docx','doc'], key='active_2')
        with col_b:
            st.markdown("**Historical correspondence (optional)**")
            st.markdown("*Older emails — used for background context and pattern detection*")
            hist_1 = st.file_uploader("Older email 1", type=['pdf','docx','doc'], key='hist_1')
            hist_2 = st.file_uploader("Older email 2", type=['pdf','docx','doc'], key='hist_2')
            hist_3 = st.file_uploader("Older email 3", type=['pdf','docx','doc'], key='hist_3')
            transcript = st.file_uploader("Meeting transcript (optional)", type=['pdf','docx','doc'], key='transcript')

    if main_file:
        with st.spinner("Fred is reading your document..."):
            text, error = read_file(main_file)
            if error:
                st.error(error)
            else:
                sections = identify_sections(text)
                st.session_state.extracted_sections = sections
                st.session_state.raw_text = text
                if sections:
                    st.success(f"Document read. Sections identified: {', '.join(sorted(sections.keys()))}.")
                else:
                    st.warning("FRED could not identify standard EHCP sections. Paste Section F text below.")
                    manual_f = st.text_area("Paste Section F provision text here:", height=180)
                    if manual_f:
                        st.session_state.extracted_sections['F'] = manual_f

        for i, extra in enumerate([extra_1, extra_2, extra_3] if not (st.session_state.is_subscriber or st.session_state.email_captured) else [], 1):
            if extra:
                with st.spinner(f"Reading additional document {i}..."):
                    extra_text, extra_error = read_file(extra)
                    if extra_error:
                        st.warning(f"Document {i}: {extra_error}")
                    else:
                        dtype = detect_doc_type(extra_text)
                        if dtype == 'policy':
                            st.session_state.policy_text = extra_text
                            st.success("School policy read — ready for cross-reference.")
                        elif dtype == 'email':
                            st.session_state.active_emails.append(extra_text)
                            st.success("Email read.")
                        elif dtype == 'transcript':
                            st.session_state.transcript_text = extra_text
                            st.success("Transcript read.")

        if st.session_state.is_subscriber or st.session_state.email_captured:
            active_emails = []
            for af in [active_1, active_2]:
                if af:
                    t, e = read_file(af)
                    if t:
                        active_emails.append(t)
            st.session_state.active_emails = active_emails

            history_texts = []
            for hf in [hist_1, hist_2, hist_3]:
                if hf:
                    t, e = read_file(hf)
                    if t:
                        history_texts.append(t)
            st.session_state.history_emails = history_texts

            if transcript:
                t, e = read_file(transcript)
                if t:
                    st.session_state.transcript_text = t
                    st.success("Transcript read — primary record of what was said.")

            if history_texts:
                vacuum_count = 0
                for ht in history_texts:
                    vacuum_count += len(detect_vacuum_statements(ht))
                if vacuum_count > 0:
                    st.info(f"FRED has read {len(history_texts)} historical email(s). {vacuum_count} statement(s) implying undocumented history identified and held in vault.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back to home", key="upload_back"):
                st.session_state.stage = 'landing'
                st.rerun()
        with col2:
            if st.button("Continue →", key="upload_continue"):
                st.session_state.stage = 'questions'
                st.rerun()

elif st.session_state.stage == 'questions':

    st.markdown(f"""
    <div class="fred-header-bar">
        <div class="fred-header-title">FRED</div>
        <div class="fred-header-sub">Families' Rights and Entitlements Directory</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### A few quick questions")

    q1 = st.selectbox("1. What have you uploaded?", options=[
        "My child's EHCP", "An EP report", "A specialist report (OT, SALT, or other)",
        "School or LA correspondence", "Meeting notes or transcript", "More than one of the above",
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
        "No upcoming dates right now", "Yes — annual review",
        "Yes — meeting with school or LA", "Yes — LA deadline",
    ])
    st.session_state.answers['q4'] = q4
    if q4 != "No upcoming dates right now":
        upcoming_date = st.date_input("When is this?")
        st.session_state.answers['upcoming_date'] = str(upcoming_date)

    q5 = st.selectbox("5. How would you describe your current relationship with the school or LA?", options=[
        "Warm and collaborative", "Constructive but cautious",
        "Professionally firm", "Formally assertive", "Rights-based and formal",
    ])
    st.session_state.answers['q5'] = q5

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back", key="q_back"):
            st.session_state.stage = 'upload'
            st.rerun()
    with col2:
        if st.button("Run report →", key="q_continue"):
            st.session_state.stage = 'processing'
            st.rerun()

elif st.session_state.stage == 'processing':

    st.markdown(f"""
    <div class="fred-header-bar">
        <div class="fred-header-title">FRED</div>
        <div class="fred-header-sub">Families' Rights and Entitlements Directory</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Fred is working...")

    sections = st.session_state.extracted_sections
    policy_text = st.session_state.get('policy_text', '')
    active_emails = st.session_state.get('active_emails', [])
    transcript_text = st.session_state.get('transcript_text', '')

    report_results = []
    section_e_results = []

    with st.spinner("Reading Section F provision entries..."):
        if 'F' in sections:
            entries = extract_entries(sections['F'])
            for i, entry in enumerate(entries):
                if len(entry.strip()) > 20:
                    report_results.append(audit_entry(entry, i+1, policy_text))

    with st.spinner("Checking Section E outcomes..."):
        if 'E' in sections:
            section_e_results = audit_section_e(sections['E'])

    three_findings = None
    intent_result = None
    tone_read = None
    on_record = None
    compliance_checks = None
    what_if_matches = None
    draft_email = None

    if active_emails and (st.session_state.is_subscriber or st.session_state.email_captured):
        with st.spinner("Reading correspondence..."):
            combined_active = '\n\n---\n\n'.join(active_emails)
            intent_result = detect_intent(combined_active)
            three_findings = generate_three_findings(combined_active, sections, transcript_text)
            tone_read = generate_tone_read(intent_result, combined_active)
            on_record = generate_on_the_record(combined_active)
            compliance_checks = generate_ehcp_compliance_check(combined_active, sections)
            what_if_matches = match_what_if_scenarios(combined_active)
            draft_email = generate_post_meeting_email({'contradictions': [], 'deflected': []}, st.session_state.answers)

    sneak_peek = None
    for r in report_results:
        if r['unlawful_deficiencies']:
            sneak_peek = r
            break
    if sneak_peek is None and report_results:
        sneak_peek = report_results[0]

    st.session_state.report_results = report_results
    st.session_state.section_e_results = section_e_results
    st.session_state.three_findings = three_findings
    st.session_state.intent_result = intent_result
    st.session_state.tone_read = tone_read
    st.session_state.on_record = on_record
    st.session_state.compliance_checks = compliance_checks
    st.session_state.what_if_matches = what_if_matches
    st.session_state.draft_email = draft_email
    st.session_state.sneak_peek_result = sneak_peek
    st.session_state.stage = 'preview'
    st.rerun()

elif st.session_state.stage == 'preview':

    st.markdown(f"""
    <div class="fred-header-bar">
        <div class="fred-header-title">FRED</div>
        <div class="fred-header-sub">Families' Rights and Entitlements Directory</div>
    </div>
    """, unsafe_allow_html=True)

    sneak_peek = st.session_state.sneak_peek_result

    if sneak_peek:
        unlawful = sneak_peek['unlawful_deficiencies'][:3]
        entry_preview = sneak_peek['entry_text'][:200]
        st.markdown(f"""
        <div class="fred-sneak-header" style="background:{BRAND_BLUE};color:white;
            padding:10px 16px;border-radius:6px 6px 0 0;font-size:13px;font-weight:500;">
            FRED has read your plan — here is one finding
        </div>
        <div style="padding:14px 16px;background:white;border:1px solid #D5D8DC;border-top:none;">
            <div style="font-size:12px;color:{GREY};font-style:italic;margin-bottom:10px;line-height:1.5;">
                "{entry_preview}{'...' if len(sneak_peek['entry_text']) > 200 else ''}"
            </div>
            {''.join(f'<div class="unlawful-flag">⚠ {d}</div>' for d in unlawful)}
            <div class="anchor-line">If it is not specified and evidenced, it is not lawfully enforceable under the Children and Families Act 2014.</div>
            <div class="evidence-line">Lack of evidence is evidence of lack.</div>
        </div>
        <div style="background:#F4F6F7;padding:16px;text-align:center;
            border:1px solid #D5D8DC;border-top:none;border-radius:0 0 6px 6px;">
            <div style="font-size:14px;font-weight:500;color:#1A252F;margin-bottom:4px;">
                This is one entry from Section F of your plan
            </div>
            <div style="font-size:12px;color:{GREY};margin-bottom:10px;line-height:1.6;max-width:360px;margin-left:auto;margin-right:auto;">
                Your full report covers every provision entry across Section F and Section E outcomes —
                with tactical advice and required specification for each finding.
            </div>
            <div style="font-size:13px;font-weight:500;color:{BRAND_BLUE};margin-bottom:12px;">
                Your report is ready.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Get your full report — beta is free")
    st.markdown(
        "FRED is in beta. Enter your email to access your full report and the complete service. "
        "No payment required during beta."
    )

    st.markdown(f"""
    <div style='text-align:center;padding:20px;background:#F4F6F7;
        border-radius:10px;margin:12px 0;'>
        <div style='font-size:14px;color:#2C3E50;margin-bottom:16px;line-height:1.6;'>
            Enter your email to unlock your full report instantly.
            No payment. No commitment. Beta access is free.
        </div>
        <a href='https://tally.so/r/Ek8kqo' target='_blank'
            style='background:#1B4F72;color:white;text-decoration:none;
            padding:13px 32px;border-radius:8px;font-size:15px;font-weight:500;
            display:inline-block;'>
            Get full access →
        </a>
        <div style='font-size:11px;color:#717D7E;margin-top:10px;font-style:italic;'>
            Your email is used to send your report only. Not shared with third parties.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("*Already submitted your email? Click below to continue to your full report.*")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back", key="preview_back"):
            st.session_state.stage = 'questions'
            st.rerun()
    with col2:
        if st.button("I have submitted my email — show my report →", key="bypass_email"):
            st.session_state.email_captured = True
            st.session_state.is_subscriber = True
            st.session_state.stage = 'results'
            st.rerun()

elif st.session_state.stage == 'results':

    st.markdown(f"""
    <div class="fred-header-bar">
        <div class="fred-header-title">FRED</div>
        <div class="fred-header-sub">Families' Rights and Entitlements Directory</div>
    </div>
    """, unsafe_allow_html=True)

    report_results = st.session_state.report_results
    section_e_results = st.session_state.get('section_e_results', [])
    answers = st.session_state.answers
    three_findings = st.session_state.get('three_findings')
    intent_result = st.session_state.get('intent_result')
    tone_read = st.session_state.get('tone_read', '')
    on_record = st.session_state.get('on_record', [])
    compliance_checks = st.session_state.get('compliance_checks', [])
    what_if_matches = st.session_state.get('what_if_matches', [])
    draft_email = st.session_state.get('draft_email', '')

    if three_findings is not None and intent_result is not None:
        render_three_findings(three_findings, tone_read, on_record, compliance_checks, what_if_matches, intent_result)
        if st.session_state.correspondence_action == 'draft':
            render_draft_with_options(draft_email, answers)
        st.markdown("---")

    if report_results or section_e_results:
        render_full_report(report_results, section_e_results, answers)

    st.markdown("---")
    st.markdown("### Download your report")
    c1, c2 = st.columns(2)
    with c1:
        docx_buf = generate_docx(report_results, section_e_results, answers)
        st.download_button("⬇ Download as Word (.docx)", data=docx_buf,
            file_name="FRED_Report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            help="Best for Windows and Microsoft Office users")
    with c2:
        pdf_buf = generate_pdf(report_results, section_e_results, answers)
        st.download_button("⬇ Download as PDF", data=pdf_buf,
            file_name="FRED_Report.pdf", mime="application/pdf",
            help="Best for Apple devices")

    st.markdown("---")
    st.markdown("### Add more documents")
    st.markdown("Upload emails, transcripts, or specialist reports to build the complete picture.")
    extra_post = st.file_uploader("Add a document", type=['pdf','docx','doc'], key='post_report_upload')
    if extra_post:
        with st.spinner("Reading..."):
            extra_text, extra_error = read_file(extra_post)
            if extra_error:
                st.warning(extra_error)
            else:
                dtype = detect_doc_type(extra_text)
                if dtype == 'email':
                    st.session_state.active_emails = [extra_text]
                    st.success("Email read. Go back to run the correspondence briefing.")
                elif dtype == 'transcript':
                    st.session_state.transcript_text = extra_text
                    st.success("Transcript read and added.")
                elif dtype == 'policy':
                    st.session_state.policy_text = extra_text
                    st.success("School policy read and added.")
                else:
                    st.success("Document read and added.")

    render_survey()

    st.markdown("---")
    if st.button("Start new report"):
        for key in list(defaults.keys()):
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

if st.session_state.stage not in ('landing',):
    st.markdown(
        f"<div style='text-align:center;color:{GREY};font-size:12px;padding-top:8px;'>"
        "FRED — Families' Rights and Entitlements Directory &nbsp;|&nbsp; "
        "Beta v0.6 &nbsp;|&nbsp; Not legal advice &nbsp;|&nbsp; "
        "Documents read during your session only — not stored or retained"
        "</div>",
        unsafe_allow_html=True
    )

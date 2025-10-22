# app.py
# Rate My Captain - Single-file Flask app implementing your finalized spec
# Run: python app.py  -> open http://127.0.0.1:5000
import os, uuid, hmac, hashlib, secrets, string
from datetime import datetime, timedelta, date
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from sqlalchemy import create_engine, select, Column, Integer, String, DateTime, ForeignKey, Text, and_, or_, func
from sqlalchemy.orm import Session, declarative_base, relationship

# ----------------------------
# Config
# ----------------------------
APP_NAME = "Rate My Captain"
DB_PATH = "app.db"
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
INVITE_CODE = os.getenv("INVITE_CODE", "fly-safe")
REVIEWER_PEPPER = os.getenv("REVIEWER_PEPPER", "dev-pepper-change-me")
MIN_DISPLAY_REVIEWS = 3

SUGGESTION_WINDOW_DAYS = 14
CONSENSUS_THRESHOLD = 2
SUGGESTION_EXPIRE_DAYS = 60

ALLOWED_BASES = ALLOWED_BASES = ["ORD","IAH","DEN","EWR","IAD","DCA","SFO","LAX","CLE","LGA","GUM","LAS","MCO"]
  # edit as you like
ALLOWED_FLEETS = ["737","757","767","777","787","A319","A320","A321"]

# ----------------------------
# Flask
# ----------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

# ----------------------------
# Filesystem bootstrap (write templates/css if missing)
# ----------------------------
BASE_DIR = Path(__file__).parent
(TEMPLATES := BASE_DIR / "templates").mkdir(exist_ok=True)
(STATIC := BASE_DIR / "static").mkdir(exist_ok=True)

def _write_if_missing(path: Path, content: str):
    if not path.exists():
        path.write_text(content.strip("\n"), encoding="utf-8")

# Base layout
_write_if_missing(
    TEMPLATES / "base.html",
    """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>{{ title or "Rate My Captain" }}</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='main.css') }}">
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
</head>
<body>
  <header class="wrap">
    <div class="hdr">
      <h1><a href="{{ url_for('index') }}">Rate My Captain</a></h1>
      <nav>
        {% if not session.get('authed') %}
          <a class="btn" href="{{ url_for('login') }}">Enter</a>
        {% else %}
          <a class="btn subtle" href="{{ url_for('index') }}">Home</a>
        {% endif %}
      </nav>
    </div>
  </header>
  <main class="wrap">
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <div class="flash">{{ messages[0] }}</div>
      {% endif %}
    {% endwith %}
    {% block content %}{% endblock %}
  </main>
  <footer class="wrap small muted" style="margin-top:40px;">
    <hr/>
    <p>Built by line pilots for line pilots. Keep it professional.</p>
  </footer>
</body>
</html>
"""
)

# Homepage
_write_if_missing(
    TEMPLATES / "index.html",
    """
{% extends "base.html" %}
{% block content %}
<div class="trust">
  <div class="shield">🛡️</div>
  <div>
    <div class="trust-title">Anonymous & Professional</div>
    <div class="trust-text">No names, emails, or IDs — just honest 1–5 ratings. Every review is 100% confidential.</div>
  </div>
</div>

<form method="get" class="row">
  <input class="input" name="q" placeholder="Search by captain, base, or fleet..." value="{{ q }}">
  <button class="btn" type="submit">Search</button>
  {% if session.get('authed') %}
    <a class="btn" href="{{ url_for('captain_new') }}">Add Captain</a>
  {% endif %}
</form>

<div class="cards">
{% for c, avg, count in data %}
  <a class="card" href="{{ url_for('captain_page', cid=c.id) }}">
    <div class="card-title">{{ c.name }}</div>
    <div class="muted">{{ c.base or "—" }} · {{ c.fleet or "—" }}</div>
    <div class="mt8">
      {% if count >= min_display %}
        Avg: <strong>{{ "%.2f"|format(avg) }}</strong> ({{ count }} reviews)
      {% elif count > 0 %}
        <em>More ratings needed ({{ count }}/{{ min_display }})</em>
      {% else %}
        <em>No reviews yet</em>
      {% endif %}
    </div>
  </a>
{% endfor %}
</div>
{% endblock %}
"""
)

# Captain page
_write_if_missing(
    TEMPLATES / "captain.html",
    """
{% extends "base.html" %}
{% block content %}
<div class="row space-between center">
  <div>
    <h2>{{ captain.name }}</h2>
    <div class="muted">{{ captain.base or "—" }} · {{ captain.fleet or "—" }}</div>
    {% if last_updated %}
      <div class="small muted">Last updated {{ last_updated }}{% if pending_count %} · {{ pending_count }} pending suggestion{{ 's' if pending_count != 1 else '' }}{% endif %}</div>
    {% endif %}
  </div>
  <div class="row" style="gap:8px;">
    {% if session.get('authed') %}
      <a class="btn" href="{{ url_for('review_new', cid=captain.id) }}">Rate this Captain</a>
      <a class="btn subtle" href="{{ url_for('suggest_update', cid=captain.id) }}">Suggest Update</a>
    {% endif %}
  </div>
</div>

{% if count >= min_display %}
  <p class="mt12">Overall: <strong>{{ overall }}</strong> / 5 (based on {{ count }} reviews)</p>

  <h3>Operational & Teamwork</h3>
  <div class="grid">
    {% for key,label in eval_labels_1 %}
      <div class="chip"><div>{{ label }}</div><div class="chip-value">{{ '%.2f'|format(cat_avgs.get(key,0)) }}</div></div>
    {% endfor %}
  </div>

  <h3>Airmanship & Professional Conduct</h3>
  <div class="grid">
    {% for key,label in eval_labels_2 %}
      <div class="chip"><div>{{ label }}</div><div class="chip-value">{{ '%.2f'|format(cat_avgs.get(key,0)) }}</div></div>
    {% endfor %}
  </div>

  <h3>Overall Impression</h3>
  <div class="grid">
    <div class="chip"><div>Would Fly Again</div><div class="chip-value">{{ '%.2f'|format(cat_avgs.get('would_fly_again',0)) }}</div></div>
  </div>

  <h3>Personality & Style <span class="small muted">(does not affect overall score)</span></h3>
  <div class="grid">
    {% for key,label in style_labels %}
      <div class="chip"><div>{{ label }}</div><div class="chip-value">{{ '%.2f'|format(cat_avgs.get(key,0)) }}</div></div>
    {% endfor %}
  </div>
{% elif count > 0 %}
  <p class="mt12"><em>More ratings needed to show averages ({{ count }}/{{ min_display }}).</em></p>
{% else %}
  <p class="mt12"><em>No reviews yet. Be the first.</em></p>
{% endif %}
{% endblock %}
"""
)

# New Review page with radio scales and sections
_write_if_missing(
    TEMPLATES / "review_new.html",
    """
{% extends "base.html" %}
{% block content %}
<h2>Rate {{ captain.name }}</h2>
<p class="muted small">(1 = negative → 5 = positive) • No text is collected.</p>

<form method="post" class="col">
  <h3 class="mt12">Crew Coordination & Workflow</h3>
  {% for key, label, hint in eval_block_1 %}
    <div class="q">
      <label class="q-label">{{ label }} <span class="muted small">({{ hint }})</span></label>
      <div class="scale">
        {% for v in range(1,6) %}
          <label class="dot"><input type="radio" name="{{ key }}" value="{{ v }}" {% if v==3 %}checked{% endif %}><span>{{ v }}</span></label>
        {% endfor %}
      </div>
    </div>
  {% endfor %}

  <h3 class="mt12">Airmanship & Professional Conduct</h3>
  {% for key, label, hint in eval_block_2 %}
    <div class="q">
      <label class="q-label">{{ label }} <span class="muted small">({{ hint }})</span></label>
      <div class="scale">
        {% for v in range(1,6) %}
          <label class="dot"><input type="radio" name="{{ key }}" value="{{ v }}" {% if v==3 %}checked{% endif %}><span>{{ v }}</span></label>
        {% endfor %}
      </div>
    </div>
  {% endfor %}

  <h3 class="mt12">Overall Impression</h3>
  <div class="q">
    <label class="q-label">Would Fly Again <span class="muted small">(1 = avoid → 5 = definitely would)</span></label>
    <div class="scale">
      {% for v in range(1,6) %}
        <label class="dot"><input type="radio" name="would_fly_again" value="{{ v }}" {% if v==3 %}checked{% endif %}><span>{{ v }}</span></label>
      {% endfor %}
    </div>
  </div>

  <h3 class="mt12">Personality & Style <span class="small muted">(does not affect overall score)</span></h3>
  {% for key, label, hint in style_block %}
    <div class="q">
      <label class="q-label">{{ label }} <span class="muted small">({{ hint }})</span></label>
      <div class="scale">
        {% for v in range(1,6) %}
          <label class="dot"><input type="radio" name="{{ key }}" value="{{ v }}" {% if v==3 %}checked{% endif %}><span>{{ v }}</span></label>
        {% endfor %}
      </div>
    </div>
  {% endfor %}

  <button class="btn" type="submit">Submit</button>
</form>
{% endblock %}
"""
)

# Login
_write_if_missing(
    TEMPLATES / "login.html",
    """
{% extends "base.html" %}
{% block content %}
<h2>Access</h2>
<form method="post" class="col">
  <input class="input" name="code" placeholder="Invite code" required>
  <button class="btn" type="submit">Enter</button>
</form>
{% endblock %}
"""
)

# Add Captain
_write_if_missing(
    TEMPLATES / "captain_new.html",
    """
{% extends "base.html" %}
{% block content %}
<h2>Add a Captain</h2>
<form method="post" class="col" style="max-width:520px;">
  <label>Name
    <input class="input" name="name" placeholder="e.g., Taylor Nguyen" required>
  </label>
  <label>Base
    <select class="input" name="base" required>
      <option value="" selected disabled>Select base</option>
      {% for b in bases %}<option value="{{ b }}">{{ b }}</option>{% endfor %}
    </select>
  </label>
  <label>Fleet
    <select class="input" name="fleet" required>
      <option value="" selected disabled>Select fleet</option>
      {% for f in fleets %}<option value="{{ f }}">{{ f }}</option>{% endfor %}
    </select>
  </label>
  <button class="btn" type="submit">Add Captain</button>
</form>
{% endblock %}
"""
)

# Suggest Update
_write_if_missing(
    TEMPLATES / "suggest_update.html",
    """
{% extends "base.html" %}
{% block content %}
<h2>Suggest Base/Fleet Update for {{ captain.name }}</h2>
<p class="small muted">When two different FOs suggest the same change within 14 days, it auto-applies.</p>
<form method="post" class="col" style="max-width:520px;">
  <label>New Base
    <select class="input" name="base" required>
      <option value="" selected disabled>Select base</option>
      {% for b in bases %}<option value="{{ b }}">{{ b }}</option>{% endfor %}
    </select>
  </label>
  <label>New Fleet
    <select class="input" name="fleet" required>
      <option value="" selected disabled>Select fleet</option>
      {% for f in fleets %}<option value="{{ f }}">{{ f }}</option>{% endfor %}
    </select>
  </label>
  <button class="btn" type="submit">Submit Suggestion</button>
</form>

{% if pending and pending|length > 0 %}
  <h3 class="mt12">Pending Suggestions</h3>
  <ul>
    {% for s in pending %}
      <li class="small">{{ s.new_base }} / {{ s.new_fleet }} • submitted {{ s.created_at.date() }}</li>
    {% endfor %}
  </ul>
{% endif %}
{% endblock %}
"""
)

# CSS
_write_if_missing(
    STATIC / "main.css",
    """
:root { --fg:#111; --bg:#fff; --muted:#666; --accent:#2563eb; --card:#f7f7f8; --line:#e5e7eb; }
*{box-sizing:border-box} body{margin:0;font-family:system-ui,Segoe UI,Roboto,Arial,sans-serif;color:var(--fg);background:var(--bg)}
a{color:inherit;text-decoration:none}
.wrap{max-width:960px;margin:0 auto;padding:16px}
.hdr{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--line)}
h1{font-size:20px;margin:8px 0}
h2{margin:12px 0 4px}
.row{display:flex;gap:8px;align-items:flex-start}
.col{display:flex;flex-direction:column;gap:12px}
.space-between{justify-content:space-between}
.center{align-items:center}
.mt8{margin-top:8px}.mt12{margin-top:12px}
.small{font-size:12px}.muted{color:var(--muted)}
.btn{background:var(--accent);color:#fff;border:none;border-radius:10px;padding:8px 14px;cursor:pointer}
.btn:hover{opacity:.95}
.btn.subtle{background:#eef2ff;color:#1d4ed8}
.input{padding:10px 12px;border:1px solid var(--line);border-radius:10px;min-width:240px}
.flash{background:#fff3cd;color:#8a6d3b;border:1px solid #ffeeba;border-radius:10px;padding:8px 12px;margin:12px 0}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;margin-top:12px}
.card{border:1px solid var(--line);background:var(--card);padding:12px;border-radius:14px}
.card-title{font-weight:600;margin-bottom:4px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px;margin-top:12px}
.chip{border:1px solid var(--line);padding:10px;border-radius:12px;background:#fff;display:flex;justify-content:space-between;align-items:center}
.chip-value{font-weight:700}
.trust{display:flex;gap:10px;align-items:flex-start;background:#f7f9fc;border:1px solid var(--line);padding:12px;border-radius:12px;margin-bottom:12px}
.trust-title{font-weight:600}
.trust .shield{font-size:20px}
.q{padding:8px 10px;border:1px solid var(--line);border-radius:12px;background:#fff}
.q-label{display:block;margin-bottom:6px;font-weight:600}
.scale{display:flex;gap:14px;align-items:center}
.dot{display:flex;flex-direction:column;align-items:center;font-size:12px;color:#444}
.dot input[type=radio]{accent-color:#2563eb;transform:scale(1.2);cursor:pointer}
"""
)

# ----------------------------
# Database (SQLAlchemy)
# ----------------------------
Base = declarative_base()
engine = create_engine(f"sqlite:///{DB_PATH}", future=True)

class Captain(Base):
    __tablename__ = "captains"
    id = Column(Integer, primary_key=True)
    employee_id = Column(String, unique=True, nullable=False)   # non-PII slug like CA-XXXX
    name = Column(String, nullable=False)
    base = Column(String, nullable=False)
    fleet = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)

    reviews = relationship("Review", back_populates="captain")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    captain_id = Column(Integer, ForeignKey("captains.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewer_hash = Column(String, nullable=True)

    # Crew Coordination & Workflow (1-7)
    crm_inclusion = Column(Integer, nullable=False)
    communication = Column(Integer, nullable=False)
    easy_to_fly = Column(Integer, nullable=False)
    micromanage = Column(Integer, nullable=False)  # invert
    workload_share = Column(Integer, nullable=False)
    helps_box = Column(Integer, nullable=False)
    helps_walk = Column(Integer, nullable=False)

    # Airmanship & Conduct (8-12)
    skill_sop = Column(Integer, nullable=False)
    temperament = Column(Integer, nullable=False)
    respectfulness = Column(Integer, nullable=False)
    boundaries = Column(Integer, nullable=False)
    cabin_respect = Column(Integer, nullable=False)

    # Overall Impression (13)
    would_fly_again = Column(Integer, nullable=False)

    # Personality & Style (non-scoring) (14-16)
    chattiness = Column(Integer, nullable=False)
    mentorship = Column(Integer, nullable=False)
    humor_vibe = Column(Integer, nullable=False)

    captain = relationship("Captain", back_populates="reviews")

class CaptainAssignment(Base):
    __tablename__ = "captain_assignments"
    id = Column(Integer, primary_key=True)
    captain_id = Column(Integer, ForeignKey("captains.id"), nullable=False)
    base = Column(String, nullable=False)
    fleet = Column(String, nullable=False)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow)

class EditSuggestion(Base):
    __tablename__ = "edit_suggestions"
    id = Column(Integer, primary_key=True)
    captain_id = Column(Integer, ForeignKey("captains.id"), nullable=False)
    new_base = Column(String, nullable=False)
    new_fleet = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending/approved/rejected/expired
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    creator_hash = Column(String, nullable=False)

def bootstrap_db():
    Base.metadata.create_all(engine)
    # Seed a couple captains if empty
    with Session(engine) as s:
        if s.query(Captain).count() == 0:
            for nm, b, f in [("John Smith","ORD","737"),("Alex Chen","IAH","787"),("Maria Lopez","DEN","A320")]:
                c = Captain(employee_id=f"CA-{secrets.token_hex(4).upper()}", name=nm, base=b, fleet=f)
                s.add(c)
                s.flush()
                s.add(CaptainAssignment(captain_id=c.id, base=b, fleet=f))
            s.commit()

bootstrap_db()

# ----------------------------
# Ratings config & helpers
# ----------------------------
def inv(x:int)->int: return 6 - x

# Keys, labels, and hints (1→5)
EVAL_BLOCK_1 = [
  ("crm_inclusion", "CRM & Inclusion", "1 = shuts FO out → 5 = collaborative"),
  ("communication", "Communication", "1 = poor/confusing → 5 = clear and timely"),
  ("easy_to_fly", "Easy to Fly With", "1 = difficult → 5 = low-friction and easygoing"),
  ("micromanage", "Micromanagement (inverse)", "1 = nitpicks tasks → 5 = trusts appropriately"),
  ("workload_share", "Workload Sharing", "1 = leaves you hanging → 5 = pitches in"),
  ("helps_box", "Helps with Box Work", "1 = never helps → 5 = proactively helps"),
  ("helps_walk", "Helps with Walkaround", "1 = never helps → 5 = proactively helps"),
]
EVAL_BLOCK_2 = [
  ("skill_sop", "Skill / SOP Knowledge", "1 = sloppy/guessy → 5 = sharp & standard"),
  ("temperament", "Temperament / Stress Handling", "1 = easily frustrated → 5 = calm & steady"),
  ("respectfulness", "Respectfulness", "1 = rude/hostile → 5 = courteous/decent"),
  ("boundaries", "Professional Boundaries", "1 = makes people uncomfortable → 5 = appropriate & respectful"),
  ("cabin_respect", "Cabin Crew Respect", "1 = dismissive → 5 = consistently respectful"),
]
STYLE_BLOCK = [
  ("chattiness", "Chattiness", "1 = mostly reserved → 5 = very chatty"),
  ("mentorship", "Mentorship / Coaching", "1 = no extra guidance → 5 = supportive teacher"),
  ("humor_vibe", "Humor / Vibe", "1 = humorless/tense → 5 = positive, light-hearted"),
]

EVAL_KEYS = [k for k,_,_ in EVAL_BLOCK_1 + EVAL_BLOCK_2] + ["would_fly_again"]
STYLE_KEYS = [k for k,_,_ in STYLE_BLOCK]

# For captain page grouping
EVAL_LABELS_1 = [(k,l) for k,l,_ in EVAL_BLOCK_1]
EVAL_LABELS_2 = [(k,l) for k,l,_ in EVAL_BLOCK_2]
STYLE_LABELS = [(k,l) for k,l,_ in STYLE_BLOCK]

def overall_from_review(r: Review) -> float:
    vals = [
        r.crm_inclusion, r.communication, r.easy_to_fly,
        inv(r.micromanage),
        r.workload_share, r.helps_box, r.helps_walk,
        r.skill_sop, r.temperament, r.respectfulness, r.boundaries, r.cabin_respect,
        r.would_fly_again
    ]
    return sum(vals)/len(vals)

# ----------------------------
# Anonymous cookie token -> hashed reviewer id
# ----------------------------
REV_COOKIE = "rev_token"
REV_COOKIE_MAX_AGE = 60*60*24*365*2  # 2 years

def get_or_set_reviewer_token():
    token = request.cookies.get(REV_COOKIE)
    if token:
        return token, None
    new_token = str(uuid.uuid4())
    return new_token, new_token

def reviewer_hash_from_token(token: str) -> str:
    digest = hmac.new(REVIEWER_PEPPER.encode(), token.encode(), hashlib.sha256).hexdigest()
    return digest[:32]

def new_identifier(prefix="CA"):
    alphabet = string.ascii_uppercase + string.digits
    return f"{prefix}-{''.join(secrets.choice(alphabet) for _ in range(8))}"

# ----------------------------
# Routes
# ----------------------------
@app.route("/")
def index():
    stmt = select(Captain)
    q = request.args.get("q", "")

    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Captain.name.ilike(like),
                              Captain.base.ilike(like),
                              Captain.fleet.ilike(like)))

    captains = s.scalars(stmt.order_by(Captain.name.asc())).all()

    data = []
    with Session(engine) as s:
        for c in captains:
            reviews = s.scalars(select(Review).where(Review.captain_id == c.id)).all()
            count = len(reviews)
            avg = None
            if count >= MIN_DISPLAY_REVIEWS:
                avg = sum(overall_from_review(r) for r in reviews) / count
                data.append((c, avg, count))

        # 👇 this is the new line that gathers all captain names for autocomplete
        all_names = [c.name for c in captains]

    # 👇 updated render_template call that passes all_names to index.html
    return render_template(
        "index.html",
        data=data,
        q=q,
        min_display=MIN_DISPLAY_REVIEWS,
        title=APP_NAME,
        all_names=all_names
    )

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form.get("code","") == INVITE_CODE:
            session["authed"] = True
            return redirect(url_for("index"))
        flash("Invalid code.")
    return render_template("login.html", title=f"{APP_NAME} · Access")

@app.route("/captains/<int:cid>")
def captain_page(cid):
    with Session(engine) as s:
        c = s.get(Captain, cid)
        if not c: return "Not found", 404
        reviews = s.scalars(select(Review).where(Review.captain_id == c.id)).all()
        count = len(reviews)
        cat_avgs = {}
        overall = None
        if count >= MIN_DISPLAY_REVIEWS:
            # compute per-key averages (invert micromanage)
            all_keys = EVAL_KEYS + STYLE_KEYS
            for key in all_keys:
                vals = [getattr(r,key) for r in reviews]
                if key == "micromanage":
                    vals = [inv(v) for v in vals]
                cat_avgs[key] = round(sum(vals)/len(vals), 2)
            overall = round(sum(cat_avgs[k] for k in EVAL_KEYS)/len(EVAL_KEYS), 2)
        # last updated & pending suggestions
        last_updated = c.updated_at.date() if c.updated_at else None
        pending_count = s.scalar(select(func.count(EditSuggestion.id)).where(
            and_(EditSuggestion.captain_id==c.id, EditSuggestion.status=="pending")
        ))
    return render_template(
        "captain.html",
        captain=c, count=count, min_display=MIN_DISPLAY_REVIEWS,
        cat_avgs=cat_avgs, overall=overall, last_updated=last_updated, pending_count=pending_count,
        eval_labels_1=EVAL_LABELS_1, eval_labels_2=EVAL_LABELS_2, style_labels=STYLE_LABELS,
        title=f"{APP_NAME} · {c.name}"
    )

@app.route("/review/new/<int:cid>", methods=["GET","POST"])
def review_new(cid):
    if not session.get("authed"): return redirect(url_for("login"))

    with Session(engine) as s:
        c = s.get(Captain, cid)
        if not c: return "Not found", 404

    token, to_set = get_or_set_reviewer_token()

    if request.method == "POST":
        r_hash = reviewer_hash_from_token(token)
        twentyfour_ago = datetime.utcnow() - timedelta(hours=24)
        with Session(engine) as s:
            recent = s.scalars(select(Review).where(and_(
                Review.captain_id==cid,
                Review.reviewer_hash==r_hash,
                Review.created_at >= twentyfour_ago
            ))).all()
            if recent:
                flash("You’ve already reviewed this captain recently. Try again later.")
                resp = redirect(url_for("captain_page", cid=cid))
                if to_set: resp.set_cookie(REV_COOKIE, to_set, max_age=REV_COOKIE_MAX_AGE, httponly=True, samesite='Lax')
                return resp

            payload = {}
            # Collect evaluative & style keys
            for key in EVAL_KEYS + STYLE_KEYS:
                v = request.form.get(key)
                payload[key] = int(v) if v and v.isdigit() else 3

            r = Review(captain_id=cid, reviewer_hash=r_hash, **payload)
            s.add(r)
            s.commit()

        resp = redirect(url_for("captain_page", cid=cid))
        if to_set: resp.set_cookie(REV_COOKIE, to_set, max_age=REV_COOKIE_MAX_AGE, httponly=True, samesite='Lax')
        return resp

    return make_response(render_template(
        "review_new.html",
        captain=c,
        eval_block_1=EVAL_BLOCK_1,
        eval_block_2=EVAL_BLOCK_2,
        style_block=STYLE_BLOCK,
        title=f"{APP_NAME} · Rate {c.name}"
    ))

@app.route("/captain/new", methods=["GET","POST"])
def captain_new():
    if not session.get("authed"): return redirect(url_for("login"))
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        base = (request.form.get("base") or "").strip().upper()
        fleet = (request.form.get("fleet") or "").strip().upper()
        if not name or base not in ALLOWED_BASES or fleet not in ALLOWED_FLEETS:
            flash("Name, Base, and Fleet are required.")
            return redirect(url_for("captain_new"))
        norm_name = " ".join(p.capitalize() for p in name.split())
        with Session(engine) as s:
            existing = s.scalars(select(Captain).where(and_(
                func.lower(Captain.name)==norm_name.lower(),
                Captain.base==base,
                Captain.fleet==fleet
            ))).first()
            if existing:
                flash("Captain already exists. Taking you to their page.")
                return redirect(url_for("captain_page", cid=existing.id))
            c = Captain(employee_id=new_identifier("CA"), name=norm_name, base=base, fleet=fleet)
            s.add(c); s.flush()
            s.add(CaptainAssignment(captain_id=c.id, base=base, fleet=fleet))
            s.commit()
            flash("Captain added!")
            return redirect(url_for("captain_page", cid=c.id))
    return render_template("captain_new.html", bases=ALLOWED_BASES, fleets=ALLOWED_FLEETS, title=f"{APP_NAME} · Add Captain")

@app.route("/captain/<int:cid>/suggest", methods=["GET","POST"])
def suggest_update(cid):
    if not session.get("authed"): return redirect(url_for("login"))

    with Session(engine) as s:
        c = s.get(Captain, cid)
        if not c: return "Not found", 404

    token, to_set = get_or_set_reviewer_token()
    creator_hash = reviewer_hash_from_token(token)

    if request.method == "POST":
        new_base = (request.form.get("base") or "").strip().upper()
        new_fleet = (request.form.get("fleet") or "").strip().upper()
        if new_base not in ALLOWED_BASES or new_fleet not in ALLOWED_FLEETS:
            flash("Select a valid base and fleet.")
            return redirect(url_for("suggest_update", cid=cid))

        with Session(engine) as s:
            # Prevent multiple active suggestions by same creator for this captain
            existing_mine = s.scalars(select(EditSuggestion).where(and_(
                EditSuggestion.captain_id==cid,
                EditSuggestion.creator_hash==creator_hash,
                EditSuggestion.status=="pending"
            ))).first()
            if existing_mine:
                flash("You already have a pending suggestion for this captain.")
                resp = redirect(url_for("suggest_update", cid=cid))
                if to_set: resp.set_cookie(REV_COOKIE, to_set, max_age=REV_COOKIE_MAX_AGE, httponly=True, samesite='Lax')
                return resp

            # Create suggestion
            sug = EditSuggestion(captain_id=cid, new_base=new_base, new_fleet=new_fleet, creator_hash=creator_hash)
            s.add(sug); s.flush()

            # Check for consensus within window among different creators
            since = datetime.utcnow() - timedelta(days=SUGGESTION_WINDOW_DAYS)
            matches = s.scalars(select(EditSuggestion).where(and_(
                EditSuggestion.captain_id==cid,
                EditSuggestion.new_base==new_base,
                EditSuggestion.new_fleet==new_fleet,
                EditSuggestion.status=="pending",
                EditSuggestion.created_at >= since
            ))).all()

            # unique creators
            creators = set(m.creator_hash for m in matches)
            if len(creators) >= CONSENSUS_THRESHOLD:
                # Approve all matching pending; update captain + history
                for m in matches:
                    m.status = "approved"; m.resolved_at = datetime.utcnow()
                cap = s.get(Captain, cid)
                # Close current assignment
                current = s.scalars(select(CaptainAssignment).where(and_(
                    CaptainAssignment.captain_id==cid,
                    CaptainAssignment.end_date.is_(None)
                ))).first()
                if current:
                    current.end_date = datetime.utcnow()
                # Add new assignment and update captain
                s.add(CaptainAssignment(captain_id=cid, base=new_base, fleet=new_fleet))
                cap.base = new_base; cap.fleet = new_fleet; cap.updated_at = datetime.utcnow()
                s.commit()
                flash(f"Consensus reached: Updated to {new_base} / {new_fleet}.")
                resp = redirect(url_for("captain_page", cid=cid))
                if to_set: resp.set_cookie(REV_COOKIE, to_set, max_age=REV_COOKIE_MAX_AGE, httponly=True, samesite='Lax')
                return resp
            else:
                s.commit()
                flash("Suggestion recorded. When two FOs suggest the same change within 14 days, it auto-applies.")
                resp = redirect(url_for("captain_page", cid=cid))
                if to_set: resp.set_cookie(REV_COOKIE, to_set, max_age=REV_COOKIE_MAX_AGE, httponly=True, samesite='Lax')
                return resp

    # GET: show form + list pending
    with Session(engine) as s:
        pending = s.scalars(select(EditSuggestion).where(and_(
            EditSuggestion.captain_id==cid,
            EditSuggestion.status=="pending"
        )).order_by(EditSuggestion.created_at.desc())).all()

    resp = make_response(render_template(
        "suggest_update.html",
        captain=c, bases=ALLOWED_BASES, fleets=ALLOWED_FLEETS, pending=pending,
        title=f"{APP_NAME} · Suggest Update"
    ))
    if to_set: resp.set_cookie(REV_COOKIE, to_set, max_age=REV_COOKIE_MAX_AGE, httponly=True, samesite='Lax')
    return resp

# ----------------------------
# Main
# ----------------------------
@app.route("/top")
def top_rated():
    # Optional filters: /top?base=ORD&fleet=737
    base = (request.args.get("base") or "").upper().strip()
    fleet = (request.args.get("fleet") or "").upper().strip()
    min_reviews = MIN_DISPLAY_REVIEWS
    top_limit = 10

    rows = []
    with Session(engine) as s:
        captains = s.scalars(select(Captain)).all()
        for c in captains:
            if base and c.base != base:
                continue
            if fleet and c.fleet != fleet:
                continue
            reviews = s.scalars(select(Review).where(Review.captain_id == c.id)).all()
            count = len(reviews)
            if count < min_reviews:
                continue
            avg = sum(overall_from_review(r) for r in reviews) / count
            rows.append((c, round(avg, 2), count))

    # Sort: best average first, then by review count (desc)
    rows.sort(key=lambda x: (x[1], x[2]), reverse=True)
    rows = rows[:top_limit]

    return render_template(
        "top.html",
        rows=rows,
        bases=ALLOWED_BASES,
        fleets=ALLOWED_FLEETS,
        sel_base=base,
        sel_fleet=fleet,
        min_reviews=min_reviews,
        title="Top Rated"
    )

if __name__ == "__main__":
    bootstrap_db()
    port = int(os.environ.get("PORT", 5000))  # Render assigns this dynamically
    print(f"\n{APP_NAME} running on 0.0.0.0:{port} (Render)\n")
    app.run(host="0.0.0.0", port=port, debug=False)


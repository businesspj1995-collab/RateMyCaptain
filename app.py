# app.py — FOmatters / Rate My Captain (Option B: Hero access on homepage)

import os, uuid, hmac, hashlib, secrets, string
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from sqlalchemy import create_engine, select, Column, Integer, String, DateTime, ForeignKey, and_, or_, func
from sqlalchemy.orm import Session, declarative_base, relationship

# ----------------------------
# Config (env with safe fallbacks)
# ----------------------------
APP_NAME = "FOmatters"
DB_PATH = "app.db"
SECRET_KEY = os.getenv("SECRET_KEY") or "dev-secret-change-me"
INVITE_CODE = os.getenv("INVITE_CODE") or "FOmatters"
REVIEWER_PEPPER = os.getenv("REVIEWER_PEPPER") or "dev-pepper-change-me"
MIN_DISPLAY_REVIEWS = 3

SUGGESTION_WINDOW_DAYS = 14
CONSENSUS_THRESHOLD = 2

# Updated bases
ALLOWED_BASES = ["ORD","IAH","DEN","EWR","IAD","DCA","SFO","LAX","CLE","LGA","GUM","LAS","MCO"]
ALLOWED_FLEETS = ["737","757","767","777","787","A319","A320","A321"]

# ----------------------------
# Flask
# ----------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

# ----------------------------
# DB (SQLite / SQLAlchemy)
# ----------------------------
Base = declarative_base()
engine = create_engine(f"sqlite:///{DB_PATH}", future=True)

class Captain(Base):
    __tablename__ = "captains"
    id = Column(Integer, primary_key=True)
    employee_id = Column(String, unique=True, nullable=False)  # non-PII slug e.g., CA-XXXX
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

    # Crew Coordination & Workflow
    crm_inclusion = Column(Integer, nullable=False)
    communication = Column(Integer, nullable=False)
    easy_to_fly = Column(Integer, nullable=False)
    micromanage = Column(Integer, nullable=False)  # inverted in calc
    workload_share = Column(Integer, nullable=False)
    helps_box = Column(Integer, nullable=False)
    helps_walk = Column(Integer, nullable=False)
    # Airmanship & Conduct
    skill_sop = Column(Integer, nullable=False)
    temperament = Column(Integer, nullable=False)
    respectfulness = Column(Integer, nullable=False)
    boundaries = Column(Integer, nullable=False)
    cabin_respect = Column(Integer, nullable=False)
    # Overall
    would_fly_again = Column(Integer, nullable=False)
    # Personality (non-scoring)
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
    status = Column(String, default="pending")  # pending/approved/rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    creator_hash = Column(String, nullable=False)

def bootstrap_db():
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        if s.query(Captain).count() == 0:
            for nm, b, f in [("John Smith","ORD","737"), ("Alex Chen","IAH","787"), ("Maria Lopez","DEN","A320")]:
                c = Captain(employee_id=f"CA-{secrets.token_hex(4).upper()}",
                            name=nm, base=b, fleet=f)
                s.add(c); s.flush()
                s.add(CaptainAssignment(captain_id=c.id, base=b, fleet=f))
            s.commit()

# ----------------------------
# Rating config & helpers
# ----------------------------
def inv(x:int)->int: return 6 - x

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

def overall_from_review(r) -> float:
    vals = [
        r.crm_inclusion, r.communication, r.easy_to_fly,
        inv(r.micromanage),
        r.workload_share, r.helps_box, r.helps_walk,
        r.skill_sop, r.temperament, r.respectfulness, r.boundaries, r.cabin_respect,
        r.would_fly_again
    ]
    return sum(vals)/len(vals)

# Reviewer token (anonymous)
REV_COOKIE = "rev_token"
REV_COOKIE_MAX_AGE = 60*60*24*365*2

def get_or_set_reviewer_token():
    token = request.cookies.get(REV_COOKIE)
    if token: return token, None
    new_token = str(uuid.uuid4())
    return new_token, new_token

def reviewer_hash_from_token(token: str) -> str:
    return hmac.new(REVIEWER_PEPPER.encode(), token.encode(), hashlib.sha256).hexdigest()[:32]

def new_identifier(prefix="CA"):
    alphabet = string.ascii_uppercase + string.digits
    return f"{prefix}-{''.join(secrets.choice(alphabet) for _ in range(8))}"

# ----------------------------
# Routes
# ----------------------------
@app.route("/", methods=["GET"])
def index():
    # Not authed → show hero access only (no data)
    if not session.get("authed"):
        return render_template("index.html", title=APP_NAME)

    # Authed → search + cards
    q = (request.args.get("q", "") or "").strip()
    with Session(engine) as s:
        stmt = select(Captain)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(or_(
                Captain.name.ilike(like),
                Captain.base.ilike(like),
                Captain.fleet.ilike(like)
            ))
        captains = s.scalars(stmt.order_by(Captain.name.asc())).all()

        data = []
        for c in captains:
            reviews = s.scalars(select(Review).where(Review.captain_id == c.id)).all()
            count = len(reviews)
            avg = None
            if count >= MIN_DISPLAY_REVIEWS:
                avg = sum(overall_from_review(r) for r in reviews) / count
            data.append((c, avg, count))

        all_names = [c.name for c in captains]

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
    if not session.get("authed"): return redirect(url_for("index"))
    with Session(engine) as s:
        c = s.get(Captain, cid)
        if not c: return "Not found", 404
        reviews = s.scalars(select(Review).where(Review.captain_id == c.id)).all()
        count = len(reviews)
        cat_avgs, overall = {}, None
        if count >= MIN_DISPLAY_REVIEWS:
            all_keys = EVAL_KEYS + STYLE_KEYS
            for key in all_keys:
                vals = [getattr(r,key) for r in reviews]
                if key == "micromanage": vals = [inv(v) for v in vals]
                cat_avgs[key] = round(sum(vals)/len(vals), 2)
            overall = round(sum(cat_avgs[k] for k in EVAL_KEYS)/len(EVAL_KEYS), 2)
        last_updated = c.updated_at.date() if c.updated_at else None
        pending_count = s.scalar(select(func.count(EditSuggestion.id)).where(
            and_(EditSuggestion.captain_id==c.id, EditSuggestion.status=="pending")
        ))
    return render_template(
        "captain.html",
        captain=c, count=count, min_display=MIN_DISPLAY_REVIEWS,
        cat_avgs=cat_avgs, overall=overall, last_updated=last_updated, pending_count=pending_count,
        eval_labels_1=[(k,l) for k,l,_ in EVAL_BLOCK_1],
        eval_labels_2=[(k,l) for k,l,_ in EVAL_BLOCK_2],
        style_labels=[(k,l) for k,l,_ in STYLE_BLOCK],
        title=f"{APP_NAME} · {c.name}"
    )

@app.route("/review/new/<int:cid>", methods=["GET","POST"])
def review_new(cid):
    if not session.get("authed"): return redirect(url_for("index"))
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
            for key in EVAL_KEYS + STYLE_KEYS:
                v = request.form.get(key)
                payload[key] = int(v) if v and v.isdigit() else 3
            r = Review(captain_id=cid, reviewer_hash=r_hash, **payload)
            s.add(r); s.commit()
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
    if not session.get("authed"): return redirect(url_for("index"))
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
    if not session.get("authed"): return redirect(url_for("index"))
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
            mine = s.scalars(select(EditSuggestion).where(and_(
                EditSuggestion.captain_id==cid,
                EditSuggestion.creator_hash==creator_hash,
                EditSuggestion.status=="pending"
            ))).first()
            if mine:
                flash("You already have a pending suggestion for this captain.")
                resp = redirect(url_for("suggest_update", cid=cid))
                if to_set: resp.set_cookie(REV_COOKIE, to_set, max_age=REV_COOKIE_MAX_AGE, httponly=True, samesite='Lax')
                return resp
            sug = EditSuggestion(captain_id=cid, new_base=new_base, new_fleet=new_fleet, creator_hash=creator_hash)
            s.add(sug); s.flush()
            since = datetime.utcnow() - timedelta(days=SUGGESTION_WINDOW_DAYS)
            matches = s.scalars(select(EditSuggestion).where(and_(
                EditSuggestion.captain_id==cid,
                EditSuggestion.new_base==new_base,
                EditSuggestion.new_fleet==new_fleet,
                EditSuggestion.status=="pending",
                EditSuggestion.created_at >= since
            ))).all()
            creators = set(m.creator_hash for m in matches)
            if len(creators) >= CONSENSUS_THRESHOLD:
                for m in matches:
                    m.status = "approved"; m.resolved_at = datetime.utcnow()
                cap = s.get(Captain, cid)
                current = s.scalars(select(CaptainAssignment).where(and_(
                    CaptainAssignment.captain_id==cid,
                    CaptainAssignment.end_date.is_(None)
                ))).first()
                if current: current.end_date = datetime.utcnow()
                s.add(CaptainAssignment(captain_id=cid, base=new_base, fleet=new_fleet))
                cap.base, cap.fleet, cap.updated_at = new_base, new_fleet, datetime.utcnow()
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

@app.route("/top")
def top_rated():
    if not session.get("authed"): return redirect(url_for("index"))
    base = (request.args.get("base") or "").upper().strip()
    fleet = (request.args.get("fleet") or "").upper().strip()
    min_reviews = MIN_DISPLAY_REVIEWS
    top_limit = 10

    rows = []
    with Session(engine) as s:
        captains = s.scalars(select(Captain)).all()
        for c in captains:
            if base and c.base != base: continue
            if fleet and c.fleet != fleet: continue
            reviews = s.scalars(select(Review).where(Review.captain_id == c.id)).all()
            count = len(reviews)
            if count < min_reviews: continue
            avg = sum(overall_from_review(r) for r in reviews)/count
            rows.append((c, round(avg, 2), count))

    rows.sort(key=lambda x: (x[1], x[2]), reverse=True)
    rows = rows[:top_limit]

    return render_template(
        "top.html",
        rows=rows, bases=ALLOWED_BASES, fleets=ALLOWED_FLEETS,
        sel_base=base, sel_fleet=fleet, min_reviews=min_reviews,
        title="Top Rated"
    )

# ----------------------------
# Main (Render-friendly)
# ----------------------------
if __name__ == "__main__":
    bootstrap_db()
    port = int(os.environ.get("PORT", 5000))
    print(f"\n{APP_NAME} running on http://0.0.0.0:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)

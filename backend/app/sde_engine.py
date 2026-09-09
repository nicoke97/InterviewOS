"""SDE study engine: queue, pools, 5+5+5+2, flojo, voice gate."""
from __future__ import annotations

import random
import unicodedata
from datetime import date, datetime

from sqlalchemy.orm import Session

from .executor import run_leetcode_code
from .models import (
    SdeAlgoProgress,
    SdeAnalysis,
    SdeCardProgress,
    SdeCursor,
    SdeDebugProgress,
    SdeOfflineLog,
    SdeSectionProgress,
    Streak,
)
from .progress import update_streak
from .sde_content import day1_sheet_ids, get_sheet, load_sde, recovery_sheet_ids
from .sde_i18n import (
    PACK,
    analysis_view,
    codi_copy,
    is_es,
    localize_card,
    localize_section,
    pick as pick_field,
    sheet_prompt,
)

LANG_LABEL = {"csharp": "C#", "python": "Python"}
FOUNDATION_WEEK = "w00-fundamentos"


def _is_foundation(section: dict) -> bool:
    return section.get("week_id") == FOUNDATION_WEEK


def _mastered_section_ids(db: Session) -> set[str]:
    return {
        r.section_id
        for r in db.query(SdeSectionProgress).filter(SdeSectionProgress.status == "mastered").all()
    }


def _sync_section_cursor(db: Session, cur: SdeCursor, sections: list[dict]) -> None:
    """If foundations were inserted at the front after the user already progressed, keep the later pointer."""
    n = sum(1 for s in sections if _is_foundation(s))
    if n == 0 or cur.next_section_index >= n:
        return
    later = db.query(SdeSectionProgress).filter(
        SdeSectionProgress.status.in_(["mastered", "current", "dirty"]),
    ).all()
    if any(r.section_id and not str(r.section_id).startswith("w00-") for r in later):
        cur.next_section_index += n


def _pick_theory_section(db: Session, cur: SdeCursor, sections: list[dict]) -> dict | None:
    mastered = _mastered_section_ids(db)
    for sec in sections:
        if _is_foundation(sec) and sec["id"] not in mastered:
            return sec
    if cur.next_section_index < len(sections):
        return sections[cur.next_section_index]
    return None


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in text.lower() if not unicodedata.combining(ch))


def weighted_sample(items: list, weights: list[float], k: int) -> list:
    pool = list(zip(items, weights))
    chosen = []
    for _ in range(min(k, len(pool))):
        total = sum(w for _, w in pool) or 1
        r = random.random() * total
        acc = 0.0
        for i, (item, w) in enumerate(pool):
            acc += w
            if r <= acc:
                chosen.append(item)
                pool.pop(i)
                break
    return chosen


def get_cursor(db: Session) -> SdeCursor:
    row = db.query(SdeCursor).first()
    data = load_sde()
    if not row:
        row = SdeCursor(
            active_algo_id=(data["algo_order"] or ["two-sum"])[0],
            active_lang=data["first_lang"],
            algo_phase="day1",
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    _sync_section_cursor(db, row, data["sections"])
    return row


def _algo_row(db: Session, algo_id: str, lang: str) -> SdeAlgoProgress:
    row = db.query(SdeAlgoProgress).filter_by(algo_id=algo_id, lang=lang).first()
    if not row:
        row = SdeAlgoProgress(algo_id=algo_id, lang=lang, status="active")
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _card_row(db: Session, card_id: str, section_id: str) -> SdeCardProgress:
    row = db.query(SdeCardProgress).filter_by(card_id=card_id).first()
    if not row:
        row = SdeCardProgress(card_id=card_id, section_id=section_id)
        db.add(row)
        db.flush()
    return row


def _touch(db: Session, cur: SdeCursor) -> None:
    cur.last_evidence_date = date.today()
    update_streak(db)
    db.commit()


def _save_analysis(db: Session, cause: str, line: str, cta: str, payload: dict | None = None) -> None:
    db.add(SdeAnalysis(cause=cause, line=line, cta=cta, payload=payload or {}))
    db.commit()


def _latest_analysis(db: Session, locale: str = "en") -> dict | None:
    row = db.query(SdeAnalysis).order_by(SdeAnalysis.id.desc()).first()
    if not row:
        return None
    payload = row.payload or {}
    return analysis_view(
        row.cause,
        locale,
        title=str(payload.get("title") or ""),
        n=int(payload.get("n") or 0),
        fallback_line=row.line,
        fallback_cta=row.cta,
    )


def inactivity_days(db: Session, cur: SdeCursor) -> int:
    last = cur.last_evidence_date
    streak = db.query(Streak).first()
    dates = [d for d in (last, streak.last_active_date if streak else None) if d]
    if not dates:
        return 0
    return max(0, (date.today() - max(dates)).days)


def _unlocked_cards(db: Session) -> list[dict]:
    data = load_sde()
    mastered = {
        r.section_id
        for r in db.query(SdeSectionProgress).filter(SdeSectionProgress.status.in_(["mastered", "current", "dirty"])).all()
    }
    # also cards from any section already seen via progress, plus today's current section
    cur = get_cursor(db)
    sections = data["sections"]
    if cur.next_section_index < len(sections):
        mastered.add(sections[cur.next_section_index]["id"])
    for sec in sections:
        if _is_foundation(sec):
            mastered.add(sec["id"])
    seen_ids = {c.card_id for c in db.query(SdeCardProgress).all()}
    out = []
    for c in data["cards"]:
        if c["section_id"] in mastered or c["id"] in seen_ids:
            out.append(c)
    return out


def _pick_cards(db: Session, light: bool) -> list[dict]:
    data = load_sde()
    cards = _unlocked_cards(db)
    cap = data["card_cap_light"] if light else data["card_cap"]
    if not cards:
        return []
    weights = []
    enriched = []
    for c in cards:
        row = db.query(SdeCardProgress).filter_by(card_id=c["id"]).first()
        fails = row.fails if row else 0
        enriched.append(c)
        weights.append(1.0 + fails * 3)
    if len(enriched) <= cap:
        random.shuffle(enriched)
        return [_card_payload(c) for c in enriched]
    picked = weighted_sample(enriched, weights, cap)
    return [_card_payload(c) for c in picked]


def _card_payload(c: dict) -> dict:
    return {
        "type": "flashcard",
        "id": c["id"],
        "section_id": c["section_id"],
        "front": c.get("front"),
        "front_es": c.get("front_es"),
        "back": c.get("back"),
        "back_es": c.get("back_es"),
    }


def _assignment_sheet(algo_id: str, lang: str, sheet_id: str, reason: str) -> dict:
    data = load_sde()
    algo = data["algos"][algo_id]
    sheet = get_sheet(algo, lang, sheet_id) or {}
    return {
        "type": "algo_sheet",
        "id": f"{algo_id}:{lang}:{sheet_id}",
        "algo_id": algo_id,
        "lang": lang,
        "sheet_id": sheet_id,
        "reason": reason,
        "title": algo.get("title", algo_id),
        "prompt": sheet.get("prompt", ""),
        "prompt_es": sheet.get("prompt_es"),
        "prompt_en": sheet.get("prompt_en"),
        "rung": sheet.get("rung"),
        "kind": sheet.get("kind"),
        "fn_name": sheet.get("fn_name") or (algo.get("languages") or {}).get(lang, {}).get("fn_name"),
        "language": lang,
    }


def _debug_row(db: Session, bug_id: str) -> SdeDebugProgress:
    row = db.query(SdeDebugProgress).filter_by(bug_id=bug_id).first()
    if not row:
        row = SdeDebugProgress(bug_id=bug_id, status="unseen")
        db.add(row)
        db.flush()
    return row


def _debug_assignment(bug: dict, reason: str) -> dict:
    return {
        "type": "debug",
        "id": f"debug:{bug['id']}:{reason}",
        "bug_id": bug["id"],
        "reason": reason,
        "title": bug.get("title"),
        "title_es": bug.get("title_es"),
        "difficulty": bug.get("difficulty"),
        "family": bug.get("family"),
        "lang": bug.get("lang", "csharp"),
        "error_hint": bug.get("error_hint"),
        "error_hint_es": bug.get("error_hint_es"),
    }


def _pick_debug_assignments(db: Session, cur: SdeCursor) -> list[dict]:
    data = load_sde()
    bugs = data.get("debug") or []
    if not bugs:
        return []
    by_id = data["debug_by_id"]
    items: list[dict] = []
    taken: set[str] = set()

    failed = db.query(SdeDebugProgress).filter_by(status="failed").all()
    if failed:
        bug = by_id.get(failed[0].bug_id)
        if bug:
            items.append(_debug_assignment(bug, "pool"))
            taken.add(bug["id"])
    else:
        done = [r for r in db.query(SdeDebugProgress).filter_by(status="completed").all() if r.bug_id in by_id]
        if done:
            pick = random.choice(done)
            items.append(_debug_assignment(by_id[pick.bug_id], "pool"))
            taken.add(pick.bug_id)

    unseen = [b for b in bugs if b["id"] not in taken]
    rows = {r.bug_id: r for r in db.query(SdeDebugProgress).all()}
    fresh = [b for b in unseen if rows.get(b["id"], None) is None or rows[b["id"]].status == "unseen"]
    if fresh:
        items.append(_debug_assignment(fresh[0], "new"))
    elif unseen:
        idx = cur.next_debug_index % len(unseen)
        items.append(_debug_assignment(unseen[idx], "new"))
        cur.next_debug_index = (idx + 1) % max(1, len(unseen))
    return items


def _build_assignments(db: Session, cur: SdeCursor, kind: str) -> list[dict]:
    data = load_sde()
    items: list[dict] = []
    light = kind in {"flojo", "return"}
    items.append({
        "type": "flashcards",
        "id": "cards",
        "cards": _pick_cards(db, light),
        "cap": data["card_cap_light"] if light else data["card_cap"],
    })

    if kind == "advance":
        items.extend(_pick_debug_assignments(db, cur))

    if kind == "return":
        items.append({
            "type": "return",
            "id": "return",
            "prompt": "3+ days without evidence. Cards plus one full pool problem or warm-up.",
            "prompt_es": "3+ días sin evidencia. Cartas + un entero del pool o warm-up.",
        })
        completed = db.query(SdeAlgoProgress).filter_by(status="completed").all()
        if completed:
            pick = random.choice(completed)
            items.append(_assignment_sheet(pick.algo_id, pick.lang, "full-recall", "return"))
        elif cur.last_sheet_id:
            items.append(_assignment_sheet(cur.active_algo_id, cur.active_lang, cur.last_sheet_id, "warmup"))
        return items

    if kind == "flojo" and cur.last_sheet_id:
        items.append(_assignment_sheet(cur.active_algo_id, cur.active_lang, cur.last_sheet_id, "warmup"))
        return items

    failed = db.query(SdeAlgoProgress).filter_by(status="failed").all()
    if failed:
        f = failed[0]
        algo = data["algos"][f.algo_id]
        for sid in day1_sheet_ids(algo, f.lang):
            items.append(_assignment_sheet(f.algo_id, f.lang, sid, "failed_restart"))
        return items

    completed = db.query(SdeAlgoProgress).filter_by(status="completed").all()
    if completed:
        pick = random.choice(completed)
        items.append(_assignment_sheet(pick.algo_id, pick.lang, "full-recall", "pool"))

    algo = data["algos"][cur.active_algo_id]
    if cur.algo_phase == "day1":
        ids = day1_sheet_ids(algo, cur.active_lang)[cur.day1_index:]
        for sid in ids:
            items.append(_assignment_sheet(cur.active_algo_id, cur.active_lang, sid, "day1"))
    elif cur.algo_phase == "rung1":
        ids = day1_sheet_ids(algo, cur.active_lang)[:5]
        for sid in ids:
            items.append(_assignment_sheet(cur.active_algo_id, cur.active_lang, sid, "rung1"))
    elif cur.algo_phase == "day2":
        items.append(_assignment_sheet(cur.active_algo_id, cur.active_lang, "full-recall", "day2"))
    elif cur.algo_phase == "voice":
        items.append(_voice_assignment(cur.active_algo_id, cur.active_lang))

    if cur.pending_voice_algo and cur.algo_phase != "voice":
        items.append(_voice_assignment(cur.pending_voice_algo, cur.pending_voice_lang or "csharp"))

    if kind == "advance":
        sections = data["sections"]
        sec = _pick_theory_section(db, cur, sections)
        if sec:
            dirty = db.query(SdeSectionProgress).filter_by(section_id=sec["id"], status="dirty").first()
            items.append({
                "type": "theory",
                "id": sec["id"],
                "section_id": sec["id"],
                "title": sec.get("title"),
                "title_es": sec.get("title_es"),
                "week_title": sec.get("week_title"),
                "week_title_es": sec.get("week_title_es"),
                "anchor": sec.get("anchor"),
                "anchor_es": sec.get("anchor_es"),
                "restudy": bool(dirty),
            })
        wd = date.today().weekday()
        if wd in (0, 2, 4):
            items.append({"type": "story", "id": "story"})
        if wd == 5 and data["sql"]:
            drill = data["sql"][min(cur.next_section_index, len(data["sql"]) - 1)]
            items.append({
                "type": "sql",
                "id": drill["id"],
                "prompt": drill.get("prompt"),
                "prompt_es": drill.get("prompt_es"),
            })
    return items


def _voice_assignment(algo_id: str, lang: str) -> dict:
    data = load_sde()
    algo = data["algos"][algo_id]
    voice = algo.get("voice") or {}
    return {
        "type": "voice",
        "id": f"voice:{algo_id}:{lang}",
        "algo_id": algo_id,
        "lang": lang,
        "title": algo.get("title"),
        "prompt": voice.get("prompt"),
        "prompt_en": voice.get("prompt_en"),
    }


def _codi_for(kind: str, assignments: list[dict], analysis: dict | None, locale: str = "en") -> dict:
    if analysis:
        copy = {"headline": analysis["line"], "cta": analysis.get("cta") or codi_copy("ready", locale)["cta"]}
        copy["mood"] = "worried"
        copy["to"] = _cta_path(assignments)
        return copy
    if kind == "return":
        return {**codi_copy("return", locale), "mood": "think", "to": "/sde/cards"}
    if kind == "flojo":
        return {**codi_copy("flojo", locale), "mood": "idle", "to": _cta_path(assignments)}
    first = next((a for a in assignments if not a.get("completed")), None)
    to = _cta_path(assignments)
    if first and first.get("type") == "algo_sheet" and first.get("reason") == "pool":
        return {
            **codi_copy("pool", locale, title=first.get("title") or ""),
            "mood": "happy",
            "to": to,
        }
    if first and first.get("type") == "algo_sheet":
        return {
            **codi_copy(
                "sheet",
                locale,
                title=first.get("title") or "",
                lang=LANG_LABEL.get(first.get("lang"), ""),
                prompt=(first.get("prompt") or "")[:80],
            ),
            "mood": "happy",
            "to": to,
        }
    return {**codi_copy("ready", locale), "mood": "happy", "to": to or "/sde/cards"}


def _localize_assignment(a: dict, locale: str) -> dict:
    data = load_sde()
    out = {k: v for k, v in a.items() if k != "starter_code"}
    typ = out.get("type")
    if typ == "flashcards":
        cards = []
        by_id = {c["id"]: c for c in data["cards"]}
        for c in out.get("cards") or []:
            src = by_id.get(c.get("id"), c)
            cards.append({**localize_card(src, locale), "section_id": c.get("section_id") or src.get("section_id")})
        out["cards"] = cards
    elif typ == "algo_sheet":
        algo = data["algos"].get(out.get("algo_id") or "")
        sheet = get_sheet(algo, out.get("lang") or "csharp", out.get("sheet_id") or "") if algo else {}
        out["prompt"] = sheet_prompt(sheet or out, locale)
        out["title"] = (algo or {}).get("title") or out.get("title")
    elif typ == "theory":
        sec = data["section_by_id"].get(out.get("section_id") or out.get("id") or "")
        if sec:
            loc = localize_section(sec, locale)
            out["title"] = loc["title"]
            out["week_title"] = loc["week_title"]
            out["anchor"] = loc["anchor"]
    elif typ == "voice":
        out["prompt"] = pick_field(out, "prompt", locale)
    elif typ == "sql":
        drill = next((d for d in data["sql"] if d["id"] == out.get("id")), None)
        out["prompt"] = pick_field(drill or out, "prompt", locale)
    elif typ == "debug":
        bug = data["debug_by_id"].get(out.get("bug_id") or "")
        src = bug or out
        out["title"] = pick_field(src, "title", locale) or src.get("title")
        out["error_hint"] = pick_field(src, "error_hint", locale) or src.get("error_hint")
    elif typ == "return":
        out["prompt"] = pick_field(out, "prompt", locale)
    elif typ == "reading":
        week = data.get("week_by_id", {}).get(out.get("week_id") or "")
        if week:
            out["title"] = pick_field(week, "title", locale) or out.get("title")
            out["intro"] = pick_field(week, "intro", locale) or out.get("intro")
        else:
            out["title"] = pick_field(out, "title", locale) or out.get("title")
            out["intro"] = pick_field(out, "intro", locale) or out.get("intro")
    elif typ in {"debug", "design", "project"}:
        out["title"] = pick_field(out, "title", locale) or out.get("title")
    return out


def _assignment_href(a: dict) -> str | None:
    typ = a.get("type")
    if typ == "reading":
        week_id = a.get("week_id") or str(a.get("id") or "").removeprefix("reading:")
        return f"/sde/reading/{week_id}" if week_id else None
    if typ == "flashcards":
        return "/sde/cards"
    if typ == "algo_sheet":
        return f"/sde/algo/{a['algo_id']}/{a['lang']}/{a['sheet_id']}"
    if typ == "theory":
        return f"/sde/section/{a.get('section_id') or a.get('id')}"
    if typ == "voice":
        return "/sde/voice"
    if typ == "sql":
        return f"/sde/sql/{a.get('id')}"
    if typ == "story":
        return "/stories"
    if typ == "debug":
        bug_id = a.get("bug_id")
        if not bug_id:
            raw = str(a.get("id") or "").removeprefix("debug:")
            bug_id = raw.rsplit(":", 1)[0] if raw else ""
        return f"/sde/debug/{bug_id}" if bug_id else None
    return None


def _cta_path(assignments: list[dict]) -> str:
    for a in assignments:
        if a.get("completed"):
            continue
        href = _assignment_href(a)
        if href:
            return href
    return "/"


def ensure_today(db: Session, locale: str = "en") -> dict:
    cur = get_cursor(db)
    data = load_sde()
    today = date.today()
    gap = inactivity_days(db, cur)
    rebuild = cur.session_date != today or not cur.today_assignments

    if rebuild:
        kind = "advance"
        if gap >= data["inactivity_days"] and cur.last_evidence_date:
            kind = "return"
        elif (
            cur.session_date
            and cur.session_date < today
            and not cur.session_complete
            and (today - cur.session_date).days == 1
        ):
            kind = "flojo"
        cur.session_date = today
        cur.session_kind = kind
        cur.session_complete = False
        cur.today_assignments = _build_assignments(db, cur, kind)
        db.commit()

    analysis = _latest_analysis(db, locale)
    assignments = [_localize_assignment(a, locale) for a in (cur.today_assignments or [])]
    return {
        "date": today.isoformat(),
        "kind": cur.session_kind,
        "complete": cur.session_complete,
        "assignments": assignments,
        "cursor": {
            "active_algo_id": cur.active_algo_id,
            "active_lang": cur.active_lang,
            "algo_phase": cur.algo_phase,
            "day1_index": cur.day1_index,
            "next_section_index": cur.next_section_index,
        },
        "analysis": analysis,
        "codi": _codi_for(cur.session_kind, assignments, analysis, locale),
    }


def _mark_assignment_done(cur: SdeCursor, assignment_id: str) -> None:
    from sqlalchemy.orm.attributes import flag_modified
    for a in cur.today_assignments or []:
        if a.get("id") == assignment_id:
            a["completed"] = True
    cur.today_assignments = list(cur.today_assignments or [])
    flag_modified(cur, "today_assignments")
    remaining = [a for a in cur.today_assignments if not a.get("completed") and a.get("type") != "story"]
    if not remaining:
        cur.session_complete = True


def review_cards(db: Session, results: list[dict]) -> dict:
    cur = get_cursor(db)
    dirty_sections: set[str] = set()
    fails = 0
    for r in results:
        cid = r["id"]
        ok = bool(r.get("ok"))
        section_id = r.get("section_id") or ""
        row = _card_row(db, cid, section_id)
        row.seen += 1
        row.last_ok = ok
        if not ok:
            row.fails += 1
            fails += 1
            if section_id:
                dirty_sections.add(section_id)
        elif row.fails > 0 and ok:
            row.fails = max(0, row.fails - 1)
    for sid in dirty_sections:
        sec = db.query(SdeSectionProgress).filter_by(section_id=sid).first()
        if not sec:
            sec = SdeSectionProgress(section_id=sid, status="dirty", dirty_fails=1)
            db.add(sec)
        else:
            sec.status = "dirty"
            sec.dirty_fails += 1
    _touch(db, cur)
    _mark_assignment_done(cur, "cards")
    db.commit()
    if fails:
        _save_analysis(db, "card_fail", f"{fails} carta(s) mal. Esas salen más mañana.", "Mazo", {"n": fails})
    return {"ok": True, "fails": fails, "dirty_sections": list(dirty_sections)}


def submit_sheet(db: Session, algo_id: str, lang: str, sheet_id: str, code: str) -> dict:
    data = load_sde()
    algo = data["algos"][algo_id]
    sheet = get_sheet(algo, lang, sheet_id)
    if not sheet:
        return {"passed": False, "error": "Hoja no encontrada"}
    fn = sheet.get("fn_name") or (algo.get("languages") or {}).get(lang, {}).get("fn_name")
    result = run_leetcode_code(code, algo.get("test_cases") or [], fn_name=fn, language=lang)
    passed = bool(result.get("passed"))
    cur = get_cursor(db)
    cur.last_sheet_id = sheet_id
    reason = None
    for a in cur.today_assignments or []:
        if a.get("id") == f"{algo_id}:{lang}:{sheet_id}":
            reason = a.get("reason")
            break

    prog = _algo_row(db, algo_id, lang)
    if not passed:
        if reason == "pool":
            prog.pool_fails += 1
            if prog.pool_fails >= 2:
                prog.status = "failed"
                _save_analysis(db, "pool_fail2", f"{algo.get('title')} al pool de fallados. Día 1 de nuevo.", "Reiniciar", {"title": algo.get("title")})
            else:
                # inject recovery sheets tomorrow by setting phase — today add remaining recovery
                _save_analysis(db, "pool_fail", f"{algo.get('title')} falló. Peldaños 1-2-3 y el entero.", "Peldaños", {"title": algo.get("title")})
                extra = []
                for sid in recovery_sheet_ids(algo, lang):
                    extra.append(_assignment_sheet(algo_id, lang, sid, "pool_recovery"))
                cur.today_assignments = (cur.today_assignments or []) + extra
        elif reason == "warmup":
            _save_analysis(db, "warmup_fail", "Warm-up mal: solo esta hoja hoy.", "Repetir hoja")
        else:
            _save_analysis(db, "sheet_fail", "Esta hoja otra vez. No avanzas el peldaño.", "Repetir")
        _touch(db, cur)
        db.commit()
        return {**result, "passed": False}

    # passed
    if reason == "failed_restart":
        ids = day1_sheet_ids(algo, lang)
        if sheet_id == ids[-1]:
            prog.status = "active"
            prog.pool_fails = 0
            cur.algo_phase = "day2"
            cur.active_algo_id = algo_id
            cur.active_lang = lang
    if reason == "pool":
        prog.pool_fails = 0
    if reason == "day1" or reason == "rung1" or reason == "failed_restart":
        ids = day1_sheet_ids(algo, lang)
        if reason == "rung1":
            ids = ids[:5]
        try:
            idx = ids.index(sheet_id)
            cur.day1_index = max(cur.day1_index, idx + 1)
            if cur.day1_index >= len(ids):
                if reason == "rung1":
                    cur.algo_phase = "day1"
                    # finished intro 5; remaining day1 continues next advance day
                    cur.day1_index = 5
                else:
                    cur.algo_phase = "day2"
                    cur.day1_index = 0
        except ValueError:
            pass
    if reason == "day2":
        prog.status = "completed"
        prog.completed_at = datetime.utcnow()
        prog.pool_fails = 0
        cur.pending_voice_algo = algo_id
        cur.pending_voice_lang = lang
        cur.algo_phase = "voice"
        voice = _voice_assignment(algo_id, lang)
        cur.today_assignments = list(cur.today_assignments or []) + [voice]
    if reason == "pool_recovery":
        if sheet_id == "full-recall":
            prog.pool_fails = 0
            prog.status = "completed"

    _mark_assignment_done(cur, f"{algo_id}:{lang}:{sheet_id}")
    _touch(db, cur)
    db.commit()
    return {**result, "passed": True}


def submit_voice(db: Session, algo_id: str, lang: str, transcript: str) -> dict:
    data = load_sde()
    algo = data["algos"][algo_id]
    keys = [_norm(k) for k in (algo.get("voice") or {}).get("keywords") or []]
    blob = _norm(transcript)
    hits = [k for k in keys if k in blob]
    passed = len(hits) >= max(1, min(2, len(keys)))
    cur = get_cursor(db)
    prog = _algo_row(db, algo_id, lang)
    if not passed:
        _save_analysis(db, "voice_fail", "No cerró la explicación. No hay cambio de idioma.", "Hablar otra vez")
        _touch(db, cur)
        db.commit()
        return {"passed": False, "hits": hits, "needed": keys[:4]}

    prog.voice_passed = True
    cur.pending_voice_algo = None
    cur.pending_voice_lang = None
    # next language or next algo
    first, second = data["first_lang"], data["second_lang"]
    if lang == first:
        other = _algo_row(db, algo_id, second)
        if other.status != "completed":
            cur.active_algo_id = algo_id
            cur.active_lang = second
            cur.algo_phase = "rung1"
            cur.day1_index = 0
            extra = [
                _assignment_sheet(algo_id, second, sid, "rung1")
                for sid in day1_sheet_ids(data["algos"][algo_id], second)[:5]
            ]
            cur.today_assignments = list(cur.today_assignments or []) + extra
        else:
            _advance_algo(cur, data, db)
    else:
        _advance_algo(cur, data, db)
        extra = [
            _assignment_sheet(cur.active_algo_id, cur.active_lang, sid, "rung1")
            for sid in day1_sheet_ids(data["algos"][cur.active_algo_id], cur.active_lang)[:5]
        ]
        cur.today_assignments = list(cur.today_assignments or []) + extra
    _mark_assignment_done(cur, f"voice:{algo_id}:{lang}")
    _touch(db, cur)
    db.commit()
    return {"passed": True, "hits": hits}


def _advance_algo(cur: SdeCursor, data: dict, db: Session) -> None:
    order = data["algo_order"]
    try:
        i = order.index(cur.active_algo_id)
    except ValueError:
        i = 0
    nxt = order[i + 1] if i + 1 < len(order) else order[0]
    cur.active_algo_id = nxt
    cur.active_lang = data["first_lang"]
    cur.algo_phase = "rung1"
    cur.day1_index = 0
    _algo_row(db, nxt, data["first_lang"])


def submit_theory(db: Session, section_id: str, answers: list[int], locale: str = "en") -> dict:
    data = load_sde()
    sec = data["section_by_id"].get(section_id)
    if not sec:
        return {"passed": False, "error": "Section not found" if not is_es(locale) else "Sección no existe"}
    loc = localize_section(sec, locale)
    qs = sec.get("questions") or []
    correct = 0
    for i, q in enumerate(qs):
        if i < len(answers) and answers[i] == q.get("answer"):
            correct += 1
    passed = correct >= max(1, len(qs) - 1)
    row = db.query(SdeSectionProgress).filter_by(section_id=section_id).first()
    if not row:
        row = SdeSectionProgress(section_id=section_id)
        db.add(row)
    row.last_score = correct / max(1, len(qs))
    cur = get_cursor(db)
    if not passed:
        row.status = "dirty"
        row.dirty_fails += 1
        _save_analysis(db, "theory_fail", "Quiz mal. Mañana la misma sección, no la siguiente.", "Releer")
    else:
        row.status = "mastered"
        if cur.next_section_index < len(data["sections"]) and data["sections"][cur.next_section_index]["id"] == section_id:
            cur.next_section_index += 1
        for c in sec.get("cards") or []:
            _card_row(db, c["id"], section_id)
    _mark_assignment_done(cur, section_id)
    _touch(db, cur)
    db.commit()
    return {
        "passed": passed,
        "correct": correct,
        "total": len(qs),
        "cards": [{**localize_card(c, locale), "section_id": section_id} for c in sec.get("cards") or []],
        "reading": loc["reading"],
        "title": loc["title"],
        "questions": loc["questions"],
    }


def get_section(section_id: str, locale: str = "en") -> dict | None:
    sec = load_sde()["section_by_id"].get(section_id)
    return localize_section(sec, locale) if sec else None


def get_reading(week_id: str, locale: str = "en") -> dict | None:
    week = load_sde().get("week_by_id", {}).get(week_id)
    if not week:
        return None
    return {
        "id": f"reading:{week_id}",
        "type": "reading",
        "week_id": week_id,
        "title": pick_field(week, "title", locale) or week.get("title"),
        "intro": pick_field(week, "intro", locale) or week.get("intro"),
        "minutes": week.get("minutes"),
    }


def complete_reading(db: Session, week_id: str) -> dict:
    cur = get_cursor(db)
    _mark_assignment_done(cur, f"reading:{week_id}")
    _touch(db, cur)
    db.commit()
    return {"ok": True}


def get_debug(bug_id: str, locale: str = "en") -> dict | None:
    data = load_sde()
    bug = data["debug_by_id"].get(bug_id)
    if not bug:
        return None
    return {
        "id": bug["id"],
        "title": pick_field(bug, "title", locale) or bug.get("title"),
        "difficulty": bug.get("difficulty"),
        "family": bug.get("family"),
        "lang": bug.get("lang", "csharp"),
        "error_hint": pick_field(bug, "error_hint", locale) or bug.get("error_hint"),
        "fn_name": bug.get("fn_name"),
        "broken_code": bug.get("broken_code", ""),
        "test_cases": bug.get("test_cases") or [],
        "cause_locked": True,
    }


def submit_debug(db: Session, bug_id: str, code: str, locale: str = "en") -> dict:
    data = load_sde()
    bug = data["debug_by_id"].get(bug_id)
    if not bug:
        return {"passed": False, "error": "debug bug not found"}
    lang = bug.get("lang", "csharp")
    try:
        result = run_leetcode_code(code, bug.get("test_cases") or [], fn_name=bug.get("fn_name") or "solution", language=lang)
    except FileNotFoundError:
        return {"passed": False, "error": "C# runner is not available (dotnet missing)."}
    except Exception as exc:
        return {"passed": False, "error": str(exc)}
    row = _debug_row(db, bug_id)
    cur = get_cursor(db)
    if result.get("passed"):
        row.status = "completed"
        row.completed_at = datetime.utcnow()
        for a in cur.today_assignments or []:
            if a.get("type") == "debug" and a.get("bug_id") == bug_id:
                _mark_assignment_done(cur, a.get("id") or f"debug:{bug_id}")
                break
        else:
            _mark_assignment_done(cur, f"debug:{bug_id}")
        _touch(db, cur)
        db.commit()
        return {**result, "cause": pick_field(bug, "cause", locale) or bug.get("cause")}
    row.status = "failed"
    row.fails = (row.fails or 0) + 1
    db.commit()
    return result


def get_sheet_payload(algo_id: str, lang: str, sheet_id: str, locale: str = "en") -> dict | None:
    data = load_sde()
    algo = data["algos"].get(algo_id)
    if not algo:
        return None
    sheet = get_sheet(algo, lang, sheet_id)
    if not sheet:
        return None
    payload = _assignment_sheet(algo_id, lang, sheet_id, "open")
    payload["prompt"] = sheet_prompt(sheet, locale)
    payload["starter_code"] = sheet.get("starter_code", "")
    payload["description"] = f"{algo.get('title')} · {LANG_LABEL.get(lang, lang)}"
    payload["test_cases"] = algo.get("test_cases")
    return payload


def log_offline(db: Session, kinds: list[str], section_id: str | None) -> dict:
    db.add(SdeOfflineLog(date=date.today(), kinds=kinds, section_id=section_id, verified=False))
    db.commit()
    return {"ok": True, "verify": True}


def verify_offline(db: Session, passed: bool) -> dict:
    row = db.query(SdeOfflineLog).filter_by(verified=False).order_by(SdeOfflineLog.id.desc()).first()
    if row:
        row.verified = True
    cur = get_cursor(db)
    if passed:
        _touch(db, cur)
    db.commit()
    return {"ok": True, "passed": passed}


def submit_sql(db: Session, drill_id: str, sql: str) -> dict:
    data = load_sde()
    drill = next((d for d in data["sql"] if d["id"] == drill_id), None)
    if not drill:
        return {"passed": False}
    def norm(s: str) -> str:
        return " ".join((s or "").lower().replace(";", " ").split())
    passed = norm(sql) == norm(drill.get("expected", ""))
    cur = get_cursor(db)
    if passed:
        _mark_assignment_done(cur, drill_id)
        _touch(db, cur)
    else:
        _save_analysis(db, "sql_fail", "SQL mal. Revisa el join/índice y reintenta.", "SQL")
        _touch(db, cur)
    db.commit()
    return {"passed": passed, "expected": drill.get("expected") if not passed else None}


def travel_pack(db: Session, locale: str = "en") -> str:
    today = ensure_today(db, locale)
    loc = "es" if is_es(locale) else "en"
    lines = [PACK["title"][loc], ""]
    for a in today["assignments"]:
        if a.get("type") == "flashcards":
            lines.append(PACK["cards"][loc])
            for c in a.get("cards") or []:
                lines.append(f"- {c['front']}")
                lines.append(f"  {c['back']}")
        if a.get("type") == "theory":
            sec = get_section(a["section_id"], locale)
            if sec:
                lines.append(f"## {sec['title']}")
                lines.append(sec.get("reading") or "")
        if a.get("type") == "algo_sheet":
            lines.append(f"## {a.get('title')} {a.get('sheet_id')}")
            lines.append(a.get("prompt") or "")
    return "\n".join(lines)

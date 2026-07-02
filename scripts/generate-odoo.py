#!/usr/bin/env python3
"""Generate the independent Odoo track (levels OA, OB, OC — 50 pages each).

Same domain-mastery engine as the Python track. Exercises simulate real Odoo
patterns (recordsets, domains, ORM create/write/search, support flows) with
runnable, checkable Python. Each level closes with a practical checkpoint.
"""
from __future__ import annotations

import contextlib
import io
import shutil
from pathlib import Path

import yaml

from kumon_starters import safe_starter

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "odoo"
STD_PATH = ROOT / "content" / "schedule" / "odoo-levels.yaml"
PAGES_PER_SET = 10


def run_capture(code: str) -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(code, "<drill>", "exec"), {})  # noqa: S102 (trusted content)
    return buf.getvalue().rstrip("\n")


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def explicit(items: list[tuple[str, str]]) -> list[dict]:
    return [{"prompt": p, "code": c} for p, c in items]


def scaffolding_for(order: int) -> str:
    if order <= 3:
        return "full"
    if order <= 7:
        return "minimal"
    return "none"


# ---------------------------------------------------------------------------
# OA — Registros y dominios
# ---------------------------------------------------------------------------

def level_oa() -> list[list[dict]]:
    return [
        explicit([
            ("Crea un registro cliente con name='ACME' y city='Lima'; imprime su name.", "rec = {'name': 'ACME', 'city': 'Lima'}\nprint(rec['name'])"),
            ("Crea un registro producto con name='Laptop' y price=900; imprime el price.", "rec = {'name': 'Laptop', 'price': 900}\nprint(rec['price'])"),
            ("Crea un ticket con subject='Error' y state='new'; imprime el state.", "rec = {'subject': 'Error', 'state': 'new'}\nprint(rec['state'])"),
            ("Crea un registro con name='Bob' y agrega despues el campo email='b@x.com'; imprime el dict.", "rec = {'name': 'Bob'}\nrec['email'] = 'b@x.com'\nprint(rec)"),
            ("Crea una orden con amount=150; aplicale 10% de descuento e imprime el nuevo amount.", "order = {'amount': 150}\nprint(order['amount'] * 0.9)"),
            ("Crea un partner con name='Globex'; imprime cuantos campos tiene el registro.", "rec = {'name': 'Globex', 'vat': '123', 'active': True}\nprint(len(rec))"),
            ("Crea un producto con price=200 y qty=3; imprime el subtotal (price*qty).", "rec = {'price': 200, 'qty': 3}\nprint(rec['price'] * rec['qty'])"),
            ("Crea un ticket con priority=2; usa .get('priority', 0) e imprime el valor.", "rec = {'subject': 'X', 'priority': 2}\nprint(rec.get('priority', 0))"),
            ("Crea un cliente sin email; usa .get('email', 'N/A') e imprime el resultado.", "rec = {'name': 'NoMail'}\nprint(rec.get('email', 'N/A'))"),
            ("Crea un registro con active=True; cambialo a False e imprime el registro.", "rec = {'name': 'Old', 'active': True}\nrec['active'] = False\nprint(rec)"),
        ]),
        explicit([
            ("Crea un recordset (lista) de 3 ordenes e imprime cuantas hay.", "orders = [{'id': 1}, {'id': 2}, {'id': 3}]\nprint(len(orders))"),
            ("Dado un recordset de productos, imprime el name del primero.", "products = [{'name': 'A'}, {'name': 'B'}]\nprint(products[0]['name'])"),
            ("Dado un recordset de clientes, imprime el name del ultimo.", "partners = [{'name': 'X'}, {'name': 'Y'}, {'name': 'Z'}]\nprint(partners[-1]['name'])"),
            ("Recorre un recordset de 3 tickets e imprime cada subject separado por '|'.", "tickets = [{'subject': 'a'}, {'subject': 'b'}, {'subject': 'c'}]\nprint('|'.join(t['subject'] for t in tickets))"),
            ("Agrega una orden nueva al recordset e imprime el total de ordenes.", "orders = [{'id': 1}, {'id': 2}]\norders.append({'id': 3})\nprint(len(orders))"),
            ("Dado un recordset de productos con price, imprime una lista de precios.", "products = [{'price': 10}, {'price': 20}, {'price': 5}]\nprint([p['price'] for p in products])"),
            ("Imprime True si el recordset de ordenes esta vacio.", "orders = []\nprint(len(orders) == 0)"),
            ("Dado un recordset, imprime el id de cada registro separado por espacio.", "recs = [{'id': 7}, {'id': 8}, {'id': 9}]\nfor r in recs:\n    print(r['id'], end=' ')"),
            ("Cuenta cuantos productos tienen price mayor a 50.", "products = [{'price': 100}, {'price': 30}, {'price': 80}]\nprint(len([p for p in products if p['price'] > 50]))"),
            ("Dado un recordset de tickets, imprime el subject de los abiertos (state=='open').", "tickets = [{'subject': 'a', 'state': 'open'}, {'subject': 'b', 'state': 'done'}]\nprint([t['subject'] for t in tickets if t['state'] == 'open'])"),
        ]),
        explicit([
            ("Dominio [('state','=','done')]: filtra y cuenta las ordenes hechas.", "orders = [{'state': 'done'}, {'state': 'open'}, {'state': 'done'}]\nprint(len([o for o in orders if o['state'] == 'done']))"),
            ("Filtra los productos con price > 100 e imprime cuantos hay.", "products = [{'price': 150}, {'price': 90}, {'price': 200}]\nprint(len([p for p in products if p['price'] > 100]))"),
            ("Filtra los clientes activos (active==True) e imprime sus names.", "partners = [{'name': 'A', 'active': True}, {'name': 'B', 'active': False}]\nprint([p['name'] for p in partners if p['active']])"),
            ("Dominio [('priority','>=',2)]: filtra tickets y cuenta.", "tickets = [{'priority': 1}, {'priority': 3}, {'priority': 2}]\nprint(len([t for t in tickets if t['priority'] >= 2]))"),
            ("Filtra ordenes con amount entre 100 y 500 (inclusive) e imprime cuantas.", "orders = [{'amount': 50}, {'amount': 200}, {'amount': 600}, {'amount': 100}]\nprint(len([o for o in orders if 100 <= o['amount'] <= 500]))"),
            ("Filtra productos cuyo name empiece con 'A' e imprime los names.", "products = [{'name': 'Apple'}, {'name': 'Banana'}, {'name': 'Avocado'}]\nprint([p['name'] for p in products if p['name'].startswith('A')])"),
            ("Dominio combinado: tickets 'open' Y priority>=2; cuenta cuantos cumplen.", "tickets = [{'state': 'open', 'priority': 3}, {'state': 'open', 'priority': 1}, {'state': 'done', 'priority': 3}]\nprint(len([t for t in tickets if t['state'] == 'open' and t['priority'] >= 2]))"),
            ("Filtra los registros sin email (no tienen la clave) e imprime cuantos.", "recs = [{'name': 'A', 'email': 'a@x'}, {'name': 'B'}, {'name': 'C'}]\nprint(len([r for r in recs if 'email' not in r]))"),
            ("Filtra ordenes con state distinto de 'cancel' e imprime cuantas quedan.", "orders = [{'state': 'done'}, {'state': 'cancel'}, {'state': 'open'}]\nprint(len([o for o in orders if o['state'] != 'cancel']))"),
            ("Dominio ['|',('state','=','open'),('state','=','draft')]: cuenta open o draft.", "tickets = [{'state': 'open'}, {'state': 'draft'}, {'state': 'done'}]\nprint(len([t for t in tickets if t['state'] in ('open', 'draft')]))"),
        ]),
        explicit([
            ("mapped('name'): imprime la lista de names de los productos.", "products = [{'name': 'A'}, {'name': 'B'}, {'name': 'C'}]\nprint([p['name'] for p in products])"),
            ("mapped('amount'): imprime la lista de montos de las ordenes.", "orders = [{'amount': 10}, {'amount': 20}]\nprint([o['amount'] for o in orders])"),
            ("mapped('id'): imprime los ids de un recordset.", "recs = [{'id': 5}, {'id': 6}, {'id': 7}]\nprint([r['id'] for r in recs])"),
            ("mapped sobre relacion: imprime el name del partner de cada orden.", "orders = [{'partner': {'name': 'X'}}, {'partner': {'name': 'Y'}}]\nprint([o['partner']['name'] for o in orders])"),
            ("mapped con transformacion: imprime los precios con 16% IVA.", "products = [{'price': 100}, {'price': 50}]\nprint([round(p['price'] * 1.16, 2) for p in products])"),
            ("mapped('state') y unicos: imprime los estados distintos ordenados.", "tickets = [{'state': 'open'}, {'state': 'done'}, {'state': 'open'}]\nprint(sorted(set(t['state'] for t in tickets)))"),
            ("mapped('qty') y suma: imprime la cantidad total.", "lines = [{'qty': 2}, {'qty': 3}, {'qty': 5}]\nprint(sum(l['qty'] for l in lines))"),
            ("mapped a mayusculas: imprime los names en mayuscula.", "products = [{'name': 'a'}, {'name': 'b'}]\nprint([p['name'].upper() for p in products])"),
            ("mapped con filtro: names de productos con price>50.", "products = [{'name': 'A', 'price': 100}, {'name': 'B', 'price': 20}]\nprint([p['name'] for p in products if p['price'] > 50])"),
            ("mapped('email') con default: usa .get para los que no tienen.", "recs = [{'email': 'a@x'}, {}, {'email': 'c@x'}]\nprint([r.get('email', 'N/A') for r in recs])"),
        ]),
        explicit([
            ("Suma el amount_total de todas las ordenes.", "orders = [{'amount': 100}, {'amount': 250}, {'amount': 50}]\nprint(sum(o['amount'] for o in orders))"),
            ("Calcula el promedio de price de los productos.", "products = [{'price': 10}, {'price': 20}, {'price': 30}]\nprint(sum(p['price'] for p in products) / len(products))"),
            ("Suma solo los amounts de ordenes 'done'.", "orders = [{'amount': 100, 'state': 'done'}, {'amount': 50, 'state': 'open'}, {'amount': 30, 'state': 'done'}]\nprint(sum(o['amount'] for o in orders if o['state'] == 'done'))"),
            ("Imprime el amount maximo entre las ordenes.", "orders = [{'amount': 100}, {'amount': 400}, {'amount': 250}]\nprint(max(o['amount'] for o in orders))"),
            ("Suma qty*price de cada linea (subtotal total).", "lines = [{'qty': 2, 'price': 10}, {'qty': 1, 'price': 50}]\nprint(sum(l['qty'] * l['price'] for l in lines))"),
            ("Cuenta cuantas ordenes hay por estado (dict).", "orders = [{'state': 'done'}, {'state': 'open'}, {'state': 'done'}]\nfreq = {}\nfor o in orders:\n    freq[o['state']] = freq.get(o['state'], 0) + 1\nprint(freq)"),
            ("Imprime el name del producto mas caro.", "products = [{'name': 'A', 'price': 100}, {'name': 'B', 'price': 300}]\nprint(max(products, key=lambda p: p['price'])['name'])"),
            ("Suma los amounts y aplica 18% IGV al total.", "orders = [{'amount': 100}, {'amount': 200}]\nprint(round(sum(o['amount'] for o in orders) * 1.18, 2))"),
            ("Cuenta cuantos productos tienen stock 0.", "products = [{'stock': 0}, {'stock': 5}, {'stock': 0}]\nprint(len([p for p in products if p['stock'] == 0]))"),
            ("Imprime el total de unidades vendidas (suma de qty) de las lineas 'done'.", "lines = [{'qty': 3, 'state': 'done'}, {'qty': 2, 'state': 'draft'}, {'qty': 4, 'state': 'done'}]\nprint(sum(l['qty'] for l in lines if l['state'] == 'done'))"),
        ]),
    ]


# ---------------------------------------------------------------------------
# OB — ORM y modelos
# ---------------------------------------------------------------------------

def level_ob() -> list[list[dict]]:
    return [
        explicit([
            ("Define un modelo product con campos name='' y price=0.0; imprime las claves.", "product = {'name': '', 'price': 0.0}\nprint(list(product.keys()))"),
            ("Define un modelo partner con name, email y active=True; imprime el dict.", "partner = {'name': '', 'email': '', 'active': True}\nprint(partner)"),
            ("Define un modelo ticket con state='new' por defecto; imprime el state.", "ticket = {'subject': '', 'state': 'new'}\nprint(ticket['state'])"),
            ("Define un modelo con un campo Float price con default 0.0; imprime su tipo.", "product = {'price': 0.0}\nprint(type(product['price']).__name__)"),
            ("Define un modelo order con line_ids=[] (one2many vacio); imprime su longitud.", "order = {'line_ids': []}\nprint(len(order['line_ids']))"),
            ("Define un modelo con campo Boolean active=True; niegalo e imprime.", "rec = {'active': True}\nprint(not rec['active'])"),
            ("Define un modelo con campo Integer sequence=10; aumentalo en 1 e imprime.", "rec = {'sequence': 10}\nrec['sequence'] += 1\nprint(rec['sequence'])"),
            ("Define un modelo con name requerido; valida que no este vacio e imprime True.", "rec = {'name': 'X'}\nprint(bool(rec['name']))"),
            ("Define un modelo con default qty=1; imprime qty.", "line = {'qty': 1}\nprint(line['qty'])"),
            ("Define un modelo con campo Selection state en ('draft','done'); imprime las opciones.", "states = ('draft', 'done')\nprint(states)"),
        ]),
        explicit([
            ("create: agrega un registro nuevo (id autoincrement) e imprime su id.", "records = [{'id': 1}, {'id': 2}]\nnew = {'id': len(records) + 1, 'name': 'C'}\nrecords.append(new)\nprint(new['id'])"),
            ("create: agrega un producto y luego imprime cuantos registros hay.", "records = [{'id': 1}]\nrecords.append({'id': 2, 'name': 'P'})\nprint(len(records))"),
            ("create con valores por defecto: state='draft' si no se especifica.", "vals = {'name': 'T'}\nrec = {'state': 'draft', **vals}\nprint(rec)"),
            ("create varios: agrega 3 registros en un bucle e imprime el total.", "records = []\nfor i in range(1, 4):\n    records.append({'id': i})\nprint(len(records))"),
            ("create: el nuevo id es max(ids)+1; calculalo e imprimelo.", "records = [{'id': 4}, {'id': 7}, {'id': 2}]\nnew_id = max(r['id'] for r in records) + 1\nprint(new_id)"),
            ("create y devuelve el registro creado; imprime su name.", "def create(records, vals):\n    rec = {'id': len(records) + 1, **vals}\n    records.append(rec)\n    return rec\nprint(create([], {'name': 'Acme'})['name'])"),
            ("create con campo calculado total=qty*price; imprime el total.", "vals = {'qty': 3, 'price': 20}\nrec = {**vals, 'total': vals['qty'] * vals['price']}\nprint(rec['total'])"),
            ("create copiando defaults y sobreescribiendo uno; imprime el dict.", "defaults = {'state': 'draft', 'active': True}\nrec = {**defaults, 'state': 'open'}\nprint(rec)"),
            ("create varios y devuelve la lista de ids creados.", "records = []\nfor n in ['A', 'B', 'C']:\n    records.append({'id': len(records) + 1, 'name': n})\nprint([r['id'] for r in records])"),
            ("create con validacion: no crear si name vacio; imprime cuantos se crearon.", "records = []\nfor name in ['A', '', 'C']:\n    if name:\n        records.append({'name': name})\nprint(len(records))"),
        ]),
        explicit([
            ("write: actualiza el price del registro id=1 a 99 e imprime el registro.", "records = [{'id': 1, 'price': 10}]\nfor r in records:\n    if r['id'] == 1:\n        r['price'] = 99\nprint(records[0])"),
            ("write: cambia el state del ticket id=2 a 'done'; imprime el state.", "tickets = [{'id': 1, 'state': 'new'}, {'id': 2, 'state': 'new'}]\nfor t in tickets:\n    if t['id'] == 2:\n        t['state'] = 'done'\nprint(tickets[1]['state'])"),
            ("write masivo: pon active=False en todos los registros; imprime la lista.", "records = [{'active': True}, {'active': True}]\nfor r in records:\n    r['active'] = False\nprint(records)"),
            ("write: incrementa el stock de todos los productos en 10; imprime los stocks.", "products = [{'stock': 5}, {'stock': 0}]\nfor p in products:\n    p['stock'] += 10\nprint([p['stock'] for p in products])"),
            ("write condicional: marca 'done' los tickets con priority 3; cuenta cuantos cambiaron.", "tickets = [{'priority': 3, 'state': 'open'}, {'priority': 1, 'state': 'open'}]\nc = 0\nfor t in tickets:\n    if t['priority'] == 3:\n        t['state'] = 'done'\n        c += 1\nprint(c)"),
            ("write: aplica 10% de descuento al price de cada producto; imprime los nuevos precios.", "products = [{'price': 100}, {'price': 50}]\nfor p in products:\n    p['price'] = round(p['price'] * 0.9, 2)\nprint([p['price'] for p in products])"),
            ("write: agrega un campo 'updated'=True a un registro; imprime el dict.", "rec = {'id': 1, 'name': 'X'}\nrec['updated'] = True\nprint(rec)"),
            ("write con funcion update(): cambia varios campos a la vez.", "rec = {'a': 1, 'b': 2}\nrec.update({'b': 20, 'c': 30})\nprint(rec)"),
            ("write: renombra el name del registro id=3 a 'Nuevo'; imprime el name.", "records = [{'id': 3, 'name': 'Viejo'}]\nfor r in records:\n    if r['id'] == 3:\n        r['name'] = 'Nuevo'\nprint(records[0]['name'])"),
            ("write: suma 1 a la sequence de cada registro; imprime la lista de sequences.", "records = [{'sequence': 1}, {'sequence': 5}]\nfor r in records:\n    r['sequence'] += 1\nprint([r['sequence'] for r in records])"),
        ]),
        explicit([
            ("search([('state','=','open')]): imprime los ids de los registros abiertos.", "recs = [{'id': 1, 'state': 'open'}, {'id': 2, 'state': 'done'}, {'id': 3, 'state': 'open'}]\nprint([r['id'] for r in recs if r['state'] == 'open'])"),
            ("search([('price','>',100)]): imprime cuantos productos cumplen.", "products = [{'price': 150}, {'price': 50}, {'price': 200}]\nprint(len([p for p in products if p['price'] > 100]))"),
            ("search_count: cuenta los tickets con priority>=2.", "tickets = [{'priority': 1}, {'priority': 3}, {'priority': 2}]\nprint(len([t for t in tickets if t['priority'] >= 2]))"),
            ("search con limit=1: imprime el name del primer producto activo.", "products = [{'name': 'A', 'active': False}, {'name': 'B', 'active': True}, {'name': 'C', 'active': True}]\nactivos = [p for p in products if p['active']]\nprint(activos[0]['name'])"),
            ("search con order: imprime los names de productos ordenados por price.", "products = [{'name': 'A', 'price': 30}, {'name': 'B', 'price': 10}]\nprint([p['name'] for p in sorted(products, key=lambda x: x['price'])])"),
            ("search([('name','ilike','a')]): imprime names que contienen 'a' (minuscula).", "products = [{'name': 'Apple'}, {'name': 'Kiwi'}, {'name': 'Banana'}]\nprint([p['name'] for p in products if 'a' in p['name'].lower()])"),
            ("browse(2): busca el registro con id=2 e imprime su name.", "recs = [{'id': 1, 'name': 'X'}, {'id': 2, 'name': 'Y'}]\nrec = next(r for r in recs if r['id'] == 2)\nprint(rec['name'])"),
            ("search domain AND: state 'open' Y amount>100; imprime ids.", "recs = [{'id': 1, 'state': 'open', 'amount': 150}, {'id': 2, 'state': 'open', 'amount': 50}]\nprint([r['id'] for r in recs if r['state'] == 'open' and r['amount'] > 100])"),
            ("search devuelve [] si no hay coincidencias; imprime el resultado.", "recs = [{'state': 'done'}]\nprint([r for r in recs if r['state'] == 'cancel'])"),
            ("exists: imprime True si existe algun ticket 'new'.", "tickets = [{'state': 'new'}, {'state': 'done'}]\nprint(any(t['state'] == 'new' for t in tickets))"),
        ]),
        explicit([
            ("many2one: dado partner_id=2, busca el name del partner en el diccionario de partners.", "partners = {1: 'ACME', 2: 'Globex'}\norder = {'partner_id': 2}\nprint(partners[order['partner_id']])"),
            ("many2one: imprime el name del partner de cada orden.", "partners = {1: 'A', 2: 'B'}\norders = [{'partner_id': 1}, {'partner_id': 2}]\nprint([partners[o['partner_id']] for o in orders])"),
            ("one2many: cuenta cuantas lineas tiene una orden.", "order = {'line_ids': [{'qty': 1}, {'qty': 2}, {'qty': 3}]}\nprint(len(order['line_ids']))"),
            ("many2one con default: si partner_id no existe, imprime 'Sin cliente'.", "partners = {1: 'A'}\norder = {'partner_id': 9}\nprint(partners.get(order['partner_id'], 'Sin cliente'))"),
            ("one2many: suma los subtotales (qty*price) de las lineas de la orden.", "order = {'lines': [{'qty': 2, 'price': 10}, {'qty': 1, 'price': 5}]}\nprint(sum(l['qty'] * l['price'] for l in order['lines']))"),
            ("many2one inverso: cuenta cuantas ordenes tiene el partner_id=1.", "orders = [{'partner_id': 1}, {'partner_id': 2}, {'partner_id': 1}]\nprint(len([o for o in orders if o['partner_id'] == 1]))"),
            ("many2many: imprime las etiquetas (tags) de un ticket.", "ticket = {'tag_ids': ['urgente', 'bug']}\nprint(ticket['tag_ids'])"),
            ("Relacion anidada: imprime el name de la ciudad del partner de la orden.", "order = {'partner': {'name': 'X', 'city': {'name': 'Lima'}}}\nprint(order['partner']['city']['name'])"),
            ("many2one: agrupa los names de partner por sus ordenes e imprime la lista.", "partners = {1: 'A', 2: 'B'}\norders = [{'partner_id': 2}, {'partner_id': 1}, {'partner_id': 2}]\nprint([partners[o['partner_id']] for o in orders])"),
            ("one2many: imprime True si todas las lineas tienen qty>0.", "order = {'lines': [{'qty': 1}, {'qty': 2}]}\nprint(all(l['qty'] > 0 for l in order['lines']))"),
        ]),
    ]


# ---------------------------------------------------------------------------
# OC — Flujos y soporte
# ---------------------------------------------------------------------------

def level_oc() -> list[list[dict]]:
    return [
        explicit([
            ("Un ticket pasa de 'new' a 'in_progress'; imprime el nuevo estado.", "flujo = {'new': 'in_progress', 'in_progress': 'done'}\nprint(flujo['new'])"),
            ("De 'in_progress' el ticket pasa a 'done'; imprime el nuevo estado.", "flujo = {'new': 'in_progress', 'in_progress': 'done'}\nprint(flujo['in_progress'])"),
            ("Define next_state(s) con el flujo new->in_progress->done; llamala con 'new'.", "def next_state(s):\n    flujo = {'new': 'in_progress', 'in_progress': 'done'}\n    return flujo.get(s, s)\nprint(next_state('new'))"),
            ("Si el estado es 'done', next_state lo deja igual; imprime el resultado con 'done'.", "def next_state(s):\n    flujo = {'new': 'in_progress', 'in_progress': 'done'}\n    return flujo.get(s, s)\nprint(next_state('done'))"),
            ("Imprime True si la transicion de 'new' a 'in_progress' es valida.", "validas = {('new', 'in_progress'), ('in_progress', 'done')}\nprint(('new', 'in_progress') in validas)"),
            ("Imprime False si se intenta pasar de 'new' directo a 'done'.", "validas = {('new', 'in_progress'), ('in_progress', 'done')}\nprint(('new', 'done') in validas)"),
            ("Avanza un ticket dos pasos desde 'new' e imprime el estado final.", "flujo = {'new': 'in_progress', 'in_progress': 'done'}\ns = 'new'\nfor _ in range(2):\n    s = flujo.get(s, s)\nprint(s)"),
            ("Cierra un ticket: pon state='done' y closed=True; imprime el dict.", "ticket = {'state': 'in_progress'}\nticket['state'] = 'done'\nticket['closed'] = True\nprint(ticket)"),
            ("Cuenta cuantos tickets quedan abiertos (state != 'done').", "tickets = [{'state': 'new'}, {'state': 'done'}, {'state': 'in_progress'}]\nprint(len([t for t in tickets if t['state'] != 'done']))"),
            ("Reabre un ticket 'done' poniendolo en 'new'; imprime el estado.", "ticket = {'state': 'done'}\nticket['state'] = 'new'\nprint(ticket['state'])"),
        ]),
        explicit([
            ("Valida que un ticket tenga 'assignee'; si no, imprime 'sin asignar'.", "ticket = {'subject': 'X'}\nprint(ticket.get('assignee', 'sin asignar'))"),
            ("Guard clause: no cerrar un ticket sin solucion; imprime 'falta solucion'.", "def cerrar(t):\n    if not t.get('solucion'):\n        return 'falta solucion'\n    return 'cerrado'\nprint(cerrar({'subject': 'X'}))"),
            ("Si el ticket tiene solucion, cerrar() retorna 'cerrado'; pruebalo.", "def cerrar(t):\n    if not t.get('solucion'):\n        return 'falta solucion'\n    return 'cerrado'\nprint(cerrar({'solucion': 'reinicio'}))"),
            ("Valida priority entre 0 y 3; con 5 lanza ValueError y captura el mensaje.", "def set_priority(p):\n    if not 0 <= p <= 3:\n        raise ValueError('prioridad invalida')\n    return p\ntry:\n    set_priority(5)\nexcept ValueError as e:\n    print(e)"),
            ("Valida email con '@'; imprime True si 'a@x.com' es valido.", "def valido(e):\n    return '@' in e and '.' in e\nprint(valido('a@x.com'))"),
            ("Guard: si amount<=0 retorna 'monto invalido'; pruebalo con 0.", "def facturar(amount):\n    if amount <= 0:\n        return 'monto invalido'\n    return amount\nprint(facturar(0))"),
            ("Valida que el state este en los permitidos; imprime True para 'open'.", "permitidos = {'new', 'open', 'done'}\nprint('open' in permitidos)"),
            ("Si falta el campo 'partner_id', usa 0 por defecto; imprime el valor.", "order = {'amount': 100}\nprint(order.get('partner_id', 0))"),
            ("Valida stock suficiente: pide 5, hay 3 -> imprime 'sin stock'.", "stock, pedido = 3, 5\nprint('ok' if stock >= pedido else 'sin stock')"),
            ("Guard combinado: ticket cerrable solo si tiene assignee Y solucion; prueba con ambos.", "def cerrable(t):\n    if not t.get('assignee') or not t.get('solucion'):\n        return False\n    return True\nprint(cerrable({'assignee': 'Ana', 'solucion': 'fix'}))"),
        ]),
        explicit([
            ("Ordena los tickets por priority descendente; imprime los subjects.", "tickets = [{'subject': 'a', 'priority': 1}, {'subject': 'b', 'priority': 3}, {'subject': 'c', 'priority': 2}]\nprint([t['subject'] for t in sorted(tickets, key=lambda x: x['priority'], reverse=True)])"),
            ("Imprime el subject del ticket de mayor prioridad.", "tickets = [{'subject': 'a', 'priority': 1}, {'subject': 'b', 'priority': 3}]\nprint(max(tickets, key=lambda t: t['priority'])['subject'])"),
            ("Ordena las ordenes por amount ascendente; imprime los amounts.", "orders = [{'amount': 300}, {'amount': 100}, {'amount': 200}]\nprint([o['amount'] for o in sorted(orders, key=lambda x: x['amount'])])"),
            ("SLA: cuenta cuantos tickets superan 24 horas de espera.", "tickets = [{'horas': 30}, {'horas': 10}, {'horas': 48}]\nprint(len([t for t in tickets if t['horas'] > 24]))"),
            ("Ordena tickets por (priority desc, horas desc); imprime el primer subject.", "tickets = [{'subject': 'a', 'priority': 2, 'horas': 5}, {'subject': 'b', 'priority': 2, 'horas': 10}]\nprint(sorted(tickets, key=lambda t: (-t['priority'], -t['horas']))[0]['subject'])"),
            ("Marca como 'urgente' los tickets con priority 3; cuenta cuantos.", "tickets = [{'priority': 3}, {'priority': 1}, {'priority': 3}]\nprint(len([t for t in tickets if t['priority'] == 3]))"),
            ("Ordena productos por stock ascendente e imprime el de menor stock.", "products = [{'name': 'A', 'stock': 5}, {'name': 'B', 'stock': 1}]\nprint(sorted(products, key=lambda p: p['stock'])[0]['name'])"),
            ("Calcula el tiempo promedio de resolucion (horas) de los tickets.", "tickets = [{'horas': 10}, {'horas': 20}, {'horas': 30}]\nprint(sum(t['horas'] for t in tickets) / len(tickets))"),
            ("Top 2 tickets por prioridad: imprime sus subjects.", "tickets = [{'subject': 'a', 'priority': 1}, {'subject': 'b', 'priority': 3}, {'subject': 'c', 'priority': 2}]\ntop = sorted(tickets, key=lambda t: t['priority'], reverse=True)[:2]\nprint([t['subject'] for t in top])"),
            ("Cuenta cuantos tickets cumplen el SLA (horas <= 24).", "tickets = [{'horas': 12}, {'horas': 30}, {'horas': 24}]\nprint(len([t for t in tickets if t['horas'] <= 24]))"),
        ]),
        explicit([
            ("Reporte: cuenta cuantos tickets hay por estado (dict).", "tickets = [{'state': 'new'}, {'state': 'done'}, {'state': 'new'}]\nrep = {}\nfor t in tickets:\n    rep[t['state']] = rep.get(t['state'], 0) + 1\nprint(rep)"),
            ("Reporte: suma el amount por cada partner_id (dict).", "orders = [{'partner_id': 1, 'amount': 100}, {'partner_id': 1, 'amount': 50}, {'partner_id': 2, 'amount': 30}]\nrep = {}\nfor o in orders:\n    rep[o['partner_id']] = rep.get(o['partner_id'], 0) + o['amount']\nprint(rep)"),
            ("Reporte: cuantos productos hay por categoria (dict).", "products = [{'cat': 'A'}, {'cat': 'B'}, {'cat': 'A'}]\nrep = {}\nfor p in products:\n    rep[p['cat']] = rep.get(p['cat'], 0) + 1\nprint(rep)"),
            ("Reporte: imprime el estado con MAS tickets.", "tickets = [{'state': 'new'}, {'state': 'new'}, {'state': 'done'}]\nrep = {}\nfor t in tickets:\n    rep[t['state']] = rep.get(t['state'], 0) + 1\nprint(max(rep, key=rep.get))"),
            ("Reporte: total facturado (suma de amounts de ordenes 'done').", "orders = [{'amount': 100, 'state': 'done'}, {'amount': 50, 'state': 'open'}]\nprint(sum(o['amount'] for o in orders if o['state'] == 'done'))"),
            ("Reporte: cuenta tickets por prioridad usando un dict.", "tickets = [{'priority': 1}, {'priority': 3}, {'priority': 1}]\nrep = {}\nfor t in tickets:\n    rep[t['priority']] = rep.get(t['priority'], 0) + 1\nprint(rep)"),
            ("Reporte: lista de estados unicos presentes (ordenados).", "tickets = [{'state': 'done'}, {'state': 'new'}, {'state': 'done'}]\nprint(sorted(set(t['state'] for t in tickets)))"),
            ("Reporte: promedio de amount por orden, redondeado a 2 decimales.", "orders = [{'amount': 100}, {'amount': 55}]\nprint(round(sum(o['amount'] for o in orders) / len(orders), 2))"),
            ("Reporte: cuantas ordenes por encima del promedio de amount.", "orders = [{'amount': 100}, {'amount': 50}, {'amount': 150}]\nprom = sum(o['amount'] for o in orders) / len(orders)\nprint(len([o for o in orders if o['amount'] > prom]))"),
            ("Reporte agrupado: imprime {estado: cantidad} ordenado por estado.", "tickets = [{'state': 'open'}, {'state': 'done'}, {'state': 'open'}]\nrep = {}\nfor t in tickets:\n    rep[t['state']] = rep.get(t['state'], 0) + 1\nprint(dict(sorted(rep.items())))"),
        ]),
        explicit([
            ("Integra ordenes con clientes por partner_id; imprime los names de cliente.", "partners = {1: 'ACME', 2: 'Globex'}\norders = [{'partner_id': 1}, {'partner_id': 2}]\nprint([partners[o['partner_id']] for o in orders])"),
            ("Combina dos listas de tickets (de dos fuentes) e imprime el total.", "fuente1 = [{'id': 1}, {'id': 2}]\nfuente2 = [{'id': 3}]\nprint(len(fuente1 + fuente2))"),
            ("Une productos con su stock por id; imprime una lista de (name, stock).", "products = [{'id': 1, 'name': 'A'}, {'id': 2, 'name': 'B'}]\nstock = {1: 10, 2: 0}\nprint([(p['name'], stock[p['id']]) for p in products])"),
            ("Cruza ventas y devoluciones por order_id; imprime el neto por orden.", "ventas = {1: 100, 2: 200}\ndevol = {1: 20}\nprint({k: ventas[k] - devol.get(k, 0) for k in ventas})"),
            ("Combina tags de dos tickets en un set ordenado.", "t1 = {'tags': ['a', 'b']}\nt2 = {'tags': ['b', 'c']}\nprint(sorted(set(t1['tags']) | set(t2['tags'])))"),
            ("Deduplica clientes de dos fuentes por id; imprime cuantos unicos hay.", "f1 = [{'id': 1}, {'id': 2}]\nf2 = [{'id': 2}, {'id': 3}]\nids = {r['id'] for r in f1 + f2}\nprint(len(ids))"),
            ("Enriquece ordenes con el name del cliente; imprime la primera orden completa.", "partners = {1: 'ACME'}\norders = [{'id': 9, 'partner_id': 1}]\norders[0]['partner_name'] = partners[orders[0]['partner_id']]\nprint(orders[0])"),
            ("Suma el total facturado por cliente combinando ordenes; imprime el dict.", "partners = {1: 'A', 2: 'B'}\norders = [{'partner_id': 1, 'amount': 100}, {'partner_id': 2, 'amount': 50}, {'partner_id': 1, 'amount': 25}]\nrep = {}\nfor o in orders:\n    name = partners[o['partner_id']]\n    rep[name] = rep.get(name, 0) + o['amount']\nprint(rep)"),
            ("Une dos diccionarios de configuracion (modulo base + custom).", "base = {'lang': 'es', 'tz': 'UTC'}\ncustom = {'tz': 'America/Lima'}\nprint({**base, **custom})"),
            ("Cruza productos sin stock con pedidos pendientes; imprime cuantos faltan.", "stock = {1: 0, 2: 5}\npedidos = [{'product_id': 1}, {'product_id': 2}, {'product_id': 1}]\nprint(len([p for p in pedidos if stock[p['product_id']] == 0]))"),
        ]),
    ]


LEVEL_BUILDERS = {"OA": level_oa, "OB": level_ob, "OC": level_oc}


def load_set_standards() -> dict[str, list[int]]:
    with open(STD_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    out: dict[str, list[int]] = {}
    for level, ldata in data["levels"].items():
        stds = [s.get("standard_seconds", 600) for s in ldata["blocks"]["A"].get("sets", [])]
        out[level] = stds
    return out


def generate_kumon() -> int:
    standards = load_set_standards()
    count = 0
    for level, builder in LEVEL_BUILDERS.items():
        sets = builder()
        if len(sets) != 5:
            raise SystemExit(f"{level}: expected 5 sets, got {len(sets)}")
        level_std = standards[level]
        for set_idx, drills in enumerate(sets):
            if len(drills) != PAGES_PER_SET:
                raise SystemExit(f"{level} set {set_idx + 1}: expected 10 drills")
            set_number = set_idx + 1
            std = level_std[set_idx] if set_idx < len(level_std) else 600
            per_page = max(20, std // PAGES_PER_SET)
            for j, d in enumerate(drills):
                order = j + 1
                page = set_idx * PAGES_PER_SET + order
                expected = run_capture(d["code"])
                scaff = scaffolding_for(order)
                data = {
                    "id": f"{level}{page}",
                    "level": level,
                    "page": page,
                    "set": set_number,
                    "block": "A",
                    "block_id": f"{level}.A",
                    "order": order,
                    "scaffolding": scaff,
                    "time_estimate_seconds": per_page,
                    "prompt": d["prompt"],
                    "hints": ["Modela los registros como diccionarios y aplica el patron de Odoo paso a paso."] if scaff != "none" else [],
                    "validation": {"type": "run_and_match_stdout", "expected": expected},
                    "starter_code": safe_starter(d["code"], order) if scaff == "full" else "",
                }
                if scaff == "full":
                    data["reference_code"] = d["code"]
                write_yaml(CONTENT / f"level-{level.lower()}" / "kumon" / f"{data['id']}.yaml", data)
                count += 1
    return count


def generate_checkpoints() -> int:
    problems = {
        "level-oa": {
            "id": "oa-cp-total-orders", "title": "Total facturado", "fn_name": "total_done",
            "description": "Suma el 'amount' de las ordenes cuyo state sea 'done'.",
            "test_cases": [
                {"args": [[{"amount": 100, "state": "done"}, {"amount": 50, "state": "open"}, {"amount": 30, "state": "done"}]], "expected": 130},
                {"args": [[{"amount": 10, "state": "open"}]], "expected": 0},
            ],
            "starter1": "def total_done(orders):\n    # suma amount donde state == 'done'\n    return ___",
        },
        "level-ob": {
            "id": "ob-cp-search-write", "title": "Search + write", "fn_name": "close_big",
            "description": "Pon state='done' a los registros con amount>100 y retorna cuantos cambiaron.",
            "test_cases": [
                {"args": [[{"id": 1, "amount": 120, "state": "open"}, {"id": 2, "amount": 80, "state": "open"}]], "expected": 1},
                {"args": [[{"id": 1, "amount": 50, "state": "open"}]], "expected": 0},
            ],
            "starter1": "def close_big(records):\n    cambiados = 0\n    # recorre, si amount > 100 -> state 'done'\n    return cambiados",
        },
        "level-oc": {
            "id": "oc-cp-group-tickets", "title": "Agrupar tickets", "fn_name": "group_by_state",
            "description": "Devuelve un dict {state: cantidad} contando los tickets por estado.",
            "test_cases": [
                {"args": [[{"state": "new"}, {"state": "new"}, {"state": "done"}]], "expected": {"new": 2, "done": 1}},
                {"args": [[]], "expected": {}},
            ],
            "starter1": "def group_by_state(tickets):\n    rep = {}\n    # cuenta por state\n    return rep",
        },
    }
    count = 0
    for level, p in problems.items():
        fn = p["fn_name"]
        data = {
            "id": p["id"], "title": p["title"], "fn_name": fn, "description": p["description"],
            "test_cases": p["test_cases"],
            "tiers": {
                1: {"starter_code": p["starter1"], "explain_checklist": ["Identifica el dominio/condicion", "Recuerda el patron de Odoo"], "hints_allowed": True},
                2: {"starter_code": f"def {fn}(*args):\n    pass", "narration_prompts": ["Explica tu enfoque"], "hints_allowed": True},
                3: {"starter_code": f"def {fn}(*args):\n    pass", "narration_prompts": [], "hints_allowed": False},
            },
        }
        write_yaml(CONTENT / level / "leetcode" / f"{p['id']}.yaml", data)
        count += 1
    return count


def main() -> None:
    if CONTENT.exists():
        print("Cleaning old Odoo content...")
        shutil.rmtree(CONTENT)
    print("Generating Odoo Kumon pages (OA, OB, OC)...")
    k = generate_kumon()
    print(f"  -> {k} Odoo pages")
    print("Generating Odoo checkpoints...")
    cp = generate_checkpoints()
    print(f"  -> {cp} checkpoint problems")
    print("Done.")


if __name__ == "__main__":
    main()

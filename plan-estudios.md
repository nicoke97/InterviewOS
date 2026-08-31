# Plan de estudios — Nico

Tres bloques. Nada más.

1. Código (LeetCode + lenguajes)
2. Historias de entrevista
3. SlabHQ (lo que esté trabado)

No Azure. No Terraform. No Odoo functional. No otra carrera.

---

## Semana tipo

| Cuándo | Qué | Tiempo |
|--------|-----|--------|
| Diario | LeetCode en Codenda (medium: arrays, hashes, two pointers) | 1 h |
| Diario | El mismo problema, segunda pasada en el lenguaje del día | 20–30 min |
| 3× semana | Historias en voz alta (grabate o recita) | 20 min |
| El resto | SlabHQ: Mercado Libre, eBay, pagos, el blocker de esta semana | lo que quede |

Lenguaje del día (rotar): **C# → Python → TypeScript → C# → …**

---

## Cómo correr una sesión en Codenda

Esto es el plan, metido en la app. No improvises el flujo.

1. Abre el **dashboard**. Pestaña **LeetCodes** (es la default).
2. Tiempo: **60 min** (también hay 45 / 90). Pulsa **Calcular sesión**.
3. Sale **un** problema. Hasta que arrays/hashes y two pointers estén dominados, no te manda hard ni otros temas.
4. Entra. Arriba está el ritual del día.
5. 2 min de plan en papel. La **primera pista está bloqueada 25 min**. La solución no se muestra en esta sesión.
6. Codea y envía en **Python** (el juez solo corre Python).
7. Abajo: complejidad en una línea, bitácora solo/pista/fail, y la **segunda pasada** en el lenguaje del día (C# / Python / TypeScript).
8. Lun / mié / vie: en el dashboard aparece la **historia** (eBay, .NET, SlabHQ). Díla en voz alta y márcala.

Python/Kumon sigue en la otra pestaña, 15 min. Eso no es el plan de entrevista.

---

## 1. LeetCode (Codenda)

Objetivo: pasar la prueba. No “terminar el curriculum”.

### Temas (en este orden)

1. Arrays
2. Hash maps / sets
3. Two pointers
4. Sliding window (cuando lo anterior ya salga en medium)
5. Stack / string (si ya no fallas 1–3)

Quédate en **medium**. Easy solo de calentamiento (5 min). Hard no, hasta que medium no te tumbe.

### Cómo usar la hora

1. Lee el prompt. 2 min de plan en papel (entradas, outputs, un ejemplo).
2. Codéalo en Codenda / el lenguaje del día. Sin copiar la solución.
3. Si a los 25 min no hay camino, mira hint **una** vez y sigue.
4. Al final: complejidad (tiempo/espacio) en una línea.
5. Anota en la bitácora: problema, lenguaje, solo / hint / fail.

### Los tres lenguajes

Ya usas los tres en la vida real (Solera = C#/.NET, Codenda = Python, SlabHQ = TypeScript). El estudio no es un bootcamp desde cero: es **que la entrevista no te pille en sintaxis**.

| Lenguaje | Para qué | Qué practicar en cada problema |
|----------|----------|--------------------------------|
| **C# / .NET** | El jale al que aplicas | `List<T>`, `Dictionary<,>`, `HashSet<>`, LINQ solo si lo controlas, tipos nulos |
| **Python** | Codenda + pruebas que piden Python | `list`, `dict`, `set`, slicing, comprehensions sin volverte loco |
| **TypeScript** | SlabHQ + front | tipos (`number[]`, `Record<string, number>`), `Map`, `Set`, no `any` |

Misma lógica, tres sintaxis. El algoritmo no cambia.

### .NET (solo lo que sale en entrevista de engineer)

No un temario de Azure. Cuando toque C#, que sepas decir:

- async/await y I/O (APIs, HTTP)
- DI a nivel “qué inyecto y por qué”
- SQL: índice, N+1, transacción
- REST vs SOAP (esto ya lo viviste en eLink)

Si una vacante pide algo concreto, lo estudias **esa semana**. No antes.

---

## 2. Historias en voz alta

Esto es la entrevista de verdad. 20 min, tres veces por semana, **hablado** (no releer el portafolio).

Cada historia, misma ficha:

1. Qué estaba roto / qué pedían
2. Cómo lo diseñaste (el corte, no el tutorial)
3. Qué se rompía por el camino
4. Qué cortaste y cómo supiste que estaba bien
5. Qué harías distinto

### Las tres

**eBay SOAP → REST (eLink, Solera)**  
Deprecaron llamadas y no lo anunciaron. Cliente C# del WSDL, XML, Faults dentro de un 200. Interfaz única listings/orders/inventory. Dual-run, comparar payloads, REST único writer.

**Migración .NET Framework 4.8 → Core 8**  
15 servicios. El proyecto era el **grafo** (quién depende de quién), no el compilador. Dual-run, compatibilidad primero.

**SlabHQ**  
Por qué existe (México / Mercado Libre vs eBay US). Binder → listing desk. Scan, inventario, canales. Qué está live, qué está a medias (pagos, eBay US, sync). Tú eres founder: decisiones, no tickets.

Cuando una salga fluida (~3 min, sin leer), pásala a la siguiente. No memorices un script: memoriza la **estructura**.

---

## 3. SlabHQ — lo de esta semana

No hay temario. El producto manda.

Cada lunes, **una** línea:

> Esta semana destrabo: _______________

Ejemplos (elige el que esté bloqueado, no la lista entera):

- Mercado Libre (listar / stock / tokens)
- eBay (API, listing, sync)
- Pagos
- Lo que haya roto a un usuario de verdad

Viernes: ¿quedó shipped o no? Si no, sigue siendo *el* tema. No abras otro frente.

Estudiar TypeScript aquí **cuenta**: el código de SlabHQ es la práctica, no un curso aparte.

---

## Bitácora (cópiala abajo)

### Semana del ____

**SlabHQ:** destrabo _______________

| Día | Lenguaje | Problema | Solo / hint / fail | Historia (sí/no) | SlabHQ (qué hiciste) |
|-----|----------|----------|--------------------|------------------|----------------------|
| L | | | | | |
| M | | | | | |
| X | | | | | |
| J | | | | | |
| V | | | | | |
| S | | | | | |
| D | | | | | |

---

## Fuera de alcance

Cursos de cloud, certs, otra stack “por si acaso”, functional support como plan de estudios.

Si una vacante pide algo que no está aquí, entra **esa semana** al bloque 1 o 3. No rediseñes el plan.

# Mutantes generados por GEMINI

- Modelo: Flash
- Version: 3.6
- Fecha: 02/09/2026

## Prompt enviado

```
Below is a Python file. Each line is prefixed with its line number.

Generate exactly 20 mutants for this code. A mutant is a small change to a SINGLE line that alters the program's behaviour, in the style of mutation testing.

Rules:
- Each mutant modifies exactly one line.
- `precode` must be the ORIGINAL line, copied character by character, including its leading indentation, exactly as it appears at that line number.
- `aftercode` is the mutated version of that same line, keeping valid Python syntax and the same indentation.
- Do not mutate comments, blank lines, import statements or the class/def headers.
- Prefer semantic changes (boundaries, operators, constants, conditions) over cosmetic ones.
- Do not repeat the same mutant twice.

Answer with a JSON array and nothing else. No explanation, no markdown fences.

IMPORTANT: the code contains double-quoted Python strings. Inside a JSON string every double quote MUST be escaped as \". Look carefully at the second example below: the quotes around "pending" are escaped.

[
  {"id": 1, "line": 12, "precode": "        if x >= 10:", "aftercode": "        if x > 10:"},
  {"id": 2, "line": 34, "precode": "        if s.status != \"pending\":", "aftercode": "        if s.status == \"pending\":"},
  ...
]

Here is the code:

  1 | from datetime import timedelta
  2 |
  3 | from src.models import Reservation, InvalidReservation, InvalidTransition
  4 |
  5 |
  6 | VALID_TIERS = ("standard", "silver", "gold")
  7 |
  8 |
  9 | class ReservationService:
 10 |
 11 |     def __init__(self, clock, notifier):
 12 |         self.clock = clock
 13 |         self.notifier = notifier
 14 |         self.reservations = {}
 15 |
 16 |     def create(self, code, guest, tier, check_in, nights, nightly_rate):
 17 |         if code in self.reservations:
 18 |             raise InvalidReservation("codigo duplicado")
 19 |         if tier not in VALID_TIERS:
 20 |             raise InvalidReservation("categoria desconocida")
 21 |         if not isinstance(nights, int) or nights < 1 or nights > 30:
 22 |             raise InvalidReservation("noches fuera de rango")
 23 |         if nightly_rate <= 0:
 24 |             raise InvalidReservation("tarifa invalida")
 25 |         now = self.clock.now()
 26 |         if check_in < now:
 27 |             raise InvalidReservation("fecha en el pasado")
 28 |         if (check_in - now).days > 365:
 29 |             raise InvalidReservation("fecha demasiado lejana")
 30 |         reservation = Reservation(code, guest, tier, check_in, nights, nightly_rate)
 31 |         self.reservations[code] = reservation
 32 |         self.notifier.send(guest, "reserva creada " + code)
 33 |         return reservation
 34 |
 35 |     def quote(self, reservation):
 36 |         total = reservation.nights * reservation.nightly_rate
 37 |         if reservation.nights >= 21:
 38 |             total = total * 0.85
 39 |         elif reservation.nights >= 7:
 40 |             total = total * 0.90
 41 |         if reservation.tier == "gold":
 42 |             total = total * 0.88
 43 |         elif reservation.tier == "silver":
 44 |             total = total * 0.94
 45 |         if reservation.check_in.month in (1, 2, 7):
 46 |             total = total * 1.18
 47 |         if total < reservation.nightly_rate:
 48 |             total = reservation.nightly_rate
 49 |         return round(total, 2)
 50 |
 51 |     def confirm(self, reservation):
 52 |         if reservation.status != "pending":
 53 |             raise InvalidTransition("solo se confirma una reserva pendiente")
 54 |         remaining = reservation.check_in - self.clock.now()
 55 |         if remaining < timedelta(hours=48) and reservation.tier != "gold":
 56 |             raise InvalidTransition("confirmacion tardia")
 57 |         reservation.status = "confirmed"
 58 |         reservation.paid = self.quote(reservation)
 59 |         self.notifier.send(reservation.guest, "reserva confirmada " + reservation.code)
 60 |         if reservation.tier == "gold":
 61 |             self.notifier.send(reservation.guest, "late checkout " + reservation.code)
 62 |         return reservation.paid
 63 |
 64 |     def reschedule(self, reservation, new_check_in):
 65 |         if reservation.status not in ("pending", "confirmed"):
 66 |             raise InvalidTransition("no se puede reprogramar")
 67 |         now = self.clock.now()
 68 |         if new_check_in < now:
 69 |             raise InvalidReservation("fecha en el pasado")
 70 |         if (reservation.check_in - now).days < 3:
 71 |             raise InvalidTransition("reprogramacion fuera de plazo")
 72 |         shift = (new_check_in - reservation.check_in).days
 73 |         if shift > 60 or shift < -60:
 74 |             raise InvalidReservation("cambio demasiado grande")
 75 |         reservation.check_in = new_check_in
 76 |         if reservation.status == "confirmed":
 77 |             reservation.paid = self.quote(reservation)
 78 |         self.notifier.send(reservation.guest, "reserva reprogramada " + reservation.code)
 79 |         return reservation
 80 |
 81 |     def cancel(self, reservation, reason=None):
 82 |         if reservation.status == "cancelled":
 83 |             raise InvalidTransition("la reserva ya fue cancelada")
 84 |         if reservation.status == "completed":
 85 |             raise InvalidTransition("no se cancela una reserva completada")
 86 |         days_ahead = (reservation.check_in - self.clock.now()).days
 87 |         if days_ahead >= 30:
 88 |             rate = 0.0
 89 |         elif days_ahead >= 15:
 90 |             rate = 0.25
 91 |         elif days_ahead >= 7:
 92 |             rate = 0.5
 93 |         elif days_ahead >= 1:
 94 |             rate = 0.8
 95 |         else:
 96 |             rate = 1.0
 97 |         if reservation.tier == "gold" and days_ahead >= 1:
 98 |             rate = rate / 2
 99 |         fee = round(self.quote(reservation) * rate, 2)
100 |         reservation.status = "cancelled"
101 |         if reason:
102 |             reservation.notes = reason
103 |         self.notifier.send(reservation.guest, "reserva cancelada " + reservation.code)
104 |         return fee
105 |
106 |     def complete(self, reservation):
107 |         if reservation.status != "confirmed":
108 |             raise InvalidTransition("solo se completa una reserva confirmada")
109 |         end = reservation.check_in + timedelta(days=reservation.nights)
110 |         if self.clock.now() < end:
111 |             raise InvalidTransition("la estadia aun no termina")
112 |         reservation.status = "completed"
113 |         return reservation
114 |
115 |     def summary(self, code):
116 |         if code not in self.reservations:
117 |             raise InvalidReservation("reserva inexistente")
118 |         reservation = self.reservations[code]
119 |         days_ahead = (reservation.check_in - self.clock.now()).days
120 |         if reservation.status == "cancelled":
121 |             label = "cancelada"
122 |         elif reservation.status == "completed":
123 |             label = "finalizada"
124 |         elif days_ahead > 7:
125 |             label = "proxima"
126 |         elif days_ahead >= 0:
127 |             label = "inminente"
128 |         else:
129 |             label = "vencida"
130 |         return {"code": reservation.code, "guest": reservation.guest, "status": label}
```

## Respuesta completa del modelo

```json
[
{"id": 1, "line": 17, "precode": "        if code in self.reservations:", "aftercode": "        if code not in self.reservations:"},
{"id": 2, "line": 19, "precode": "        if tier not in VALID_TIERS:", "aftercode": "        if tier in VALID_TIERS:"},
{"id": 3, "line": 21, "precode": "        if not isinstance(nights, int) or nights < 1 or nights > 30:", "aftercode": "        if not isinstance(nights, int) or nights <= 1 or nights > 30:"},
{"id": 4, "line": 23, "precode": "        if nightly_rate <= 0:", "aftercode": "        if nightly_rate < 0:"},
{"id": 5, "line": 26, "precode": "        if check_in < now:", "aftercode": "        if check_in <= now:"},
{"id": 6, "line": 28, "precode": "        if (check_in - now).days > 365:", "aftercode": "        if (check_in - now).days >= 365:"},
{"id": 7, "line": 37, "precode": "        if reservation.nights >= 21:", "aftercode": "        if reservation.nights > 21:"},
{"id": 8, "line": 38, "precode": "            total = total * 0.85", "aftercode": "            total = total * 0.80"},
{"id": 9, "line": 39, "precode": "        elif reservation.nights >= 7:", "aftercode": "        elif reservation.nights > 7:"},
{"id": 10, "line": 41, "precode": "        if reservation.tier == "gold":", "aftercode": "        if reservation.tier != "gold":"},
{"id": 11, "line": 47, "precode": "        if total < reservation.nightly_rate:", "aftercode": "        if total <= reservation.nightly_rate:"},
{"id": 12, "line": 52, "precode": "        if reservation.status != "pending":", "aftercode": "        if reservation.status == "pending":"},
{"id": 13, "line": 55, "precode": "        if remaining < timedelta(hours=48) and reservation.tier != "gold":", "aftercode": "        if remaining < timedelta(hours=48) or reservation.tier != "gold":"},
{"id": 14, "line": 70, "precode": "        if (reservation.check_in - now).days < 3:", "aftercode": "        if (reservation.check_in - now).days <= 3:"},
{"id": 15, "line": 73, "precode": "        if shift > 60 or shift < -60:", "aftercode": "        if shift >= 60 or shift < -60:"},
{"id": 16, "line": 87, "precode": "        if days_ahead >= 30:", "aftercode": "        if days_ahead > 30:"},
{"id": 17, "line": 97, "precode": "        if reservation.tier == "gold" and days_ahead >= 1:", "aftercode": "        if reservation.tier == "gold" and days_ahead > 1:"},
{"id": 18, "line": 107, "precode": "        if reservation.status != "confirmed":", "aftercode": "        if reservation.status == "confirmed":"},
{"id": 19, "line": 110, "precode": "        if self.clock.now() < end:", "aftercode": "        if self.clock.now() <= end:"},
{"id": 20, "line": 124, "precode": "        elif days_ahead > 7:", "aftercode": "        elif days_ahead >= 7:"}
]
```

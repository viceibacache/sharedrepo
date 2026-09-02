from datetime import timedelta

from src.models import Reservation, InvalidReservation, InvalidTransition


VALID_TIERS = ("standard", "silver", "gold")


class ReservationService:

    def __init__(self, clock, notifier):
        self.clock = clock
        self.notifier = notifier
        self.reservations = {}

    def create(self, code, guest, tier, check_in, nights, nightly_rate):
        if code in self.reservations:
            raise InvalidReservation("codigo duplicado")
        if tier not in VALID_TIERS:
            raise InvalidReservation("categoria desconocida")
        if not isinstance(nights, int) or nights < 1 or nights > 30:
            raise InvalidReservation("noches fuera de rango")
        if nightly_rate <= 0:
            raise InvalidReservation("tarifa invalida")
        now = self.clock.now()
        if check_in < now:
            raise InvalidReservation("fecha en el pasado")
        if (check_in - now).days > 365:
            raise InvalidReservation("fecha demasiado lejana")
        reservation = Reservation(code, guest, tier, check_in, nights, nightly_rate)
        self.reservations[code] = reservation
        self.notifier.send(guest, "reserva creada " + code)
        return reservation

    def quote(self, reservation):
        total = reservation.nights * reservation.nightly_rate
        if reservation.nights >= 21:
            total = total * 0.85
        elif reservation.nights >= 7:
            total = total * 0.90
        if reservation.tier == "gold":
            total = total * 0.88
        elif reservation.tier == "silver":
            total = total * 0.94
        if reservation.check_in.month in (1, 2, 7):
            total = total * 1.18
        if total < reservation.nightly_rate:
            total = reservation.nightly_rate
        return round(total, 2)

    def confirm(self, reservation):
        if reservation.status != "pending":
            raise InvalidTransition("solo se confirma una reserva pendiente")
        remaining = reservation.check_in - self.clock.now()
        if remaining < timedelta(hours=48) and reservation.tier != "gold":
            raise InvalidTransition("confirmacion tardia")
        reservation.status = "confirmed"
        reservation.paid = self.quote(reservation)
        self.notifier.send(reservation.guest, "reserva confirmada " + reservation.code)
        if reservation.tier == "gold":
            self.notifier.send(reservation.guest, "late checkout " + reservation.code)
        return reservation.paid

    def reschedule(self, reservation, new_check_in):
        if reservation.status not in ("pending", "confirmed"):
            raise InvalidTransition("no se puede reprogramar")
        now = self.clock.now()
        if new_check_in < now:
            raise InvalidReservation("fecha en el pasado")
        if (reservation.check_in - now).days < 3:
            raise InvalidTransition("reprogramacion fuera de plazo")
        shift = (new_check_in - reservation.check_in).days
        if shift > 60 or shift < -60:
            raise InvalidReservation("cambio demasiado grande")
        reservation.check_in = new_check_in
        if reservation.status == "confirmed":
            reservation.paid = self.quote(reservation)
        self.notifier.send(reservation.guest, "reserva reprogramada " + reservation.code)
        return reservation

    def cancel(self, reservation, reason=None):
        if reservation.status == "cancelled":
            raise InvalidTransition("la reserva ya fue cancelada")
        if reservation.status == "completed":
            raise InvalidTransition("no se cancela una reserva completada")
        days_ahead = (reservation.check_in - self.clock.now()).days
        if days_ahead >= 30:
            rate = 0.0
        elif days_ahead >= 15:
            rate = 0.25
        elif days_ahead >= 7:
            rate = 0.5
        elif days_ahead >= 1:
            rate = 0.8
        else:
            rate = 1.0
        if reservation.tier == "gold" and days_ahead >= 1:
            rate = rate / 2
        fee = round(self.quote(reservation) * rate, 2)
        reservation.status = "cancelled"
        if reason:
            reservation.notes = reason
        self.notifier.send(reservation.guest, "reserva cancelada " + reservation.code)
        return fee

    def complete(self, reservation):
        if reservation.status != "confirmed":
            raise InvalidTransition("solo se completa una reserva confirmada")
        end = reservation.check_in + timedelta(days=reservation.nights)
        if self.clock.now() < end:
            raise InvalidTransition("la estadia aun no termina")
        reservation.status = "completed"
        return reservation

    def summary(self, code):
        if code not in self.reservations:
            raise InvalidReservation("reserva inexistente")
        reservation = self.reservations[code]
        days_ahead = (reservation.check_in - self.clock.now()).days
        if reservation.status == "cancelled":
            label = "cancelada"
        elif reservation.status == "completed":
            label = "finalizada"
        elif days_ahead > 7:
            label = "proxima"
        elif days_ahead >= 0:
            label = "inminente"
        else:
            label = "vencida"
        return {"code": reservation.code, "guest": reservation.guest, "status": label}

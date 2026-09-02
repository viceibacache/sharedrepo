class ReservationError(Exception):
    pass


class InvalidReservation(ReservationError):
    pass


class InvalidTransition(ReservationError):
    pass


class Reservation:
    def __init__(self, code, guest, tier, check_in, nights, nightly_rate):
        self.code = code
        self.guest = guest
        self.tier = tier
        self.check_in = check_in
        self.nights = nights
        self.nightly_rate = nightly_rate
        self.status = "pending"
        self.paid = 0.0
        self.notes = ""

    def __repr__(self):
        return "Reservation(%s, %s, %s)" % (self.code, self.tier, self.status)

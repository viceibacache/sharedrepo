"""Bateria de tests base de la Actividad 2.

Alcanza 100% de statement y branch coverage sobre src/reservation.py.
NO MODIFICAR: los mutantes se evaluan contra esta suite exacta.
"""
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock

from src.reservation import ReservationService
from src.models import Reservation, InvalidReservation, InvalidTransition


NOW = datetime(2026, 4, 1, 10, 0, 0)


def make_service(now=NOW):
    clock = Mock()
    clock.now.return_value = now
    notifier = Mock()
    return ReservationService(clock, notifier)


def make_reservation(**kw):
    data = dict(code="R1", guest="ana@uc.cl", tier="standard",
                check_in=NOW + timedelta(days=40), nights=3, nightly_rate=100.0)
    data.update(kw)
    return Reservation(**data)


class TestCreate(unittest.TestCase):

    def test_crea_reserva_valida(self):
        svc = make_service()
        r = svc.create("R1", "ana@uc.cl", "gold", NOW + timedelta(days=10), 2, 100.0)
        self.assertEqual(r.status, "pending")
        self.assertIn("R1", svc.reservations)
        svc.notifier.send.assert_called_once_with("ana@uc.cl", "reserva creada R1")

    def test_codigo_duplicado(self):
        svc = make_service()
        svc.create("R1", "ana@uc.cl", "gold", NOW + timedelta(days=10), 2, 100.0)
        with self.assertRaises(InvalidReservation):
            svc.create("R1", "otro@uc.cl", "gold", NOW + timedelta(days=10), 2, 100.0)

    def test_tier_desconocido(self):
        svc = make_service()
        with self.assertRaises(InvalidReservation):
            svc.create("R2", "ana@uc.cl", "platinum", NOW + timedelta(days=10), 2, 100.0)

    def test_noches_no_entero(self):
        svc = make_service()
        with self.assertRaises(InvalidReservation):
            svc.create("R3", "ana@uc.cl", "gold", NOW + timedelta(days=10), 2.5, 100.0)

    def test_noches_bajo_minimo(self):
        svc = make_service()
        with self.assertRaises(InvalidReservation):
            svc.create("R4", "ana@uc.cl", "gold", NOW + timedelta(days=10), 0, 100.0)

    def test_noches_sobre_maximo(self):
        svc = make_service()
        with self.assertRaises(InvalidReservation):
            svc.create("R5", "ana@uc.cl", "gold", NOW + timedelta(days=10), 31, 100.0)

    def test_tarifa_invalida(self):
        svc = make_service()
        with self.assertRaises(InvalidReservation):
            svc.create("R6", "ana@uc.cl", "gold", NOW + timedelta(days=10), 2, 0)

    def test_fecha_en_el_pasado(self):
        svc = make_service()
        with self.assertRaises(InvalidReservation):
            svc.create("R7", "ana@uc.cl", "gold", NOW - timedelta(days=1), 2, 100.0)

    def test_fecha_demasiado_lejana(self):
        svc = make_service()
        with self.assertRaises(InvalidReservation):
            svc.create("R8", "ana@uc.cl", "gold", NOW + timedelta(days=400), 2, 100.0)


class TestQuote(unittest.TestCase):

    def test_sin_descuentos(self):
        svc = make_service()
        r = make_reservation(nights=3, tier="standard", check_in=datetime(2026, 5, 1))
        self.assertEqual(svc.quote(r), 300.0)

    def test_descuento_estadia_larga_intermedia(self):
        svc = make_service()
        r = make_reservation(nights=7, tier="standard", check_in=datetime(2026, 5, 1))
        self.assertEqual(svc.quote(r), 630.0)

    def test_descuento_estadia_muy_larga(self):
        svc = make_service()
        r = make_reservation(nights=21, tier="standard", check_in=datetime(2026, 5, 1))
        self.assertEqual(svc.quote(r), 1785.0)

    def test_descuento_gold(self):
        svc = make_service()
        r = make_reservation(nights=2, tier="gold", check_in=datetime(2026, 5, 1))
        self.assertEqual(svc.quote(r), 176.0)

    def test_descuento_silver(self):
        svc = make_service()
        r = make_reservation(nights=2, tier="silver", check_in=datetime(2026, 5, 1))
        self.assertEqual(svc.quote(r), 188.0)

    def test_recargo_temporada_alta(self):
        svc = make_service()
        r = make_reservation(nights=2, tier="standard", check_in=datetime(2027, 1, 15))
        self.assertEqual(svc.quote(r), 236.0)

    def test_piso_minimo_una_tarifa(self):
        svc = make_service()
        r = make_reservation(nights=1, tier="gold", check_in=datetime(2026, 5, 1))
        self.assertEqual(svc.quote(r), 100.0)


class TestConfirm(unittest.TestCase):

    def test_confirma_pendiente(self):
        svc = make_service()
        r = make_reservation(tier="standard", check_in=NOW + timedelta(days=10))
        paid = svc.confirm(r)
        self.assertEqual(r.status, "confirmed")
        self.assertEqual(paid, r.paid)
        self.assertEqual(svc.notifier.send.call_count, 1)

    def test_confirma_gold_envia_beneficio(self):
        svc = make_service()
        r = make_reservation(tier="gold", check_in=NOW + timedelta(days=10))
        svc.confirm(r)
        self.assertEqual(svc.notifier.send.call_count, 2)

    def test_no_confirma_si_no_esta_pendiente(self):
        svc = make_service()
        r = make_reservation()
        r.status = "confirmed"
        with self.assertRaises(InvalidTransition):
            svc.confirm(r)

    def test_confirmacion_tardia_no_gold(self):
        svc = make_service()
        r = make_reservation(tier="silver", check_in=NOW + timedelta(hours=10))
        with self.assertRaises(InvalidTransition):
            svc.confirm(r)

    def test_confirmacion_tardia_gold_permitida(self):
        svc = make_service()
        r = make_reservation(tier="gold", check_in=NOW + timedelta(hours=10))
        svc.confirm(r)
        self.assertEqual(r.status, "confirmed")


class TestReschedule(unittest.TestCase):

    def test_reprograma_pendiente(self):
        svc = make_service()
        r = make_reservation(check_in=NOW + timedelta(days=40))
        nueva = NOW + timedelta(days=50)
        svc.reschedule(r, nueva)
        self.assertEqual(r.check_in, nueva)

    def test_reprograma_confirmada_recalcula_pago(self):
        svc = make_service()
        r = make_reservation(check_in=NOW + timedelta(days=40))
        r.status = "confirmed"
        svc.reschedule(r, NOW + timedelta(days=50))
        self.assertEqual(r.paid, svc.quote(r))

    def test_no_reprograma_cancelada(self):
        svc = make_service()
        r = make_reservation()
        r.status = "cancelled"
        with self.assertRaises(InvalidTransition):
            svc.reschedule(r, NOW + timedelta(days=50))

    def test_nueva_fecha_en_el_pasado(self):
        svc = make_service()
        r = make_reservation(check_in=NOW + timedelta(days=40))
        with self.assertRaises(InvalidReservation):
            svc.reschedule(r, NOW - timedelta(days=1))

    def test_fuera_de_plazo(self):
        svc = make_service()
        r = make_reservation(check_in=NOW + timedelta(days=2))
        with self.assertRaises(InvalidTransition):
            svc.reschedule(r, NOW + timedelta(days=20))

    def test_cambio_muy_hacia_adelante(self):
        svc = make_service()
        r = make_reservation(check_in=NOW + timedelta(days=40))
        with self.assertRaises(InvalidReservation):
            svc.reschedule(r, NOW + timedelta(days=200))

    def test_cambio_muy_hacia_atras(self):
        svc = make_service()
        r = make_reservation(check_in=NOW + timedelta(days=100))
        with self.assertRaises(InvalidReservation):
            svc.reschedule(r, NOW + timedelta(days=1))


class TestCancel(unittest.TestCase):

    def test_sin_cargo_con_mucha_antelacion(self):
        svc = make_service()
        r = make_reservation(check_in=NOW + timedelta(days=40))
        self.assertEqual(svc.cancel(r), 0.0)
        self.assertEqual(r.status, "cancelled")

    def test_cargo_25(self):
        svc = make_service()
        r = make_reservation(check_in=NOW + timedelta(days=20))
        self.assertEqual(svc.cancel(r), round(svc.quote(r) * 0.25, 2))

    def test_cargo_50(self):
        svc = make_service()
        r = make_reservation(check_in=NOW + timedelta(days=10))
        self.assertEqual(svc.cancel(r), round(svc.quote(r) * 0.5, 2))

    def test_cargo_80(self):
        svc = make_service()
        r = make_reservation(check_in=NOW + timedelta(days=3))
        self.assertEqual(svc.cancel(r), round(svc.quote(r) * 0.8, 2))

    def test_cargo_total_mismo_dia(self):
        svc = make_service()
        r = make_reservation(check_in=NOW + timedelta(hours=5))
        self.assertEqual(svc.cancel(r), round(svc.quote(r) * 1.0, 2))

    def test_gold_paga_la_mitad(self):
        svc = make_service()
        r = make_reservation(tier="gold", check_in=NOW + timedelta(days=10))
        self.assertEqual(svc.cancel(r), round(svc.quote(r) * 0.25, 2))

    def test_gold_mismo_dia_no_tiene_rebaja(self):
        svc = make_service()
        r = make_reservation(tier="gold", check_in=NOW + timedelta(hours=5))
        self.assertEqual(svc.cancel(r), round(svc.quote(r) * 1.0, 2))

    def test_guarda_motivo(self):
        svc = make_service()
        r = make_reservation(check_in=NOW + timedelta(days=40))
        svc.cancel(r, "viaje suspendido")
        self.assertEqual(r.notes, "viaje suspendido")

    def test_no_cancela_dos_veces(self):
        svc = make_service()
        r = make_reservation()
        r.status = "cancelled"
        with self.assertRaises(InvalidTransition):
            svc.cancel(r)

    def test_no_cancela_completada(self):
        svc = make_service()
        r = make_reservation()
        r.status = "completed"
        with self.assertRaises(InvalidTransition):
            svc.cancel(r)


class TestComplete(unittest.TestCase):

    def test_completa_estadia_terminada(self):
        svc = make_service(now=NOW + timedelta(days=50))
        r = make_reservation(check_in=NOW + timedelta(days=40), nights=3)
        r.status = "confirmed"
        svc.complete(r)
        self.assertEqual(r.status, "completed")

    def test_no_completa_si_no_esta_confirmada(self):
        svc = make_service()
        r = make_reservation()
        with self.assertRaises(InvalidTransition):
            svc.complete(r)

    def test_no_completa_estadia_en_curso(self):
        svc = make_service(now=NOW + timedelta(days=41))
        r = make_reservation(check_in=NOW + timedelta(days=40), nights=3)
        r.status = "confirmed"
        with self.assertRaises(InvalidTransition):
            svc.complete(r)


class TestSummary(unittest.TestCase):

    def _registrar(self, svc, r):
        svc.reservations[r.code] = r
        return r

    def test_reserva_inexistente(self):
        svc = make_service()
        with self.assertRaises(InvalidReservation):
            svc.summary("NOPE")

    def test_proxima(self):
        svc = make_service()
        r = self._registrar(svc, make_reservation(check_in=NOW + timedelta(days=40)))
        self.assertEqual(svc.summary(r.code)["status"], "proxima")

    def test_inminente(self):
        svc = make_service()
        r = self._registrar(svc, make_reservation(check_in=NOW + timedelta(days=3)))
        self.assertEqual(svc.summary(r.code)["status"], "inminente")

    def test_vencida(self):
        svc = make_service()
        r = self._registrar(svc, make_reservation(check_in=NOW - timedelta(days=3)))
        self.assertEqual(svc.summary(r.code)["status"], "vencida")

    def test_cancelada(self):
        svc = make_service()
        r = self._registrar(svc, make_reservation())
        r.status = "cancelled"
        self.assertEqual(svc.summary(r.code)["status"], "cancelada")

    def test_finalizada(self):
        svc = make_service()
        r = self._registrar(svc, make_reservation())
        r.status = "completed"
        self.assertEqual(svc.summary(r.code)["status"], "finalizada")


if __name__ == "__main__":
    unittest.main()

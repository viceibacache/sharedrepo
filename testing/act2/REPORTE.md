# Actividad 2 — Mutation Testing con LLMs

**Nombre: Vicente Ibacache**
**Número de alumno/a: 21640785**

|                      | GPT          | Gemini     |
| -------------------- | ------------ | ---------- |
| Modelo y versión     | GPT 5.6 Luna | Flash 3.6  |
| Fecha de la consulta | 09/02/2026   | 09/02/2026 |

---

## Tabla 1 - Mutantes por fuente

| Fuente  | Total | Invalidos | Validos | Equivalentes | Killed | Sobreviven | Score ajustado |
| ------- | ----- | --------- | ------- | ------------ | ------ | ---------- | -------------- |
| gpt     | 20    | 0         | 20      | 1            | 10     | 9          | 52.6%          |
| gemini  | 20    | 0         | 20      | 1            | 10     | 9          | 52.6%          |
| clasico | 146   | 0         | 146     | 0            | 106    | 40         | 72.6%          |

---

## Mutantes inválidos

Para cada modelo, clasifica por qué fallaron. **Si un modelo no produjo ninguno,
escribe "0 mutantes inválidos" y sigue: es un resultado válido, no una sección
faltante.**

0 mutantes invalidos.

## Mutantes equivalentes

Uno por fila, con la justificación de por qué ningún test podría matarlo.

**Si no identificaste equivalentes, escribe "no identifiqué mutantes equivalentes"
y explica en una línea por qué cada sobreviviente es un hueco real de la batería.
No inventes equivalentes: marcar como equivalente algo que sí es un hueco se
penaliza.**

| Modelo | #   | Línea | Cambio                                | Por qué es equivalente                                                                                                                                                |
| ------ | --- | ----- | ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Gemini | 11  | 47    | if total <= reservation.nightly_rate: | el mutante entra pero el original no, pero en ambos casos el valor final de total es menor o igual al nightly_rate, por lo que la condición se cumple en ambos casos. |
| GPT    | 14  | 47    | if total <= reservation.nightly_rate: | En ambos casos el valor final de total es menor o igual al nightly_rate, por lo que la condición se cumple en ambos casos.                                            |

## Tres sobrevivientes comentados

Elige tres sobrevivientes **no equivalentes** y para cada uno escribe el test que lo
mataría. Pueden venir de cualquiera de las tres fuentes: el baseline clásico siempre
deja sobrevivientes, así que los tres siempre están disponibles aunque los mutantes
de los modelos hayan muerto todos.

### Sobreviviente 1

- **Fuente y #: GPT #13**
- **Línea y cambio: if reservation.check_in.month in (1, 2, 7): a if reservation.check_in.month in (1, 2, 8):**
- **Por qué la batería base no lo detecta: ningún test de quote() usa una check_in con mes 7 o 8. El único mes de "temporada alta" probado es el mes 1 (test_recargo_temporada_alta, check_in=datetime(2027, 1, 15)), y este está en ambos conjuntos (1,2,7) y (1,2,8), así que el resultado es idéntico con o sin la mutación.**
- **Test que lo mataría** (nombre, entrada, aserción):

```
def test_recargo_temporada_alta_julio(self):
    svc = make_service()
    r = make_reservation(nights=2, tier="standard", check_in=datetime(2026, 7, 15))
    self.assertEqual(svc.quote(r), 236.0)
```

### Sobreviviente 2

- **Fuente y #: Gemini #19**
- **Línea y cambio: if self.clock.now() < end: a if self.clock.now() <= end:**
- **Por qué la batería base no lo detecta: los dos tests de complete() que ejecutan esta condición usan now estrictamente antes o después. En ninguno de los dos casos now == end, que es exactamente el único punto donde < y <= difieren.**
- **Test que lo mataría** (nombre, entrada, aserción):

```
def test_completa_justo_al_finalizar_estadia(self):
    svc = make_service(now=NOW + timedelta(days=43))
    r = make_reservation(check_in=NOW + timedelta(days=40), nights=3)
    r.status = "confirmed"
    svc.complete(r)
    self.assertEqual(r.status, "completed")
```

### Sobreviviente 3

- **Fuente y #: Clasico #14**
- **Línea y cambio: if nightly_rate <= 0: a if nightly_rate <= 1.0:**
- **Por qué la batería base no lo detecta: test_tarifa_invalida usa nightly_rate=0, que da la excepción en ambas versiones (0<=0 y 0<=1.0 son ambas True), y el resto de los tests usan nightly_rate=100.0, lo que válido en ambas versiones. Nunca se prueba un valor en el rango 0 a 1.0, que es justo donde el mutante se comporta distinto.**
- **Test que lo mataría** (nombre, entrada, aserción):

```
def test_tarifa_baja_pero_valida(self):
    svc = make_service()
    r = svc.create("R9", "ana@uc.cl", "gold", NOW + timedelta(days=10), 2, 0.5)
    self.assertEqual(r.nightly_rate, 0.5)
```

---

## Análisis

**1. ¿Qué modelo produjo más mutantes inválidos? ¿De qué tipo fueron los errores?**
Ambos modelos produjeron 0 mutantes inválidos.

**2. Compara los scores de GPT y Gemini. Si uno es más alto, ¿significa que ese
modelo generó mutantes "mejores"? Explica por qué un score alto puede indicar
mutantes triviales en vez de una batería sólida.**
Ambos modelos tuvieron el mismo score de 50%. Ambos modelos generaron mutantes similares e hicieron cambios bastante triviales (ambos modelos de concentraron en cambios como if (check_in - now).days > 365: a if (check_in - now).days >= 365:). Un score alto puede indicar mutantes triviales ya que esto puede ser una indicación de que se toma poco "riesgo" al crear nuevas mutantes, creando mutaciones fáciles de detectar (como cambiar true a un false en una condición importante) y disminuyendo la cobertura en casos borde.

**3. La batería base tiene 100% de statement y branch coverage. ¿Qué mutation
score obtuvo contra los mutantes clásicos? Explica con un ejemplo concreto por qué
la cobertura no garantiza detección de fallas.**
La batería obtuvo 72.6% de mutation score pese al 100% de statement/branch coverage porque coverage solo exige ejecutar cada línea y rama al menos una vez, no probar el valor límite exacto que distingue una parte correcta de una mutada. Por ejemplo, en el caso de check_in < now se cubre con check_in muy en el pasado o muy en el futuro, pero nunca con check_in == now, que es el único punto donde < y <= producen resultados distintos.

**4. ¿Los mutantes del LLM fueron más difíciles de matar que los clásicos? Compara
los tres scores y da un ejemplo de un mutante que solo una de las fuentes propuso.**
Ambos LLM tuvieron un score de 50%, lo que los hace más dificiles de matar que las mutaciones clásicas. Una mutante que solo se presenta en la rama clásica es el mutante nightly_rate <= 0 a nightly_rate <= 1.0. Aplica un swap de literal genérico sin entender que 0 es el límite de negocio relevante, a diferencia de mutantes tipo LLM que suelen apuntar a combinaciones semánticas (por ejemplo tier=="gold" and days_ahead>=1→>1) y dado al razonamiento de su existencia, los LLMs no lo hacen.

**5. ¿Qué tipo de mutante sobrevivió con más frecuencia? ¿Qué te dice eso sobre lo
que la batería base no está verificando?**
El tipo dominante fue el mutante de tipo </<= >/>= en rangos y umbrales como noches, días de anticipación, horas de plazo y meses de temporada. Esto indica que la suite prueba clases de equivalencia como válido o inválido pero nunca ancla tests en el valor límite exacto (== umbral).

**6. Si tuvieras que agregar tres tests a la batería base para subir el mutation
score, ¿cuáles serían y por qué esos?**

- Un test con nights=1, nights=30, check_in==now y check_in a exactamente 365 días, que mata a varias mutantes de create() de una vez.
- Un test de ciclo de vida con confirmación a 30 horas, reprogramación a exactamente 3 días, cancelación a exactamente 30 días, y cancelación gold a exactamente 1 día, con el fin de cubrir los umbrales más frecuentemente.
- Un test con check_in en el mes 7 para el recargo de temporada alta y otro con days_ahead==7 para el límite "próxima/inminente".

_Pregunta hipotética: descríbelos, no los escribas ni los ejecutes.
`tests/test_base.py` no se modifica._

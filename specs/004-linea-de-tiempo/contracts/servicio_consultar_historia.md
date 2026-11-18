# Contrato de Interfaz: `EstadoJuegoServicio.consultarHistoria`

**Capacidad**: `004-linea-de-tiempo`  
**Capa**: Servicio (`Servicio/EstadoJuegoServicio.py`)  
**Fecha**: 2026-11-08  

---

## Firma del Método

```python
def consultarHistoria(
    self, 
    instante: int | None = None, 
    accion: int | None = None
) -> ResumenEstadoDTO:
    """Consulta el estado del juego en un instante virtual o número de acción pasado.
    
    Parámetros:
      instante: Coordenada de tiempo virtual (t >= 0).
      accion: Número ordinal de acción en la línea de tiempo vigente (k >= 1).
      
    Retorna:
      ResumenEstadoDTO con el estado exacto en ese instante o acción.
      
    Lanza:
      ValueError:
        - Si ambos parámetros son None o ambos son provistos simultáneamente.
        - Si el valor provisto es booleano, no es entero o es negativo.
        - Si accion == 0 (las acciones son 1-based, k >= 1).
        - Si instante > reloj actual de la partida.
        - Si accion > acciones_vigentes + 1.
    """
```

---

## Precondiciones

1. La firma y el tipo de retorno deben ser estrictamente compatibles con la interfaz provisional ya existente (`test_historia_firma.py`).
2. Exactamente uno de los dos parámetros (`instante` o `accion`) debe ser distinto de `None`.
3. El servicio puede tener una partida viva o haber concluido (victoria o derrota). En ambos casos la consulta es válida.
4. Si el servicio no ha sido iniciado (caso de prueba de firma aislada `test_historia_firma.py`), retorna un `ResumenEstadoDTO` por defecto para preservar la compatibilidad con pruebas unitarias existentes de firma.

---

## Comportamiento y Postcondiciones

1. **Aislamiento absoluto**:
   - `self._estadoJuegoLogica.estadoJuego.reloj.tiempo_actual` permanece inalterado.
   - `self._estadoJuegoLogica.acciones_linea_tiempo` permanece inalterado.
   - `self._almacenLog` no registra nuevas líneas.
   - La bitácora `self._estadoJuegoLogica.logEventosJuego` permanece idéntica.
   - El historial de `RetrocesoLogica()` mantiene los mismos cambios antes y después de la invocación.
   - El generador de azar de la partida viva (`self._estadoJuegoLogica.gestorEventos.azar.getstate()`) no avanza.
2. **Determinismo**:
   - Para un mismo estado de partida, dos llamadas consecutivas con los mismos argumentos devuelven objetos equivalentes campo por campo.
   - `consultarHistoria(instante=0)` y `consultarHistoria(accion=1)` devuelven el estado inicial (equivalente al punto de control 0).
   - Si la acción $k$ comenzó en el instante $t$, `consultarHistoria(accion=k)` y `consultarHistoria(instante=t)` devuelven estados equivalentes (SC-002).
3. **Presupuesto de Red**:
   - Delta de solicitudes de red $= 0$.

---

## Casos de Error y Excepciones

| Condición | Tipo de Excepción | Mensaje descriptivo esperado |
|---|---|---|
| `instante is None and accion is None` | `ValueError` | `"Indica exactamente uno: instante (historia <t>) o accion (historia #k)"` |
| `instante is not None and accion is not None` | `ValueError` | `"Indica exactamente uno: instante (historia <t>) o accion (historia #k)"` |
| `instante < 0` o `accion < 0` o tipos no enteros (`float`, `str`, `bool`) | `ValueError` | `"El instante o el número de acción debe ser un entero mayor o igual que 0"` / `"El número de acción debe ser mayor o igual que 1"` |
| `accion == 0` | `ValueError` | `"El número de acción debe ser mayor o igual que 1"` (FR-435) |
| `instante > reloj_actual` | `ValueError` | `"El instante consultado aún no ha ocurrido"` (FR-433) |
| `accion > acciones_vigentes + 1` | `ValueError` | `"La acción consultada aún no ha ocurrido"` (FR-436) |

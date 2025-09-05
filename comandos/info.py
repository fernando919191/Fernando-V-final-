# comandos/info.py
import logging
from typing import Any, Dict, Optional, Tuple, Union
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes

# Según tu proyecto
from funcionamiento.licencias import usuario_tiene_licencia_activa
import funcionamiento.usuarios as usuarios
import funcionamiento.licencias as licencias

logger = logging.getLogger(__name__)

# =========================
# Utilidades de reflexión
# =========================
def _safe_getattr(obj, name: str):
    fn = getattr(obj, name, None)
    return fn if callable(fn) else None

def _call_first_available(obj, fn_names: Tuple[str, ...], *args, **kwargs):
    for fname in fn_names:
        fn = _safe_getattr(obj, fname)
        if fn:
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error en {obj.__name__}.{fname}: {e}", exc_info=True)
    return None

# =========================
# Normalización de objetos
# =========================
def _normalize_user_obj(obj: Any) -> Dict[str, Any]:
    """Convierte distintos formatos a un dict estándar."""
    if obj is None:
        return {}

    if isinstance(obj, dict):
        mapping = {
            "id": "user_id",
            "user_id": "user_id",
            "telegram_id": "user_id",
            "chat_id": "user_id",
            "username": "username",
            "first_name": "first_name",
            "last_name": "last_name",
            "nombre": "first_name",
            "apellido": "last_name",
            "es_admin": "is_admin",
            "is_admin": "is_admin",
            "fecha_registro": "created_at",
            "created_at": "created_at",
            "ultimo_acceso": "last_seen",
            "last_seen": "last_seen",
        }
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            std_key = mapping.get(k, k)
            out[std_key] = v
        return out

    if hasattr(obj, "__dict__"):
        return _normalize_user_obj(obj.__dict__.copy())

    # Tuplas/listas no se pueden normalizar sin esquema
    return {}

def _normalize_license_obj(obj: Any) -> Dict[str, Any]:
    """
    Intenta homogeneizar una licencia:
      - plan: nombre del plan (plan, tipo, nombre_plan…)
      - started_at: datetime inicio
      - expires_at: datetime expiración
      - status: 'activa'/'expirada' si se puede inferir
    """
    if obj is None:
        return {}

    if hasattr(obj, "__dict__") and not isinstance(obj, dict):
        obj = obj.__dict__.copy()

    if isinstance(obj, dict):
        plan = obj.get("plan") or obj.get("tipo") or obj.get("nombre_plan") or obj.get("level") or obj.get("tier")
        started = obj.get("started_at") or obj.get("fecha_inicio") or obj.get("inicio") or obj.get("created_at")
        expires = obj.get("expires_at") or obj.get("expira_en") or obj.get("fecha_expiracion") or obj.get("expiration")

        return {
            "plan": str(plan) if plan is not None else None,
            "started_at": _parse_to_dt(started),
            "expires_at": _parse_to_dt(expires),
            "raw": obj,
        }

    return {}

# =========================
# Parsing de fechas
# =========================
def _parse_to_dt(value: Any) -> Optional[datetime]:
    """
    Acepta:
      - datetime
      - int/float epoch (segundos o ms)
      - str en ISO/variantes comunes
    Devuelve timezone-aware (UTC).
    """
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    # epoch
    if isinstance(value, (int, float)):
        # heurística: si es muy grande, probablemente ms
        try:
            if value > 1e12:  # ms
                return datetime.fromtimestamp(value / 1000.0, tz=timezone.utc)
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except Exception:
            return None

    if isinstance(value, str):
        s = value.strip()
        # ISO directo
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            pass

        # Formatos comunes
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S",
                    "%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                dt = datetime.strptime(s, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except Exception:
                continue

    return None

def _human_delta(to_dt: datetime, from_dt: Optional[datetime] = None) -> Tuple[str, bool]:
    """
    Devuelve (texto_humano, is_expired).
    """
    now = from_dt or datetime.now(timezone.utc)
    delta = to_dt - now
    seconds = int(delta.total_seconds())
    expired = seconds <= 0
    seconds = abs(seconds)

    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60

    if days > 0:
        txt = f"{days} día(s) {hours} h"
    elif hours > 0:
        txt = f"{hours} h {minutes} min"
    else:
        txt = f"{minutes} min"

    return (("expirada hace " if expired else "restan ") + txt, expired)

# =========================
# Búsqueda de datos
# =========================
def _try_fetch_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    data = _call_first_available(
        usuarios,
        ("obtener_usuario_por_id", "get_usuario_por_id", "buscar_usuario_por_id"),
        user_id,
    )
    return _normalize_user_obj(data) if data else None

def _try_fetch_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    data = _call_first_available(
        usuarios,
        ("obtener_usuario_por_username", "get_usuario_por_username", "buscar_usuario_por_username"),
        username,
    )
    return _normalize_user_obj(data) if data else None

def _try_fetch_active_license(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Intenta varias funciones típicas de tu capa de licencias para traer
    la licencia activa (o la más reciente) del usuario.
    """
    data = _call_first_available(
        licencias,
        (
            "obtener_licencia_activa",
            "get_licencia_activa",
            "obtener_licencia_por_usuario",
            "get_licencia_por_usuario",
            "licencia_activa_de",
        ),
        user_id,
    )
    if data:
        return _normalize_license_obj(data)
    # Fallback: buscar premium_hasta en usuarios
    user_data = _try_fetch_user_by_id(user_id)
    if user_data and user_data.get("premium_hasta"):
        expires = _parse_to_dt(user_data["premium_hasta"])
        return {
            "plan": "Premium",
            "started_at": None,
            "expires_at": expires,
            "raw": {"premium_hasta": user_data["premium_hasta"]},
        }
    return None

# =========================
# Formateo de salida
# =========================
def _fmt_bool(v: Optional[bool]) -> str:
    return "Sí ✅" if v else "No ❌"

def _build_info_msg(found_user: Dict[str, Any], target_id: Optional[str], target_username: Optional[str]) -> str:
    # ID y username a mostrar
    user_id = str(found_user.get("user_id") or (target_id if (target_id and target_id.isdigit()) else "")).strip()
    username = found_user.get("username") or target_username

    # Licencia: detalle
    plan = None
    started_at = None
    expires_at = None
    lic_text = "Desconocido"

    if user_id:
        try:
            lic_detail = _try_fetch_active_license(user_id)
            if lic_detail:
                plan = lic_detail.get("plan")
                started_at = lic_detail.get("started_at")
                expires_at = lic_detail.get("expires_at")
        except Exception as e:
            logger.error(f"Error obteniendo licencia detallada de {user_id}: {e}")

        # fallback al booleano si no tenemos detalle
        try:
            activa = usuario_tiene_licencia_activa(user_id)
            if activa and not plan:
                lic_text = "Activa ✅"
            elif not activa and not plan:
                lic_text = "No activa ❌"
        except Exception:
            pass

    # Construcción del mensaje
    lines = ["🛈 *Información del usuario*"]
    if user_id:
        lines.append(f"• ID: `{user_id}`")
    if username:
        uname = username[1:] if isinstance(username, str) and username.startswith("@") else username
        lines.append(f"• Username: @{uname}")

    if found_user.get("first_name") or found_user.get("last_name"):
        nombre = f"{found_user.get('first_name','')} {found_user.get('last_name','')}".strip()
        if nombre:
            lines.append(f"• Nombre: {nombre}")

    if found_user.get("is_admin") is not None:
        lines.append(f"• Admin: {_fmt_bool(bool(found_user.get('is_admin')))}")

    if found_user.get("created_at"):
        lines.append(f"• Registrado: {found_user.get('created_at')}")
    if found_user.get("last_seen"):
        lines.append(f"• Último acceso: {found_user.get('last_seen')}")

    # Bloque de licencia detallada
    lines.append("—")
    lines.append("*Licencia*")

    if plan or started_at or expires_at:
        if plan:
            lines.append(f"• Plan: *{plan}*")
        if started_at:
            lines.append(f"• Inicio: {started_at.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        if expires_at:
            exp_txt, expired = _human_delta(expires_at)
            lines.append(f"• Expira: {expires_at.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
            lines.append(f"• Estado: {'Expirada ❌' if expired else 'Activa ✅'}")
            lines.append(f"• Tiempo restante: {exp_txt.replace('restan ', '').replace('expirada hace ', '') if not expired else exp_txt}")
        else:
            # Si no hay expiración, mostramos booleano (si lo tenemos)
            if lic_text != "Desconocido":
                lines.append(f"• Estado: {lic_text}")
    else:
        # Sin detalle → estado booleano o mensaje
        lines.append(f"• Estado: {lic_text}")

    return "\n".join(lines)

# =========================
# Handler principal
# =========================
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Uso:
      .info                 → tu propio usuario
      .info 123456          → por ID
      .info @pepito         → por username
      .info@pepito          → (index.py pone 'pepito' en context.args[0])
      /info [id|@user]      → también funciona como slash
    """
    try:
        target_id: Optional[str] = None
        target_username: Optional[str] = None

        if context.args:
            raw = (context.args[0] or "").strip()
            if raw.startswith("@"):
                target_username = raw[1:]
            elif raw.isdigit():
                target_id = raw
            else:
                target_username = raw
        else:
            # Sin args → propio usuario
            if update.effective_user:
                target_id = str(update.effective_user.id)
                if update.effective_user.username:
                    target_username = update.effective_user.username

        found: Dict[str, Any] = {}
        if target_id and target_id.isdigit():
            data = _try_fetch_user_by_id(target_id)
            if data:
                found.update(data)

        if not found and target_username:
            data = _try_fetch_user_by_username(target_username)
            if data:
                found.update(data)
                if not target_id:
                    tid = data.get("user_id") or data.get("id")
                    if tid:
                        target_id = str(tid)

        msg = _build_info_msg(found, target_id, target_username)

        if update.message:
            await update.message.reply_text(msg, parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.edit_message_text(msg, parse_mode="Markdown")
        else:
            if update.effective_chat:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error en comando info: {e}", exc_info=True)
        if update.message:
            await update.message.reply_text("⚠️ Ocurrió un error consultando la información.")

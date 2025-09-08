# comandos/info.py
import logging
import sqlite3
import os
from typing import Any, Dict, Optional, Tuple, Union
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes

# Configuración de la base de datos
DB_PATH = 'database.db'

logger = logging.getLogger(__name__)

# =========================
# Conexión a la base de datos
# =========================
def get_db_connection():
    """Establece conexión con la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# =========================
# Funciones de base de datos (CORREGIDAS)
# =========================
def obtener_usuario_por_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene usuario por ID desde la base de datos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        return dict(user) if user else None
    except Exception as e:
        logger.error(f"Error obteniendo usuario por ID {user_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def obtener_usuario_por_username(username: str) -> Optional[Dict[str, Any]]:
    """Obtiene usuario por username desde la base de datos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE username = ?", (username,))
        user = cursor.fetchone()
        return dict(user) if user else None
    except Exception as e:
        logger.error(f"Error obteniendo usuario por username {username}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def obtener_licencia_activa(user_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene la licencia activa de un usuario desde la base de datos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM licencias WHERE user_id = ? AND activa = 1", (user_id,))
        licencia = cursor.fetchone()
        return dict(licencia) if licencia else None
    except Exception as e:
        logger.error(f"Error obteniendo licencia activa para usuario {user_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def usuario_tiene_licencia_activa(user_id: str) -> bool:
    """Verifica si un usuario tiene licencia activa"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM licencias 
            WHERE user_id = ? AND activa = 1 AND fecha_expiracion > datetime('now')
        """, (user_id,))
        result = cursor.fetchone()
        return result['count'] > 0 if result else False
    except Exception as e:
        logger.error(f"Error verificando licencia activa para usuario {user_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

# =========================
# Utilidades de reflexión (simplificadas)
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
            "fecha_registro": "fecha_registro",
            "created_at": "fecha_registro",
            "ultimo_acceso": "ultima_vez_visto",
            "last_seen": "ultima_vez_visto",
            "premium_hasta": "premium_hasta"
        }
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            std_key = mapping.get(k, k)
            out[std_key] = v
        return out

    if hasattr(obj, "__dict__"):
        return _normalize_user_obj(obj.__dict__.copy())

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
        # Usar 'das' para determinar el plan (ej: 30 días = Plan Premium 30)
        das = obj.get("das")
        if das:
            plan = f"Premium {das} días"
        else:
            plan = obj.get("plan") or obj.get("tipo") or "Premium"
            
        started = obj.get("started_at") or obj.get("fecha_activacion") or obj.get("fecha_sciivacion")
        expires = obj.get("expires_at") or obj.get("fecha_expiracion")

        return {
            "plan": str(plan),
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

        # Formatos comunes para SQLite
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
    data = obtener_usuario_por_id(user_id)
    return _normalize_user_obj(data) if data else None

def _try_fetch_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    data = obtener_usuario_por_username(username)
    return _normalize_user_obj(data) if data else None

def _try_fetch_active_license(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Intenta varias funciones típicas de tu capa de licencias para traer
    la licencia activa (o la más reciente) del usuario.
    """
    data = obtener_licencia_activa(user_id)
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

def _fmt_date(dt: Optional[datetime]) -> str:
    if not dt:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M UTC")

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

    # Campo is_admin puede no existir en tu tabla, lo omitimos si no está presente
    if found_user.get("is_admin") is not None:
        lines.append(f"• Admin: {_fmt_bool(bool(found_user.get('is_admin')))}")

    if found_user.get("fecha_registro"):
        lines.append(f"• Registrado: {_fmt_date(_parse_to_dt(found_user.get('fecha_registro')))}")
    if found_user.get("ultima_vez_visto"):
        lines.append(f"• Último acceso: {_fmt_date(_parse_to_dt(found_user.get('ultima_vez_visto')))}")

    # Bloque de licencia detallada
    lines.append("—")
    lines.append("*Licencia*")

    if plan or started_at or expires_at:
        if plan:
            lines.append(f"• Plan: *{plan}*")
        if started_at:
            lines.append(f"• Inicio: {_fmt_date(started_at)}")
        if expires_at:
            exp_txt, expired = _human_delta(expires_at)
            lines.append(f"• Expira: {_fmt_date(expires_at)}")
            lines.append(f"• Estado: {'Expirada ❌' if expired else 'Activa ✅'}")
            lines.append(f"• Tiempo: {exp_txt}")
        else:
            if lic_text != "Desconocido":
                lines.append(f"• Estado: {lic_text}")
    else:
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

# Función auxiliar para verificar la conexión
def verificar_conexion_db():
    """Verifica que la base de datos esté accesible"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_names = [table['name'] for table in tables]
        logger.info(f"Tablas en la base de datos: {table_names}")
        
        # Verificar que existan las tablas necesarias
        if 'usuarios' not in table_names:
            logger.error("❌ La tabla 'usuarios' no existe en la base de datos")
        if 'licencias' not in table_names:
            logger.error("❌ La tabla 'licencias' no existe en la base de datos")
            
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        return False

# Verificar conexión al importar
if __name__ != "__main__":
    verificar_conexion_db()
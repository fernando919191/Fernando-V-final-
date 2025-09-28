import aiohttp
import asyncio
import logging
import json
from typing import Dict, Optional, Tuple
import ipaddress

logger = logging.getLogger(__name__)

class IPLookup:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.ipdata.co"
        self.session = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json',
                },
                timeout=aiohttp.ClientTimeout(total=10)
            )
        return self.session
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def validate_ip(self, ip_str: str) -> bool:
        """Validate IP address format"""
        try:
            ipaddress.ip_address(ip_str)
            return True
        except ValueError:
            return False
    
    async def lookup_ip(self, ip_address: str) -> Tuple[bool, Optional[Dict], str]:
        """Lookup IP information using ipdata.co API"""
        if not self.validate_ip(ip_address):
            return False, None, "❌ Dirección IP inválida"
        
        try:
            session = await self.get_session()
            url = f"{self.base_url}/{ip_address}?api-key={self.api_key}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return True, data, "✅ Búsqueda exitosa"
                elif response.status == 400:
                    return False, None, "❌ IP inválida o mal formada"
                elif response.status == 401:
                    return False, None, "❌ API key inválida o no autorizada"
                elif response.status == 404:
                    return False, None, "❌ IP no encontrada en la base de datos"
                elif response.status == 429:
                    return False, None, "❌ Límite de tasa excedido"
                else:
                    return False, None, f"❌ Error HTTP {response.status}"
                    
        except asyncio.TimeoutError:
            return False, None, "❌ Timeout de conexión (10s)"
        except aiohttp.ClientError as e:
            return False, None, f"❌ Error de conexión: {str(e)}"
        except json.JSONDecodeError:
            return False, None, "❌ Respuesta JSON inválida"
        except Exception as e:
            logger.error(f"Error in IP lookup: {e}")
            return False, None, f"❌ Error interno: {str(e)}"
    
    def calculate_threat_score(self, ip_data: Dict) -> int:
        """Calculate threat score based on IP data"""
        score = 100  # Start with perfect score
        
        # Reduce score based on threats
        if ip_data.get('threat', {}).get('is_threat', False):
            score -= 40
        
        # Reduce score based on tor or proxy
        if ip_data.get('threat', {}).get('is_tor', False):
            score -= 30
        if ip_data.get('threat', {}).get('is_proxy', False):
            score -= 25
        
        # Reduce score based on anonymous usage
        if ip_data.get('threat', {}).get('is_anonymous', False):
            score -= 20
        
        # Ensure score doesn't go below 0
        return max(0, score)
    
    def format_response(self, ip_address: str, ip_data: Dict, threat_score: int) -> str:
        """Format the IP lookup response"""
        country = ip_data.get('country_name', 'Desconocido')
        country_code = ip_data.get('country_code', 'N/A')
        city = ip_data.get('city', 'Desconocida')
        region = ip_data.get('region', 'Desconocida')
        asn = ip_data.get('asn', {}).get('asn', 'N/A')
        organization = ip_data.get('asn', {}).get('name', 'Desconocida')
        isp = ip_data.get('asn', {}).get('domain', 'Desconocido')
        carrier = ip_data.get('carrier', {}).get('name', 'N/A')
        
        # Threat indicators
        threats = ip_data.get('threat', {})
        is_threat = threats.get('is_threat', False)
        is_tor = threats.get('is_tor', False)
        is_proxy = threats.get('is_proxy', False)
        is_anonymous = threats.get('is_anonymous', False)
        
        # Emoji for threat score
        if threat_score >= 80:
            score_emoji = "🟢"
            risk_level = "Bajo riesgo"
        elif threat_score >= 60:
            score_emoji = "🟡"
            risk_level = "Riesgo medio"
        elif threat_score >= 40:
            score_emoji = "🟠"
            risk_level = "Riesgo alto"
        else:
            score_emoji = "🔴"
            risk_level = "Riesgo muy alto"
        
        # Threat indicators text
        threat_indicators = []
        if is_threat:
            threat_indicators.append("🔴 Amenaza conocida")
        if is_tor:
            threat_indicators.append("🟡 Nodo TOR")
        if is_proxy:
            threat_indicators.append("🟠 Proxy/VPN")
        if is_anonymous:
            threat_indicators.append("🔵 Anónimo")
        
        threat_text = "\n".join(threat_indicators) if threat_indicators else "🟢 Sin amenazas detectadas"
        
        response = f"""
🌐 *INFORMACIÓN DE IP*
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬

🆔 *IP:* `{ip_address}`
🏴 *País:* {country} ({country_code})
🏙️ *Ciudad:* {city}
📍 *Región:* {region}

🏢 *Organización:* {organization}
📡 *ISP:* {isp}
📶 *Carrier:* {carrier}
🔢 *ASN:* {asn}

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
🛡️ *REPUTACIÓN:* {score_emoji} `{threat_score}/100`
📊 *NIVEL DE RIESGO:* {risk_level}

🔍 *AMENAZAS:*
{threat_text}

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
💾 *Fuente:* ipdata.co
⚡ *Nota:* Entre mayor reputación, mejor tu IP.
"""
        return response

# Global instance with your API key
ip_lookup = IPLookup(api_key="782bca965c5f37b9e633e1cd8d531554a247a85ab5c645586cd07feb")
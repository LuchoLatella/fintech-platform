"""
Middleware: Autenticación JWT + Rate Limiting por usuario/IP.
"""
import time
from typing import Optional

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings

ALGORITHM = "HS256"

# Rutas que no requieren autenticación
PUBLIC_PATHS = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/v1/argentina/dolar",    # datos públicos sin auth
    "/api/v1/argentina/riesgo-pais",
}

# Rate limits: (requests, ventana en segundos)
RATE_LIMITS = {
    "free":       (60,  60),    # 60 req/min
    "pro":        (300, 60),    # 300 req/min
    "enterprise": (1000, 60),   # 1000 req/min
    "anonymous":  (20,  60),    # 20 req/min sin auth
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting por usuario autenticado o por IP para anónimos.
    Usa Redis para contar requests en ventanas deslizantes.
    """

    async def dispatch(self, request: Request, call_next):
        # Obtener Redis del estado de la app
        redis = getattr(request.app.state, "redis", None)
        if not redis:
            return await call_next(request)

        # Identificar al solicitante
        user_id, plan = await self._identify(request)
        key = f"ratelimit:{user_id}"
        limit, window = RATE_LIMITS.get(plan, RATE_LIMITS["anonymous"])

        # Conteo con ventana deslizante en Redis
        now = int(time.time())
        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, now - window)
        pipe.zadd(key, {str(now * 1000): now})
        pipe.zcard(key)
        pipe.expire(key, window)
        results = await pipe.execute()
        count = results[2]

        if count > limit:
            return JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit excedido. Límite: {limit} requests/{window}s"},
                headers={"Retry-After": str(window)},
            )

        # Agregar headers informativos
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
        return response

    async def _identify(self, request: Request):
        """Extrae user_id y plan del JWT si existe, sino usa la IP."""
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("sub", "anon")
                plan = payload.get("plan", "free")
                return user_id, plan
            except JWTError:
                pass
        ip = request.client.host if request.client else "unknown"
        return f"ip:{ip}", "anonymous"


class JWTBearer(HTTPBearer):
    """Dependencia reutilizable para proteger endpoints con JWT."""

    def __init__(self, required_plan: Optional[str] = None, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.required_plan = required_plan

    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        credentials = await super().__call__(request)
        if not credentials:
            return None

        try:
            payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "access":
                raise HTTPException(status_code=403, detail="Token inválido")

            # Verificar plan si es necesario
            if self.required_plan:
                plan_hierarchy = {"free": 0, "pro": 1, "enterprise": 2}
                user_plan = payload.get("plan", "free")
                if plan_hierarchy.get(user_plan, 0) < plan_hierarchy.get(self.required_plan, 0):
                    raise HTTPException(
                        status_code=403,
                        detail=f"Esta función requiere plan {self.required_plan} o superior"
                    )
        except JWTError:
            raise HTTPException(status_code=401, detail="Token JWT inválido o vencido")

        return credentials


# Instancias listas para usar como Depends()
require_auth = JWTBearer()
require_pro = JWTBearer(required_plan="pro")
require_enterprise = JWTBearer(required_plan="enterprise")
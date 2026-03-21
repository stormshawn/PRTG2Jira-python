"""
IP whitelisting middleware
Corresponds to app.Use in Program.cs

"""
from typing import Callable, List
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class IPWhitelistMiddleware(BaseHTTPMiddleware):
    # def __init__(self, app: Callable, allowedipaddresses: List[str], dispatch = None):
    #     super().__init__(app, dispatch)
    def __init__(self, app: Callable, allowed_ips: List[str], enabled: bool = True):
        super().__init__(app)
        self.allowed_ips: List[str] = allowed_ips
        self.enabled: bool = enabled
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Delegate how incoming requests IP addresses should be handled
        """
        if not self.enabled:
            return await call_next(request)
        
        client_ip: str = request.client.host if request.client else ""

        if client_ip.startswith("::ffff:"):
            client_ip = client_ip[7:]
            
        if client_ip not in self.allowed_ips:
            raise HTTPException(status_code=403, detail="Client IP address not allowed")
        
        return await call_next(request)

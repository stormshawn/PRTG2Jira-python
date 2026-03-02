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
    def __init__(self, app: Callable, allowedipaddresses: List[str], isenabled: bool = True):
         super().__init__(app)
         self.allowedipaddresses: List[str] = allowedipaddresses
         self.isenabled: bool = isenabled 
    async def dispatch(self, request: Request, callnext: Callable) -> Response:
        """
        Delegate how incoming requests IP addresses should be handled
        """
        if not self.isenabled:
            return await callnext(request)
        client_ip_addr: str = request.client.host if request.client else ""

        if client_ip_addr.startswith("::ffff:"):
            client_ip_addr = client_ip_addr[7:]
            
        if client_ip_addr not in self.allowedipaddresses:
            raise HTTPException(status_code=403, detail="Client IP address not allowed")
        return await callnext(request)


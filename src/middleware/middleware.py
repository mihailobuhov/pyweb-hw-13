import re
from fastapi import Request, status
from fastapi.responses import JSONResponse
from typing import Callable

# Бан-лист User-Agent
user_agent_ban_list = [r"Googlebot", r"Python-urllib"]


# Middleware для блокування за User-Agent
async def user_agent_ban_middleware(request: Request, call_next: Callable):
    user_agent = request.headers.get("user-agent")
    print(user_agent)  # Вивести user-agent для діагностики
    for ban_pattern in user_agent_ban_list:
        if re.search(ban_pattern, user_agent):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "You are banned"},
            )
    response = await call_next(request)
    return response

"""Grocery checkout stubs for the explore sandbox."""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Dict, List, Optional

from .models import Ingredient

ProgressCallback = Callable[[Dict[str, Any]], Awaitable[None]]


async def groceries_checkout(
    ingredients: List[Ingredient],
    progress_cb: Optional[ProgressCallback] = None,
) -> Optional[str]:
    if progress_cb:
        await progress_cb({"type": "status", "message": "Creating demo grocery cart..."})

    await asyncio.sleep(0)

    if not ingredients:
        return None

    return f"https://example.com/cart?items={len(ingredients)}"


__all__ = ["groceries_checkout", "ProgressCallback"]

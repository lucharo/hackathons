"""MCP (Model Context Protocol) server API endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/mcp", tags=["mcp"])

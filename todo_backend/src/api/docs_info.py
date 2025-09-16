from fastapi import APIRouter
from starlette.responses import JSONResponse

# PUBLIC_INTERFACE
def get_docs_router() -> APIRouter:
    """
    Create a router that exposes documentation helper endpoints.

    Returns:
        APIRouter: Router with documentation related endpoints like WebSocket usage notes.
    """
    router = APIRouter()

    @router.get(
        "/docs/websocket-usage",
        tags=["docs"],
        summary="WebSocket usage notes",
        operation_id="websocket_usage_notes",
        description=(
            "This project currently does not expose WebSocket endpoints.\n"
            "If real-time features are added in the future, they should be registered with explicit tags, "
            "operation IDs, and documented at /docs/websocket-usage."
        ),
        responses={
            200: {
                "description": "WebSocket usage documentation",
                "content": {"application/json": {}},
            }
        },
    )
    def websocket_usage_docs() -> JSONResponse:
        """
        Returns a structured note indicating WebSocket usage guidance for the project.
        """
        return JSONResponse(
            {
                "websocket": {
                    "enabled": False,
                    "notes": "No WebSocket endpoints are currently available. Future endpoints should be documented here."
                }
            }
        )

    return router

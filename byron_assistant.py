"""Floating B.Y.R.O.N. assistant for the Streamlit app."""

from __future__ import annotations

import base64
import html
import json
from pathlib import Path

import streamlit.components.v1 as components


PROJECT_FOLDER = Path(__file__).resolve().parent
ROBOT_IMAGE = PROJECT_FOLDER / "assets" / "byron_robot.png"


def _image_data_uri() -> str:
    if not ROBOT_IMAGE.exists():
        return ""

    image_bytes = ROBOT_IMAGE.read_bytes()
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def show_byron(
    message: str = "Hey friend... ready to see what the market is doing?",
    mood: str = "idle",
) -> None:
    safe_message = html.escape(message)
    message_json = json.dumps(safe_message)
    mood_json = json.dumps(mood)
    image_uri_json = json.dumps(_image_data_uri())

    component_html = f"""
    <script>
    (() => {{
        const parentDocument = window.parent.document;
        const parentWindow = window.parent;
        const assistantId = "byron-floating-assistant";
        const styleId = "byron-floating-assistant-style";

        if (!parentDocument.getElementById(styleId)) {{
            const style = parentDocument.createElement("style");
            style.id = styleId;
            style.textContent = `
                #byron-floating-assistant {{
                    position: fixed;
                    right: 18px;
                    bottom: 18px;
                    z-index: 999999;
                    display: flex;
                    align-items: flex-end;
                    gap: 10px;
                    pointer-events: none;
                    font-family: Arial, sans-serif;
                }}

                #byron-floating-assistant .byron-bubble {{
                    max-width: 260px;
                    background: rgba(14, 17, 23, 0.96);
                    color: white;
                    border: 1px solid rgba(57, 217, 138, 0.65);
                    border-radius: 16px 16px 4px 16px;
                    padding: 12px 14px;
                    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.35);
                    font-size: 14px;
                    line-height: 1.35;
                }}

                #byron-floating-assistant .byron-character {{
                    width: 112px;
                    height: 145px;
                    display: flex;
                    justify-content: center;
                    align-items: flex-end;
                    transform-origin: bottom center;
                    animation: byron-idle 3s ease-in-out infinite;
                }}

                #byron-floating-assistant .byron-character img {{
                    display: block;
                    max-width: 112px;
                    max-height: 145px;
                    object-fit: contain;
                    filter: drop-shadow(0 8px 12px rgba(0, 0, 0, 0.4));
                }}

                #byron-floating-assistant .byron-fallback {{
                    font-size: 72px;
                    line-height: 1;
                }}

                #byron-floating-assistant.byron-thinking .byron-character {{
                    animation: byron-thinking 0.9s ease-in-out infinite;
                }}

                #byron-floating-assistant.byron-success .byron-character {{
                    animation: byron-celebrate 0.6s ease-in-out 3;
                }}

                #byron-floating-assistant.byron-error .byron-character {{
                    animation: byron-awkward 0.7s ease-in-out 2;
                }}

                #byron-floating-assistant.byron-tapping .byron-character {{
                    animation: byron-tap 0.55s ease-in-out 4;
                }}

                @keyframes byron-idle {{
                    0%, 100% {{ transform: translateY(0); }}
                    50% {{ transform: translateY(-4px); }}
                }}

                @keyframes byron-thinking {{
                    0%, 100% {{ transform: rotate(-1deg) translateY(0); }}
                    50% {{ transform: rotate(1deg) translateY(-5px); }}
                }}

                @keyframes byron-celebrate {{
                    0%, 100% {{ transform: translateY(0) scale(1); }}
                    50% {{ transform: translateY(-12px) scale(1.04); }}
                }}

                @keyframes byron-awkward {{
                    0%, 100% {{ transform: translateX(0); }}
                    25% {{ transform: translateX(-4px); }}
                    75% {{ transform: translateX(4px); }}
                }}

                @keyframes byron-tap {{
                    0%, 100% {{ transform: translateX(0) rotate(0deg); }}
                    50% {{ transform: translateX(-12px) rotate(-3deg); }}
                }}

                @media (max-width: 640px) {{
                    #byron-floating-assistant {{
                        right: 8px;
                        bottom: 8px;
                        gap: 6px;
                    }}

                    #byron-floating-assistant .byron-bubble {{
                        max-width: 180px;
                        font-size: 12px;
                        padding: 9px 10px;
                    }}

                    #byron-floating-assistant .byron-character {{
                        width: 76px;
                        height: 102px;
                    }}

                    #byron-floating-assistant .byron-character img {{
                        max-width: 76px;
                        max-height: 102px;
                    }}
                }}
            `;
            parentDocument.head.appendChild(style);
        }}

        let assistant = parentDocument.getElementById(assistantId);

        if (!assistant) {{
            assistant = parentDocument.createElement("div");
            assistant.id = assistantId;
            assistant.innerHTML = `
                <div class="byron-bubble" aria-live="polite"></div>
                <div class="byron-character"></div>
            `;
            parentDocument.body.appendChild(assistant);
        }}

        const bubble = assistant.querySelector(".byron-bubble");
        const character = assistant.querySelector(".byron-character");
        const imageUri = {image_uri_json};

        if (imageUri) {{
            character.innerHTML = `<img src="${{imageUri}}" alt="B.Y.R.O.N. assistant">`;
        }} else {{
            character.innerHTML = `<div class="byron-fallback">🤖</div>`;
        }}

        assistant.className = "";
        assistant.classList.add(`byron-${{{mood_json}}}`);
        bubble.innerHTML = {message_json};

        if (!parentWindow.__byronIdleListenerInstalled) {{
            parentWindow.__byronIdleListenerInstalled = true;
            let idleTimer = null;
            let idleAllowed = true;

            const resetIdleTimer = () => {{
                const currentAssistant = parentDocument.getElementById(assistantId);

                if (currentAssistant && currentAssistant.classList.contains("byron-tapping")) {{
                    currentAssistant.className = "byron-idle";
                    currentAssistant.querySelector(".byron-bubble").textContent =
                        "There you are. I thought you left me over here by myself.";
                }}

                if (idleTimer) {{
                    parentWindow.clearTimeout(idleTimer);
                }}

                if (!idleAllowed) {{
                    return;
                }}

                idleTimer = parentWindow.setTimeout(() => {{
                    const activeAssistant = parentDocument.getElementById(assistantId);

                    if (!activeAssistant) {{
                        return;
                    }}

                    activeAssistant.className = "byron-tapping";
                    activeAssistant.querySelector(".byron-bubble").textContent =
                        "Tap, tap... friend, we analyzing something or just vibing?";

                    idleAllowed = false;

                    parentWindow.setTimeout(() => {{
                        idleAllowed = true;
                        resetIdleTimer();
                    }}, 60000);
                }}, 25000);
            }};

            ["mousemove", "mousedown", "keydown", "scroll", "touchstart"].forEach((eventName) => {{
                parentWindow.addEventListener(eventName, resetIdleTimer, {{ passive: true }});
            }});

            resetIdleTimer();
        }}
    }})();
    </script>
    """

    components.html(component_html, height=0, width=0)

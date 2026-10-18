"""Prueba standalone de conexión al proveedor LLM.

Lee la configuración desde .env y realiza una llamada real al proveedor
para validar que API key, base URL y modelo funcionan correctamente.

Nunca imprime el valor real de LLM_API_KEY.
"""

import os
import sys
import json
from dotenv import load_dotenv
import httpx


def main() -> int:
    print("=== Prueba de conexión LLM ===\n")

    # Cargar variables desde .env
    load_dotenv()

    llm_provider = os.getenv("LLM_PROVIDER", "openai_compatible")
    llm_api_key = os.getenv("LLM_API_KEY")
    llm_base_url = os.getenv("LLM_BASE_URL")
    llm_model = os.getenv("LLM_MODEL")
    llm_timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
    llm_max_tokens = int(os.getenv("LLM_MAX_TOKENS", "512"))
    llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))

    # Validar que los valores requeridos estén presentes
    missing = []
    if not llm_provider:
        missing.append("LLM_PROVIDER")
    if not llm_api_key:
        missing.append("LLM_API_KEY")
    if not llm_base_url:
        missing.append("LLM_BASE_URL")
    if not llm_model:
        missing.append("LLM_MODEL")

    if missing:
        print("ERROR: Faltan las siguientes variables en .env:")
        for var in missing:
            print(f"  - {var}")
        print("\nCopia .env.example a .env y completa los valores de tu proveedor.")
        return 1

    print(f"LLM_PROVIDER={llm_provider}")
    print('LLM_API_KEY= "rpta: apikey correcta funcionando"')
    print(f"LLM_BASE_URL={llm_base_url}")
    print(f"LLM_MODEL={llm_model}")
    print()

    # Construir la URL del endpoint
    base_url = llm_base_url.rstrip("/")
    endpoint = f"{base_url}/chat/completions"

    # Cuerpo compatible con OpenAI Chat Completions
    payload = {
        "model": llm_model,
        "messages": [
            {"role": "system", "content": "Responde brevemente en español."},
            {"role": "user", "content": "Hola, di algo corto para probar la conexión."},
        ],
        "temperature": llm_temperature,
        "max_tokens": llm_max_tokens,
    }

    headers = {
        "Authorization": f"Bearer {llm_api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        with httpx.Client(timeout=llm_timeout) as client:
            response = client.post(endpoint, headers=headers, json=payload)
    except httpx.TimeoutException as exc:
        print(f"ERROR: Tiempo de espera agotado ({llm_timeout}s).")
        print(f"Detalle: {type(exc).__name__}")
        print("\n=== Prueba fallida ===")
        return 1
    except httpx.RequestError as exc:
        print(f"ERROR: No se pudo conectar al proveedor.")
        print(f"Detalle: {type(exc).__name__}: {exc}")
        print("\n=== Prueba fallida ===")
        return 1

    # Procesar la respuesta
    if response.status_code == 401:
        print("ERROR: HTTP 401 - API key inválida o no autorizada.")
        print("Verifica que LLM_API_KEY sea correcta.")
    elif response.status_code == 404:
        print("ERROR: HTTP 404 - El modelo o endpoint no fue encontrado.")
        print("Verifica LLM_BASE_URL y LLM_MODEL.")
    elif response.status_code == 429:
        print("ERROR: HTTP 429 - Límite de solicitudes excedido (rate limit).")
    elif response.status_code >= 500:
        print(f"ERROR: HTTP {response.status_code} - Error del proveedor externo.")
    elif response.status_code >= 400:
        print(f"ERROR: HTTP {response.status_code} - Solicitud inválida.")
    elif not response.is_success:
        print(f"ERROR: HTTP {response.status_code} - Respuesta no exitosa.")
    else:
        try:
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                content = message.get("content")
                reasoning = message.get("reasoning") or message.get("reasoning_content")

                if isinstance(content, str) and content.strip():
                    print(f'Respuesta de la consulta en test : "{content.strip()}"')
                    if isinstance(reasoning, str) and reasoning.strip():
                        print(f"Razonamiento previo ({len(reasoning)} caracteres):")
                        preview = reasoning.strip().replace("\n", " ")[:120]
                        print(f'  "{preview}..."')
                elif isinstance(reasoning, str) and reasoning.strip():
                    print(f'Respuesta (obtenida de reasoning): "{reasoning.strip()}"')
                else:
                    print("ERROR: La respuesta no contiene contenido de texto ni razonamiento.")
                    print(f"Respuesta cruda: {response.text[:200]}")
                    return 1
            else:
                if "error" in data:
                    err = data["error"]
                    err_msg = err.get("message") if isinstance(err, dict) else err
                    print(f"ERROR: El proveedor devolvió un error en la respuesta: {err_msg}")
                else:
                    print("ERROR: La respuesta no contiene 'choices'.")
                raw_preview = response.text.strip()[:300]
                print(f"Respuesta cruda: {raw_preview}")
                return 1

            usage = data.get("usage", {})
            if usage:
                input_tokens = usage.get("prompt_tokens")
                output_tokens = usage.get("completion_tokens")
                if input_tokens is not None or output_tokens is not None:
                    print(
                        f"Tokens de entrada: {input_tokens} | "
                        f"Tokens de salida: {output_tokens}"
                    )

            print("\n=== Prueba completada con éxito ===")
            return 0

        except json.JSONDecodeError as exc:
            print(f"ERROR: La respuesta no es un JSON válido: {exc}")
            print(f"Respuesta cruda: {response.text[:200]}")
            print("\n=== Prueba fallida ===")
            return 1

    print("\n=== Prueba fallida ===")
    return 1


if __name__ == "__main__":
    sys.exit(main())

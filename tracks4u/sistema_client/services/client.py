import requests
from sistema_client.config.settings import (
    SISTEMA_API_BASE_URL,
    SISTEMA_API_TIMEOUT
)


class SistemaAPIClient:
    """
    Cliente para consumir el API externo del sistema.
    """

    def __init__(self):
        self.base_url = SISTEMA_API_BASE_URL
        self.timeout = SISTEMA_API_TIMEOUT

    def _get(self, endpoint: str):
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            return {
                "error": True,
                "message": str(e),
                "endpoint": endpoint
            }

    # 🔥 TU ENDPOINT ESPECÍFICO
    def get_estado_sistema(self):
        return self._get("/sistema/estado/")
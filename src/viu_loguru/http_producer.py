"""
HTTP Producer para envio de logs ao VIU via API
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

LOG = logging.getLogger(__name__)


class HTTPProducer:
    """
    Producer HTTP para enviar logs ao VIU via API

    Benefícios:
    - Não expõe Kafka diretamente
    - Autenticação via API Key
    - Mais simples de configurar
    - Rate limiting e validação no backend
    """

    def __init__(
        self,
        api_url: str,
        api_key: str,
        timeout: int = 10,
        max_retries: int = 3,
        retry_backoff: float = 0.5,
    ):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

        # Configurar retry
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        self.session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Headers padrão
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"ApiKey {api_key}",
        }

    def _build_url(self, path: str = "/logs") -> str:
        """Constrói URL completa"""
        return urljoin(self.api_url, path)

    def send(self, log_entry: Dict[str, Any]) -> bool:
        """
        Envia um log para a API

        Args:
            log_entry: Dicionário com os dados do log

        Returns:
            True se enviou com sucesso, False caso contrário
        """
        try:
            url = self._build_url("/api/v1/logs")
            response = self.session.post(
                url,
                json=log_entry,
                headers=self.headers,
                timeout=self.timeout,
            )

            if response.status_code in (200, 201, 202):
                LOG.debug(f"Log sent successfully to {url}")
                return True
            else:
                LOG.error(
                    f"Failed to send log: {response.status_code} - {response.text}"
                )
                return False

        except requests.exceptions.Timeout:
            LOG.error(f"Timeout sending log to {self.api_url}")
            return False
        except requests.exceptions.RequestException as e:
            LOG.error(f"Error sending log: {e}")
            return False

    def send_batch(self, log_entries: List[Dict[str, Any]]) -> bool:
        """
        Envia múltiplos logs em uma única requisição

        Args:
            log_entries: Lista de dicionários com os dados dos logs

        Returns:
            True se enviou com sucesso, False caso contrário
        """
        try:
            url = self._build_url("/api/v1/logs")
            response = self.session.post(
                url,
                json=log_entries,
                headers=self.headers,
                timeout=self.timeout,
            )

            if response.status_code in (200, 201, 202):
                LOG.debug(f"Batch of {len(log_entries)} logs sent successfully")
                return True
            else:
                LOG.error(
                    f"Failed to send batch: {response.status_code} - {response.text}"
                )
                return False

        except requests.exceptions.Timeout:
            LOG.error(f"Timeout sending batch to {self.api_url}")
            return False
        except requests.exceptions.RequestException as e:
            LOG.error(f"Error sending batch: {e}")
            return False

    def health_check(self) -> bool:
        """
        Verifica se a API está acessível

        Returns:
            True se a API está respondendo, False caso contrário
        """
        try:
            # Tenta acessar health endpoint ou root
            url = self.api_url.rstrip("/")
            response = self.session.get(url, timeout=5)
            return response.status_code < 500
        except Exception:
            return False

    def close(self):
        """Fecha a sessão HTTP"""
        if self.session:
            self.session.close()


class HTTPProducerAsync:
    """
    Producer HTTP assíncrono para enviar logs ao VIU via API
    """

    def __init__(
        self,
        api_url: str,
        api_key: str,
        timeout: int = 10,
    ):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"ApiKey {self.api_key}",
        }

    def _build_url(self, path: str = "/logs") -> str:
        return urljoin(self.api_url, path)

    async def send(self, log_entry: Dict[str, Any]) -> bool:
        """Envia um log de forma assíncrona"""
        try:
            import aiohttp

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = self._build_url("/api/v1/logs")
                async with session.post(
                    url,
                    json=log_entry,
                    headers=self._get_headers(),
                ) as response:
                    return response.status in (200, 201, 202)

        except Exception as e:
            LOG.error(f"Error sending async log: {e}")
            return False

    async def send_batch(self, log_entries: List[Dict[str, Any]]) -> bool:
        """Envia múltiplos logs de forma assíncrona"""
        try:
            import aiohttp

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = self._build_url("/api/v1/logs")
                async with session.post(
                    url,
                    json=log_entries,
                    headers=self._get_headers(),
                ) as response:
                    return response.status in (200, 201, 202)

        except Exception as e:
            LOG.error(f"Error sending async batch: {e}")
            return False

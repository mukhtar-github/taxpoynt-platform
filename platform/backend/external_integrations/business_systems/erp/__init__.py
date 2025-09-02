"""
External Integrations - ERP Business Systems

Specific ERP system connector implementations.
Uses the universal connector framework for consistent interfaces.
"""

from external_integrations.connector_framework import BaseERPConnector, GenericERPConnector
from .odoo import OdooConnector
from .sap import SAPConnector
from .oracle import OracleERPConnector
from .dynamics import DynamicsERPConnector
from .netsuite import NetSuiteERPConnector

__all__ = [
    "BaseERPConnector",
    "GenericERPConnector", 
    "OdooConnector",
    "SAPConnector",
    "OracleERPConnector",
    "DynamicsERPConnector",
    "NetSuiteERPConnector"
]
"""
Configuration des règles de validation de date de naissance par pays.
Zone OMEA (Océan Indien, Moyen-Orient, Afrique de l'Est)
"""

from typing import Dict, Any
from datetime import datetime


DOB_VALIDATION_RULES = {
    "Madagascar": {
        "min_age": 18,
        "max_age": 95,
        "description": "Date de naissance - Minimum 18 ans, Maximum 95 ans"
    },
    "Mauritius": {
        "min_age": 18,
        "max_age": 95,
        "description": "Date de naissance - Minimum 18 ans, Maximum 95 ans"
    },
    "Seychelles": {
        "min_age": 18,
        "max_age": 95,
        "description": "Date de naissance - Minimum 18 ans, Maximum 95 ans"
    },
}


def get_dob_validation_rules(country: str) -> Dict[str, Any]:
    """
    Récupère les règles de validation DOB pour un pays.
    
    Args:
        country: Nom du pays
    
    Returns:
        Dict avec règles de validation
    """
    
    if country not in DOB_VALIDATION_RULES:
        # Retourner les règles par défaut
        return {
            "min_age": 18,
            "max_age": 95,
            "description": "Default rules - Minimum 18 years, Maximum 95 years"
        }
    
    return DOB_VALIDATION_RULES[country]

def detect_dob_format(dob_str: str) -> str:
    """
    Détecte le format d'une date de naissance.
    Supporte plusieurs formats car les données ne sont pas toujours propres.
    """
    import re
    
    dob_str = str(dob_str).strip()
    
    # ISO 8601 datetime avec heure (ex: 1997-12-25T00:00:00.000Z)
    # Testé en premier car son pattern est un sur-ensemble de YYYY-MM-DD
    if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', dob_str):
        return "ISO_DATETIME"
    
    # YYYY-MM-DD
    if re.match(r'^\d{4}-\d{2}-\d{2}$', dob_str):
        return "YYYY-MM-DD"
    
    # DD-MM-YYYY
    if re.match(r'^\d{2}-\d{2}-\d{4}$', dob_str):
        return "DD-MM-YYYY"
    
    # DD/MM/YYYY
    if re.match(r'^\d{2}/\d{2}/\d{4}$', dob_str):
        return "DD/MM/YYYY"
    
    # YYYY/MM/DD
    if re.match(r'^\d{4}/\d{2}/\d{2}$', dob_str):
        return "YYYY/MM/DD"
    
    # DDMMYYYY (sans séparateur)
    if re.match(r'^\d{8}$', dob_str):
        return "DDMMYYYY"
    
    # DD.MM.YYYY (point comme séparateur)
    if re.match(r'^\d{2}\.\d{2}\.\d{4}$', dob_str):
        return "DD.MM.YYYY"
    
    # YYYY.MM.DD (point comme séparateur)
    if re.match(r'^\d{4}\.\d{2}\.\d{2}$', dob_str):
        return "YYYY.MM.DD"
    
    return "UNKNOWN"


def parse_dob(dob_str: str, detected_format: str) -> datetime:
    """
    Parse une date de naissance selon son format détecté.
    Gère les erreurs de parsing gracieusement.
    """
    from datetime import datetime
    
    dob_str = str(dob_str).strip()
    
    try:
        if detected_format == "ISO_DATETIME":
            # Ne garder que la partie date (avant le T)
            date_part = dob_str.split('T')[0]
            return datetime.strptime(date_part, "%Y-%m-%d")
        elif detected_format == "YYYY-MM-DD":
            return datetime.strptime(dob_str, "%Y-%m-%d")
        elif detected_format == "DD-MM-YYYY":
            return datetime.strptime(dob_str, "%d-%m-%Y")
        elif detected_format == "DD/MM/YYYY":
            return datetime.strptime(dob_str, "%d/%m/%Y")
        elif detected_format == "YYYY/MM/DD":
            return datetime.strptime(dob_str, "%Y/%m/%d")
        elif detected_format == "DDMMYYYY":
            return datetime.strptime(dob_str, "%d%m%Y")
        elif detected_format == "DD.MM.YYYY":
            return datetime.strptime(dob_str, "%d.%m.%Y")
        elif detected_format == "YYYY.MM.DD":
            return datetime.strptime(dob_str, "%Y.%m.%d")
        else:
            return None
    except ValueError:
        return None

def validate_dob(dob_str: str, country: str) -> Dict[str, Any]:
    """
    Valide une date de naissance selon les règles du pays.
    
    Args:
        dob_str: Chaîne de date
        country: Pays
    
    Returns:
        Dict avec résultats de validation
    """
    
    from datetime import datetime
    
    if not dob_str or str(dob_str).strip() == "":
        return {
            "valid": False,
            "error": "Empty date of birth",
            "format": None,
            "age": None
        }
    
    # Détecter le format
    detected_format = detect_dob_format(dob_str)
    
    if detected_format == "UNKNOWN":
        return {
            "valid": False,
            "error": "Unknown date format",
            "format": detected_format,
            "age": None
        }
    
    # Parser la date
    parsed_dob = parse_dob(dob_str, detected_format)
    
    if parsed_dob is None:
        return {
            "valid": False,
            "error": "Invalid date value",
            "format": detected_format,
            "age": None
        }
    
    # Vérifier que la date n'est pas dans le futur
    if parsed_dob > datetime.now():
        return {
            "valid": False,
            "error": "Date of birth is in the future",
            "format": detected_format,
            "age": None
        }
    
    # Calculer l'âge
    today = datetime.now()
    age = today.year - parsed_dob.year
    if (today.month, today.day) < (parsed_dob.month, parsed_dob.day):
        age -= 1
    
    # Récupérer les règles du pays
    rules = get_dob_validation_rules(country)
    min_age = rules["min_age"]
    max_age = rules["max_age"]
    
    # Vérifier l'âge
    if age < min_age:
        return {
            "valid": False,
            "error": f"Age {age} is below minimum {min_age}",
            "format": detected_format,
            "age": age
        }
    
    if age > max_age:
        return {
            "valid": False,
            "error": f"Age {age} exceeds maximum {max_age}",
            "format": detected_format,
            "age": age
        }
    
    return {
        "valid": True,
        "error": None,
        "format": detected_format,
        "age": age
    }

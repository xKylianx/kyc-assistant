"""
Configuration des règles de validation des numéros d'ID par pays et type.
Zone OMEA (Océan Indien, Moyen-Orient, Afrique de l'Est)
"""

from typing import Dict, Any, Optional
import re


ID_VALIDATION_RULES = {
    "Madagascar": {
        "CNI": {
            "name": "Carte Nationale d'Identité",
            "format": "12 digits",
            "pattern": r"^\d{12}$",
            "length": 12,
            "min_length": 12,
            "max_length": 12,
            "allowed_characters": "0-9",
            "description": "Numéro de CNI Madagascar - 12 chiffres",
            "examples": ["123456789012", "987654321098"],
            "validation_rules": {
                "numeric_only": True,
                "exact_length": 12,
                "checksum": None,  # À implémenter si besoin
            }
        },
        "Passport": {
            "name": "Passeport",
            "format": "2 letters + 7 digits",
            "pattern": r"^[A-Z]{2}\d{7}$",
            "length": 9,
            "min_length": 9,
            "max_length": 9,
            "allowed_characters": "A-Z, 0-9",
            "description": "Numéro de Passeport Madagascar",
            "examples": ["AB1234567", "CD9876543"],
            "validation_rules": {
                "numeric_only": False,
                "exact_length": 9,
                "checksum": None,
            }
        },
        "Driving_License": {
            "name": "Permis de Conduire",
            "format": "Variable",
            "pattern": r"^[A-Z0-9]{6,20}$",
            "length": None,
            "min_length": 6,
            "max_length": 20,
            "allowed_characters": "A-Z, 0-9",
            "description": "Numéro de Permis de Conduire Madagascar",
            "examples": ["ABC123456", "DL1234567890"],
            "validation_rules": {
                "numeric_only": False,
                "exact_length": None,
                "checksum": None,
            }
        }
    },
    
    # Placeholder pour autres pays OMEA
    "Mauritius": {
        "NIC": {
            "name": "National Identity Card",
            "format": "Variable",
            "pattern": r"^[A-Z0-9]{6,20}$",
            "length": None,
            "min_length": 6,
            "max_length": 20,
            "allowed_characters": "A-Z, 0-9",
            "description": "Numéro de NIC Maurice",
            "examples": [],
            "validation_rules": {
                "numeric_only": False,
                "exact_length": None,
                "checksum": None,
            }
        }
    },
    
    "Botswana": {
        "CNI": {
            "name": "Carte Nationale d'Identité",
            "format": "9 digits",
            "pattern": r"^\d{9}$",
            "length": 9,
            "min_length": 9,
            "max_length": 9,
            "allowed_characters": "0-9",
            "description": "Numéro de CNI Botswana - 9 chiffres",
            "examples": ["123456789", "987654321"],
            "validation_rules": {
                "numeric_only": True,
                "exact_length": 9,
                "checksum": None,  # À implémenter si besoin
            }
        }
    }
}


def get_id_validation_rules(
    country: str,
    id_type: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Récupère les règles de validation pour un pays et type d'ID.
    
    Args:
        country: Nom du pays
        id_type: Type d'ID (CNI, Passport, etc.)
    
    Returns:
        Dict avec règles de validation ou None
    """
    
    if country not in ID_VALIDATION_RULES:
        return None
    
    country_rules = ID_VALIDATION_RULES[country]
    
    if id_type is None:
        # Retourner tous les types pour ce pays
        return country_rules
    
    # Normaliser le type d'ID
    id_type_normalized = id_type.upper().replace(" ", "_")
    
    return country_rules.get(id_type_normalized)


def validate_id_number(
    id_number: str,
    country: str,
    id_type: str
) -> Dict[str, Any]:
    """
    Valide un numéro d'ID contre les règles du pays/type.
    
    Args:
        id_number: Numéro d'ID à valider
        country: Pays
        id_type: Type d'ID
    
    Returns:
        Dict avec résultats de validation
    """
    
    rules = get_id_validation_rules(country, id_type)
    
    if not rules:
        return {
            "valid": False,
            "error": f"No validation rules for {country} - {id_type}"
        }
    
    id_number_str = str(id_number).strip()
    
    # Vérifier si vide
    if not id_number_str:
        return {
            "valid": False,
            "error": "ID number is empty"
        }
    
    # Vérifier la longueur
    if rules.get("validation_rules", {}).get("exact_length"):
        expected_length = rules["length"]
        if len(id_number_str) != expected_length:
            return {
                "valid": False,
                "error": f"Expected length {expected_length}, got {len(id_number_str)}"
            }
    else:
        min_length = rules.get("min_length")
        max_length = rules.get("max_length")
        
        if min_length and len(id_number_str) < min_length:
            return {
                "valid": False,
                "error": f"Length {len(id_number_str)} is below minimum {min_length}"
            }
        
        if max_length and len(id_number_str) > max_length:
            return {
                "valid": False,
                "error": f"Length {len(id_number_str)} exceeds maximum {max_length}"
            }
    
    # Vérifier le pattern
    pattern = rules.get("pattern")
    if pattern:
        if not re.match(pattern, id_number_str):
            return {
                "valid": False,
                "error": f"Does not match expected format: {rules.get('format')}"
            }
    
    # Vérifier si numérique uniquement
    if rules.get("validation_rules", {}).get("numeric_only"):
        if not id_number_str.isdigit():
            return {
                "valid": False,
                "error": "Must contain only digits"
            }
    
    return {
        "valid": True,
        "error": None
    }


def get_expected_id_types(country: str) -> list:
    """
    Récupère les types d'ID attendus pour un pays.
    
    Args:
        country: Nom du pays
    
    Returns:
        Liste des types d'ID
    """
    
    if country not in ID_VALIDATION_RULES:
        return []
    
    return list(ID_VALIDATION_RULES[country].keys())

def validate_id_number_any_type(
    id_number: str,
    country: str
) -> Dict[str, Any]:
    """
    Valide un numéro d'ID contre TOUS les types de règles connus du pays,
    sans présupposer le type. Utilisé quand la colonne type d'ID est absente
    ou de mauvaise qualité — un ID est considéré valide s'il correspond à
    au moins un format attendu pour ce pays.
    
    Args:
        id_number: Numéro d'ID à valider
        country: Pays
    
    Returns:
        Dict avec :
            valid: bool
            matched_type: str|None — le type qui a matché, si trouvé
            error: str|None
    """
    country_rules = ID_VALIDATION_RULES.get(country)
    
    if not country_rules:
        return {
            "valid": False,
            "matched_type": None,
            "error": f"No validation rules defined for country {country}",
        }
    
    id_number_str = str(id_number).strip()
    
    if not id_number_str:
        return {
            "valid": False,
            "matched_type": None,
            "error": "ID number is empty",
        }
    
    # Teste chaque type de règle du pays, s'arrête au premier match
    for id_type_key in country_rules.keys():
        result = validate_id_number(id_number_str, country, id_type_key)
        if result["valid"]:
            return {
                "valid": True,
                "matched_type": id_type_key,
                "error": None,
            }
    
    return {
        "valid": False,
        "matched_type": None,
        "error": f"Does not match any known ID format for {country}",
    }
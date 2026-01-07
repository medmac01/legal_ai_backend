"""
Description: 
    Jinja2 template engine for rendering NDA documents.
    Provides functionality to render NDA templates with user-provided context.
    
Author: Adapted from Streamlit app for FastAPI
Date  : 2025/01/07
"""

import os
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

# Get the directory where this module is located
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_TEMPLATES_DIR = os.path.join(_MODULE_DIR, 'templates')

# Load templates from the templates directory
env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR))


def render_template(user_inputs: dict) -> str:
    """
    Render the NDA template with the provided context.
    
    Args:
        user_inputs: Dictionary containing the values to render in the template.
            Required fields:
            - first_party: Name of the first party
            - first_party_address: Address of the first party
            - first_party_incorporation_state: Incorporation state of the first party
            - first_party_representative: Representative of the first party
            - first_party_registration_number: Registration number of the first party
            - first_party_role: Role of the first party ('Disclosing Party', 'Receiving Party', or 'Both (Bilateral)')
            - second_party: Name of the second party
            - second_party_address: Address of the second party
            - second_party_incorporation_state: Incorporation state of the second party
            - second_party_representative: Representative of the second party
            - second_party_registration_number: Registration number of the second party
            - purpose: Purpose of the NDA
            - applicable_law: Governing law
            - language: Language of the contract
            - duration: Duration in months
            - date: Effective date
            - litigation: Dispute resolution mechanism
    
    Returns:
        Rendered NDA document as a string.
    
    Raises:
        ValueError: If required fields are missing.
        TemplateNotFound: If the template file is not found.
    """
    # Validate required fields
    required_fields = [
        'first_party', 'first_party_address', 'first_party_incorporation_state',
        'first_party_representative', 'first_party_registration_number', 'first_party_role',
        'second_party', 'second_party_address', 'second_party_incorporation_state',
        'second_party_representative', 'second_party_registration_number',
        'purpose', 'applicable_law', 'language', 'duration', 'date', 'litigation'
    ]
    
    missing_fields = [field for field in required_fields if field not in user_inputs or not user_inputs[field]]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    # Select template based on first party role
    first_party_role = user_inputs.get('first_party_role', '')
    
    if first_party_role == 'Disclosing Party':
        template_name = 'nda_template_disclosing.j2'
    elif first_party_role == 'Receiving Party':
        template_name = 'nda_template_receiving.j2'
    elif first_party_role == 'Both (Bilateral)':
        template_name = 'nda_template_bilateral.j2'
    else:
        raise ValueError(f"Invalid first_party_role: '{first_party_role}'. Must be 'Disclosing Party', 'Receiving Party', or 'Both (Bilateral)'.")
    
    try:
        template = env.get_template(template_name)
        return template.render(user_inputs)
    except TemplateNotFound:
        raise TemplateNotFound(f"Template '{template_name}' not found in {_TEMPLATES_DIR}")


def get_available_templates() -> list:
    """
    Get a list of available NDA templates.
    
    Returns:
        List of template names.
    """
    return [
        'nda_template_disclosing.j2',
        'nda_template_receiving.j2',
        'nda_template_bilateral.j2'
    ]

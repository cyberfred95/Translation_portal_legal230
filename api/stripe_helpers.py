"""
Stripe API utility functions.

This module provides utility functions for Stripe-related API operations,
including URL building and response formatting.
"""

from urllib.parse import urlencode, urlparse, parse_qs, urlunparse


def _parse_existing_query_params(query_string: str) -> dict[str, str]:
    """
    Parse existing query parameters from URL query string.
    
    Args:
        query_string: URL query string.
        
    Returns:
        dict: Dictionary of query parameters with string keys and values.
    """
    if not query_string:
        return {}
    
    parsed_params = parse_qs(query_string, keep_blank_values=True)
    query_params = {}
    
    for key, value_list in parsed_params.items():
        key_str = str(key)
        if isinstance(value_list, list) and value_list:
            query_params[key_str] = str(value_list[0])
        elif value_list:
            query_params[key_str] = str(value_list)
        else:
            query_params[key_str] = ""
    
    return query_params


def _build_url_components(parsed_url) -> tuple[str, str, str, str, str]:
    """
    Extract and convert URL components to strings.
    
    Args:
        parsed_url: Parsed URL result from urlparse.
        
    Returns:
        tuple: (scheme, netloc, path, params, fragment) as strings.
    """
    return (
        str(parsed_url.scheme) if parsed_url.scheme else '',
        str(parsed_url.netloc) if parsed_url.netloc else '',
        str(parsed_url.path) if parsed_url.path else '',
        str(parsed_url.params) if parsed_url.params else '',
        str(parsed_url.fragment) if parsed_url.fragment else ''
    )


def build_pricing_url_with_client_secret(base_url: str, client_secret: str) -> str:
    """
    Build pricing page URL with Stripe customer session client_secret parameter.
    
    Args:
        base_url: Base pricing page URL.
        client_secret: Stripe customer session client_secret.
        
    Returns:
        Complete URL with client_secret parameter.
        
    Raises:
        ValueError: If base_url is None or empty.
    """
    if not base_url:
        raise ValueError("base_url cannot be None or empty")
    
    parsed = urlparse(str(base_url))
    
    # Parse existing query parameters
    query_params = _parse_existing_query_params(parsed.query)
    
    # Add the client_secret parameter
    query_params['customer_session_client_secret'] = str(client_secret)
    
    # Build query string
    new_query = urlencode([(str(k), str(v)) for k, v in query_params.items()])
    
    # Build URL components as strings
    scheme, netloc, path, params, fragment = _build_url_components(parsed)
    
    return urlunparse((scheme, netloc, path, params, new_query, fragment))

"""
Schema.org structured data validator for SEO Auditor
Validates JSON-LD, Microdata, and RDFa markup
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import re

import requests
from jsonschema import validate as json_validate, ValidationError as JsonSchemaValidationError

from utils.cache import CacheManager
from utils.logger import log_execution_time

logger = logging.getLogger(__name__)


class SchemaValidationError(Exception):
    """Custom exception for schema validation errors"""
    pass


class SchemaValidator:
    """
    Schema.org structured data validator
    """

    # Common Schema.org types and their required properties
    SCHEMA_REQUIREMENTS = {
        'Article': ['headline', 'author', 'datePublished'],
        'NewsArticle': ['headline', 'author', 'datePublished'],
        'BlogPosting': ['headline', 'author', 'datePublished'],
        'Product': ['name', 'image'],
        'Organization': ['name'],
        'Person': ['name'],
        'LocalBusiness': ['name', 'address'],
        'Event': ['name', 'startDate', 'location'],
        'Recipe': ['name', 'image', 'author'],
        'VideoObject': ['name', 'description', 'thumbnailUrl', 'uploadDate'],
        'BreadcrumbList': ['itemListElement'],
        'FAQPage': ['mainEntity'],
        'HowTo': ['name', 'step'],
        'JobPosting': ['title', 'description', 'datePosted'],
        'Course': ['name', 'description', 'provider']
    }

    # Google recommended properties
    GOOGLE_RECOMMENDED = {
        'Article': ['image', 'dateModified'],
        'Product': ['aggregateRating', 'offers', 'review'],
        'Organization': ['logo', 'url', 'sameAs'],
        'LocalBusiness': ['telephone', 'priceRange'],
        'Event': ['image', 'description', 'offers'],
        'Recipe': ['recipeIngredient', 'recipeInstructions', 'totalTime'],
        'VideoObject': ['contentUrl', 'duration']
    }

    def __init__(self, config: Dict = None, cache_manager: Optional[CacheManager] = None):
        """
        Initialize schema validator

        Args:
            config: Configuration dictionary
            cache_manager: Optional cache manager
        """
        self.config = config or {}
        self.cache_manager = cache_manager

        # Get configuration
        validator_config = self.config.get('integrations', {}).get('schema_validator', {})
        self.enabled = validator_config.get('enabled', True)
        self.strict_mode = validator_config.get('strict_mode', False)

        # Statistics
        self.stats = {
            'total_validations': 0,
            'passed': 0,
            'failed': 0,
            'warnings': 0
        }

        logger.info("Schema validator initialized")

    @log_execution_time(logger)
    def validate_structured_data(
            self,
            structured_data: List[Dict],
            url: str = ""
    ) -> Dict[str, Any]:
        """
        Validate structured data from a page

        Args:
            structured_data: List of structured data objects (from parsers.py)
            url: URL being validated

        Returns:
            Dictionary with validation results
        """
        self.stats['total_validations'] += 1

        results = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'total_schemas': len(structured_data),
            'valid_schemas': 0,
            'schemas': [],
            'errors': [],
            'warnings': [],
            'summary': {
                'has_structured_data': len(structured_data) > 0,
                'types_found': [],
                'validation_passed': False
            }
        }

        if not structured_data:
            results['warnings'].append({
                'type': 'missing_structured_data',
                'message': 'No structured data found on page',
                'severity': 'warning'
            })
            self.stats['warnings'] += 1
            return results

        # Validate each schema
        for idx, schema in enumerate(structured_data):
            schema_result = self._validate_single_schema(schema, idx)
            results['schemas'].append(schema_result)

            if schema_result['valid']:
                results['valid_schemas'] += 1

            # Collect errors and warnings
            results['errors'].extend(schema_result.get('errors', []))
            results['warnings'].extend(schema_result.get('warnings', []))

            # Track schema types
            schema_type = schema_result.get('type', 'Unknown')
            if schema_type not in results['summary']['types_found']:
                results['summary']['types_found'].append(schema_type)

        # Determine overall validation status
        if results['valid_schemas'] == results['total_schemas'] and len(results['errors']) == 0:
            results['summary']['validation_passed'] = True
            self.stats['passed'] += 1
        else:
            self.stats['failed'] += 1

        logger.info(f"Validated {results['total_schemas']} schemas for {url}")
        return results

    def _validate_single_schema(self, schema: Dict, index: int) -> Dict[str, Any]:
        """
        Validate a single schema object

        Args:
            schema: Schema object to validate
            index: Index in the list

        Returns:
            Validation result dictionary
        """
        result = {
            'index': index,
            'type': self._get_schema_type(schema),
            'context': schema.get('@context', 'Unknown'),
            'valid': True,
            'errors': [],
            'warnings': [],
            'missing_required': [],
            'missing_recommended': []
        }

        schema_type = result['type']

        # Check if it's a valid Schema.org context
        if not self._is_valid_schema_org_context(schema.get('@context')):
            result['valid'] = False
            result['errors'].append({
                'property': '@context',
                'message': 'Invalid or missing @context for Schema.org',
                'severity': 'error'
            })

        # Validate JSON-LD structure
        if '@type' not in schema:
            result['valid'] = False
            result['errors'].append({
                'property': '@type',
                'message': '@type property is required',
                'severity': 'error'
            })
            return result

        # Check required properties
        if schema_type in self.SCHEMA_REQUIREMENTS:
            required_props = self.SCHEMA_REQUIREMENTS[schema_type]
            missing_required = self._check_required_properties(schema, required_props)

            if missing_required:
                result['missing_required'] = missing_required
                result['valid'] = False if self.strict_mode else result['valid']

                for prop in missing_required:
                    error_level = 'error' if self.strict_mode else 'warning'
                    result['errors' if self.strict_mode else 'warnings'].append({
                        'property': prop,
                        'message': f'Required property "{prop}" is missing for {schema_type}',
                        'severity': error_level
                    })

        # Check recommended properties
        if schema_type in self.GOOGLE_RECOMMENDED:
            recommended_props = self.GOOGLE_RECOMMENDED[schema_type]
            missing_recommended = self._check_required_properties(schema, recommended_props)

            if missing_recommended:
                result['missing_recommended'] = missing_recommended

                for prop in missing_recommended:
                    result['warnings'].append({
                        'property': prop,
                        'message': f'Recommended property "{prop}" is missing for {schema_type}',
                        'severity': 'info'
                    })

        # Validate specific schema types
        type_specific_validation = self._validate_type_specific(schema, schema_type)
        if not type_specific_validation['valid']:
            result['valid'] = False
            result['errors'].extend(type_specific_validation['errors'])
        result['warnings'].extend(type_specific_validation['warnings'])

        return result

    def _get_schema_type(self, schema: Dict) -> str:
        """Extract schema type from object"""
        schema_type = schema.get('@type', 'Unknown')

        # Handle array of types
        if isinstance(schema_type, list):
            return schema_type[0] if schema_type else 'Unknown'

        return schema_type

    def _is_valid_schema_org_context(self, context: Any) -> bool:
        """Check if context is valid Schema.org"""
        if not context:
            return False

        valid_contexts = [
            'https://schema.org',
            'http://schema.org',
            'https://schema.org/',
            'http://schema.org/'
        ]

        if isinstance(context, str):
            return context in valid_contexts
        elif isinstance(context, list):
            return any(ctx in valid_contexts for ctx in context if isinstance(ctx, str))

        return False

    def _check_required_properties(self, schema: Dict, required: List[str]) -> List[str]:
        """
        Check for missing required properties

        Returns:
            List of missing property names
        """
        missing = []

        for prop in required:
            if prop not in schema or not schema[prop]:
                missing.append(prop)

        return missing

    def _validate_type_specific(self, schema: Dict, schema_type: str) -> Dict[str, Any]:
        """
        Type-specific validation rules

        Args:
            schema: Schema object
            schema_type: Type of schema

        Returns:
            Validation result with errors and warnings
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        # Article validations
        if schema_type in ['Article', 'NewsArticle', 'BlogPosting']:
            # Check author format
            if 'author' in schema:
                if not self._validate_author(schema['author']):
                    result['warnings'].append({
                        'property': 'author',
                        'message': 'Author should be a Person or Organization schema',
                        'severity': 'warning'
                    })

            # Check date format
            if 'datePublished' in schema:
                if not self._validate_date_format(schema['datePublished']):
                    result['errors'].append({
                        'property': 'datePublished',
                        'message': 'Invalid date format for datePublished (should be ISO 8601)',
                        'severity': 'error'
                    })
                    result['valid'] = False

        # Product validations
        elif schema_type == 'Product':
            # Check offers structure
            if 'offers' in schema:
                if not self._validate_offers(schema['offers']):
                    result['errors'].append({
                        'property': 'offers',
                        'message': 'Offers must include price and priceCurrency',
                        'severity': 'error'
                    })
                    result['valid'] = False

        # Event validations
        elif schema_type == 'Event':
            # Check location structure
            if 'location' in schema:
                if not self._validate_location(schema['location']):
                    result['warnings'].append({
                        'property': 'location',
                        'message': 'Location should be a Place schema with address',
                        'severity': 'warning'
                    })

        # BreadcrumbList validations
        elif schema_type == 'BreadcrumbList':
            if 'itemListElement' in schema:
                if not self._validate_breadcrumb_list(schema['itemListElement']):
                    result['errors'].append({
                        'property': 'itemListElement',
                        'message': 'BreadcrumbList items must have position and item properties',
                        'severity': 'error'
                    })
                    result['valid'] = False

        return result

    def _validate_author(self, author: Any) -> bool:
        """Validate author property"""
        if isinstance(author, dict):
            author_type = author.get('@type', '')
            return author_type in ['Person', 'Organization']
        elif isinstance(author, str):
            return len(author) > 0
        return False

    def _validate_date_format(self, date_str: str) -> bool:
        """Validate ISO 8601 date format"""
        if not isinstance(date_str, str):
            return False

        # ISO 8601 patterns
        patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # YYYY-MM-DDTHH:MM:SS
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$',  # With Z
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$'  # With timezone
        ]

        return any(re.match(pattern, date_str) for pattern in patterns)

    def _validate_offers(self, offers: Any) -> bool:
        """Validate offers structure"""
        if isinstance(offers, dict):
            offers = [offers]

        if isinstance(offers, list):
            for offer in offers:
                if not isinstance(offer, dict):
                    return False
                if 'price' not in offer or 'priceCurrency' not in offer:
                    return False
            return True

        return False

    def _validate_location(self, location: Any) -> bool:
        """Validate location structure"""
        if isinstance(location, dict):
            location_type = location.get('@type', '')
            return location_type in ['Place', 'VirtualLocation']
        return False

    def _validate_breadcrumb_list(self, items: List) -> bool:
        """Validate breadcrumb list structure"""
        if not isinstance(items, list) or len(items) == 0:
            return False

        for item in items:
            if not isinstance(item, dict):
                return False
            if 'position' not in item or 'item' not in item:
                return False

        return True

    def generate_schema_report(
            self,
            validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive schema validation report

        Args:
            validation_results: Results from validate_structured_data

        Returns:
            Formatted report dictionary
        """
        report = {
            'url': validation_results.get('url', ''),
            'timestamp': validation_results.get('timestamp', ''),
            'overall_status': 'passed' if validation_results['summary']['validation_passed'] else 'failed',
            'summary': {
                'total_schemas': validation_results['total_schemas'],
                'valid_schemas': validation_results['valid_schemas'],
                'schema_types': validation_results['summary']['types_found'],
                'total_errors': len(validation_results['errors']),
                'total_warnings': len(validation_results['warnings'])
            },
            'details': [],
            'recommendations': []
        }

        # Add schema details
        for schema in validation_results['schemas']:
            detail = {
                'type': schema['type'],
                'valid': schema['valid'],
                'errors': len(schema['errors']),
                'warnings': len(schema['warnings']),
                'missing_required': schema.get('missing_required', []),
                'missing_recommended': schema.get('missing_recommended', [])
            }
            report['details'].append(detail)

        # Generate recommendations
        if not validation_results['summary']['has_structured_data']:
            report['recommendations'].append(
                'Add structured data markup to improve search visibility'
            )

        if validation_results['errors']:
            report['recommendations'].append(
                f'Fix {len(validation_results["errors"])} critical errors in structured data'
            )

        if validation_results['warnings']:
            report['recommendations'].append(
                f'Address {len(validation_results["warnings"])} warnings to improve markup quality'
            )

        return report

    def get_statistics(self) -> Dict[str, Any]:
        """Get validator statistics"""
        return {
            'enabled': self.enabled,
            'total_validations': self.stats['total_validations'],
            'passed': self.stats['passed'],
            'failed': self.stats['failed'],
            'warnings': self.stats['warnings']
        }

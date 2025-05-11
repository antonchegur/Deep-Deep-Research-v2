"""
Template Management Service Module

This module provides a TemplateManager for loading and processing
language-specific report templates.
"""

import os
from typing import Dict, Any, Optional

from src.multilingual.config import Language, MultilingualConfig, DEFAULT_CONFIG
from src.multilingual.exceptions import FormattingError
from src.multilingual import get_current_language
from src.error_handling import error_manager, ResearchError, ErrorSeverity

# Define the base path for templates relative to this file or a known project root
# This might need adjustment based on your project structure
TEMPLATE_BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates') 


class TemplateManager:
    """
    Manages loading and rendering of language-specific templates.
    
    Currently supports simple text file templates with basic placeholder replacement.
    Can be extended to use a more sophisticated templating engine like Jinja2.
    """
    
    def __init__(self, config: Optional[MultilingualConfig] = None, template_dir: Optional[str] = None):
        self.config = config or DEFAULT_CONFIG
        self.template_base_path = os.path.abspath(template_dir or TEMPLATE_BASE_DIR)
        self.name = "TemplateManager"
        
        if not os.path.isdir(self.template_base_path):
            init_error = ResearchError(f"Template base directory not found: {self.template_base_path}", \
                                       error_severity=ErrorSeverity.MEDIUM, component=self.name)
            error_manager.handle_error(init_error)
            # You might want to raise an error here or handle it gracefully

    def _get_template_path(self, template_name: str, language: Language) -> Optional[str]:
        """Construct the path to a language-specific template file."""
        lang_code = language.value
        # e.g., templates/en/report_header.txt
        path = os.path.join(self.template_base_path, lang_code, template_name)
        if os.path.exists(path):
            return path
        
        # Fallback to default language if specific language template not found
        if language != self.config.default_language:
            fallback_info = ResearchError(f"Template '{template_name}' not found for '{lang_code}'. Trying default '{self.config.default_language.value}'.", \
                                          error_severity=ErrorSeverity.LOW, component=self.name)
            error_manager.handle_error(fallback_info)
            default_lang_code = self.config.default_language.value
            path = os.path.join(self.template_base_path, default_lang_code, template_name)
            if os.path.exists(path):
                return path
        
        return None

    def load_template(self, template_name: str, language: Optional[Language] = None) -> Optional[str]:
        """
        Load the content of a language-specific template.
        
        Args:
            template_name: The name of the template file (e.g., 'report_header.txt').
            language: The language for the template. If None, uses current language.
            
        Returns:
            The template content as a string, or None if not found.
        """
        language = language or get_current_language()
        template_path = self._get_template_path(template_name, language)
        
        if template_path:
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                load_err = FormattingError(f"Error loading template {template_path}: {e}", language.value, \
                                           error_code="TemplateLoadError", component=self.name)
                error_manager.handle_error(load_err)
                return None
        else:
            not_found_err = ResearchError(f"Template '{template_name}' not found for '{language.value}' or default.", \
                                          error_severity=ErrorSeverity.MEDIUM, component=self.name)
            error_manager.handle_error(not_found_err)
            return None

    def render_template(self, 
                        template_name: str, 
                        context: Dict[str, Any], 
                        language: Optional[Language] = None) -> str:
        """
        Load a template and render it with the given context.
        Uses simple string.format() for now. Extend for Jinja2 or other engines.
        
        Args:
            template_name: The name of the template file.
            context: A dictionary of context variables for rendering.
            language: The language for the template. If None, uses current language.
            
        Returns:
            The rendered template as a string.
            
        Raises:
            FormattingError: If template loading or rendering fails.
        """
        current_render_lang = language or get_current_language()
        template_content = self.load_template(template_name, current_render_lang)
        
        if template_content is None:
            raise FormattingError(f"Could not load template '{template_name}' for rendering.", 
                                  current_render_lang.value, component=self.name)
        
        try:
            rendered_content = template_content
            for key, value in context.items():
                placeholder = "{" + str(key) + "}"
                rendered_content = rendered_content.replace(placeholder, str(value))
            return rendered_content
            
        except KeyError as e:
            missing_key = str(e)
            err_msg = f"Missing key '{missing_key}' in context for template '{template_name}'"
            render_key_err = FormattingError(err_msg, current_render_lang.value, \
                                            error_code="TemplateRenderKeyError", component=self.name)
            error_manager.handle_error(render_key_err)
            
            safe_context = {str(k): v for k,v in context.items()}
            try:
                return template_content.format_map(safe_context)
            except KeyError as ke:
                err_msg_fm = f"Missing key '{str(ke)}' in context for template '{template_name}' using format_map."
                render_key_err_fm = FormattingError(err_msg_fm, current_render_lang.value, \
                                                   error_code="TemplateRenderKeyErrorFormatMap", component=self.name)
                error_manager.handle_error(render_key_err_fm)
                return f"<!-- Template Error: {err_msg_fm} -->\n{template_content}"

        except Exception as e:
            render_err = FormattingError(f"Error rendering template '{template_name}': {str(e)}", 
                                         current_render_lang.value, component=self.name)
            error_manager.handle_error(render_err)
            raise render_err 
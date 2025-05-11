"""
Prompt engineering framework for research synthesis.

This module provides a structured approach for crafting effective prompts
for GPT-4 Turbo and other LLMs to optimize research synthesis quality.
"""

import json
import logging
import os
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from ..adapters import SourceResult, SourceType
from .base import SynthesisType


logger = logging.getLogger(__name__)


class PromptTemplate:
    """
    A structured template for generating prompts with versioning.
    
    PromptTemplate manages the structure, parameters, and versioning
    of prompts for different research synthesis tasks.
    """
    
    def __init__(self, 
                template_id: str,
                system_template: str,
                user_template: str,
                version: str = "1.0.0",
                description: str = "",
                parameters: Optional[Dict[str, str]] = None,
                metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a prompt template.
        
        Args:
            template_id: Unique identifier for the template
            system_template: System message template with placeholders
            user_template: User message template with placeholders
            version: Semantic version of the template
            description: Description of the template's purpose
            parameters: Description of parameters used in the template
            metadata: Additional metadata for the template
        """
        self.template_id = template_id
        self.system_template = system_template
        self.user_template = user_template
        self.version = version
        self.description = description
        self.parameters = parameters or {}
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()
        
        # Validate template structure
        self._validate_templates()
    
    def _validate_templates(self):
        """Validate template structure and placeholders."""
        # Check if templates are not empty
        if not self.system_template or not self.user_template:
            raise ValueError("System and user templates cannot be empty")
        
        # Extract placeholders from templates
        system_placeholders = set(re.findall(r'\{\{([\w_]+)\}\}', self.system_template))
        user_placeholders = set(re.findall(r'\{\{([\w_]+)\}\}', self.user_template))
        all_placeholders = system_placeholders.union(user_placeholders)
        
        # Check if all placeholders have parameter descriptions
        for placeholder in all_placeholders:
            if placeholder not in self.parameters:
                logger.warning(f"Missing parameter description for placeholder: {placeholder}")
    
    def format(self, **kwargs) -> Dict[str, str]:
        """
        Format the template with provided parameters.
        
        Args:
            **kwargs: Key-value pairs for template placeholders
            
        Returns:
            Dictionary with formatted system and user prompts
            
        Raises:
            ValueError: If required parameters are missing
        """
        # Check for missing required parameters
        system_placeholders = set(re.findall(r'\{\{([\w_]+)\}\}', self.system_template))
        user_placeholders = set(re.findall(r'\{\{([\w_]+)\}\}', self.user_template))
        all_placeholders = system_placeholders.union(user_placeholders)
        
        missing = all_placeholders - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")
        
        # Format templates
        system_prompt = self.system_template
        user_prompt = self.user_template
        
        for key, value in kwargs.items():
            placeholder = f"{{{{{key}}}}}"
            system_prompt = system_prompt.replace(placeholder, str(value))
            user_prompt = user_prompt.replace(placeholder, str(value))
        
        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary for serialization."""
        return {
            "template_id": self.template_id,
            "system_template": self.system_template,
            "user_template": self.user_template,
            "version": self.version,
            "description": self.description,
            "parameters": self.parameters,
            "metadata": self.metadata,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptTemplate':
        """Create template from dictionary representation."""
        return cls(
            template_id=data["template_id"],
            system_template=data["system_template"],
            user_template=data["user_template"],
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            parameters=data.get("parameters", {}),
            metadata=data.get("metadata", {})
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'PromptTemplate':
        """Create template from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


class PromptLibrary:
    """
    Library of prompt templates for research synthesis.
    
    Manages a collection of prompt templates, providing versioning,
    loading/saving, and selection capabilities.
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize the prompt library.
        
        Args:
            templates_dir: Directory containing template JSON files
        """
        self.templates: Dict[str, List[PromptTemplate]] = {}
        self.templates_dir = templates_dir
        
        if templates_dir:
            self.load_templates(templates_dir)
        else:
            self._load_default_templates()
    
    def _load_default_templates(self):
        """Load built-in default templates."""
        # Add default research synthesis templates
        for synthesis_type in SynthesisType:
            if synthesis_type == SynthesisType.CUSTOM:
                continue
                
            template_id = f"research_{synthesis_type.value}"
            system_template = self._get_default_system_template(synthesis_type)
            user_template = self._get_default_user_template()
            
            template = PromptTemplate(
                template_id=template_id,
                system_template=system_template,
                user_template=user_template,
                description=f"Default template for {synthesis_type.value} research synthesis",
                parameters={
                    "query": "Research query or topic",
                    "sources": "Formatted source data",
                    "language": "Target language for the response"
                }
            )
            
            self.add_template(template)
    
    def _get_default_system_template(self, synthesis_type: SynthesisType) -> str:
        """Get default system template for synthesis type."""
        # These templates match those in GPT4Synthesizer.SYNTHESIS_PROMPTS
        if synthesis_type == SynthesisType.SUMMARY:
            return """
            You are a research assistant tasked with creating concise summaries of complex topics.
            Your task is to synthesize the information from multiple sources into a clear, brief summary.
            Focus on the most important points, main concepts, and key findings.
            Include:
            - A concise overview of the topic
            - Key facts and data points
            - Main consensus points from the sources
            Keep your response straightforward and focused on the essential information.
            
            Topic: {{query}}
            Target language: {{language}}
            """
            
        elif synthesis_type == SynthesisType.COMPREHENSIVE:
            return """
            You are an expert research analyst tasked with creating comprehensive analyses of complex topics.
            Your task is to synthesize information from multiple sources into a detailed, thorough analysis.
            Include:
            - A structured overview of the topic with clear sections
            - In-depth examination of key aspects, arguments, and evidence
            - Comparative analysis of different perspectives and methodologies
            - Critical evaluation of the quality and reliability of sources
            - Identification of knowledge gaps or areas for further research
            - Specific citations to sources when presenting important information
            Organize your response with clear headings and a logical flow that helps the reader
            understand the full scope and complexity of the topic.
            
            Topic: {{query}}
            Target language: {{language}}
            """
            
        elif synthesis_type == SynthesisType.COMPARISON:
            return """
            You are a research analyst specializing in comparative analysis.
            Your task is to identify and analyze similarities and differences across multiple sources.
            Focus on:
            - Explicitly comparing different perspectives, methodologies, or findings
            - Highlighting points of consensus and disagreement
            - Analyzing why differences exist (methodological differences, data sources, perspectives, etc.)
            - Evaluating the strengths and weaknesses of different approaches
            - Presenting information in clear comparative frameworks (tables/structured format when appropriate)
            Your analysis should help the reader understand the range of viewpoints and evidence
            available on the topic, without unduly favoring any particular perspective.
            
            Topic: {{query}}
            Target language: {{language}}
            """
            
        elif synthesis_type == SynthesisType.FACT_CHECK:
            return """
            You are a fact-checking specialist assessing the accuracy of information.
            Your task is to evaluate claims against the available evidence from multiple sources.
            For each major claim or assertion, provide:
            - A clear statement of the claim
            - The evidence supporting or contradicting the claim
            - An assessment of reliability of the sources providing evidence
            - A verdict on the claim (Verified, Partly Verified, Unverified, Refuted, or Insufficient Evidence)
            - Explanation of any context or nuance important for understanding the claim's accuracy
            Be precise in distinguishing between verified facts, consensus views, competing claims,
            and areas where evidence is insufficient. Remain neutral and focus solely on the evidence.
            
            Topic: {{query}}
            Target language: {{language}}
            """
            
        elif synthesis_type == SynthesisType.CRITIQUE:
            return """
            You are a critical analyst providing an evaluative assessment of a topic.
            Your task is to critically analyze the information from multiple sources,
            evaluating strengths, weaknesses, gaps, and implications.
            Include:
            - Critical assessment of methodologies, evidence, and arguments presented
            - Identification of biases, limitations, or flaws in the research
            - Evaluation of the strength and quality of evidence
            - Analysis of unstated assumptions or implications
            - Suggestions for how research or understanding could be improved
            Your critique should be constructive and fair, acknowledging strengths
            while also highlighting areas for improvement or further consideration.
            
            Topic: {{query}}
            Target language: {{language}}
            """
            
        elif synthesis_type == SynthesisType.LATEST_RESEARCH:
            return """
            You are a research specialist focusing on the most recent developments on a topic.
            Your task is to prioritize and synthesize the newest research and findings.
            Focus on:
            - Highlighting the most recent studies, discoveries, or developments
            - Explaining how new findings build on, confirm, or challenge previous understanding
            - Identifying emerging trends, methods, or shifts in the field
            - Noting any paradigm shifts or significant breakthroughs
            - Discussing the implications of recent developments for future research or applications
            Give special attention to publication dates and recency of sources, prioritizing
            the newest reliable information while placing it in context of the broader field.
            
            Topic: {{query}}
            Target language: {{language}}
            """
            
        elif synthesis_type == SynthesisType.HISTORICAL:
            return """
            You are a historical research specialist analyzing how a topic has developed over time.
            Your task is to trace and analyze the historical evolution of ideas, findings, or practices.
            Include:
            - A chronological narrative of how understanding or approaches have developed
            - Key turning points, breakthroughs, or paradigm shifts
            - How earlier ideas influenced later developments
            - Changing methodologies or frameworks over time
            - Historical context that shaped the evolution of the field
            Present your analysis as a coherent historical narrative that helps the reader
            understand not just what is known, but how that knowledge developed over time.
            
            Topic: {{query}}
            Target language: {{language}}
            """
            
        # Default generic template
        return """
        You are a research assistant tasked with analyzing information from multiple sources.
        Please synthesize this information into a coherent response.
        
        Topic: {{query}}
        Target language: {{language}}
        """
    
    def _get_default_user_template(self) -> str:
        """Get default user template for source data."""
        return """
        Research Query: {{query}}
        
        Sources:
        {{sources}}
        
        Please synthesize the information from these sources to address the research query.
        Use {{language}} language for your response.
        """
    
    def load_templates(self, directory: str):
        """
        Load templates from JSON files in a directory.
        
        Args:
            directory: Path to directory containing template JSON files
        """
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            logger.warning(f"Templates directory not found: {directory}")
            return
        
        # Load each JSON file in the directory
        for file_path in dir_path.glob('*.json'):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                    # Support both single template and template collection
                    if isinstance(data, dict) and "template_id" in data:
                        # Single template
                        template = PromptTemplate.from_dict(data)
                        self.add_template(template)
                    elif isinstance(data, list):
                        # List of templates
                        for template_data in data:
                            template = PromptTemplate.from_dict(template_data)
                            self.add_template(template)
                    else:
                        logger.warning(f"Invalid template format in {file_path}")
                
            except Exception as e:
                logger.error(f"Error loading template from {file_path}: {e}")
    
    def save_templates(self, directory: Optional[str] = None):
        """
        Save all templates to JSON files.
        
        Args:
            directory: Directory to save templates (defaults to self.templates_dir)
        """
        save_dir = Path(directory or self.templates_dir)
        if not save_dir.exists():
            save_dir.mkdir(parents=True)
        
        # Save each template category to a separate file
        for template_id, versions in self.templates.items():
            file_path = save_dir / f"{template_id}.json"
            
            try:
                templates_data = [t.to_dict() for t in versions]
                with open(file_path, 'w') as f:
                    json.dump(templates_data, f, indent=2)
                
            except Exception as e:
                logger.error(f"Error saving templates to {file_path}: {e}")
    
    def add_template(self, template: PromptTemplate):
        """
        Add a template to the library.
        
        Args:
            template: Prompt template to add
        """
        if template.template_id not in self.templates:
            self.templates[template.template_id] = []
            
        # Add as a new version
        self.templates[template.template_id].append(template)
        
        # Sort versions by semantic version
        self.templates[template.template_id].sort(
            key=lambda t: [int(x) for x in t.version.split('.')],
            reverse=True
        )
    
    def get_template(self, template_id: str, version: Optional[str] = None) -> Optional[PromptTemplate]:
        """
        Get a template by ID and optional version.
        
        Args:
            template_id: Template identifier
            version: Specific version to retrieve (defaults to latest)
            
        Returns:
            Prompt template or None if not found
        """
        if template_id not in self.templates or not self.templates[template_id]:
            return None
            
        if version:
            # Find specific version
            for template in self.templates[template_id]:
                if template.version == version:
                    return template
            return None
        else:
            # Return latest version (first in list due to sorting)
            return self.templates[template_id][0]
    
    def get_template_for_synthesis(self, synthesis_type: SynthesisType) -> Optional[PromptTemplate]:
        """
        Get the appropriate template for a synthesis type.
        
        Args:
            synthesis_type: Type of synthesis to perform
            
        Returns:
            Prompt template or None if not found
        """
        if synthesis_type == SynthesisType.CUSTOM:
            return None
            
        template_id = f"research_{synthesis_type.value}"
        return self.get_template(template_id)
    
    def format_sources(self, source_results: List[SourceResult]) -> str:
        """
        Format source results for inclusion in prompts.
        
        Args:
            source_results: List of source results to format
            
        Returns:
            Formatted source data as string
        """
        if not source_results:
            return "No sources provided."
            
        formatted_sources = []
        
        for i, source in enumerate(source_results, 1):
            source_text = f"SOURCE {i}: {source.title}\n"
            source_text += f"Source Type: {source.source_type.value}\n"
            source_text += f"Source: {source.source_name}\n"
            
            if source.url:
                source_text += f"URL: {source.url}\n"
                
            # Add metadata if relevant
            if source.metadata:
                relevant_metadata = []
                
                # Only include relevant metadata
                if "year" in source.metadata:
                    relevant_metadata.append(f"Year: {source.metadata['year']}")
                if "authors" in source.metadata:
                    authors = source.metadata["authors"]
                    relevant_metadata.append(f"Authors: {authors if isinstance(authors, str) else ', '.join(authors)}")
                if "publisher" in source.metadata:
                    relevant_metadata.append(f"Publisher: {source.metadata['publisher']}")
                    
                if relevant_metadata:
                    source_text += "Metadata: " + "; ".join(relevant_metadata) + "\n"
            
            # Add content with clear separation
            source_text += "Content:\n"
            
            # Truncate extremely long content for token efficiency
            content = source.content
            if len(content) > 8000:
                content = content[:8000] + "... [content truncated due to length]"
                
            source_text += content + "\n"
            
            # Add separator between sources
            formatted_sources.append(source_text)
            
        return "\n" + "-" * 40 + "\n".join(formatted_sources)
    
    def create_prompt(self, 
                     query: str,
                     source_results: List[SourceResult],
                     synthesis_type: SynthesisType = SynthesisType.COMPREHENSIVE,
                     language: str = "en",
                     custom_system_prompt: Optional[str] = None) -> Dict[str, str]:
        """
        Create formatted prompts for research synthesis.
        
        Args:
            query: Research query or topic
            source_results: List of source results to analyze
            synthesis_type: Type of synthesis to perform
            language: Target language code
            custom_system_prompt: Optional custom system prompt
            
        Returns:
            Dictionary with system_prompt and user_prompt
            
        Raises:
            ValueError: If template not found and no custom prompt provided
        """
        if synthesis_type == SynthesisType.CUSTOM:
            if not custom_system_prompt:
                raise ValueError("Custom system prompt is required for CUSTOM synthesis type")
                
            # For custom prompts, use default user template
            user_template = self._get_default_user_template()
            
            # Format user prompt
            formatted_sources = self.format_sources(source_results)
            user_prompt = user_template.replace("{{query}}", query)
            user_prompt = user_prompt.replace("{{sources}}", formatted_sources)
            user_prompt = user_prompt.replace("{{language}}", language)
            
            return {
                "system_prompt": custom_system_prompt,
                "user_prompt": user_prompt
            }
        
        # For standard synthesis types, use templates
        template = self.get_template_for_synthesis(synthesis_type)
        if not template:
            raise ValueError(f"No template found for synthesis type: {synthesis_type.value}")
            
        # Format source data
        formatted_sources = self.format_sources(source_results)
        
        # Format template
        return template.format(
            query=query,
            sources=formatted_sources,
            language=language
        )


class PromptEvaluator:
    """
    Evaluates and compares prompt effectiveness.
    
    Provides metrics and benchmarking for different prompt templates.
    """
    
    def __init__(self):
        """Initialize prompt evaluator."""
        self.results: List[Dict[str, Any]] = []
    
    def log_result(self, 
                  template_id: str,
                  version: str,
                  synthesis_type: SynthesisType,
                  metrics: Dict[str, Any],
                  query: str,
                  metadata: Optional[Dict[str, Any]] = None):
        """
        Log evaluation results for a prompt.
        
        Args:
            template_id: Template identifier
            version: Template version
            synthesis_type: Type of synthesis performed
            metrics: Metrics measuring effectiveness
            query: The research query used
            metadata: Additional metadata about the evaluation
        """
        result = {
            "template_id": template_id,
            "version": version,
            "synthesis_type": synthesis_type.value,
            "metrics": metrics,
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.results.append(result)
    
    def get_results(self, 
                   template_id: Optional[str] = None,
                   synthesis_type: Optional[SynthesisType] = None) -> List[Dict[str, Any]]:
        """
        Get filtered evaluation results.
        
        Args:
            template_id: Filter by template ID
            synthesis_type: Filter by synthesis type
            
        Returns:
            List of matching evaluation results
        """
        filtered = self.results
        
        if template_id:
            filtered = [r for r in filtered if r["template_id"] == template_id]
            
        if synthesis_type:
            filtered = [r for r in filtered if r["synthesis_type"] == synthesis_type.value]
            
        return filtered
    
    def save_results(self, file_path: str):
        """
        Save evaluation results to a JSON file.
        
        Args:
            file_path: Path to save results file
        """
        try:
            with open(file_path, 'w') as f:
                json.dump(self.results, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving evaluation results: {e}")
    
    def load_results(self, file_path: str):
        """
        Load evaluation results from a JSON file.
        
        Args:
            file_path: Path to results file
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                self.results = data
        except Exception as e:
            logger.error(f"Error loading evaluation results: {e}")
    
    def compare_prompts(self, template_ids: List[str]) -> Dict[str, Any]:
        """
        Compare effectiveness of different prompt templates.
        
        Args:
            template_ids: List of template IDs to compare
            
        Returns:
            Comparison metrics
        """
        comparison = {}
        
        for template_id in template_ids:
            results = self.get_results(template_id=template_id)
            
            if not results:
                comparison[template_id] = {"error": "No evaluation data found"}
                continue
                
            # Calculate average metrics
            avg_metrics = {}
            for metric_key in results[0]["metrics"].keys():
                values = [r["metrics"][metric_key] for r in results if metric_key in r["metrics"]]
                if values and all(isinstance(v, (int, float)) for v in values):
                    avg_metrics[metric_key] = sum(values) / len(values)
            
            # Count synthesis types
            synthesis_counts = {}
            for r in results:
                synthesis_type = r["synthesis_type"]
                synthesis_counts[synthesis_type] = synthesis_counts.get(synthesis_type, 0) + 1
            
            comparison[template_id] = {
                "average_metrics": avg_metrics,
                "synthesis_counts": synthesis_counts,
                "total_evaluations": len(results)
            }
        
        return comparison 
#!/usr/bin/env python3
"""
Content Organization System Demonstration

This script demonstrates how to use the Content Organization System to
structure research content, generate executive summaries, and create
tables of contents for research reports.
"""

import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.research.content_organizer import (
    ContentOrganizer,
    ContentAnalyzer,
    ExecutiveSummarizer,
    TableOfContentsGenerator
)
from src.research.synthesizer import (
    SynthesisResult,
    SynthesisType,
    GPT4Synthesizer
)
from src.research.adapters import SourceResult, SourceType


async def demo_with_mock_synthesis_result():
    """Demonstrate the content organization system with a mock synthesis result."""
    print("\n=== Content Organization Demo with Mock Data ===\n")
    
    # Create a mock synthesis result
    mock_result = create_mock_synthesis_result()
    
    # Initialize the content organizer
    organizer = ContentOrganizer(max_summary_length=300, toc_max_depth=3)
    
    # Organize the content
    print("Organizing content...")
    organized_content = organizer.organize_content(mock_result, output_format='markdown')
    
    # Create an output directory for the demo results
    os.makedirs("docs/examples", exist_ok=True)
    
    # Save the organized content to a markdown file
    output_path = "docs/examples/organized_content_demo.md"
    with open(output_path, 'w') as f:
        f.write(organized_content.formatted_content)
    
    print(f"Organized content saved to {output_path}")
    print("\nTitle:", organized_content.title)
    print("\nExecutive Summary:", organized_content.executive_summary[:100] + "...")
    print("\nTable of Contents:", organized_content.table_of_contents)


async def demo_with_real_synthesis():
    """Demonstrate the content organization system with a real GPT-4 synthesis."""
    print("\n=== Content Organization Demo with Real Synthesis ===\n")
    
    # Check if API key is available
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Skipping real synthesis demo because OPENAI_API_KEY is not set.")
        return
    
    print("Initializing GPT-4 synthesizer...")
    synthesizer = GPT4Synthesizer(api_key=api_key)
    
    # Create sample source results
    sources = [
        SourceResult(
            title="The Evolution of AI in Healthcare",
            content="""
            Artificial Intelligence (AI) is transforming healthcare across multiple domains.
            From diagnostic tools that can identify diseases from medical images with accuracy
            rivaling human experts, to predictive models that can forecast patient deterioration
            before clinical signs are obvious, AI applications are expanding rapidly.
            
            Deep learning models have demonstrated particular promise in radiology, pathology,
            and dermatology, where they can analyze images to detect patterns that may be difficult
            for the human eye to discern. Natural language processing is being applied to electronic
            health records to extract relevant information and support clinical decision-making.
            
            Despite these advances, significant challenges remain. These include ensuring the
            reliability and safety of AI systems, addressing potential biases in training data,
            integrating AI tools into existing clinical workflows, and ensuring that healthcare
            professionals maintain appropriate oversight of AI-assisted decisions.
            """,
            source_name="Medical AI Journal",
            source_type=SourceType.ACADEMIC,
            url="https://example.com/medical-ai-journal/2023/evolution",
            section_headers=["Introduction", "Applications", "Challenges"],
            metadata={"year": 2023, "peer_reviewed": True}
        ),
        SourceResult(
            title="Ethical Considerations in Healthcare AI",
            content="""
            The rapid adoption of artificial intelligence in healthcare raises important ethical
            questions that must be addressed to ensure that these technologies benefit patients
            while respecting fundamental ethical principles.
            
            Patient autonomy may be affected if AI systems make recommendations that influence
            treatment decisions without patients understanding the basis for these recommendations.
            Informed consent processes may need to be updated to include information about how AI
            contributes to diagnoses or treatment plans.
            
            Privacy concerns are paramount, as AI systems require access to vast amounts of sensitive
            health data. Robust data governance frameworks are essential to prevent misuse of this
            information and to ensure that patients understand how their data is being used.
            
            Questions of equity arise when considering potential biases in AI systems. If training data
            does not adequately represent diverse populations, AI tools may perform less effectively
            for underrepresented groups, potentially exacerbating existing healthcare disparities.
            
            Transparency and explainability are critical for building trust in AI healthcare applications.
            Healthcare professionals and patients should be able to understand, at an appropriate level,
            how AI systems reach their conclusions and what limitations they may have.
            """,
            source_name="Bioethics Today",
            source_type=SourceType.ACADEMIC,
            url="https://example.com/bioethics-today/ethical-ai",
            section_headers=["Autonomy", "Privacy", "Equity", "Transparency"],
            metadata={"year": 2022, "peer_reviewed": True}
        ),
        SourceResult(
            title="AI in Clinical Practice: A Survey of Current Applications",
            content="""
            This survey examines how artificial intelligence is currently being used in clinical settings
            and identifies trends in adoption across different medical specialties.
            
            Radiology leads in AI adoption, with numerous FDA-approved algorithms for detecting conditions
            ranging from fractures to tumors. These tools are increasingly integrated into picture archiving
            and communication systems (PACS) used by radiologists.
            
            In cardiology, AI algorithms analyze ECG data to identify arrhythmias and predict cardiac events.
            Some smart watches and consumer devices now include AI-powered ECG features that can alert users
            to potential heart rhythm abnormalities.
            
            Oncology has seen AI applications in treatment planning, where algorithms can analyze genomic data
            to recommend personalized therapy options. AI tools also help optimize radiation therapy to maximize
            tumor targeting while minimizing damage to surrounding healthy tissue.
            
            Primary care is beginning to adopt AI for risk stratification, helping physicians identify patients
            who may benefit from additional screening or preventive interventions. Virtual nursing assistants
            powered by AI are being tested to support patient monitoring and basic care coordination.
            
            Emergency medicine departments are piloting AI systems that help triage patients and predict which
            individuals are at highest risk for rapid deterioration, allowing resources to be allocated more
            efficiently during high-volume periods.
            """,
            source_name="Journal of Medical Informatics",
            source_type=SourceType.ACADEMIC,
            url="https://example.com/jmi/ai-clinical-practice",
            section_headers=["Radiology", "Cardiology", "Oncology", "Primary Care", "Emergency Medicine"],
            metadata={"year": 2023, "peer_reviewed": True}
        )
    ]
    
    # Query for synthesis
    query = "What are the current applications and ethical considerations of AI in healthcare?"
    
    # Perform synthesis
    print(f"Synthesizing research on: {query}")
    print("This may take a minute or two...\n")
    
    synthesis_result = await synthesizer.synthesize(
        query=query,
        source_results=sources,
        synthesis_type=SynthesisType.COMPREHENSIVE
    )
    
    if not synthesis_result:
        print("Error: Synthesis failed. Please check API key and try again.")
        return
    
    print("Synthesis complete. Now organizing content...")
    
    # Initialize the content organizer
    organizer = ContentOrganizer(max_summary_length=300, toc_max_depth=3)
    
    # Organize the content
    organized_content = organizer.organize_content(synthesis_result, output_format='markdown')
    
    # Create an output directory for the demo results
    os.makedirs("docs/examples", exist_ok=True)
    
    # Save the organized content to a markdown file
    output_path = "docs/examples/ai_healthcare_research.md"
    with open(output_path, 'w') as f:
        f.write(organized_content.formatted_content)
    
    print(f"Organized content saved to {output_path}")
    print("\nTitle:", organized_content.title)
    print("\nExecutive Summary:", organized_content.executive_summary[:150] + "...")
    print("\nTable of Contents:\n", organized_content.table_of_contents)


def demo_content_from_plain_text():
    """Demonstrate organizing plain text content without synthesis."""
    print("\n=== Content Organization Demo with Plain Text ===\n")
    
    # Sample text content (from the Tesla vs Waymo example)
    title = "Autonomous Vehicle Leadership: Tesla vs. Waymo Analysis"
    content = """
    # Overview
    
    Tesla and Waymo represent two fundamentally different approaches to autonomous driving.
    Tesla relies primarily on vision-based systems with real-world training from its fleet of
    consumer vehicles, while Waymo uses a combination of lidar, radar, cameras, and HD maps
    with a focus on specific geo-fenced areas. This report analyzes both companies' strengths,
    weaknesses, current market position, and future prospects to determine which approach may
    ultimately prevail in the autonomous vehicle race.
    
    # Technology Approaches
    
    ## Tesla's Vision-Based System
    
    Tesla's approach relies heavily on vision-based neural networks trained on data
    collected from its consumer vehicle fleet, which includes over 2 million cars
    on the road. Tesla's "Autopilot" and "Full Self-Driving (FSD)" systems use 8
    cameras, ultrasonic sensors, and radar (though radar was removed in newer models).
    Tesla rejects lidar, with CEO Elon Musk calling it a "crutch" and emphasizing
    that humans drive using vision alone.
    
    ## Waymo's Sensor Fusion
    
    Waymo, a subsidiary of Alphabet (Google's parent company), uses a more sensor-rich
    approach with lidar, radar, cameras, and precise HD maps. Waymo's system creates
    a detailed 3D model of its surroundings and operates primarily within geo-fenced
    areas that have been extensively mapped. Their approach prioritizes safety and
    reliability in specific operational domains before expanding.
    
    # Current Deployment Status
    
    Tesla has deployed its FSD Beta software to hundreds of thousands of customers
    in North America, with plans for wider release. However, it remains a Level 2
    system requiring constant driver supervision. Tesla collects data from consumer
    vehicles to improve its neural networks, claiming a data advantage from its large
    fleet.
    
    Waymo operates a fully driverless (Level 4) commercial ride-hailing service called
    Waymo One in Phoenix, San Francisco, and is expanding to Los Angeles and Austin.
    These vehicles operate without safety drivers in specific areas. Waymo's approach
    focuses on perfecting driverless operation in limited domains before expanding.
    
    # Business Models
    
    Tesla integrates autonomous technology into consumer vehicles, generating revenue
    through software sales (FSD currently costs $8,000-12,000 per vehicle or $199/month
    subscription). Tesla has announced plans for a "robotaxi" network but hasn't
    launched it yet.
    
    Waymo focuses on ride-hailing services rather than consumer vehicle sales. Their
    business model depends on transportation as a service (TaaS), eliminating driver
    costs which represent about 80% of ride-hailing expenses. Waymo has partnerships
    with automakers like Jaguar Land Rover and Volvo to build vehicles specifically
    designed for autonomy.
    
    # Conclusion
    
    The competition between Tesla and Waymo represents a fascinating contrast in approaches to solving
    autonomous driving: Tesla's vision-based neural networks with fleet learning versus Waymo's
    sensor-fusion and mapping-based approach.
    
    In the short to medium term (3-5 years), Waymo appears better positioned for commercial success in
    limited domains. Their fully driverless ride-hailing service is already operational and generating
    revenue, with a clear business model and safety record. Waymo's focus on specific geo-fenced areas
    allows them to perfect operation in controlled environments.
    
    In the longer term (5-10+ years), Tesla's approach may offer more scaling potential if their
    vision-based AI can overcome current limitations. Tesla's integrated hardware-software business model
    and large fleet for data collection provide unique advantages for iterative improvement.
    """
    
    # Initialize the content organizer
    organizer = ContentOrganizer(max_summary_length=300, toc_max_depth=3)
    
    # Organize the plain text content
    print("Organizing plain text content...")
    organized_content = organizer.organize_from_text(title, content, output_format='markdown')
    
    # Create an output directory for the demo results
    os.makedirs("docs/examples", exist_ok=True)
    
    # Save the organized content to a markdown file
    output_path = "docs/examples/tesla_waymo_organized.md"
    with open(output_path, 'w') as f:
        f.write(organized_content.formatted_content)
    
    print(f"Organized content saved to {output_path}")
    print("\nTitle:", organized_content.title)
    print("\nExecutive Summary:", organized_content.executive_summary[:150] + "...")
    print("\nTable of Contents:", organized_content.table_of_contents)


def create_mock_synthesis_result() -> SynthesisResult:
    """Create a mock synthesis result for demonstration purposes."""
    return SynthesisResult(
        title="Artificial Intelligence Applications in Healthcare",
        content="""
        Artificial Intelligence (AI) is transforming healthcare through various applications
        that have the potential to improve patient outcomes, increase efficiency, and reduce
        costs. However, these advances come with significant ethical considerations that must
        be addressed.
        
        In clinical practice, AI is being used across multiple specialties. Radiology leads
        adoption with algorithms that can detect abnormalities in medical images, while
        cardiology uses AI to analyze ECG data and predict cardiac events. Oncology applications
        include treatment planning and precision medicine approaches based on genomic data.
        Primary care is beginning to use AI for risk stratification, and emergency departments
        are implementing AI-powered triage systems.
        
        Despite these promising applications, ethical concerns remain prominent. Patient autonomy
        may be compromised if AI systems influence treatment decisions without adequate transparency.
        Privacy is a major concern given the vast amounts of sensitive health data required to train
        AI systems. Equity issues arise from potential biases in training data that could lead to
        disparate performance across different populations. The "black box" nature of some AI
        algorithms raises questions about explainability and accountability.
        
        For AI to realize its full potential in healthcare, these ethical challenges must be
        addressed through thoughtful policy, robust governance frameworks, and continued dialogue
        between technologists, healthcare professionals, ethicists, and patients.
        """,
        synthesis_type=SynthesisType.COMPREHENSIVE,
        query="What are the current applications and ethical considerations of AI in healthcare?",
        sources_used=3,
        language="en",
        sections={
            "Clinical Applications": """
            AI is being applied across various medical specialties with promising results.
            
            Radiology leads adoption with numerous FDA-approved algorithms for detecting conditions
            ranging from fractures to tumors. These tools are increasingly integrated into standard
            imaging workflows used by radiologists.
            
            In cardiology, AI algorithms analyze ECG data to identify arrhythmias and predict cardiac
            events. Some consumer devices now include AI-powered ECG features that can alert users
            to potential heart rhythm abnormalities.
            
            Oncology uses AI for treatment planning, analyzing genomic data to recommend personalized
            therapy options. AI tools also help optimize radiation therapy to maximize tumor targeting
            while minimizing damage to surrounding healthy tissue.
            
            Primary care is adopting AI for risk stratification, helping physicians identify patients
            who may benefit from additional screening or preventive interventions. Virtual assistants
            powered by AI support patient monitoring and basic care coordination.
            
            Emergency medicine departments are using AI systems to help triage patients and predict
            deterioration risk, allowing more efficient resource allocation during high-volume periods.
            """,
            "Ethical Considerations": """
            The rapid adoption of AI in healthcare raises important ethical questions that must be
            addressed to ensure these technologies benefit patients while respecting fundamental
            ethical principles.
            
            Patient autonomy may be affected if AI systems make recommendations that influence
            treatment decisions without patients understanding the basis for these recommendations.
            Informed consent processes need to be updated to include information about how AI
            contributes to diagnoses or treatment plans.
            
            Privacy concerns are paramount, as AI systems require access to vast amounts of sensitive
            health data. Robust data governance frameworks are essential to prevent misuse of this
            information and to ensure patients understand how their data is being used.
            
            Questions of equity arise when considering potential biases in AI systems. If training data
            does not adequately represent diverse populations, AI tools may perform less effectively
            for underrepresented groups, potentially exacerbating existing healthcare disparities.
            
            Transparency and explainability are critical for building trust in AI healthcare applications.
            Healthcare professionals and patients should be able to understand, at an appropriate level,
            how AI systems reach their conclusions and what limitations they may have.
            """,
            "Implementation Challenges": """
            Despite the promise of AI in healthcare, significant implementation challenges remain.
            
            Integration with existing clinical workflows is essential for adoption but can be difficult
            to achieve. Systems that disrupt established processes or increase clinician workload are
            unlikely to succeed, regardless of their technical capabilities.
            
            Regulatory frameworks are still evolving to address the unique characteristics of AI-based
            medical systems. Traditional approval processes designed for static medical devices may not
            be appropriate for learning systems that continue to evolve after deployment.
            
            Technical infrastructure requirements for AI implementation can be substantial, including
            secure data storage, high-performance computing resources, and interoperability with
            existing electronic health record systems.
            
            Training and education for healthcare professionals is necessary to ensure they understand
            the capabilities and limitations of AI tools and can appropriately interpret and communicate
            AI-generated information to patients.
            """
        }
    )


if __name__ == "__main__":
    # Run the demonstration with mock data
    asyncio.run(demo_with_mock_synthesis_result())
    
    # Run the demonstration with plain text
    demo_content_from_plain_text()
    
    # Optionally run the demonstration with real synthesis if API key is available
    if os.environ.get("OPENAI_API_KEY"):
        asyncio.run(demo_with_real_synthesis())
    else:
        print("\nSkipping real synthesis demo because OPENAI_API_KEY is not set.")
        print("To run the full demo, set your OpenAI API key as an environment variable.") 
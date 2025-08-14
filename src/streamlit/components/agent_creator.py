"""
Unified Agent Creation Component
Consolidates agent creation functionality from ai_agent.py and document_generator.py
"""
import streamlit as st
import requests
from utils import get_available_models_cached
import os

FASTAPI_API = os.getenv("FASTAPI_URL", "http://localhost:9020")

def create_agent_form(template_category="general", key_prefix="", form_title="Create New Agent"):
    """
    Unified agent creation form that can be used across different components.
    
    Args:
        template_category: "general" or "rule_development" to determine which templates to show
        key_prefix: Prefix for form element keys to avoid conflicts
        form_title: Title to display for the form section
    
    Returns:
        dict: Agent creation result with success status and details
    """
    
    def pref(k): 
        return f"{key_prefix}_{k}" if key_prefix else k
    
    st.subheader(form_title)
    
    # Define template sets
    general_templates = {
        "Systems Engineering Agent": {
            "description": "Systems engineering specialist applying SEBoK principles to review and enhance requirement development processes",
            "system_prompt": """You are an experienced systems engineer with 15+ years of experience in complex system development across aerospace, defense, and technology sectors. Your expertise spans the full systems engineering lifecycle with deep knowledge of SEBoK principles. Your role is to:

1. **Requirements Analysis**: Evaluate requirements for completeness, consistency, clarity, and traceability
2. **SEBoK Application**: Apply Systems Engineering Body of Knowledge best practices and standards
3. **Stakeholder Assessment**: Analyze stakeholder needs translation into verifiable requirements
4. **Architecture Alignment**: Ensure requirements support system architecture and design decisions
5. **Verification Planning**: Assess testability and verification approaches for each requirement
6. **Risk Identification**: Identify requirement-related risks and mitigation strategies
7. **Process Improvement**: Recommend enhancements to requirement development processes

**SEBoK Framework Application:**
- Apply life cycle processes (ISO/IEC/IEEE 15288)
- Utilize requirements engineering best practices
- Ensure stakeholder needs are properly captured and managed
- Maintain traceability throughout system hierarchy
- Consider system context and boundary definitions
- Apply appropriate requirement attributes and characteristics

**Technical Approach:**
- Evaluate requirements against SMART criteria (Specific, Measurable, Achievable, Relevant, Time-bound)
- Assess requirement quality attributes (unambiguous, complete, consistent, testable)
- Review for proper categorization (functional, performance, interface, constraint)
- Analyze requirement dependencies and interactions
- Consider system integration and interface requirements

Provide structured analysis with actionable recommendations for requirement improvement and process enhancement.""",
            "user_prompt": """Please analyze the following content and provide systems engineering assessment:

{data_sample}

Provide analysis in this structured format:

## Systems Engineering Analysis

**Requirements Assessment:**
- Evaluate completeness and clarity
- Identify missing or ambiguous requirements
- Assess traceability and verification approaches

**SEBoK Compliance:**
- Review against systems engineering best practices
- Identify process improvements
- Recommend stakeholder management approaches

**Technical Recommendations:**
- Specific actionable improvements
- Risk mitigation strategies
- Process enhancement opportunities

Focus on practical, implementable recommendations that improve system development outcomes.""",
            "temperature": 0.2,
            "max_tokens": 1500,
            "recommended_model": "gpt-4"
        },
        
        "Legal Compliance Agent": {
            "description": "Legal expert specializing in regulatory compliance, contract analysis, and risk assessment",
            "system_prompt": """You are a senior legal expert with extensive experience in regulatory compliance, contract law, and legal risk assessment. Your expertise includes:

1. **Regulatory Analysis**: Identify applicable regulations and compliance requirements
2. **Contract Review**: Analyze contracts for risks, obligations, and compliance issues
3. **Risk Assessment**: Evaluate legal risks and provide mitigation strategies
4. **Compliance Monitoring**: Assess adherence to legal and regulatory standards
5. **Documentation Review**: Review legal documents for completeness and accuracy

**Legal Framework Application:**
- Apply relevant legal standards and regulations
- Identify potential legal exposures and risks
- Ensure compliance with applicable laws
- Review contractual obligations and requirements
- Assess liability and risk allocation

Provide clear, actionable legal guidance with specific references to applicable laws and regulations.""",
            "user_prompt": """Please analyze the following content for legal and compliance considerations:

{data_sample}

Provide analysis in this format:

## Legal Compliance Analysis

**Regulatory Requirements:**
- Applicable laws and regulations
- Compliance obligations
- Filing or notification requirements

**Risk Assessment:**
- Identified legal risks
- Potential liability exposure
- Mitigation strategies

**Recommendations:**
- Specific actions required
- Documentation needs
- Process improvements

Focus on practical compliance strategies and risk mitigation.""",
            "temperature": 0.1,
            "max_tokens": 1200,
            "recommended_model": "gpt-4"
        },
        
        "Technical Documentation Agent": {
            "description": "Technical writing specialist for creating comprehensive documentation, specifications, and procedures",
            "system_prompt": """You are an expert technical writer and documentation specialist with extensive experience in creating clear, comprehensive technical documentation. Your expertise includes:

1. **Documentation Standards**: Apply industry best practices for technical writing
2. **Content Organization**: Structure complex technical information logically
3. **Clarity and Precision**: Ensure technical accuracy and readability
4. **Audience Adaptation**: Tailor content for specific technical audiences
5. **Process Documentation**: Create detailed procedures and workflows

**Documentation Approach:**
- Use clear, concise language appropriate for technical audiences
- Organize information hierarchically with proper headings and structure
- Include specific details, measurements, and criteria
- Provide step-by-step procedures where applicable
- Reference relevant standards and specifications

Create documentation that is accurate, comprehensive, and immediately usable by technical teams.""",
            "user_prompt": """Please analyze and document the following technical content:

{data_sample}

Provide structured documentation in this format:

## Technical Documentation

**Overview:**
- Summary of key technical concepts
- Scope and applicability

**Detailed Specifications:**
- Technical requirements and parameters
- Performance criteria and measurements
- Referenced standards and specifications

**Procedures:**
- Step-by-step implementation guidance
- Prerequisites and dependencies
- Verification and testing procedures

**Documentation Notes:**
- Areas requiring additional clarification
- Cross-references to related documentation

Focus on creating immediately usable technical documentation.""",
            "temperature": 0.2,
            "max_tokens": 2000,
            "recommended_model": "gpt-4"
        }
    }
    
    rule_development_templates = {
        "Rule Extraction Agent": {
            "description": "Specialized agent for extracting detailed, testable rules and requirements from technical documents",
            "system_prompt": """You are a test planning expert specializing in extracting comprehensive, testable rules from technical documents.

Your expertise includes:
1. **Rule Identification**: Identify EVERY possible testable requirement which usually contains "shall", "must", "may", "will", "could" or "should"
2. **Detailed Analysis**: Extract rules that are extremely detailed, explicit, and step-by-step
3. **Measurable Criteria**: Include specific measurements, acceptable ranges, and referenced figures/tables
4. **Test Strategy**: For ambiguous requirements, describe specific test strategies
5. **Dependency Analysis**: Identify dependencies between rules and requirements
6. **Conflict Detection**: Detect and resolve conflicts between requirements

**Output Format Requirements:**
- Use markdown headings and bolded text for organization
- Use the provided template to structure the output
- Include all relevant details from the analysis

**Analysis Approach:**
- Extract both explicit and implicit requirements
- Consider edge cases and boundary conditions
- Identify verification and validation methods
- Note any assumptions or interpretations made
- Provide test-ready specifications

Focus on creating rules that are immediately testable and verifiable.""",
            "user_prompt": """Extract all testable rules and requirements from the following document:

{data_sample}

Provide comprehensive rule extraction in this format:

## Rule Extraction Analysis

**Explicit Requirements:**
- List all direct "shall", "must", "will" requirements
- Include specific measurements and criteria
- Note referenced figures/tables

**Implicit Requirements:**
- Identify implied requirements and constraints
- Extract performance expectations
- Note operational conditions

**Test Strategy:**
- Verification methods for each requirement
- Test procedures and acceptance criteria
- Equipment and setup requirements

**Dependencies and Conflicts:**
- Prerequisite requirements
- Potential conflicts between requirements
- Resolution recommendations

Focus on creating testable, verifiable requirements.""",
            "temperature": 0.3,
            "max_tokens": 3000,
            "recommended_model": "gpt-4"
        },
        
        "Test Plan Integration Agent": {
            "description": "Agent for creating comprehensive, integrated test plans from extracted rules and requirements",
            "system_prompt": """You are a test integration specialist focused on creating comprehensive, executable test plans from extracted requirements and rules.

Your responsibilities include:
1. **Test Integration**: Combine individual requirements into cohesive test procedures
2. **Sequence Optimization**: Organize tests in logical, efficient execution order
3. **Resource Planning**: Identify required equipment, personnel, and conditions
4. **Dependency Management**: Manage test dependencies and prerequisites
5. **Coverage Analysis**: Ensure complete requirement coverage
6. **Conflict Resolution**: Resolve conflicts between different test requirements

**Integration Approach:**
- Combine similar tests to reduce redundancy
- Optimize test sequence for efficiency
- Identify shared setup and resources
- Create comprehensive test matrices
- Develop integrated verification procedures

Create test plans that are executable, comprehensive, and efficient.""",
            "user_prompt": """Create an integrated test plan from the following rule analysis:

{data_sample}

Provide integration in this format:

**Integrated Test Plan:**
- Comprehensive test procedures combining related requirements
- Logical execution sequence
- Resource and setup requirements

**Test Dependencies:**
- List prerequisite tests and setup requirements
- Note any equipment or environmental conditions needed

**Conflict Resolution:**
- Address any conflicts between different rule sources
- Provide recommended resolution approaches

**Integrated Test Procedures:**
1. [Comprehensive, step-by-step test procedures]
2. [Merge similar steps, eliminate redundancy]
3. [Organize in logical execution order]
4. [Include setup, execution, and verification phases]

**Cross-References:**
- Map relationships between different test procedures
- Note shared requirements and common verification steps

Focus on creating a test plan that is logically organized, comprehensive, and efficient.""",
            "temperature": 0.3,
            "max_tokens": 3000,
            "recommended_model": "gpt-4"
        },
        
        "Document Section Analyzer": {
            "description": "Agent for analyzing document sections and preparing structured analysis",
            "system_prompt": """You are a technical document analysis expert specializing in structured content extraction and preparation.

Your capabilities include:
1. **Content Classification**: Identify types of content (requirements, procedures, specifications, etc.)
2. **Section Analysis**: Extract key topics, themes, and technical focus areas
3. **Structure Mapping**: Understand document hierarchy and relationships
4. **Content Preparation**: Prepare content for further analysis by other specialized agents
5. **Metadata Extraction**: Identify references, figures, tables, and cross-references

**Analysis Framework:**
- Identify the primary purpose and scope of each section
- Extract technical specifications and requirements
- Note procedural steps and methodologies
- Identify measurement criteria and acceptance standards
- Map relationships to other document sections
- Highlight areas needing further clarification

**Content Organization:**
- Categorize content by type (functional, performance, interface, etc.)
- Identify compliance requirements and standards references
- Extract numerical values, ranges, and specifications
- Note any conditional or situational requirements
- Highlight critical vs. optional requirements""",
            "user_prompt": """Analyze the following document section and provide structured analysis:

{data_sample}

Provide analysis in this format:

## Section Analysis: [Content-Based Title]

**Content Type:**
- Identify the primary type of content (requirements, procedures, specifications, etc.)

**Key Topics:**
- List main topics and technical focus areas
- Note any specialized terminology or concepts

**Technical Specifications:**
- Extract specific measurements, values, and criteria
- List any referenced standards or specifications

**Requirements Identified:**
- Functional requirements
- Performance requirements  
- Interface requirements
- Constraint requirements

**References and Dependencies:**
- Note any figures, tables, or cross-references mentioned
- Identify dependencies on other sections or documents

**Analysis Notes:**
- Areas requiring clarification
- Potential ambiguities or interpretation issues
- Recommendations for further analysis

This analysis will be used by specialized rule extraction agents.""",
            "temperature": 0.2,
            "max_tokens": 2000,
            "recommended_model": "gpt-4"
        }
    }
    
    # Select templates based on category
    templates = rule_development_templates if template_category == "rule_development" else general_templates
    
    # Template selection OUTSIDE the form to allow dynamic updates
    col1_pre, col2_pre = st.columns([2, 1])
    
    with col1_pre:
        selected_template = st.selectbox(
            "Choose Agent Template:",
            ["Custom"] + list(templates.keys()),
            key=pref("template_selector"),
            help="Select a template to auto-populate the form fields"
        )
    
    with col2_pre:
        if selected_template != "Custom":
            template_info = templates[selected_template]
            st.info(f"**{selected_template}**: {template_info['description']}")
    
    # Get template defaults based on selection
    if selected_template != "Custom":
        template = templates[selected_template]
        default_system_prompt = template["system_prompt"]
        default_user_prompt = template["user_prompt"]
        default_temp = template.get("temperature", 0.3)
        default_tokens = template.get("max_tokens", 2000)
        default_name = f"Custom {selected_template}"
        recommended_model = template.get("recommended_model", "gpt-4")
    else:
        default_system_prompt = ""
        default_user_prompt = ""
        default_temp = 0.3
        default_tokens = 2000
        default_name = ""
        recommended_model = "gpt-4"
    
    # Get available models
    available_models = get_available_models_cached()
    
    # Agent creation form
    with st.form(pref("create_agent_form"), clear_on_submit=False):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Basic agent information
            agent_name = st.text_input(
                "Agent Name",
                value=default_name,
                placeholder="e.g., Custom Standards Extractor",
                key=pref("agent_name")
            )
            
            # Validation for agent name
            if agent_name:
                if len(agent_name) < 3:
                    st.warning("Agent name should be at least 3 characters")
                elif len(agent_name) > 100:
                    st.warning("Agent name should be less than 100 characters")
                else:
                    st.success("Agent name looks good")
            
            # Model selection
            st.subheader("Model Selection")
            
            if available_models:
                agent_model_name = st.selectbox(
                    "Select Model", 
                    available_models,
                    key=pref("model_select")
                )
                
            else:
                st.error("No models available. Please check your model configuration.")
                agent_model_name = None
            
            # Advanced Configuration
            st.subheader("Configuration")
            
            temperature = st.slider(
                "Temperature", 
                0.0, 1.0, 
                default_temp, 
                0.1,
                key=pref("temperature"),
                help="Lower = more consistent, Higher = more creative"
            )
            
            # Temperature guidance based on model
            if agent_model_name and "gpt-4" in str(agent_model_name) and temperature > 0.7:
                st.info("GPT-4 works well with lower temperatures (0.2-0.5) for consistent results")
            elif agent_model_name and "gpt-3.5" in str(agent_model_name) and temperature < 0.3:
                st.info("GPT-3.5 may benefit from slightly higher temperatures (0.3-0.7) for creativity")
            
            max_tokens = st.number_input(
                "Max Tokens", 
                100, 4000, 
                default_tokens, 
                100,
                key=pref("max_tokens"),
                help="Maximum response length"
            )
        
        with col2:
            # System prompt
            system_prompt = st.text_area(
                "System Prompt (Define Agent's Role & Expertise)",
                value=default_system_prompt,
                height=300,
                key=pref("system_prompt"),
                help="Define the agent's role, expertise, analysis approach, and output format",
                placeholder="You are an expert specializing in..."
            )
            
            # Character count and validation for system prompt
            if system_prompt:
                char_count = len(system_prompt)
                if char_count < 100:
                    st.warning(f"System prompt is quite short ({char_count} chars). Consider adding more detail.")
                elif char_count > 3000:
                    st.warning(f"System prompt is very long ({char_count} chars). Consider condensing.")
                else:
                    st.success(f"System prompt length is good ({char_count} chars)")
            
            # User prompt template
            user_prompt_template = st.text_area(
                "User Prompt Template",
                value=default_user_prompt,
                height=200,
                key=pref("user_prompt"),
                help="Template for user queries. Must include {data_sample} placeholder for input content",
                placeholder="Analyze the following:\n\n{data_sample}\n\nProvide analysis..."
            )
            
            # Validation for user prompt template
            if user_prompt_template:
                if "{data_sample}" not in user_prompt_template:
                    st.error("User prompt template must contain {data_sample} placeholder")
                else:
                    st.success("User prompt template has required {data_sample} placeholder")
        
        # Validation summary
        col1_val, col2_val = st.columns(2)
        
        with col1_val:
            if agent_name and len(agent_name.strip()) >= 3:
                st.success("Agent name valid")
            else:
                st.error("Agent name too short")
        
        with col2_val:
            if "{data_sample}" in user_prompt_template:
                st.success("User prompt has {data_sample}")
            else:
                st.error("Missing {data_sample} placeholder")
        
        # Submit button
        submitted = st.form_submit_button(
            "Create Agent", 
            type="primary",
            use_container_width=True
        )
        
        if submitted:
            # Validation
            validation_errors = []
            
            if not agent_name or len(agent_name.strip()) < 3:
                validation_errors.append("Agent name must be at least 3 characters")
            
            if not agent_model_name:
                validation_errors.append("Please select a valid model")
            
            if not system_prompt or len(system_prompt.strip()) < 50:
                validation_errors.append("System prompt must be at least 50 characters")
            
            if not user_prompt_template or "{data_sample}" not in user_prompt_template:
                validation_errors.append("User prompt template must contain {data_sample} placeholder")
            
            if validation_errors:
                for error in validation_errors:
                    st.error(f"{error}")
                return {"success": False, "errors": validation_errors}
            
            # Create agent payload
            agent_payload = {
                "name": agent_name.strip(),
                "model_name": agent_model_name,
                "system_prompt": system_prompt.strip(),
                "user_prompt_template": user_prompt_template.strip(),
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Submit to API
            try:
                with st.spinner(f"Creating agent '{agent_name}'..."):
                    response = requests.post(f"{FASTAPI_API}/create-agent", json=agent_payload, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"Agent '{agent_name}' created successfully!")
                    
                    # Show success details
                    st.info(f"""
                    **Agent Created:**
                    - **ID**: {result.get('agent_id')}
                    - **Name**: {result.get('agent_name')}
                    - **Model**: {agent_model_name}
                    - **Temperature**: {temperature}
                    - **Max Tokens**: {max_tokens}
                    """)
                    
                    st.markdown("**Next Steps:**")
                    st.markdown("- Switch to 'AI Agent Simulation' mode to test your new agent")
                    st.markdown("- Use 'Manage Existing Agents' tab to edit or manage agents")
                    st.markdown("- Create additional specialized agents for different tasks")
                    
                    return {
                        "success": True, 
                        "agent_id": result.get('agent_id'),
                        "agent_name": result.get('agent_name'),
                        "message": result.get('message')
                    }
                else:
                    error_detail = response.json().get("detail", response.text) if response.headers.get("content-type") == "application/json" else response.text
                    
                    if "already exists" in error_detail.lower():
                        st.error(f"Agent name '{agent_name}' already exists. Please choose a different name.")
                    else:
                        st.error(f"Failed to create agent: {error_detail}")
                    
                    return {"success": False, "error": error_detail}
                    
            except requests.exceptions.Timeout:
                st.error("Request timed out. Please try again.")
                return {"success": False, "error": "Request timeout"}
            except Exception as e:
                st.error(f"Error creating agent: {str(e)}")
                return {"success": False, "error": str(e)}
    
    return {"success": False, "message": "Form not submitted"}
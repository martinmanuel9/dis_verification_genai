"""
Unified Agent Creation Component
Consolidates agent creation functionality from ai_agent.py and document_generator.py
"""
import streamlit as st
from config.settings import config
from lib.api.client import api_client

# Use centralized config for endpoints
AGENT_FASTAPI = config.endpoints.agent

def create_agent_form(template_category="general", key_prefix="", form_title="Create New Agent"):
    def pref(k): 
        return f"{key_prefix}_{k}" if key_prefix else k
    
    st.subheader(form_title)
    
    # Define template sets
    general_templates = {
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

        "Legal Research Agent": {
            "description": "Autonomous legal research specialist with access to multiple legal databases",
            "system_prompt": """You are an expert legal researcher with access to comprehensive legal databases including Harvard's Caselaw Access Project, CourtListener, Google Scholar, and Justia. Your specialties include:

1. **Case Law Research**: Find relevant legal precedents and court decisions
2. **Legal Analysis**: Analyze case law relevance and legal implications  
3. **Precedent Evaluation**: Assess binding vs. persuasive authority
4. **Jurisdictional Analysis**: Consider federal, state, and local jurisdiction impacts
5. **Legal Citation**: Provide proper legal citations and references
6. **Research Synthesis**: Combine findings from multiple sources into coherent analysis

**Research Methodology:**
- Search across multiple authoritative legal databases
- Evaluate case relevance and precedent value
- Consider jurisdictional applicability and binding authority
- Analyze legal trends and evolving interpretations
- Provide comprehensive legal research summaries

When conducting legal research, focus on finding the most relevant and authoritative sources for the given legal question.""",
            "user_prompt": """Conduct comprehensive legal research on the following query:

{data_sample}

Provide structured legal research analysis:

## Legal Research Analysis

**Research Summary:**
- Key legal questions identified
- Search strategy employed
- Database sources consulted

**Relevant Case Law:**
- Most relevant cases found
- Legal precedents and authority
- Jurisdictional considerations

**Legal Analysis:**
- Key legal principles identified
- Trends in legal interpretation
- Potential legal strategies

**Recommendations:**
- Most relevant authorities to cite
- Additional research needed
- Legal risk assessment

Focus on providing comprehensive, actionable legal research insights.""",
            "temperature": 0.2,
            "max_tokens": 2000,
            "recommended_model": "claude-3-5-sonnet-20241022",
            "default_legal_research": True
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
        default_legal_research = template.get("default_legal_research", False)
    else:
        default_system_prompt = ""
        default_user_prompt = ""
        default_temp = 0.3
        default_tokens = 2000
        default_name = ""
        recommended_model = "gpt-4"
        default_legal_research = False
    
    # Get available models from config
    available_models = config.get_available_models()
    
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
            
            # Agent Tools Configuration
            st.subheader("Agent Capabilities")
            
            st.markdown("**Legal Research Tools**")
            st.info("Select which legal databases this agent can access for research")
            
            # Individual legal database toggles (like in legal research component)
            col_legal1, col_legal2 = st.columns(2)
            
            with col_legal1:
                harvard_enabled = st.checkbox(
                    "Harvard Caselaw Access Project",
                    value=default_legal_research,
                    key=pref("harvard_legal"),
                    help="Enable access to Harvard's comprehensive caselaw database"
                )
                
                google_scholar_enabled = st.checkbox(
                    "Google Scholar",
                    value=False,
                    key=pref("google_scholar_legal"),
                    help="Enable access to Google Scholar legal database via SerpApi"
                )
            
            with col_legal2:
                courtlistener_enabled = st.checkbox(
                    "CourtListener",
                    value=default_legal_research,
                    key=pref("courtlistener_legal"),
                    help="Enable access to CourtListener federal and state case database"
                )
                
                justia_enabled = st.checkbox(
                    "Justia",
                    value=False,
                    key=pref("justia_legal"),
                    help="Enable access to Justia legal research database"
                )
            
            # Build legal sources list
            legal_sources = []
            selected_api_sources = []
            
            if harvard_enabled:
                legal_sources.append("Harvard Caselaw Access Project")
                selected_api_sources.append("caselaw")
            if courtlistener_enabled:
                legal_sources.append("CourtListener")
                selected_api_sources.append("courtlistener")
            if google_scholar_enabled:
                legal_sources.append("Google Scholar")
                selected_api_sources.append("serpapi")
            if justia_enabled:
                legal_sources.append("Justia")
                selected_api_sources.append("justia")
            
            legal_research_enabled = len(selected_api_sources) > 0
            
            # Default collection for storing results (always show if any legal research enabled)
            if legal_research_enabled:
                default_collection = st.text_input(
                    "Default RAG Collection",
                    value="agent_legal_research",
                    key=pref("legal_collection"),
                    help="Default ChromaDB collection where legal research results will be stored"
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
                help="Template for user queries. {data_sample} will be automatically appended where user input will be inserted",
                placeholder="Analyze the following content and provide detailed insights..."
            )
            
            # Show template info
            if user_prompt_template:
                char_count = len(user_prompt_template)
                if char_count < 20:
                    st.warning(f"User prompt is quite short ({char_count} chars)")
                else:
                    st.success(f"User prompt template ready ({char_count} chars)")
        
        # Validation summary
        col1_val, col2_val = st.columns(2)
        
        with col1_val:
            if agent_name and len(agent_name.strip()) >= 3:
                st.success("Agent name valid")
            else:
                st.error("Agent name too short")
        
        with col2_val:
            if user_prompt_template and len(user_prompt_template.strip()) > 10:
                st.success("User prompt template ready")
            else:
                st.error("User prompt template too short")
        
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
            
            if not user_prompt_template or len(user_prompt_template.strip()) < 10:
                validation_errors.append("User prompt template must be at least 10 characters")
            
            if validation_errors:
                for error in validation_errors:
                    st.error(f"{error}")
                return {"success": False, "errors": validation_errors}
            
            # Build tools configuration
            tools_enabled = {}
            
            if legal_research_enabled:
                tools_enabled["legal_research"] = {
                    "enabled": True,
                    "sources": selected_api_sources if 'selected_api_sources' in locals() else ["caselaw", "courtlistener"],
                    "default_collection": default_collection if 'default_collection' in locals() else "agent_legal_research"
                }
            
            # Automatically append {data_sample} to user prompt template if not present
            final_user_prompt = user_prompt_template.strip()
            if "{data_sample}" not in final_user_prompt:
                final_user_prompt += "\n\n{data_sample}"
            
            # Create agent payload
            agent_payload = {
                "name": agent_name.strip(),
                "model_name": agent_model_name,
                "system_prompt": system_prompt.strip(),
                "user_prompt_template": final_user_prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "tools_enabled": tools_enabled
            }
            
            # Submit to API
            try:
                with st.spinner(f"Creating agent '{agent_name}'..."):
                    result = api_client.post(f"{AGENT_FASTAPI}/create-agent", data=agent_payload, timeout=30)

                if result:
                    st.success(f"Agent '{agent_name}' created successfully!")
                    
                    # Show success details
                    tools_info = ""
                    if legal_research_enabled:
                        sources_list = ', '.join(legal_sources) if 'legal_sources' in locals() and legal_sources else "Default sources"
                        tools_info = f"\n    - **Legal Research**: Enabled ({sources_list})"
                    
                    st.info(f"""
                    **Agent Created:**
                    - **ID**: {result.get('agent_id')}
                    - **Name**: {result.get('agent_name')}
                    - **Model**: {agent_model_name}
                    - **Temperature**: {temperature}
                    - **Max Tokens**: {max_tokens}{tools_info}
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
                    st.error("Failed to create agent")
                    return {"success": False, "error": "Creation failed"}

            except Exception as e:
                error_msg = str(e)
                if "already exists" in error_msg.lower():
                    st.error(f"Agent name '{agent_name}' already exists. Please choose a different name.")
                elif "timeout" in error_msg.lower():
                    st.error("Request timed out. Please try again.")
                else:
                    st.error(f"Error creating agent: {error_msg}")
                return {"success": False, "error": error_msg}
    
    return {"success": False, "message": "Form not submitted"}
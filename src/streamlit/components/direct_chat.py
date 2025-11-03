import streamlit as st
from config.settings import config
from config.constants import MODEL_KEY_MAP as model_key_map, MODEL_DESCRIPTIONS as model_descriptions
from lib.api.client import api_client
from services.chromadb_service import chromadb_service
from services.chat_service import chat_service
from components.upload_documents import render_upload_component, browse_documents
from components.history import Chat_History

CHROMADB_API = config.endpoints.vectordb

@st.cache_data(show_spinner=False)
def fetch_collections():
    return chromadb_service.get_collections()

def Direct_Chat():
    if "collections" not in st.session_state:
        st.session_state.collections = fetch_collections()

    collections = st.session_state.collections
    chat_tab, eval_tab, doc_upload_tab = st.tabs([
        "Chat Interface", "Evaluate Document", "Upload Documents"
    ])

    with chat_tab:
        col1, col2 = st.columns([2, 1])
        with col1:
            mode = st.selectbox("Select AI Model:", list(model_key_map.keys()), key="chat_model")
            if model_key_map[mode] in model_descriptions:
                st.info(model_descriptions[model_key_map[mode]])

        use_rag = st.checkbox("Use RAG (Retrieval Augmented Generation)", key="chat_use_rag")
        collection_name = None
        if use_rag:
            if collections:
                collection_name = st.selectbox(
                    "Document Collection:", collections, key="chat_coll"
                )
            else:
                st.warning("No collections available. Upload docs first.")

        user_input = st.text_area(
            "Ask your question:", height=100,
            placeholder="e.g. Summarize the latest uploaded document"
        )

        if st.button("Get Analysis", type="primary", key="chat_button"):
            if not user_input:
                st.warning("Please enter a question.")
            elif use_rag and not collection_name:
                st.error("Please select a collection for RAG mode.")
            else:
                with st.spinner(f"{mode} is analyzing..."):
                    try:
                        response = chat_service.send_message(
                            query=user_input,
                            model=model_key_map[mode],
                            use_rag=use_rag,
                            collection_name=collection_name
                        )
                        st.success("Analysis Complete:")
                        st.markdown(response.response)
                        if response.response_time_ms:
                            st.caption(f"Response time: {response.response_time_ms/1000:.2f}s")
                    except Exception as e:
                        st.error(f"Request failed: {e}")

        Chat_History(key_prefix="chat_history")

    with eval_tab:
        st.header("Evaluate Document")
        use_rag_eval = st.checkbox(
            "Use RAG mode", value=True, key="eval_use_rag"
        )
        collections = st.session_state.collections
        if use_rag_eval:
            browse_documents(key_prefix="select_eval_browse")
            
            with st.container(border=True, key="eval_params_container"):
                st.subheader("Evaluation Parameters")
                
                coll_name = st.selectbox(
                    "Select Collection:", collections, key="eval_collection"
                )

                doc_id = ""
                if "documents" in st.session_state and st.session_state.documents:
                    doc_options = {}
                    for doc in st.session_state.documents:
                        if hasattr(doc, 'document_name'):
                            doc_name = doc.document_name
                            doc_id_val = doc.document_id
                        else:
                            doc_name = doc.get('document_name', 'Unknown')
                            doc_id_val = doc.get('id', doc.get('document_id', ''))
                        if doc_id_val:
                            display_name = f"{doc_name} (ID: {doc_id_val[:8]}...)"
                            doc_options[display_name] = doc_id_val
                    
                    if doc_options:
                        selected_display = st.selectbox(
                            "Select Document:",
                            options=list(doc_options.keys()),
                            key="eval_document_selector"
                        )
                        doc_id = doc_options[selected_display]
                        st.info(f"Selected Document ID: {doc_id}")
                    else:
                        st.warning("No documents found. Please load documents first.")
                else:
                    st.info("Please load documents first.")

                manual_doc_id = st.text_input(
                    "Or enter Document ID manually:",
                    placeholder="e.g. 12345abcde",
                    key="manual_doc_id"
                )

                if manual_doc_id:
                    doc_id = manual_doc_id
                
                custom_prompt = st.text_area(
                    "Custom Prompt:", height=150, key="eval_prompt"
                )
                mode2 = st.selectbox(
                    "Select AI Model:", list(model_key_map.keys()), key="eval_model"
                )

                if st.button("Evaluate", type="primary", key="eval_button"):
                    if not custom_prompt:
                        st.warning("Please enter a prompt.")
                    elif use_rag_eval and (not coll_name or not doc_id):
                        st.error("Select both collection and document for RAG mode.")
                    else:
                        with st.spinner("Evaluating document..."):
                            try:
                                if use_rag_eval:
                                    data = chat_service.evaluate_document(
                                        document_id=doc_id,
                                        collection_name=coll_name,
                                        prompt=custom_prompt,
                                        model_name=model_key_map[mode2],
                                        top_k=5
                                    )
                                    answer = data["response"]
                                    rt_ms = data.get("response_time_ms", 0)
                                    session_id = data["session_id"]
                                else:
                                    response = chat_service.send_message(
                                        query=custom_prompt,
                                        model=model_key_map[mode2],
                                        use_rag=False,
                                        collection_name=None
                                    )
                                    answer = response.response
                                    rt_ms = response.response_time_ms or 0
                                    session_id = response.session_id

                                st.success("Evaluation Complete:")
                                st.markdown(answer)
                                st.caption(f"Response time: {rt_ms/1000:.2f}s")
                                st.caption(f"Session ID: {session_id}")
                            except Exception as e:
                                st.error(f"Request failed: {e}")

            Chat_History(key_prefix="eval_chat_history")

        else:
            st.info("RAG disabled: evaluation will be pure LLM.")

    with doc_upload_tab:
        st.header("Upload Documents for RAG")
        render_upload_component(
            available_collections=collections,
            load_collections_func=lambda: st.session_state.collections,
            create_collection_func=chromadb_service.create_collection,
            upload_endpoint=f"{CHROMADB_API}/documents/upload-and-process",
            job_status_endpoint=f"{CHROMADB_API}/jobs/{{job_id}}",
            key_prefix="eval"
        )
        

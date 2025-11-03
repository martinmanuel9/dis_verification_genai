import streamlit as st
import requests
from PIL import Image
from io import BytesIO
from config.settings import config


def render_reconstructed_document(result: dict):
    md = result["reconstructed_content"]

    # Use centralized config for API endpoint
    CHROMADB_API = config.endpoints.vectordb

    # 1) Show the text first
    with st.expander("Reconstructed Document Text"):
        st.markdown(md, unsafe_allow_html=True)

    # 2) Then, for each image, display inline
    if result.get("images"):
        with st.expander("Inline Images"):
            for i, img in enumerate(result["images"], 1):
                st.subheader(f"Image {i}: {img['filename']}")
                col1, col2 = st.columns([1, 2])

                # left: actual image
                with col1:
                    try:
                        resp = requests.get(f"{CHROMADB_API}/images/{img['filename']}")
                        resp.raise_for_status()
                        image = Image.open(BytesIO(resp.content))
                        st.image(image, caption=img['filename'])
                    except Exception as e:
                        st.write(f"Image preview not available: {e}")

                # right: metadata + description
                with col2:
                    st.write(f"**Storage Path:** `{img['storage_path']}`")
                    st.text_area("Description", img["description"], height=150, key=f"recon_desc_{i}")

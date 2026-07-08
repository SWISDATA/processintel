import streamlit as st


def PNGViewer(png_base64: str, height: int = 600):
    """Display a PNG image in the streamlit app. The image is displayed in the center of the container with a maximum height and width.

    Parameters
    ----------
    png_base64 : str
        base64 encoded PNG image
    height : int, optional
        height of the image container, by default 600
    """
    html = f"""
    <div style="display: flex; justify-content: center; height:{height}px; width:100%;background-color:white;">
    <img src="data:image/png;base64,{png_base64}" alt="png" style="max-width:99%; max-height:98%;object-fit:contain">
    </div>
    """
    st.html(html)

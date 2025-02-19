from setuptools import setup, find_packages

setup(
    name="data_analysis_aibot",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'streamlit',
        'pandas',
        'numpy',
        'python-dotenv',
        'plotly',
        'matplotlib',
        'google-cloud-aiplatform',
        'google-generativeai',
        'SQLAlchemy',
        'pytest',
        'requests'
    ],
) 
import os
import yaml  # Added this import
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def get_llm(config):
    provider = config["llm"]["provider"]
    
    if provider == "openai":
        return ChatOpenAI(
            model_name=config["llm"]["models"]["openai"]["model_name"],
            temperature=config["llm"]["models"]["openai"]["temperature"],
            max_tokens=config["llm"]["models"]["openai"]["max_tokens"]
        )
    elif provider == "groq":
        return ChatGroq(
            model_name=config["llm"]["models"]["groq"]["model_name"],
            temperature=config["llm"]["models"]["groq"]["temperature"],
            max_tokens=config["llm"]["models"]["groq"]["max_tokens"]
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

def get_encoder(config):
    return HuggingFaceEmbeddings(
        model_name=config["encoder"]["model_name"],
        model_kwargs={"device": config["encoder"]["device"]}
    )
    


# config_loader.py

import yaml
from pathlib import Path
from typing import Dict, Any

def load_config(config_path: str = "config.yaml") -> Dict[Any, Any]:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        raise Exception(f"Error loading config: {str(e)}")    
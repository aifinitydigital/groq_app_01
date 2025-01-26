# utils.py

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

def handle_error_response(question: str, chat_history: list, memory_dict: Dict, error_message: str = None):
    """Handle error cases uniformly"""
    if error_message is None:
        error_message = "I apologize, but something went wrong. Please try again later."
        
    chat_history.append({"role": "user", "content": question})
    chat_history.append({"role": "assistant", "content": error_message})
    
    if memory_dict is None:
        memory_dict = {"messages": []}
    if "messages" not in memory_dict:
        memory_dict["messages"] = []
        
    memory_dict["messages"].append({"role": "user", "content": question})
    memory_dict["messages"].append({"role": "assistant", "content": error_message})
    return "", chat_history, memory_dict

def get_conversation_context(memory_dict: Dict) -> str:
    """Get relevant context from chat history"""
    messages = memory_dict.get("messages", [])
    if len(messages) > 4:  # Get last 2 exchanges (4 messages)
        messages = messages[-4:]
    
    context = "\n".join([
        f"{msg['role'].capitalize()}: {msg['content']}"
        for msg in messages
    ])
    return context

def is_simple_context_question(question: str, memory_dict: Dict) -> bool:
    """Determine if this is a simple context question"""
    simple_patterns = [
        "what is my name",
        "who am i",
        "what did i say",
        "what was my previous",
        "what did we discuss",
        "can you repeat",
        "what was the last"
    ]
    
    question_lower = question.lower()
    return any(pattern in question_lower for pattern in simple_patterns)

def get_simple_context_answer(question: str, memory_dict: Dict) -> str:
    """Handle simple context questions without legal analysis"""
    messages = memory_dict.get("messages", [])
    if not messages:
        return "I don't have any previous context to answer this question. Could you please provide more details?"
        
    question_lower = question.lower()
    if "name" in question_lower:
        for msg in messages:
            if msg["role"] == "user" and "I am" in msg["content"]:
                parts = msg["content"].split("I am")
                if len(parts) > 1:
                    name = parts[1].split(",")[0].strip()
                    return f"Your name is {name}."
    
    last_exchange = messages[-2:] if len(messages) >= 2 else messages
    return f"From our previous conversation: {' '.join(msg['content'] for msg in last_exchange)}"
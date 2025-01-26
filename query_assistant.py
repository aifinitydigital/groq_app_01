# query_assistant.py

import logging
import re
from typing import List, Dict, Union
from datetime import datetime
from config_loader import load_config, get_llm, get_encoder
from vector_store import VectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from utils import (
    handle_error_response,
    get_conversation_context,
    is_simple_context_question,
    get_simple_context_answer
)

logger = logging.getLogger(__name__)

class QueryAssistant:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize Query Assistant"""
        try:
            self.config = load_config(config_path)
            # Initialize components
            self.llm = get_llm(self.config)
            self.embedding_function = get_encoder(self.config)

            self.vector_store = VectorStore(
                persist_directory=self.config['vector_db']['persist_directory'],
                distance_strategy=self.config['vector_db']['distance_strategy']
            )
            
            # Create search prompt
            self.search_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a legal research assistant. Extract key legal search phrases from the query.
                Guidelines:
                - Return only the search phrases, one per line
                - Keep phrases short and focused (2-4 words)
                - Focus on legal terms and concepts
                - Do not include explanations
                
                Example Input: "My neighbor threatened to harm my family"
                Example Output:
                criminal intimidation
                threats of harm
                wrongful threats"""),
                ("user", "Extract key legal search phrases from this query: {query}")
            ])
            
            # Create response prompt
            self.response_prompt = ChatPromptTemplate.from_messages([
                ("system", self.config["system_prompt"]),
                ("user", """Use these inputs to provide a targeted response:

                Previous Conversation Context (for reference only):
                {conv_context}

                Document Context:
                {doc_context}
                
                Current Question: {query}
                
                Instructions:
                1. Only analyze the Current Question
                2. Use Previous Conversation for context only
                3. Only cite BNS sections from Document Context
                4. Include Telugu Language translation
                
                Provide:
                1. Legal analysis with BNS Section X citations
                2. Draft petition if needed
                3. Practical next steps
                4. Telugu Language translation of the entire response""")
            ])
            
            logger.info("Query Assistant initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Query Assistant: {str(e)}")
            raise

    def _extract_search_phrases(self, suggestions: str) -> List[str]:
        """Extract key search phrases from LLM suggestions"""
        phrases = []
        for line in suggestions.split('\n'):
            line = line.strip().lower()
            if line and not line.startswith(('here', 'these', 'you can')):
                line = re.sub(r'^[-*•"\']|\s*"$', '', line.strip())
                phrases.append(line)
        
        return list(dict.fromkeys(phrases))  # Remove duplicates while preserving order

    def process_query(self, query: str, chat_history: list, memory: dict) -> tuple:
        """Process query with conversation memory"""
        try:
            if not memory:
                memory = {"session_id": datetime.now().strftime('%Y%m%d_%H%M%S'), "messages": []}
            
            # Handle simple context questions
            if is_simple_context_question(query, memory):
                response = get_simple_context_answer(query, memory)
                chat_history.append({"role": "user", "content": query})
                chat_history.append({"role": "assistant", "content": response})
                memory["messages"].extend([
                    {"role": "user", "content": query},
                    {"role": "assistant", "content": response}
                ])
                return "", chat_history, memory
            
            # Get conversation context
            conv_context = get_conversation_context(memory)
            logger.info(f"Conversation context:\n{conv_context}")
            
            # Generate search phrases
            search_chain = self.search_prompt | self.llm | StrOutputParser()
            search_suggestions = search_chain.invoke({"query": query})
            search_phrases = self._extract_search_phrases(search_suggestions)
            logger.info(f"Search phrases: {search_phrases}")
            
            # Search for each phrase
            all_results = {}
            for phrase in search_phrases:
                results = self.vector_store.search(
                    collection_name="bns_sections",
                    query=phrase,
                    k=self.config['retrieval']['k'],
                    score_threshold=self.config['retrieval']['score_threshold']
                )
                
                for result in results:
                    section_num = result['metadata']['section_num']
                    if section_num not in all_results or result['score'] > all_results[section_num]['score']:
                        all_results[section_num] = result
            
            # Combine and sort results
            combined_results = sorted(
                all_results.values(), 
                key=lambda x: x['score'], 
                reverse=True
            )[:self.config['retrieval']['k']]
            
            # Build context from results
            doc_context = "\n\n".join([
                f"BNS Section {r['metadata']['section_num']}: {r['metadata']['title']}\n{r['content']}"
                for r in combined_results
            ])
            
            # Generate response
            chain = self.response_prompt | self.llm | StrOutputParser()
            response = chain.invoke({
                "query": query,
                "conv_context": conv_context,
                "doc_context": doc_context
            })
            
            # Update chat history and memory
            chat_history.append({"role": "user", "content": query})
            chat_history.append({"role": "assistant", "content": response})
            memory["messages"].extend([
                {"role": "user", "content": query},
                {"role": "assistant", "content": response}
            ])
            
            return "", chat_history, memory
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return handle_error_response(query, chat_history, memory)
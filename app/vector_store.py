# app/vector_store.py
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import json
import os

class VectorStore:
    def __init__(self, db_path: str = "./vector_db"):
        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name="tender_responses",
            metadata={"hnsw:space": "cosine"}
        )
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
    
    def add_response(self, question: str, answer: str, metadata: Dict = None):
        """Add a response to the vector store"""
        if metadata is None:
            metadata = {}
        
        # Create unique ID
        response_id = f"resp_{len(self.collection.get()['ids'])}"
        
        # Combine question and answer for better context
        document = f"Q: {question}\nA: {answer}"
        
        self.collection.add(
            documents=[document],
            metadatas=[{
                "question": question,
                "answer": answer,
                **metadata
            }],
            ids=[response_id]
        )
    
    def add_bulk_responses(self, responses: List[Dict]):
        """Add multiple responses at once"""
        documents = []
        metadatas = []
        ids = []
        
        existing_count = len(self.collection.get()['ids'])
        
        for i, resp in enumerate(responses):
            documents.append(f"Q: {resp['question']}\nA: {resp['answer']}")
            metadatas.append({
                "question": resp['question'],
                "answer": resp['answer'],
                **resp.get('metadata', {})
            })
            ids.append(f"resp_{existing_count + i}")
        
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
    
    def search_similar(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for similar responses"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            similar_responses = []
            if results['metadatas'] and results['metadatas'][0]:
                for metadata in results['metadatas'][0]:
                    similar_responses.append({
                        'question': metadata.get('question', ''),
                        'answer': metadata.get('answer', ''),
                        'content': metadata.get('answer', '')
                    })
            
            return similar_responses
            
        except Exception as e:
            print(f"Error searching similar responses: {e}")
            return []
    
    def get_all_responses(self) -> List[Dict]:
        """Get all stored responses"""
        try:
            results = self.collection.get()
            responses = []
            
            if results['metadatas']:
                for metadata in results['metadatas']:
                    responses.append({
                        'question': metadata.get('question', ''),
                        'answer': metadata.get('answer', '')
                    })
            
            return responses
            
        except Exception as e:
            print(f"Error getting all responses: {e}")
            return []
    
    def clear_all(self):
        """Clear all responses from the vector store"""
        try:
            self.client.delete_collection("tender_responses")
            self.collection = self.client.create_collection("tender_responses")
        except Exception as e:
            print(f"Error clearing vector store: {e}")

#!/usr/bin/env python3
"""
Simple Islamic Heritage RAG System - No TensorFlow dependencies
Uses basic text similarity and simple language models
"""

import os
import json
import glob
import re
from typing import List, Dict, Any
import warnings
warnings.filterwarnings("ignore")

# Basic imports only
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle

# Simple LLM
from transformers import pipeline
import torch

class SimpleIslamicRAG:
    def __init__(self, model_name="distilgpt2"):
        """
        Simple RAG system using TF-IDF for embeddings and basic text generation
        """
        self.model_name = model_name
        self.vectorizer = None
        self.document_vectors = None
        self.documents = []
        self.metadata = []
        self.llm = None
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        print(f"🚀 Initializing Simple Islamic Heritage RAG")
        
    def load_data(self, data_path=None):
        """Load and process data files"""
        print("📖 Loading data...")
        
        if data_path is None:
            data_path = os.path.join(self.base_dir, "data")
        
        if not os.path.exists(data_path):
            raise Exception(f"Data directory '{data_path}' not found. Run verify_setup.py first.")
        
        json_files = glob.glob(f"{data_path}/*.json")
        if not json_files:
            raise Exception(f"No JSON files found in '{data_path}'. Run verify_setup.py first.")
        
        texts = []
        
        for path in json_files:
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # Split text into chunks
                    text = data["text"]
                    chunks = self.split_text(text, chunk_size=500, overlap=50)
                    
                    for chunk in chunks:
                        texts.append(chunk)
                        self.metadata.append({
                            "title": data["title"],
                            "url": data["url"],
                            "source": os.path.basename(path)
                        })
                        
            except Exception as e:
                print(f"⚠️ Error processing {path}: {e}")
        
        self.documents = texts
        print(f"✅ Loaded {len(self.documents)} text chunks")
        
    def split_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Simple text splitting"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
                
        return chunks
        
    def create_embeddings(self):
        """Create TF-IDF embeddings"""
        print("🔧 Creating TF-IDF embeddings...")
        
        if not self.documents:
            raise Exception("No documents loaded. Call load_data() first.")
        
        # Use TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95
        )
        
        self.document_vectors = self.vectorizer.fit_transform(self.documents)
        print("✅ Embeddings created")
        
    def setup_llm(self):
        """Setup simple language model"""
        print(f"🧠 Loading language model: {self.model_name}")
        
        try:
            # Use basic text generation without TensorFlow
            self.llm = pipeline(
                "text-generation",
                model=self.model_name,
                device=-1,  # Force CPU
                max_new_tokens=150,
                temperature=0.7,
                do_sample=True,
                pad_token_id=50256,
                eos_token_id=50256
            )
            print("✅ Language model loaded")
            
        except Exception as e:
            print(f"⚠️ Error loading model: {e}")
            # Create a fallback simple responder
            self.llm = self.create_fallback_llm()
            
    def create_fallback_llm(self):
        """Create a context-aware fallback response system"""
        print("🔄 Creating fallback response system...")
        
        def context_based_responder(prompt):
            """Extract detailed answer from context"""
            # Extract context from prompt (it's formatted as "Context: ... Question: ...")
            if "Context:" in prompt and "Question:" in prompt:
                context_start = prompt.find("Context:") + 8
                question_start = prompt.find("Question:")
                context = prompt[context_start:question_start].strip()
                
                # Split context into sentences and extract more comprehensive answer
                sentences = []
                for sent in context.split('.'):
                    sent = sent.strip()
                    if sent and len(sent) > 10:  # Filter out very short fragments
                        sentences.append(sent)
                
                # Take more sentences for a detailed answer (up to 6-8 sentences or ~500 chars)
                answer_sentences = []
                char_count = 0
                max_chars = 500  # Increased from 250
                
                for sentence in sentences[:8]:  # Take up to 8 sentences instead of 4
                    if sentence:
                        answer_sentences.append(sentence)
                        char_count += len(sentence)
                        if char_count > max_chars:
                            break
                
                if answer_sentences:
                    # Join sentences and ensure proper formatting
                    answer = '. '.join(answer_sentences)
                    if not answer.endswith('.'):
                        answer += '.'
                    return answer
            
            # Fallback if context extraction fails
            return "Based on the available information in the Islamic heritage knowledge base, I can provide context about this topic."
        
        return context_based_responder
        
    def retrieve_documents(self, query: str, k: int = 3) -> List[Dict]:
        """Retrieve relevant documents using TF-IDF similarity"""
        if self.vectorizer is None or self.document_vectors is None:
            raise Exception("Embeddings not created. Call create_embeddings() first.")
        
        # Vectorize query
        query_vector = self.vectorizer.transform([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_vector, self.document_vectors).flatten()
        
        # Get top k documents
        top_indices = similarities.argsort()[-k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.01:  # Minimum similarity threshold
                results.append({
                    "content": self.documents[idx],
                    "metadata": self.metadata[idx],
                    "similarity": similarities[idx]
                })
        
        return results
        
    def generate_answer(self, query: str, context: str) -> str:
        """Generate answer using LLM"""
        prompt = f"""Based on the following information about Islamic heritage, provide a concise and factual answer.

Context: {context}

Question: {query}

Answer:"""
        
        try:
            if callable(self.llm):
                # Fallback responder
                return self.llm(prompt)
            else:
                # Transformers pipeline
                result = self.llm(prompt, max_new_tokens=100, do_sample=True, temperature=0.7)
                generated_text = result[0]['generated_text']
                
                # Extract only the answer part
                answer_start = generated_text.find("Answer:") + 7
                answer = generated_text[answer_start:].strip()
                
                # Clean up the answer
                answer = re.sub(r'\n+', ' ', answer)
                answer = answer.split('.')[0] + '.' if '.' in answer else answer
                
                return answer
                
        except Exception as e:
            return f"Based on the available information about Islamic heritage, I can provide some context about your question regarding {query}."
    
    def query(self, question: str) -> Dict[str, Any]:
        """Query the RAG system"""
        print(f"🔍 Processing query: {question}")
        
        try:
            # Retrieve relevant documents
            relevant_docs = self.retrieve_documents(question, k=3)
            
            if not relevant_docs:
                return {
                    "question": question,
                    "answer": "I don't have specific information about that topic in my knowledge base.",
                    "sources": []
                }
            
            # Combine context from retrieved documents
            context = "\n\n".join([doc["content"] for doc in relevant_docs])
            
            # Generate answer
            answer = self.generate_answer(question, context)
            
            # Format sources
            sources = []
            for doc in relevant_docs:
                sources.append({
                    "title": doc["metadata"]["title"],
                    "url": doc["metadata"]["url"],
                    "excerpt": doc["content"][:200] + "..."
                })
            
            return {
                "question": question,
                "answer": answer,
                "sources": sources
            }
            
        except Exception as e:
            return {
                "question": question,
                "answer": f"I apologize, but I encountered an error: {str(e)}",
                "sources": []
            }
    
    def setup(self):
        """Setup the complete RAG system"""
        print("🌙 Setting up Simple Islamic Heritage RAG...")
        
        try:
            self.load_data()
            self.create_embeddings()
            self.setup_llm()
            
            print("✅ Setup complete! Ready to answer questions.")
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    def save_system(self, path=None):
        """Save the system for faster loading"""
        if path is None:
            path = os.path.join(self.base_dir, "simple_rag_cache")
            
        print(f"💾 Saving system to {path}...")
        
        cache_data = {
            "vectorizer": self.vectorizer,
            "document_vectors": self.document_vectors,
            "documents": self.documents,
            "metadata": self.metadata
        }
        
        os.makedirs(path, exist_ok=True)
        with open(f"{path}/rag_cache.pkl", "wb") as f:
            pickle.dump(cache_data, f)
            
        print("✅ System saved")
    
    def load_system(self, path=None):
        """Load saved system"""
        if path is None:
            path = os.path.join(self.base_dir, "simple_rag_cache")
            
        cache_file = f"{path}/rag_cache.pkl"
        
        if os.path.exists(cache_file):
            print(f"📚 Loading cached system from {path}...")
            
            with open(cache_file, "rb") as f:
                cache_data = pickle.load(f)
            
            self.vectorizer = cache_data["vectorizer"]
            self.document_vectors = cache_data["document_vectors"]
            self.documents = cache_data["documents"]
            self.metadata = cache_data["metadata"]
            
            print("✅ Cached system loaded")
            return True
        
        return False

def test_simple_rag():
    """Test the simple RAG system"""
    print("🧪 Testing Simple RAG System")
    print("=" * 40)
    
    try:
        rag = SimpleIslamicRAG()
        
        # Try to load cached system first
        if not rag.load_system():
            # Setup from scratch
            if not rag.setup():
                return False
            # Save for next time
            rag.save_system()
        else:
            # Still need to setup LLM
            rag.setup_llm()
        
        print("\n✅ System ready! Testing queries...")
        
        test_questions = [
            "What is Islamic architecture?",
            "Tell me about the House of Wisdom",
            "Who was Ibn Khaldun?"
        ]
        
        for question in test_questions:
            print(f"\n🤔 Q: {question}")
            response = rag.query(question)
            print(f"💡 A: {response['answer']}")
            print(f"📚 Sources: {len(response['sources'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_simple_rag()
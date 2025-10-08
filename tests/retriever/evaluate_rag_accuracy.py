import os
import sys
import json
from typing import List, Dict


def load_eval_dataset(file_path: str) -> List[Dict]:
    """Load evaluation dataset from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} evaluation samples")
    return data

def convert_to_ragas_format(data: List[Dict]) -> List[Dict]:
    """Convert ground truth data to RAGAS format"""
    ragas_data = []
    for item in data:
        # Use contexts as the "answer" to make evaluation more realistic
        # This simulates what a retriever would actually return
        context_text = " ".join(item["contexts"]) if isinstance(item["contexts"], list) else str(item["contexts"])
        
        ragas_item = {
            "question": item["question"],
            "answer": context_text[:500] + "..." if len(context_text) > 500 else context_text,  # Truncate long contexts
            "contexts": item["contexts"],
            "ground_truth": item["ground_truth"]
        }
        ragas_data.append(ragas_item)
    return ragas_data

def evaluate_semantic_similarity(eval_data: List[Dict]) -> Dict:
    """Evaluate semantic similarity using RAGAS with agentic retrieval flow"""
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import answer_similarity
        from langchain_ollama import OllamaEmbeddings, ChatOllama
        from config.config import Config
        from agents.tools.reranker import RerankerTool
        from retriever.retriever import Retriever
        
        print("Converting data to RAGAS format...")
        ragas_data = convert_to_ragas_format(eval_data)
        
        # Setup tools
        retriever = Retriever()
        reranker_tool = RerankerTool()
        
        # Process each question through the agentic flow
        processed_answers = []
        
        for i, item in enumerate(ragas_data, 1):
            question = item["question"]
            print(f"Processing question {i}/{len(ragas_data)}: {question[:50]}...")
            
            try:
                # Step 1: Retrieve documents
                retrieved_docs = retriever.search(question)
                
                # Step 2: Re-rank documents (this is what happens in the actual flow)
                reranked_docs = reranker_tool._run(retrieved_docs)
                
                # Extract content from re-ranked result
                answer_content = reranked_docs
                
                processed_answers.append(answer_content)
                
            except Exception as e:
                print(f"Error processing question {i}: {e}")
                processed_answers.append("Error retrieving documents")
        
        # Convert to datasets format with processed answers
        dataset_dict = {
            "question": [item["question"] for item in ragas_data],
            "contexts": [item["contexts"] for item in ragas_data],
            "answer": processed_answers,
            "ground_truth": [item["ground_truth"] for item in ragas_data]
        }
        
        print("Creating RAGAS dataset...")
        dataset = Dataset.from_dict(dataset_dict)
        
        # Setup Ollama models
        print("Setting up Ollama models...")
        embeddings = OllamaEmbeddings(
            model=Config.EMBEDDING_MODEL_NAME,
            base_url=Config.OLLAMA_BASE_URL
        )
        
        llm = ChatOllama(
            model=Config.LLM_MODEL_NAME,
            base_url=Config.OLLAMA_BASE_URL
        )
        
        print("Running semantic evaluation...")
        results = evaluate(
            dataset, 
            metrics=[answer_similarity],
            llm=llm,
            embeddings=embeddings
        )
        
        # Extract detailed results from EvaluationResult object
        answer_sim_score = 0.0
        individual_scores = []
        
        if hasattr(results, 'answer_similarity'):
            answer_sim_score = results.answer_similarity
        elif hasattr(results, 'to_pandas'):
            # Try to get from pandas dataframe
            df = results.to_pandas()
            if 'answer_similarity' in df.columns:
                answer_sim_score = df['answer_similarity'].mean()
                individual_scores = df['answer_similarity'].tolist()
        
        # Calculate additional statistics
        total_samples = len(eval_data)
        high_similarity = sum(1 for score in individual_scores if score >= 0.8) if individual_scores else 0
        medium_similarity = sum(1 for score in individual_scores if 0.5 <= score < 0.8) if individual_scores else 0
        low_similarity = sum(1 for score in individual_scores if score < 0.5) if individual_scores else 0
        
        return {
            "answer_similarity": answer_sim_score,
            "total_samples": total_samples,
            "individual_scores": individual_scores,
            "high_similarity_count": high_similarity,
            "medium_similarity_count": medium_similarity,
            "low_similarity_count": low_similarity,
            "high_similarity_percentage": (high_similarity / total_samples * 100) if total_samples > 0 else 0,
            "medium_similarity_percentage": (medium_similarity / total_samples * 100) if total_samples > 0 else 0,
            "low_similarity_percentage": (low_similarity / total_samples * 100) if total_samples > 0 else 0
        }
        
    except ImportError as e:
        print(f"Missing dependencies: {e}")
        print("Install with: pip install ragas datasets langchain-ollama")
        return {"error": "Dependencies not available"}
    except Exception as e:
        print(f"Evaluation failed: {e}")
        return {"error": str(e)}

def run_semantic_evaluation():
    """Run semantic evaluation using RAGAS"""
    try:
        # Load evaluation dataset
        eval_data = load_eval_dataset(os.path.join(os.path.dirname(__file__), "ragas_ground_truth.json"))
        
        # Run semantic evaluation
        print("Starting semantic evaluation...")
        results = evaluate_semantic_similarity(eval_data)
        
        if "error" in results:
            print(f"Error: {results['error']}")
            return results
        
        print(f"\nAGENTIC SEMANTIC EVALUATION RESULTS:")
        print("=" * 50)
        print(f"Overall Answer Similarity: {results['answer_similarity']:.3f}")
        print(f"Total Samples Evaluated: {results['total_samples']}")
        print(f"\nSimilarity Distribution:")
        print(f"  High Similarity (>=0.800): {results['high_similarity_count']} ({results['high_similarity_percentage']:.1f}%)")
        print(f"  Medium Similarity (0.500-0.799): {results['medium_similarity_count']} ({results['medium_similarity_percentage']:.1f}%)")
        print(f"  Low Similarity (<0.500): {results['low_similarity_count']} ({results['low_similarity_percentage']:.1f}%)")
        
        if results['individual_scores']:
            print(f"\nIndividual Scores:")
            for i, score in enumerate(results['individual_scores'], 1):
                print(f"  Question {i}: {score:.3f}")
        
        print("=" * 50)
        
        return results
        
    except Exception as e:
        print(f"Semantic evaluation failed: {e}")
        raise

if __name__ == "__main__":
    run_semantic_evaluation()

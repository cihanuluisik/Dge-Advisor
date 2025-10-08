import os
import sys
import json
import logging
from typing import List, Dict

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

logging.basicConfig(level=logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


def load_conversational_dataset(file_path: str) -> List[Dict]:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} conversational test cases")
    return data

def evaluate_conversational_flow(conversational_data: List[Dict]) -> Dict:
    """Evaluate conversational flow using existing tools"""
    try:
        from agents.tools.reranker import RerankerTool
        from agents.tools.conversation import ConversationTool
        from retriever.retriever import Retriever
        
        print("Setting up tools for conversational testing...")
        retriever = Retriever()
        reranker_tool = RerankerTool()
        conversation_tool = ConversationTool(chat_id="test_conversational_eval")
        
        all_results = []
        
        for conv_idx, conversation in enumerate(conversational_data, 1):
            print(f"\nProcessing conversation {conv_idx}/{len(conversational_data)}: {conversation['conversation_id']}")
            
            conversation_results = []
            
            for turn in conversation['turns']:
                turn_num = turn['turn']
                question = turn['question']
                ground_truth = turn['ground_truth']
                
                print(f"  Turn {turn_num}: {question[:50]}...")
                
                try:
                    # Step 1: Store user message and get chat context
                    chat_context = conversation_tool._run(message=question)
                    
                    # Step 2: Retrieve documents using chat context
                    retrieved_docs = retriever.search(chat_context)
                    
                    # Step 3: Re-rank documents
                    reranked_docs = reranker_tool._run(documents=retrieved_docs)
                    
                    # Use re-ranked content as "answer"
                    answer = reranked_docs
                    
                    # Simple similarity check
                    answer_lower = answer.lower()
                    ground_truth_lower = ground_truth.lower()
                    
                    # Check if key terms from ground truth appear in answer
                    ground_truth_words = set(ground_truth_lower.split())
                    answer_words = set(answer_lower.split())
                    common_words = ground_truth_words.intersection(answer_words)
                    
                    similarity_score = len(common_words) / len(ground_truth_words) if ground_truth_words else 0
                    
                    turn_result = {
                        "turn": turn_num,
                        "question": question,
                        "answer": answer[:200] + "..." if len(answer) > 200 else answer,
                        "ground_truth": ground_truth,
                        "similarity_score": similarity_score,
                        "common_words": len(common_words),
                        "total_words": len(ground_truth_words)
                    }
                    
                    conversation_results.append(turn_result)
                    print(f"    Similarity: {similarity_score:.3f} ({len(common_words)}/{len(ground_truth_words)} words)")
                    
                except Exception as e:
                    print(f"    Error in turn {turn_num}: {e}")
                    conversation_results.append({
                        "turn": turn_num,
                        "question": question,
                        "answer": f"Error: {e}",
                        "ground_truth": ground_truth,
                        "similarity_score": 0.0,
                        "common_words": 0,
                        "total_words": len(ground_truth.split())
                    })
            
            all_results.append({
                "conversation_id": conversation['conversation_id'],
                "turns": conversation_results
            })
        
        # Calculate overall statistics
        all_scores = []
        for conv in all_results:
            for turn in conv['turns']:
                all_scores.append(turn['similarity_score'])
        
        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
        high_similarity = sum(1 for score in all_scores if score >= 0.7)
        medium_similarity = sum(1 for score in all_scores if 0.4 <= score < 0.7)
        low_similarity = sum(1 for score in all_scores if score < 0.4)
        
        return {
            "average_similarity": avg_score,
            "total_turns": len(all_scores),
            "high_similarity_count": high_similarity,
            "medium_similarity_count": medium_similarity,
            "low_similarity_count": low_similarity,
            "high_similarity_percentage": (high_similarity / len(all_scores) * 100) if all_scores else 0,
            "medium_similarity_percentage": (medium_similarity / len(all_scores) * 100) if all_scores else 0,
            "low_similarity_percentage": (low_similarity / len(all_scores) * 100) if all_scores else 0,
            "conversation_results": all_results
        }
        
    except Exception as e:
        print(f"Conversational evaluation failed: {e}")
        return {"error": str(e)}

def run_conversational_evaluation():
    """Run conversational evaluation using agentic tools"""
    try:
        # Load conversational test cases
        conversational_data = load_conversational_dataset(os.path.join(os.path.dirname(__file__), "conversational_test_cases.json"))
        
        # Run conversational evaluation
        print("Starting conversational evaluation...")
        results = evaluate_conversational_flow(conversational_data)
        
        if "error" in results:
            print(f"Error: {results['error']}")
            return results
        
        print(f"\nCONVERSATIONAL EVALUATION RESULTS:")
        print("=" * 50)
        print(f"Average Similarity: {results['average_similarity']:.3f}")
        print(f"Total Turns Evaluated: {results['total_turns']}")
        print(f"\nSimilarity Distribution:")
        print(f"  High Similarity (>=0.700): {results['high_similarity_count']} ({results['high_similarity_percentage']:.1f}%)")
        print(f"  Medium Similarity (0.400-0.699): {results['medium_similarity_count']} ({results['medium_similarity_percentage']:.1f}%)")
        print(f"  Low Similarity (<0.400): {results['low_similarity_count']} ({results['low_similarity_percentage']:.1f}%)")
        
        print(f"\nConversation Details:")
        for conv in results['conversation_results']:
            print(f"\n{conv['conversation_id']}:")
            for turn in conv['turns']:
                print(f"  Turn {turn['turn']}: {turn['similarity_score']:.3f} - {turn['question'][:40]}...")
        
        print("=" * 50)
        
        return results
        
    except Exception as e:
        print(f"Conversational evaluation failed: {e}")
        raise

if __name__ == "__main__":
    run_conversational_evaluation()

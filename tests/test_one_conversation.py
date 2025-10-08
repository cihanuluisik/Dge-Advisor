import os, sys, pytest
from typing import Dict

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.tools.reranker import RerankerTool
from agents.tools.conversation import ConversationTool
from retriever.retriever import Retriever

class TestOneConversation:
    
    def test_full_conversation_flow(self):
        test_data = self._load_test_conversation()
        
        retriever = Retriever()
        reranker = RerankerTool()
        conversation = ConversationTool(chat_id="test_chat")
        
        conversation_results = []
        
        for turn in test_data['turns']:
            turn_num = turn['turn']
            question = turn['question']
            ground_truth = turn['ground_truth']
            
            chat_context = conversation._run(chat_id="test_chat", message=question)
            retrieved_docs = retriever.search(chat_context)
            reranked_docs = reranker._run(documents=retrieved_docs)
            similarity_score = self._calculate_similarity(reranked_docs, ground_truth)
            
            turn_result = {
                "turn": turn_num,
                "question": question,
                "answer": reranked_docs[:200] + "..." if len(reranked_docs) > 200 else reranked_docs,
                "ground_truth": ground_truth,
                "similarity_score": similarity_score
            }
            
            conversation_results.append(turn_result)
            assert similarity_score >= 0.1, f"Turn {turn_num} similarity too low: {similarity_score}"
        
        assert len(conversation_results) == len(test_data['turns'])
        avg_similarity = sum(turn['similarity_score'] for turn in conversation_results) / len(conversation_results)
        assert avg_similarity >= 0.15, f"Average similarity too low: {avg_similarity}"
        
        print(f"Conversation test completed - Average similarity: {avg_similarity:.3f}, Turns: {len(conversation_results)}")
        return conversation_results
    
    def _load_test_conversation(self) -> Dict:
        return {
            "conversation_id": "test_conversation_001",
            "turns": [
                {
                    "turn": 1,
                    "question": "What are the procurement policies for IT equipment?",
                    "ground_truth": "IT equipment procurement follows standard procedures with approval requirements and vendor selection criteria."
                },
                {
                    "turn": 2,
                    "question": "What is the approval process for purchases over $10,000?",
                    "ground_truth": "Purchases over $10,000 require management approval and competitive bidding process."
                },
                {
                    "turn": 3,
                    "question": "Who can approve these purchases?",
                    "ground_truth": "Department managers and procurement officers can approve purchases based on their authority limits."
                }
            ]
        }
    
    def _calculate_similarity(self, answer: str, ground_truth: str) -> float:
        answer_words = set(answer.lower().split())
        ground_truth_words = set(ground_truth.lower().split())
        if not ground_truth_words:
            return 0.0
        common_words = answer_words.intersection(ground_truth_words)
        return len(common_words) / len(ground_truth_words)

if __name__ == "__main__":
    print("Running conversation test...")
    test_instance = TestOneConversation()
    test_instance.test_full_conversation_flow()
    print("Test completed")
